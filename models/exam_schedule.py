# models/exam_schedule.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, date
from models.exam import Exam, ExamType

@dataclass
class ExamScheduleConstraints:
    """Sinav programi kisitlari"""
    excluded_courses: List[int] = None  # Programa dahil olmayacak dersler
    start_date: Optional[date] = None  # Baslangic tarihi
    end_date: Optional[date] = None  # Bitis tarihi
    excluded_days: List[int] = None  # Hafta gunleri (0=Pazartesi, 6=Pazar)
    exam_type: ExamType = ExamType.MIDTERM
    default_duration: int = 75  # Varsayilan sinav suresi (dakika)
    break_time: int = 15  # Bekleme suresi (dakika)
    no_overlap: bool = False  # Sinavlar ayni zamana denk gelmesin mi
    custom_durations: dict = None  # {course_id: duration}
    
    def __post_init__(self):
        if self.excluded_courses is None:
            self.excluded_courses = []
        if self.excluded_days is None:
            self.excluded_days = []
        if self.custom_durations is None:
            self.custom_durations = {}

@dataclass
class ExamSchedule:
    """Sinav programi"""
    exams: List[Exam] = None
    constraints: Optional[ExamScheduleConstraints] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.exams is None:
            self.exams = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def add_exam(self, exam: Exam):
        """Programa sinav ekle"""
        self.exams.append(exam)
    
    def get_exams_by_date(self, exam_date: date) -> List[Exam]:
        """Belirli bir tarihteki sinavlari getir"""
        return [exam for exam in self.exams if exam.exam_date.date() == exam_date]
    
    def get_exams_by_course(self, course_id: int) -> List[Exam]:
        """Belirli bir derse ait sinavlari getir"""
        return [exam for exam in self.exams if exam.course_id == course_id]
