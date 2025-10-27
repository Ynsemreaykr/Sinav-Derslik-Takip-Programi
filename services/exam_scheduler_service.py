from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
from services.db import fetch_all, execute
import json

class ExamScheduler:
    """Sınav programı oluşturucu"""
    
    def __init__(self, department_id: int, constraints: dict):
        self.department_id = department_id
        self.constraints = constraints
        self.errors = []
        self.warnings = []
        
    def validate_constraints(self) -> bool:
        """Kısıtları doğrula"""
        start_date = datetime.strptime(self.constraints['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.constraints['end_date'], '%Y-%m-%d').date()
        
        if start_date >= end_date:
            self.errors.append("Baslangic tarihi bitis tarihinden once olmalidir!")
            return False

        if not self.constraints['selected_courses']:
            self.errors.append("En az bir ders secilmelidir!")
            return False

        classrooms = fetch_all(
            "SELECT COUNT(*) as count FROM classrooms WHERE department_id = %s",
            [self.department_id]
        )
        
        if not classrooms or classrooms[0]['count'] == 0:
            self.errors.append("Derslik bulunamadi! Once derslik ekleyin.")
            return False
        
        return True
    
    def generate_available_dates(self) -> List[date]:
        """Kullanılabilir tarihleri oluştur (hariç tutulan günleri çıkar)"""
        start_date = datetime.strptime(self.constraints['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.constraints['end_date'], '%Y-%m-%d').date()

        excluded_weekdays = []
        if self.constraints.get('exclude_monday'): excluded_weekdays.append(0)
        if self.constraints.get('exclude_tuesday'): excluded_weekdays.append(1)
        if self.constraints.get('exclude_wednesday'): excluded_weekdays.append(2)
        if self.constraints.get('exclude_thursday'): excluded_weekdays.append(3)
        if self.constraints.get('exclude_friday'): excluded_weekdays.append(4)
        if self.constraints.get('exclude_saturday'): excluded_weekdays.append(5)
        if self.constraints.get('exclude_sunday'): excluded_weekdays.append(6)
        
        available_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() in excluded_weekdays:
                current_date += timedelta(days=1)
                continue
            
            available_dates.append(current_date)
            current_date += timedelta(days=1)
        
        if len(available_dates) == 0:
            error_msg = "HATA: Secilen tarih araliginda uygun gun bulunamadi!"
            detail_msg = f"   >> Tarih araligi: {start_date} - {end_date}"
            detail_msg2 = f"   >> Tum gunler haric tutulmus olabilir. Lutfen tarih araligini veya haric tutulan gunleri kontrol edin."
            self.errors.append(error_msg)
            self.errors.append(detail_msg)
            self.errors.append(detail_msg2)
        
        return available_dates
    
    def get_courses_with_students(self) -> List[Dict]:
        """Seçilen dersleri ve öğrenci sayılarını al"""
        course_codes = self.constraints['selected_courses']
        
        if not course_codes:
            return []

        placeholders = ','.join(['%s'] * len(course_codes))
        
        courses = fetch_all(f"""
            SELECT c.id, c.code, c.name, c.grade, c.is_elective,
                   COUNT(DISTINCT e.student_id) as student_count
            FROM courses c
            LEFT JOIN enrollments e ON c.id = e.course_id
            WHERE c.department_id = %s AND c.code IN ({placeholders})
            GROUP BY c.id
            ORDER BY c.grade, c.code
        """, [self.department_id] + course_codes)
        
        return courses
    
    def distribute_exams_by_grade(self, courses: List[Dict], available_dates: List[date], offset: int = 0) -> Dict:
        """
        Dersleri sınıf bazlı günlere dağıt
        Kural: Aynı sınıfın dersleri farklı günlere dağıtılır
        """
        courses_by_grade = {}
        for course in courses:
            grade = course['grade']
            if grade not in courses_by_grade:
                courses_by_grade[grade] = []
            courses_by_grade[grade].append(course)

        exam_schedule = {}
        
        for grade, grade_courses in sorted(courses_by_grade.items()):
            date_index = (offset + grade) % len(available_dates)
            
            for course in grade_courses:
                exam_date = available_dates[date_index]
                
                if exam_date not in exam_schedule:
                    exam_schedule[exam_date] = []

                if len(exam_schedule[exam_date]) >= 2:
                    date_index = (date_index + 1) % len(available_dates)
                    exam_date = available_dates[date_index]
                    if exam_date not in exam_schedule:
                        exam_schedule[exam_date] = []
                
                exam_schedule[exam_date].append(course)
                date_index = (date_index + 1) % len(available_dates)

        total_exams = len(courses)
        total_slots = len(available_dates) * 4
        
        if total_exams > total_slots:
            warning_msg = f"UYARI: Tarih araligi sinav sayisi icin yetersiz olabilir!"
            detail_msg = f"   >> Toplam sinav: {total_exams}, Maksimum slot: {total_slots} ({len(available_dates)} gun x 4 slot)"
            self.warnings.append(warning_msg)
            self.warnings.append(detail_msg)
        
        return exam_schedule
    
    def assign_time_slots(self, exam_schedule: Dict) -> List[Dict]:
        """
        Her sınava saat ata
        
        DOĞRU MANTIK:
        - no_overlap AÇIK: Hiçbir sınav aynı anda olamaz (sıralı)
        - no_overlap KAPALI: Farklı sınıfların sınavları paralel olabilir
        - Her ders için özel bekleme süresi kullanılabilir
        """
        exams = []
        default_duration = self.constraints['default_duration']
        default_break = self.constraints['break_duration']
        course_exam_durations = self.constraints.get('course_exam_durations', {})
        course_break_durations = self.constraints.get('course_break_durations', {})
        no_overlap = self.constraints.get('no_overlap', False)

        start_hour = 9

        if no_overlap:
            last_end_time = {}
            
            for exam_date, day_courses in sorted(exam_schedule.items()):
                for course in day_courses:
                    course_code = course['code']
                    duration = course_exam_durations.get(course_code, default_duration)
                    break_time = course_break_durations.get(course_code, default_break)

                    if exam_date not in last_end_time:
                        start_datetime = datetime.combine(exam_date, time(start_hour, 0))
                    else:
                        start_datetime = last_end_time[exam_date] + timedelta(minutes=break_time)
                    
                    start_time = start_datetime.time()
                    end_datetime = start_datetime + timedelta(minutes=duration)
                    end_time = end_datetime.time()

                    last_end_time[exam_date] = end_datetime
                    
                    exam = {
                        'course_id': course['id'],
                        'course_code': course['code'],
                        'course_name': course['name'],
                        'grade': course['grade'],
                        'student_count': course['student_count'],
                        'exam_date': exam_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'break_after': break_time
                    }
                    exams.append(exam)
            
        else:
            day_class_schedule = {}
            
            for exam_date, day_courses in sorted(exam_schedule.items()):
                for course in day_courses:
                    course_code = course['code']
                    duration = course_exam_durations.get(course_code, default_duration)
                    break_time = course_break_durations.get(course_code, default_break)
                    grade = course['grade']

                    key = (exam_date, grade)
                    if key in day_class_schedule:
                        start_datetime = day_class_schedule[key] + timedelta(minutes=break_time)
                    else:
                        start_datetime = datetime.combine(exam_date, time(start_hour, 0))
                    
                    start_time = start_datetime.time()
                    end_datetime = start_datetime + timedelta(minutes=duration)
                    end_time = end_datetime.time()

                    day_class_schedule[key] = end_datetime
                    
                    exam = {
                        'course_id': course['id'],
                        'course_code': course['code'],
                        'course_name': course['name'],
                        'grade': course['grade'],
                        'student_count': course['student_count'],
                        'exam_date': exam_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'break_after': break_time
                    }
                    
                    exams.append(exam)

        if not no_overlap:
            exams = self.assign_times_with_classroom_awareness(exams)
        
        return exams
    
    def assign_times_with_classroom_awareness(self, exams: List[Dict]) -> List[Dict]:
        classroom_date_schedule = {}

        classrooms = fetch_all("""
            SELECT id, capacity
            FROM classrooms
            WHERE department_id = %s
            ORDER BY capacity DESC
        """, [self.department_id])
        
        if not classrooms:
            return exams

        for exam in exams:
            suitable_classroom = None
            for classroom in classrooms:
                if classroom['capacity'] >= exam['student_count']:
                    suitable_classroom = classroom
                    break
            
            if not suitable_classroom:
                continue
            
            classroom_id = suitable_classroom['id']
            exam_date = exam['exam_date']

            if classroom_id not in classroom_date_schedule:
                classroom_date_schedule[classroom_id] = {}
            
            if exam_date not in classroom_date_schedule[classroom_id]:
                classroom_date_schedule[classroom_id][exam_date] = datetime.combine(exam_date, time(9, 0))

            available_time = classroom_date_schedule[classroom_id][exam_date]

            exam['start_time'] = available_time.time()
            end_datetime = available_time + timedelta(minutes=exam['duration'])
            exam['end_time'] = end_datetime.time()

            next_available = end_datetime + timedelta(minutes=exam['break_after'])
            classroom_date_schedule[classroom_id][exam_date] = next_available
            
        
        return exams
    
    def find_student_conflicts(self, exams: List[Dict]) -> List[Tuple[int, int]]:
        """
        Öğrenci çakışmalarını bul
        Returns: [(exam1_index, exam2_index), ...]
        """
        conflicts = []
        
        for i, exam1 in enumerate(exams):
            for j, exam2 in enumerate(exams):
                if i >= j:
                    continue

                if exam1['exam_date'] != exam2['exam_date']:
                    continue

                if not (exam1['end_time'] <= exam2['start_time'] or exam2['end_time'] <= exam1['start_time']):
                    common_students_count = fetch_all("""
                        SELECT COUNT(DISTINCT s.id) as count
                        FROM students s
                        JOIN enrollments e1 ON s.id = e1.student_id
                        JOIN enrollments e2 ON s.id = e2.student_id
                        WHERE e1.course_id = %s AND e2.course_id = %s
                    """, [exam1['course_id'], exam2['course_id']])
                    
                    if common_students_count and common_students_count[0]['count'] > 0:
                        conflicts.append((i, j))
        
        return conflicts
    
    def resolve_student_conflicts(self, exams: List[Dict], max_iterations: int = 50) -> List[Dict]:
        """
        Öğrenci çakışmalarını otomatik çöz
        Çakışan sınavları farklı saatlere/günlere kaydır
        """
        from datetime import datetime, timedelta, time

        available_dates = self.generate_available_dates()
        
        iteration = 0
        resolved_conflicts = set()
        
        while iteration < max_iterations:
            conflicts = self.find_student_conflicts(exams)
            
            if not conflicts:
                return exams

            new_conflicts = [c for c in conflicts if c not in resolved_conflicts]
            if not new_conflicts and iteration > 0:
                break

            exam1_idx, exam2_idx = conflicts[0]
            exam1 = exams[exam1_idx]
            exam2 = exams[exam2_idx]

            if exam1['student_count'] <= exam2['student_count']:
                target_idx = exam1_idx
                target_exam = exam1
                other_exam = exam2
            else:
                target_idx = exam2_idx
                target_exam = exam2
                other_exam = exam1

            current_start = datetime.combine(target_exam['exam_date'], target_exam['start_time'])
            other_end = datetime.combine(other_exam['exam_date'], other_exam['end_time'])

            break_duration = self.constraints.get('break_duration', 15)
            new_start = other_end + timedelta(minutes=break_duration)

            if new_start.hour >= 17 or new_start.hour < 9:
                current_date = target_exam['exam_date']
                next_date_idx = available_dates.index(current_date) + 1
                
                if next_date_idx < len(available_dates):
                    new_date = available_dates[next_date_idx]
                    new_start = datetime.combine(new_date, time(9, 0))
                    exams[target_idx]['exam_date'] = new_date
                else:
                    new_date = available_dates[0]
                    new_start = datetime.combine(new_date, time(15, 0))
                    exams[target_idx]['exam_date'] = new_date

            exams[target_idx]['start_time'] = new_start.time()
            new_end = new_start + timedelta(minutes=target_exam['duration'])
            exams[target_idx]['end_time'] = new_end.time()

            resolved_conflicts.add((exam1_idx, exam2_idx))
            
            iteration += 1

        remaining_conflicts = self.find_student_conflicts(exams)
        if remaining_conflicts:
            conflict_details = []
            for exam1_idx, exam2_idx in remaining_conflicts[:5]:
                exam1 = exams[exam1_idx]
                exam2 = exams[exam2_idx]
                conflict_details.append(
                    f"{exam1['course_code']} ve {exam2['course_code']} "
                    f"({exam1['exam_date']} {exam1['start_time']}-{exam1['end_time']})"
                )

            error_msg = f"HATA: {len(remaining_conflicts)} ogrenci cakismasi cozulemedi!"
            self.errors.append(error_msg)

            for detail in conflict_details:
                detail_msg = f"   - Cakisma: {detail}"
                self.errors.append(detail_msg)
        
        return exams
    
    def check_and_resolve_student_conflicts(self, exams: List[Dict]) -> Tuple[List[Dict], bool]:
        """
        Öğrenci çakışmalarını kontrol et ve çöz
        Returns: (güncellenmiş_exams, çakışma_var_mı)
        """
        exams_resolved = self.resolve_student_conflicts(exams)

        conflicts = self.find_student_conflicts(exams_resolved)
        
        if conflicts:
            for i, (exam1_idx, exam2_idx) in enumerate(conflicts[:5]):
                exam1 = exams_resolved[exam1_idx]
                exam2 = exams_resolved[exam2_idx]
                conflict_msg = (
                    f"Cakisma: {exam1['course_code']} ve {exam2['course_code']} "
                    f"({exam1['exam_date']} {exam1['start_time']}-{exam1['end_time']})"
                )
                self.warnings.append(conflict_msg)
        
        return (exams_resolved, len(conflicts) == 0)
    
    def assign_classrooms_to_exams(self, exams: List[Dict]) -> List[Dict]:
        """
        Her sınava derslik ata
        Kural: Kapasite yeterli olmalı, minimum derslik kullanımı
        """
        classrooms = fetch_all("""
            SELECT id, code, name, capacity, "rows", cols, seat_group
            FROM classrooms
            WHERE department_id = %s
            ORDER BY capacity DESC
        """, [self.department_id])
        
        if not classrooms:
            self.errors.append("Derslik bulunamadi!")
            return exams
        
        for exam in exams:
            student_count = exam['student_count']

            suitable_classrooms = []
            
            for classroom in classrooms:
                if classroom['capacity'] >= student_count:
                    suitable_classrooms.append(classroom)
            
            if not suitable_classrooms:
                all_classrooms_sorted = sorted(classrooms, key=lambda x: x['capacity'], reverse=True)
                
                assigned_classrooms = []
                remaining_students = student_count
                
                for classroom in all_classrooms_sorted:
                    if remaining_students <= 0:
                        break

                    seat_group_str = str(classroom.get('seat_group', 'TRIPLE')).upper()
                    rows = classroom.get('rows', 0)
                    cols = classroom.get('cols', 0)

                    if 'DOUBLE' in seat_group_str or seat_group_str == '2':
                        seat_group_val = 2
                    elif 'TRIPLE' in seat_group_str or seat_group_str == '3':
                        seat_group_val = 3
                    elif 'QUAD' in seat_group_str or seat_group_str == '4':
                        seat_group_val = 4
                    else:
                        seat_group_val = 3

                    if rows > 0 and cols > 0 and seat_group_val > 0:
                        effective_capacity = (rows // seat_group_val) * cols * 2
                    else:
                        effective_capacity = classroom.get('capacity', 0)
                    
                    assigned_classrooms.append(classroom)
                    remaining_students -= effective_capacity
                
                if remaining_students > 0:
                    total_available = student_count - remaining_students
                    error_msg = f"HATA: '{exam['course_code']} - {exam['course_name']}' dersi icin derslik kapasitesi yetersiz!"
                    detail_msg = f"   >> Gerekli: {student_count} ogrenci, Mevcut: {total_available} kapasite, Eksik: {remaining_students} ogrenci"
                    self.errors.append(error_msg)
                    self.errors.append(detail_msg)
                    exam['classrooms'] = []
                else:
                    exam['classrooms'] = assigned_classrooms
            else:
                suitable_classrooms.sort(key=lambda x: x['capacity'])
                exam['classrooms'] = [suitable_classrooms[0]]
        
        return exams
    
    def save_to_database(self, exams: List[Dict]) -> Optional[int]:
        """Sınav programını veritabanına kaydet"""
        try:
            excluded_courses = [c for c in self.get_all_course_codes() 
                               if c not in self.constraints['selected_courses']]
            
            schedule_id = execute("""
                INSERT INTO exam_schedules (
                    department_id, name, exam_type, start_date, end_date,
                    default_duration, break_duration, no_overlap,
                    excluded_days, excluded_courses
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                self.department_id,
                self.constraints['name'],
                self.constraints['exam_type'],
                self.constraints['start_date'],
                self.constraints['end_date'],
                self.constraints['default_duration'],
                self.constraints['break_duration'],
                self.constraints['no_overlap'],
                json.dumps([]),
                json.dumps(excluded_courses)
            ], return_id=True)

            for exam in exams:
                if not exam.get('classrooms'):
                    continue
                
                exam_id = execute("""
                    INSERT INTO exams (
                        schedule_id, course_id, exam_date, start_time, end_time,
                        duration, student_count
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    schedule_id,
                    exam['course_id'],
                    exam['exam_date'],
                    exam['start_time'],
                    exam['end_time'],
                    exam['duration'],
                    exam['student_count']
                ], return_id=True)

                for classroom in exam['classrooms']:
                    execute("""
                        INSERT INTO exam_classrooms (exam_id, classroom_id, allocated_seats)
                        VALUES (%s, %s, %s)
                    """, [exam_id, classroom['id'], exam['student_count']])
            
            return schedule_id
            
        except Exception as e:
            self.errors.append(f"Veritabanina kayit hatasi: {e}")
            return None
    
    def get_all_course_codes(self) -> List[str]:
        """Tüm ders kodlarını al"""
        courses = fetch_all(
            "SELECT code FROM courses WHERE department_id = %s",
            [self.department_id]
        )
        return [c['code'] for c in courses]
    
    def create_schedule(self) -> Tuple[bool, Optional[int], List[str], List[str]]:
        """
        Sınav programını oluştur - OPTİMİZASYONLU
        
        Returns:
            (success, schedule_id, errors, warnings)
        """
        if not self.validate_constraints():
            return (False, None, self.errors, self.warnings)

        available_dates = self.generate_available_dates()
        if not available_dates:
            return (False, None, self.errors, self.warnings)

        courses = self.get_courses_with_students()
        if not courses:
            self.errors.append("Ders bulunamadi!")
            return (False, None, self.errors, self.warnings)

        max_attempts = min(10, len(available_dates))
        best_result = None
        best_error_count = float('inf')
        
        for attempt in range(max_attempts):

            self.errors = []
            self.warnings = []

            exam_schedule = self.distribute_exams_by_grade(courses, available_dates, offset=attempt)

            exams = self.assign_time_slots(exam_schedule)

            exams, conflicts_resolved = self.check_and_resolve_student_conflicts(exams)

            exams = self.assign_classrooms_to_exams(exams)

            critical_errors = [e for e in self.errors if "HATA:" in e or "yeterli kapasiteli derslik bulunamadi" in e or "cakisma" in e.lower()]
            error_count = len(critical_errors)

            if error_count < best_error_count:
                best_error_count = error_count
                best_result = {
                    'exams': exams,
                    'errors': self.errors.copy(),
                    'warnings': self.warnings.copy(),
                    'attempt': attempt + 1
                }

                if error_count == 0:
                    break

        if best_result:
            exams = best_result['exams']
            self.errors = best_result['errors']
            self.warnings = best_result['warnings']

            schedule_id = self.save_to_database(exams)
            
            critical_errors = [e for e in self.errors if "HATA:" in e or "yeterli kapasiteli derslik bulunamadi" in e or "cakisma" in e.lower()]

            if critical_errors:
                if schedule_id:
                    from services.db import execute
                    execute("DELETE FROM exam_schedules WHERE id = %s", [schedule_id])
                
                return (False, None, self.errors, self.warnings)

            if schedule_id:
                return (True, schedule_id, self.errors, self.warnings)
            else:
                return (False, None, self.errors, self.warnings)
        else:
            error_msg = "HATA: Hicbir varyasyon basarili olmadi! Lutfen kisitlari kontrol edin."
            return (False, None, [error_msg], [])


def create_exam_schedule(department_id: int, constraints: dict) -> Tuple[bool, Optional[int], List[str], List[str]]:
    scheduler = ExamScheduler(department_id, constraints)
    return scheduler.create_schedule()

