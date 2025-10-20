# models/course.py
from dataclasses import dataclass
from typing import Optional
from models.base_model import BaseModel

@dataclass
class Course(BaseModel):
    department_id: int = 0
    code: str = ""
    name: str = ""
    instructor: str = ""
    grade: Optional[int] = None
    is_elective: bool = False

    @staticmethod
    def from_row(row: dict) -> "Course":
        return Course(
            id=row.get("id"),
            department_id=row.get("department_id", 0),
            code=row.get("code", ""),
            name=row.get("name", ""),
            instructor=row.get("instructor", ""),
            grade=row.get("grade"),
            is_elective=row.get("is_elective", False),
        )
