# models/classroom.py
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from models.base_model import BaseModel


class SeatGroup(Enum):
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUAD = "QUAD"

@dataclass
class Classroom(BaseModel):
    department_id: int = 0
    code: str = ""
    name: str = ""
    capacity: int = 0
    rows: int = 0
    cols: int = 0
    seat_group: SeatGroup = SeatGroup.TRIPLE

    @staticmethod
    def from_row(row: dict) -> "Classroom":
        return Classroom(
            id=row.get("id"),
            department_id=row.get("department_id", 0),
            code=row.get("code", ""),
            name=row.get("name", ""),
            capacity=row.get("capacity", 0),
            rows=row.get("rows", 0),
            cols=row.get("cols", 0),
            seat_group=SeatGroup(row.get("seat_group", "TRIPLE")),
        )
