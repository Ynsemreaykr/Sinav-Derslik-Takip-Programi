#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sınav Programı Excel Export Servisi
"""

import pandas as pd
from datetime import datetime
from typing import Optional, List
from services.db import fetch_all
import os

class ExamExportService:
    """Sınav programlarını Excel'e aktarma servisi"""
    
    def __init__(self):
        pass
    
    def export_exam_schedule_to_excel(self, schedule_id: int, output_path: Optional[str] = None) -> str:
        """
        Sınav programını Excel formatında export eder.
        
        Args:
            schedule_id: Export edilecek program ID
            output_path: Kaydedilecek dosya yolu (None ise otomatik oluşturulur)
            
        Returns:
            str: Oluşturulan dosya yolu
        """
        print(f"\n[EXCEL EXPORT] Schedule ID: {schedule_id}")
        
        # 1. Program bilgilerini al
        schedule = fetch_all("""
            SELECT es.*, d.name as department_name
            FROM exam_schedules es
            JOIN departments d ON es.department_id = d.id
            WHERE es.id = %s
        """, [schedule_id])
        
        if not schedule:
            raise ValueError(f"Schedule ID {schedule_id} bulunamadi!")
        
        schedule = schedule[0]
        print(f"   Program: {schedule['name']} ({schedule['exam_type']})")
        
        # 2. Sınavları al
        exams = fetch_all("""
            SELECT 
                e.id,
                e.exam_date,
                e.start_time,
                e.end_time,
                e.duration,
                e.student_count,
                c.code as course_code,
                c.name as course_name,
                c.instructor,
                c.grade,
                c.is_elective,
                cl.code as classroom_code,
                cl.name as classroom_name,
                cl.capacity as classroom_capacity
            FROM exams e
            JOIN courses c ON e.course_id = c.id
            LEFT JOIN exam_classrooms ec ON e.id = ec.exam_id
            LEFT JOIN classrooms cl ON ec.classroom_id = cl.id
            WHERE e.schedule_id = %s
            ORDER BY e.exam_date, e.start_time, c.code
        """, [schedule_id])
        
        if not exams:
            raise ValueError("Bu programa ait sinav bulunamadi!")
        
        print(f"   Toplam {len(exams)} sinav bulundu")
        
        # 3. Excel için veri hazırla
        excel_data = []
        
        for exam in exams:
            # Tarih formatla
            exam_date = exam['exam_date'].strftime('%d.%m.%Y') if hasattr(exam['exam_date'], 'strftime') else str(exam['exam_date'])
            exam_day = self._get_day_name(exam['exam_date'])
            
            # Saat formatla
            start_time = exam['start_time'].strftime('%H:%M') if hasattr(exam['start_time'], 'strftime') else str(exam['start_time'])
            end_time = exam['end_time'].strftime('%H:%M') if hasattr(exam['end_time'], 'strftime') else str(exam['end_time'])
            
            # Ders türü
            course_type = "Seçmeli" if exam['is_elective'] else "Zorunlu"
            
            excel_data.append({
                'Tarih': exam_date,
                'Gün': exam_day,
                'Saat': f"{start_time} - {end_time}",
                'Süre (dk)': exam['duration'],
                'Ders Kodu': exam['course_code'],
                'Ders Adı': exam['course_name'],
                'Öğretim Üyesi': exam['instructor'] or '',
                'Sınıf': exam['grade'],
                'Tür': course_type,
                'Öğrenci Sayısı': exam['student_count'],
                'Derslik': exam['classroom_name'] or 'Atanmadı',
                'Kapasite': exam['classroom_capacity'] or 0
            })
        
        # 4. DataFrame oluştur
        df = pd.DataFrame(excel_data)
        
        # 5. Dosya yolu belirle
        if not output_path:
            # Otomatik dosya adı oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = schedule['name'].replace(' ', '_').replace('/', '-')
            filename = f"{safe_name}_{schedule['exam_type']}_{timestamp}.xlsx"
            output_path = os.path.join(os.getcwd(), filename)
        
        # 6. Excel'e yaz
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Ana sayfa - Program detayları
            df.to_excel(writer, sheet_name='Sinav Programi', index=False)
            
            # Bilgi sayfası
            info_data = {
                'Bilgi': [
                    'Program Adı',
                    'Sınav Türü',
                    'Bölüm',
                    'Başlangıç Tarihi',
                    'Bitiş Tarihi',
                    'Toplam Sınav',
                    'Oluşturulma Tarihi'
                ],
                'Değer': [
                    schedule['name'],
                    schedule['exam_type'],
                    schedule['department_name'],
                    str(schedule['start_date']),
                    str(schedule['end_date']),
                    len(exams),
                    schedule['created_at'].strftime('%d.%m.%Y %H:%M') if hasattr(schedule['created_at'], 'strftime') else str(schedule['created_at'])
                ]
            }
            
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(writer, sheet_name='Program Bilgileri', index=False)
            
            # Gün bazlı sayfa
            df_by_date = df.groupby('Tarih').size().reset_index(name='Sınav Sayısı')
            df_by_date.to_excel(writer, sheet_name='Gun Bazli Ozet', index=False)
            
            # Sınıf bazlı sayfa
            df_by_grade = df.groupby('Sınıf').size().reset_index(name='Sınav Sayısı')
            df_by_grade.to_excel(writer, sheet_name='Sinif Bazli Ozet', index=False)
            
            # Derslik bazlı sayfa
            df_by_classroom = df.groupby('Derslik').size().reset_index(name='Sınav Sayısı')
            df_by_classroom.to_excel(writer, sheet_name='Derslik Bazli Ozet', index=False)
        
        print(f"   Excel dosyasi olusturuldu: {output_path}")
        
        # 7. Excel formatting (opsiyonel - güzel görünüm için)
        self._format_excel(output_path)
        
        return output_path
    
    def _get_day_name(self, date_obj) -> str:
        """Tarihten gün adını al"""
        if hasattr(date_obj, 'weekday'):
            days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            return days[date_obj.weekday()]
        return ''
    
    def _format_excel(self, file_path: str):
        """Excel dosyasını formatla (güzel görünüm için)"""
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            
            wb = load_workbook(file_path)
            
            # Ana sayfa formatla
            if 'Sinav Programi' in wb.sheetnames:
                ws = wb['Sinav Programi']
                
                # Başlık satırı
                header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                header_font = Font(bold=True, color='FFFFFF', size=11)
                
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Kenarlıklar
                thin_border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                
                for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                    for cell in row:
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Sütun genişlikleri
                ws.column_dimensions['A'].width = 12  # Tarih
                ws.column_dimensions['B'].width = 12  # Gün
                ws.column_dimensions['C'].width = 15  # Saat
                ws.column_dimensions['D'].width = 10  # Süre
                ws.column_dimensions['E'].width = 12  # Ders Kodu
                ws.column_dimensions['F'].width = 35  # Ders Adı
                ws.column_dimensions['G'].width = 25  # Öğretim Üyesi
                ws.column_dimensions['H'].width = 8   # Sınıf
                ws.column_dimensions['I'].width = 10  # Tür
                ws.column_dimensions['J'].width = 12  # Öğrenci Sayısı
                ws.column_dimensions['K'].width = 15  # Derslik
                ws.column_dimensions['L'].width = 10  # Kapasite
            
            wb.save(file_path)
            print(f"   Excel formatlama tamamlandi")
            
        except Exception as e:
            print(f"   Formatlama hatasi (dosya yine de kullanilabilir): {e}")
    
    def export_all_schedules(self, department_id: int, output_dir: Optional[str] = None) -> List[str]:
        """
        Bir bölümün tüm sınav programlarını export eder.
        
        Args:
            department_id: Bölüm ID
            output_dir: Çıktı dizini
            
        Returns:
            List[str]: Oluşturulan dosya yolları
        """
        schedules = fetch_all("""
            SELECT id, name FROM exam_schedules 
            WHERE department_id = %s 
            ORDER BY created_at DESC
        """, [department_id])
        
        exported_files = []
        
        for schedule in schedules:
            try:
                file_path = self.export_exam_schedule_to_excel(
                    schedule['id'],
                    output_path=os.path.join(output_dir, f"{schedule['name']}.xlsx") if output_dir else None
                )
                exported_files.append(file_path)
            except Exception as e:
                print(f"Export hatasi ({schedule['name']}): {e}")
        
        return exported_files


# Global instance
exam_export_service = ExamExportService()

