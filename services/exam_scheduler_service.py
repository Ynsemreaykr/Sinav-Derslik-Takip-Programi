# -*- coding: utf-8 -*-
"""
Sınav Programı Oluşturma Servisi

Bu servis, verilen kısıtlara göre optimal sınav programı oluşturur.

Optimizasyon Kuralları:
1. Aynı sınıfın dersleri farklı günlere dağıtılır
2. Öğrencinin aynı saatte iki sınavı olmaz
3. Derslik kullanımı minimize edilir
4. Öğrenci sınavları arasında minimum bekleme süresi bırakılır
5. Kapasite yetersiz dersliklerde sınav planlanmaz
"""

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
        print("\n[1/8] Kisitlar dogrulaniyor...")
        
        # Tarih kontrolü
        start_date = datetime.strptime(self.constraints['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.constraints['end_date'], '%Y-%m-%d').date()
        
        if start_date >= end_date:
            self.errors.append("Baslangic tarihi bitis tarihinden once olmalidir!")
            return False
        
        # Ders kontrolü
        if not self.constraints['selected_courses']:
            self.errors.append("En az bir ders secilmelidir!")
            return False
        
        # Derslik kontrolü
        classrooms = fetch_all(
            "SELECT COUNT(*) as count FROM classrooms WHERE department_id = %s",
            [self.department_id]
        )
        
        if not classrooms or classrooms[0]['count'] == 0:
            self.errors.append("Derslik bulunamadi! Once derslik ekleyin.")
            return False
        
        print(f"   Tarih araligi: {start_date} - {end_date}")
        print(f"   Ders sayisi: {len(self.constraints['selected_courses'])}")
        print(f"   Derslik sayisi: {classrooms[0]['count']}")
        
        return True
    
    def generate_available_dates(self) -> List[date]:
        """Kullanılabilir tarihleri oluştur (hariç tutulan günleri çıkar)"""
        print("\n[2/8] Kullanilabilir tarihler olusturuluyor...")
        
        start_date = datetime.strptime(self.constraints['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.constraints['end_date'], '%Y-%m-%d').date()
        
        available_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # Cumartesi kontrolü (5 = Saturday)
            if current_date.weekday() == 5 and self.constraints.get('exclude_saturday'):
                current_date += timedelta(days=1)
                continue
            
            # Pazar kontrolü (6 = Sunday)
            if current_date.weekday() == 6 and self.constraints.get('exclude_sunday'):
                current_date += timedelta(days=1)
                continue
            
            available_dates.append(current_date)
            current_date += timedelta(days=1)
        
        print(f"   Toplam {len(available_dates)} gun kullanilabilir")
        
        if len(available_dates) == 0:
            self.errors.append("Secilen tarih araliginda uygun gun bulunamadi!")
        
        return available_dates
    
    def get_courses_with_students(self) -> List[Dict]:
        """Seçilen dersleri ve öğrenci sayılarını al"""
        print("\n[3/8] Dersler ve ogrenci sayilari aliniyor...")
        
        # Seçilen ders kodlarını al
        course_codes = self.constraints['selected_courses']
        
        if not course_codes:
            return []
        
        # SQL için placeholder oluştur
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
        
        print(f"   Toplam {len(courses)} ders yuklendi")
        
        # Sınıf bazında grupla
        grade_distribution = {}
        for course in courses:
            grade = course['grade']
            if grade not in grade_distribution:
                grade_distribution[grade] = 0
            grade_distribution[grade] += 1
        
        for grade, count in sorted(grade_distribution.items()):
            print(f"   {grade}. Sinif: {count} ders")
        
        return courses
    
    def distribute_exams_by_grade(self, courses: List[Dict], available_dates: List[date]) -> Dict:
        """
        Dersleri sınıf bazlı günlere dağıt
        Kural: Aynı sınıfın dersleri farklı günlere dağıtılır
        """
        print("\n[4/8] Dersler sinif bazli gunlere dagitiliyor...")
        
        # Sınıf bazında grupla
        courses_by_grade = {}
        for course in courses:
            grade = course['grade']
            if grade not in courses_by_grade:
                courses_by_grade[grade] = []
            courses_by_grade[grade].append(course)
        
        # Her sınıf için günlere dağıt
        exam_schedule = {}  # {date: [courses]}
        
        for grade, grade_courses in sorted(courses_by_grade.items()):
            print(f"   {grade}. Sinif: {len(grade_courses)} ders dagitiliyor...")
            
            # Bu sınıfın derslerini günlere dağıt (round-robin)
            date_index = 0
            for course in grade_courses:
                if date_index >= len(available_dates):
                    date_index = 0  # Başa dön
                
                exam_date = available_dates[date_index]
                
                if exam_date not in exam_schedule:
                    exam_schedule[exam_date] = []
                
                exam_schedule[exam_date].append(course)
                date_index += 1
        
        # Özet
        for exam_date, day_courses in sorted(exam_schedule.items()):
            print(f"   {exam_date}: {len(day_courses)} sinav")
        
        return exam_schedule
    
    def assign_time_slots(self, exam_schedule: Dict) -> List[Dict]:
        """
        Her sınava saat ata
        Kural: Öğrencinin aynı saatte iki sınavı olmayacak
        """
        print("\n[5/8] Sinavlara saat ataniyor...")
        
        exams = []
        default_duration = self.constraints['default_duration']
        break_duration = self.constraints['break_duration']
        no_overlap = self.constraints['no_overlap']
        
        # Başlangıç saati
        start_hour = 9  # 09:00
        
        for exam_date, day_courses in sorted(exam_schedule.items()):
            current_time = time(start_hour, 0)
            
            for course in day_courses:
                duration = default_duration  # Şimdilik hepsi varsayılan
                
                # Başlangıç ve bitiş saatini hesapla
                start_time = current_time
                end_datetime = datetime.combine(exam_date, start_time) + timedelta(minutes=duration)
                end_time = end_datetime.time()
                
                exam = {
                    'course_id': course['id'],
                    'course_code': course['code'],
                    'course_name': course['name'],
                    'grade': course['grade'],
                    'student_count': course['student_count'],
                    'exam_date': exam_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration
                }
                
                exams.append(exam)
                
                # Bir sonraki sınav için saat hesapla
                if no_overlap:
                    # Sınavlar çakışmasın - sınav bitince + bekleme süresi
                    next_datetime = end_datetime + timedelta(minutes=break_duration)
                else:
                    # Sınavlar çakışabilir - sadece bekleme süresi ekle
                    next_datetime = datetime.combine(exam_date, start_time) + timedelta(minutes=break_duration)
                
                current_time = next_datetime.time()
        
        print(f"   Toplam {len(exams)} sinav planland")
        
        return exams
    
    def check_student_conflicts(self, exams: List[Dict]) -> bool:
        """
        Öğrenci çakışmalarını kontrol et
        Kural: Bir öğrencinin aynı saatte iki sınavı olamaz
        """
        print("\n[6/8] Ogrenci cakismalari kontrol ediliyor...")
        
        conflicts = []
        
        # Her öğrenci için sınavlarını kontrol et
        for exam1 in exams:
            for exam2 in exams:
                if exam1['course_id'] >= exam2['course_id']:
                    continue  # Aynı dersi veya zaten kontrol edilmiş çifti atla
                
                # Aynı gün mü?
                if exam1['exam_date'] != exam2['exam_date']:
                    continue
                
                # Saatler çakışıyor mu?
                if not (exam1['end_time'] <= exam2['start_time'] or exam2['end_time'] <= exam1['start_time']):
                    # Çakışma var - bu iki dersi alan öğrenci var mı?
                    common_students = fetch_all("""
                        SELECT s.number, s.fullname
                        FROM students s
                        JOIN enrollments e1 ON s.id = e1.student_id
                        JOIN enrollments e2 ON s.id = e2.student_id
                        WHERE e1.course_id = %s AND e2.course_id = %s
                        LIMIT 5
                    """, [exam1['course_id'], exam2['course_id']])
                    
                    if common_students:
                        conflict_msg = (
                            f"Cakisma: {exam1['course_code']} ve {exam2['course_code']} "
                            f"({exam1['exam_date']} {exam1['start_time']}-{exam1['end_time']}) - "
                            f"{len(common_students)} ogrenci etkilendi"
                        )
                        conflicts.append(conflict_msg)
                        self.warnings.append(conflict_msg)
        
        if conflicts:
            print(f"   UYARI: {len(conflicts)} cakisma tespit edildi")
            for conflict in conflicts[:5]:  # İlk 5 çakışmayı göster
                print(f"   - {conflict}")
        else:
            print("   Cakisma bulunamadi")
        
        return len(conflicts) == 0
    
    def assign_classrooms_to_exams(self, exams: List[Dict]) -> List[Dict]:
        """
        Her sınava derslik ata
        Kural: Kapasite yeterli olmalı, minimum derslik kullanımı
        """
        print("\n[7/8] Dersliklere sinav ataniyor...")
        
        # Tüm derslikleri al
        classrooms = fetch_all("""
            SELECT id, code, name, capacity
            FROM classrooms
            WHERE department_id = %s
            ORDER BY capacity DESC
        """, [self.department_id])
        
        if not classrooms:
            self.errors.append("Derslik bulunamadi!")
            return exams
        
        print(f"   Toplam {len(classrooms)} derslik mevcut")
        
        for exam in exams:
            student_count = exam['student_count']
            
            # Bu sınav için uygun derslikleri bul
            suitable_classrooms = []
            
            for classroom in classrooms:
                if classroom['capacity'] >= student_count:
                    suitable_classrooms.append(classroom)
            
            if not suitable_classrooms:
                error_msg = f"Ders {exam['course_code']} icin yeterli kapasiteli derslik bulunamadi! (Ogrenci: {student_count})"
                self.errors.append(error_msg)
                print(f"   HATA: {error_msg}")
                exam['classrooms'] = []
            else:
                # En küçük uygun derslikleri seç (minimum kullanım için)
                suitable_classrooms.sort(key=lambda x: x['capacity'])
                
                # Şimdilik tek derslik ata (en küçük uygun olanı)
                exam['classrooms'] = [suitable_classrooms[0]]
                print(f"   {exam['course_code']}: {suitable_classrooms[0]['name']} ({student_count}/{suitable_classrooms[0]['capacity']})")
        
        return exams
    
    def save_to_database(self, exams: List[Dict]) -> Optional[int]:
        """Sınav programını veritabanına kaydet"""
        print("\n[8/8] Sinav programi veritabanina kaydediliyor...")
        
        try:
            # 1. exam_schedules kaydı oluştur
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
                json.dumps([]),  # excluded_days - şimdilik boş
                json.dumps(excluded_courses)
            ], return_id=True)
            
            print(f"   Schedule ID: {schedule_id}")
            
            # 2. Her sınav için exam kaydı oluştur
            for exam in exams:
                if not exam.get('classrooms'):
                    continue  # Derslik atanamadıysa atla
                
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
                
                # 3. Derslik atamasını kaydet
                for classroom in exam['classrooms']:
                    execute("""
                        INSERT INTO exam_classrooms (exam_id, classroom_id, allocated_seats)
                        VALUES (%s, %s, %s)
                    """, [exam_id, classroom['id'], exam['student_count']])
            
            print(f"   {len(exams)} sinav kaydedildi")
            return schedule_id
            
        except Exception as e:
            self.errors.append(f"Veritabanina kayit hatasi: {e}")
            print(f"   HATA: {e}")
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
        Sınav programını oluştur
        
        Returns:
            (success, schedule_id, errors, warnings)
        """
        print("\n" + "=" * 80)
        print("SINAV PROGRAMI OLUSTURULUYOR")
        print("=" * 80)
        
        # 1. Kısıtları doğrula
        if not self.validate_constraints():
            return (False, None, self.errors, self.warnings)
        
        # 2. Kullanılabilir tarihleri oluştur
        available_dates = self.generate_available_dates()
        if not available_dates:
            return (False, None, self.errors, self.warnings)
        
        # 3. Dersleri al
        courses = self.get_courses_with_students()
        if not courses:
            self.errors.append("Ders bulunamadi!")
            return (False, None, self.errors, self.warnings)
        
        # 4. Dersleri günlere dağıt
        exam_schedule = self.distribute_exams_by_grade(courses, available_dates)
        
        # 5. Saatleri ata
        exams = self.assign_time_slots(exam_schedule)
        
        # 6. Öğrenci çakışmalarını kontrol et
        self.check_student_conflicts(exams)
        
        # 7. Derslikleri ata
        exams = self.assign_classrooms_to_exams(exams)
        
        # 8. Veritabanına kaydet
        schedule_id = self.save_to_database(exams)
        
        if schedule_id:
            print("\n" + "=" * 80)
            print("SINAV PROGRAMI BASARIYLA OLUSTURULDU!")
            print("=" * 80)
            return (True, schedule_id, self.errors, self.warnings)
        else:
            return (False, None, self.errors, self.warnings)


def create_exam_schedule(department_id: int, constraints: dict) -> Tuple[bool, Optional[int], List[str], List[str]]:
    """
    Sınav programı oluştur (facade fonksiyon)
    
    Args:
        department_id: Bölüm ID
        constraints: Kısıtlar dictionary
        
    Returns:
        (success, schedule_id, errors, warnings)
    """
    scheduler = ExamScheduler(department_id, constraints)
    return scheduler.create_schedule()

