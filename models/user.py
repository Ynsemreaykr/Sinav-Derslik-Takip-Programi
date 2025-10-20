# models/user.py
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from models.base_model import BaseModel


class UserRole(Enum):
    ADMIN = "ADMIN"
    COORDINATOR = "COORDINATOR"

@dataclass
class User(BaseModel):
    email: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.COORDINATOR
    department_id: Optional[int] = None

    @staticmethod
    def from_row(row: dict) -> "User":
        """Veritabanı satırından User nesnesi oluşturur."""
        return User(
            id=row.get("id"),
            email=row.get("email", ""),
            password_hash=row.get("password_hash", ""),
            role=UserRole(row.get("role", "COORDINATOR")),
            department_id=row.get("department_id")
        )

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def is_coordinator(self) -> bool:
        return self.role == UserRole.COORDINATOR
