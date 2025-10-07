# models/student.py
from dataclasses import dataclass
from typing import Optional
from models.base_model import BaseModel

@dataclass
class Student(BaseModel):
    name: str = ""
    student_no: Optional[str] = None
    department_id: Optional[int] = None
    email: Optional[str] = None

    @staticmethod
    def from_row(row: dict) -> "Student":
        return Student(
            id=row.get("id"),
            name=row.get("name"),
            student_no=row.get("student_no"),
            department_id=row.get("department_id"),
            email=row.get("email"),
        )
