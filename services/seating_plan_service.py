# services/seating_plan_service.py

from typing import List, Dict, Tuple, Optional
from services.db import fetch_all, execute
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class SeatingPlanGenerator:
    """Oturma planı oluşturucu"""
    
    def __init__(self, exam_id: int):
        self.exam_id = exam_id
        self.exam_info = None
        self.classrooms = []
        self.students = []
        self.seating_plan = {}  # {classroom_id: [(student_id, row, col), ...]}
        
    def load_exam_data(self) -> bool:
        """Sınav bilgilerini yükle"""
        exam_data = fetch_all("""
            SELECT e.id, e.exam_date, e.start_time, e.end_time,
                   c.code, c.name, c.grade, c.instructor,
                   es.name as schedule_name, es.exam_type
            FROM exams e
            JOIN courses c ON e.course_id = c.id
            JOIN exam_schedules es ON e.schedule_id = es.id
            WHERE e.id = %s
        """, [self.exam_id])
        
        if not exam_data:
            return False
        
        self.exam_info = exam_data[0]

        self.classrooms = fetch_all("""
            SELECT cl.id, cl.code, cl.name, cl.capacity, cl."rows", cl.cols, cl.seat_group
            FROM exam_classrooms ec
            JOIN classrooms cl ON ec.classroom_id = cl.id
            WHERE ec.exam_id = %s
            ORDER BY cl.capacity DESC
        """, [self.exam_id])

        try:
            self.students = fetch_all("""
                SELECT DISTINCT s.id, s.number, s.fullname, s.grade
                FROM students s
                JOIN enrollments en ON s.id = en.student_id
                JOIN courses c ON en.course_id = c.id
                JOIN exams e ON c.id = e.course_id
                WHERE e.id = %s AND en.status = 'ACTIVE'
                ORDER BY s.grade, s.number
            """, [self.exam_id])
        except Exception:
            self.students = fetch_all("""
                SELECT DISTINCT s.id, s.number, s.fullname, s.grade
                FROM students s
                JOIN enrollments en ON s.id = en.student_id
                JOIN courses c ON en.course_id = c.id
                JOIN exams e ON c.id = e.course_id
                WHERE e.id = %s
                ORDER BY s.grade, s.number
            """, [self.exam_id])
        
        return True
    
    def generate_seating_plan(self) -> Tuple[bool, str]:
        if not self.classrooms:
            return (False, "Sinav icin derslik atanmamis!")
        
        if not self.students:
            return (False, "Sinava kayitli ogrenci bulunamadi!")
        
        def get_seat_group_value(seat_group_str):
            """Sıra yapısını sayısal değere çevir"""
            seat_group_str = str(seat_group_str).upper()
            if 'DOUBLE' in seat_group_str or seat_group_str == '2':
                return 2
            elif 'TRIPLE' in seat_group_str or seat_group_str == '3':
                return 3
            elif 'QUAD' in seat_group_str or seat_group_str == '4':
                return 4
            return 3  # Varsayılan
        
        def calculate_classroom_capacity(rows, cols, seat_group_str):
            seat_group_val = get_seat_group_value(seat_group_str)
            groups_per_col = rows // seat_group_val
            return groups_per_col * cols * 2

        total_capacity = sum(
            calculate_classroom_capacity(cl['rows'], cl['cols'], cl['seat_group'])
            for cl in self.classrooms
        )
        
        if len(self.students) > total_capacity:
            return (False, f"Toplam derslik kapasitesi yetersiz! "
                         f"Ogrenci: {len(self.students)}, Kapasite: {total_capacity}")

        classroom_info = []
        for classroom in self.classrooms:
            classroom_id = classroom['id']
            rows = classroom['rows']
            cols = classroom['cols']
            seat_group_str = classroom['seat_group']
            seat_group_val = get_seat_group_value(seat_group_str)
            groups_per_col = rows // seat_group_val
            capacity = groups_per_col * cols * 2
            
            classroom_info.append({
                'id': classroom_id,
                'rows': rows,
                'cols': cols,
                'seat_group_val': seat_group_val,
                'groups_per_col': groups_per_col,
                'capacity': capacity,
                'current_col': 0,
                'current_group': 0,
                'position_in_group': 0
            })
            self.seating_plan[classroom_id] = []

        classroom_idx = 0
        total_classrooms = len(classroom_info)
        
        for student_index, student in enumerate(self.students):
            if total_classrooms == 0:
                break

            current_classroom = classroom_info[classroom_idx]
            classroom_id = current_classroom['id']
            seat_group_val = current_classroom['seat_group_val']

            col = current_classroom['current_col']
            group = current_classroom['current_group']
            position = current_classroom['position_in_group']

            row_start = group * seat_group_val + 1
            
            if position == 0:
                row = row_start
            else:
                row = row_start + (seat_group_val - 1)

            self.seating_plan[classroom_id].append({
                'student_id': student['id'],
                'student_number': student['number'],
                'student_name': student['fullname'],
                'row': row,
                'col': col + 1
            })

            current_classroom['position_in_group'] += 1

            if current_classroom['position_in_group'] >= 2:
                current_classroom['position_in_group'] = 0
                current_classroom['current_group'] += 1

                if current_classroom['current_group'] >= current_classroom['groups_per_col']:
                    current_classroom['current_group'] = 0
                    current_classroom['current_col'] += 1

            classroom_idx = (classroom_idx + 1) % total_classrooms
        
        return (True, "")
    
    def save_to_database(self) -> bool:
        """Oturma planını veritabanına kaydet"""
        try:
            execute("DELETE FROM seating_plans WHERE exam_id = %s", [self.exam_id])

            for classroom_id, seats in self.seating_plan.items():
                for seat in seats:
                    seat_position = 1
                    
                    execute("""
                        INSERT INTO seating_plans 
                        (exam_id, student_id, classroom_id, row_number, col_number, seat_position)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [
                        self.exam_id,
                        seat['student_id'],
                        classroom_id,
                        seat['row'],
                        seat['col'],
                        seat_position
                    ])
            
            return True
        except Exception as e:
            return False
    
    def generate_pdf(self, output_path: str) -> str:
        try:
            font_path = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'DejaVuSans.ttf')
            if not os.path.exists(font_path):
                import platform
                if platform.system() == 'Windows':
                    font_path = 'C:\\Windows\\Fonts\\arial.ttf'
                else:
                    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                default_font = 'CustomFont'
            else:
                default_font = 'Helvetica'
        except:
            default_font = 'Helvetica'
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=default_font
        )

        title_text = f"OTURMA PLANI<br/>{self.exam_info['code']} - {self.exam_info['name']}"
        elements.append(Paragraph(title_text, title_style))

        info_text = f"Tarih: {self.exam_info['exam_date']} | " \
                   f"Saat: {self.exam_info['start_time']} - {self.exam_info['end_time']} | " \
                   f"Sinif: {self.exam_info['grade']} | " \
                   f"Tur: {self.exam_info['exam_type']}"
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName=default_font
        )
        elements.append(Paragraph(info_text, info_style))
        elements.append(Spacer(1, 0.5*cm))

        for classroom_id, seats in self.seating_plan.items():
            if not seats:
                continue

            classroom = next((cl for cl in self.classrooms if cl['id'] == classroom_id), None)
            if not classroom:
                continue

            rows = classroom['rows']
            cols = classroom['cols']
            seat_group_str = str(classroom.get('seat_group', 'TRIPLE')).upper()
            
            classroom_title = f"DERSLIK: {classroom['code']} - {classroom['name']}"
            elements.append(Paragraph(classroom_title, styles['Heading2']))

            if 'DOUBLE' in seat_group_str or seat_group_str == '2':
                seat_group_val = 2
            elif 'TRIPLE' in seat_group_str or seat_group_str == '3':
                seat_group_val = 3
            elif 'QUAD' in seat_group_str or seat_group_str == '4':
                seat_group_val = 4
            else:
                seat_group_val = 3

            detail_text = f"Kapasite: {classroom['capacity']} | " \
                         f"Ogrenci: {len(seats)} | " \
                         f"Boyut: {rows} x {cols} | " \
                         f"Sira Yapisi: {seat_group_val}'lu"
            detail_style = ParagraphStyle(
                'Detail',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#555555'),
                spaceAfter=10,
                fontName=default_font
            )
            elements.append(Paragraph(detail_text, detail_style))
            elements.append(Spacer(1, 0.2*cm))

            seat_matrix = {}
            for seat in seats:
                key = (seat['row'], seat['col'])
                seat_matrix[key] = seat

            table_data = []

            header_row = ['']
            for col in range(1, cols + 1):
                header_row.append(f'Sütun {col}')
            table_data.append(header_row)
            
            for row in range(1, rows + 1):
                if (row - 1) > 0 and (row - 1) % seat_group_val == 0:
                    corridor_row = ['KORİDOR'] + ['═ KORİDOR ═'] * cols
                    table_data.append(corridor_row)

                row_data = [f'Satır {row}']
                for col in range(1, cols + 1):
                    seat_key = (row, col)
                    if seat_key in seat_matrix:
                        seat = seat_matrix[seat_key]
                        cell_text = f"{seat['student_number']}\n{seat['student_name'][:12]}"
                        row_data.append(cell_text)
                    else:
                        row_data.append('BOŞ')
                
                table_data.append(row_data)

            available_width = 26 * cm
            row_num_width = 2 * cm
            remaining_width = available_width - row_num_width
            cell_width = remaining_width / cols if cols > 0 else 3*cm

            col_widths = [row_num_width] + [cell_width] * cols
            table = Table(table_data, colWidths=col_widths)

            table_style = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), default_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.lightgrey])
            ]

            table_style.append(('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')))
            table_style.append(('TEXTCOLOR', (0, 0), (-1, 0), colors.white))
            table_style.append(('FONTSIZE', (0, 0), (-1, 0), 9))

            for i in range(1, len(table_data)):
                if table_data[i][0] not in ['KORİDOR', '']:
                    table_style.append(('BACKGROUND', (0, i), (0, i), colors.HexColor('#3498db')))
                    table_style.append(('TEXTCOLOR', (0, i), (0, i), colors.white))
                    table_style.append(('FONTSIZE', (0, i), (0, i), 9))

            for i, row in enumerate(table_data):
                if row and row[0] == 'KORİDOR':
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f39c12')))
                    table_style.append(('TEXTCOLOR', (0, i), (-1, i), colors.white))
                    table_style.append(('FONTNAME', (0, i), (-1, i), default_font))
                    table_style.append(('FONTSIZE', (0, i), (-1, i), 10))
                else:
                    for j, cell in enumerate(row):
                        if j > 0 and cell != 'BOŞ' and cell != '═ KORİDOR ═' and not cell.startswith('Sütun'):
                            table_style.append(('BACKGROUND', (j, i), (j, i), colors.HexColor('#27ae60')))
                            table_style.append(('TEXTCOLOR', (j, i), (j, i), colors.white))
            
            table.setStyle(TableStyle(table_style))
            
            elements.append(table)
            elements.append(PageBreak())

        doc.build(elements)
        return output_path


def generate_seating_plan_for_exam(exam_id: int) -> Tuple[bool, Optional[str], Dict]:

    generator = SeatingPlanGenerator(exam_id)

    if not generator.load_exam_data():
        return (False, "Sinav bilgileri yuklenemedi!", {})

    success, error_msg = generator.generate_seating_plan()
    if not success:
        return (False, error_msg, {})

    if not generator.save_to_database():
        return (False, "Oturma plani kaydedilemedi!", {})

    result = {
        'exam_info': generator.exam_info,
        'classrooms': generator.classrooms,
        'students': generator.students,
        'seating_plan': generator.seating_plan
    }
    
    return (True, None, result)


def export_seating_plan_to_pdf(exam_id: int, output_path: str) -> Tuple[bool, Optional[str]]:

    seating_data = fetch_all("""
        SELECT sp.*, s.number as student_number, s.fullname as student_name,
               cl.code as classroom_code, cl.name as classroom_name, 
               cl.capacity, cl."rows", cl.cols
        FROM seating_plans sp
        JOIN students s ON sp.student_id = s.id
        JOIN classrooms cl ON sp.classroom_id = cl.id
        WHERE sp.exam_id = %s
        ORDER BY cl.code, sp.row_number, sp.col_number
    """, [exam_id])
    
    if not seating_data:
        return (False, "Oturma plani bulunamadi! Lutfen once oturma plani olusturun.")

    generator = SeatingPlanGenerator(exam_id)
    if not generator.load_exam_data():
        return (False, "Sinav bilgileri yuklenemedi!")

    for row in seating_data:
        classroom_id = row['classroom_id']
        if classroom_id not in generator.seating_plan:
            generator.seating_plan[classroom_id] = []
        
        generator.seating_plan[classroom_id].append({
            'student_id': row['student_id'],
            'student_number': row['student_number'],
            'student_name': row['student_name'],
            'row': row['row_number'],
            'col': row['col_number']
        })
    
    try:
        pdf_path = generator.generate_pdf(output_path)
        return (True, None)
    except Exception as e:
        return (False, f"PDF olusturma hatasi: {e}")

