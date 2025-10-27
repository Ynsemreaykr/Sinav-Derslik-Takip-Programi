# models/seating_plan.py
from dataclasses import dataclass
from models.base_model import BaseModel

@dataclass
class SeatingPlan(BaseModel):
    """Oturma plani modeli"""
    exam_id: int = 0
    student_id: int = 0
    classroom_id: int = 0
    row_number: int = 0
    col_number: int = 0
    seat_number: int = 0
    
    @staticmethod
    def from_row(row: dict) -> "SeatingPlan":
        """Veritabani satirindan SeatingPlan objesi olustur"""
        return SeatingPlan(
            id=row.get("id"),
            exam_id=row.get("exam_id"),
            student_id=row.get("student_id"),
            classroom_id=row.get("classroom_id"),
            row_number=row.get("row_number", 0),
            col_number=row.get("col_number", 0),
            seat_number=row.get("seat_number", 0)
        )
