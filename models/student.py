# models/student.py
from dataclasses import dataclass
from typing import Optional
from models.base_model import BaseModel

@dataclass
class Student(BaseModel):
    department_id: int = 0
    number: str = ""
    fullname: str = ""
    grade: Optional[int] = None

    @staticmethod
    def from_row(row: dict) -> "Student":
        return Student(
            id=row.get("id"),
            department_id=row.get("department_id", 0),
            number=row.get("number", ""),
            fullname=row.get("fullname", ""),
            grade=row.get("grade")
        )
