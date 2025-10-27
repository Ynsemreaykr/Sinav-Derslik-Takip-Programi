# models/exam.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum
from models.base_model import BaseModel

class ExamType(Enum):
    """Sinav turu"""
    MIDTERM = "vize"
    FINAL = "final"
    MAKEUP = "butunleme"

@dataclass
class Exam(BaseModel):
    """Sinav modeli"""
    course_id: int = 0
    exam_type: ExamType = ExamType.MIDTERM
    exam_date: Optional[datetime] = None
    start_time: Optional[str] = None
    duration: int = 75  # Dakika
    classroom_id: Optional[int] = None
    
    @staticmethod
    def from_row(row: dict) -> "Exam":
        """Veritabani satirindan Exam objesi olustur"""
        return Exam(
            id=row.get("id"),
            course_id=row.get("course_id"),
            exam_type=ExamType(row.get("exam_type")) if row.get("exam_type") else ExamType.MIDTERM,
            exam_date=row.get("exam_date"),
            start_time=row.get("start_time"),
            duration=row.get("duration", 75),
            classroom_id=row.get("classroom_id")
        )
