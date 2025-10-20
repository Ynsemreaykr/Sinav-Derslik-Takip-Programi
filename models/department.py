# models/department.py
from dataclasses import dataclass
from models.base_model import BaseModel

@dataclass
class Department(BaseModel):
    name: str = ""

    @staticmethod
    def from_row(row: dict) -> "Department":
        return Department(
            id=row.get("id"),
            name=row.get("name", "")
        )
