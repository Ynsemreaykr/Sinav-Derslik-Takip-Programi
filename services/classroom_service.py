from typing import List, Optional
from services.db import fetch_all, fetch_one, execute

class ClassroomService:

    def list_classrooms(self, department_id: Optional[int] = None) -> List[dict]:
        """Tüm derslikleri (isteğe göre departmana göre) döner"""
        if department_id:
            return fetch_all(
                "SELECT * FROM classrooms WHERE department_id = %s ORDER BY id",
                [department_id]
            )
        return fetch_all("SELECT * FROM classrooms ORDER BY id")

    def get_classroom(self, classroom_id: int) -> Optional[dict]:
        """Belirli bir dersliği ID'ye göre getir"""
        return fetch_one("SELECT * FROM classrooms WHERE id = %s", [classroom_id])

    def create_classroom(self, code: str, name: str, capacity: int, rows: int, cols: int,
                         seat_group: str, department_id: int) -> int:
        """Yeni derslik ekler"""
        return execute("""
            INSERT INTO classrooms (code, name, capacity, "rows", cols, seat_group, department_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [code, name, capacity, rows, cols, seat_group, department_id])

    def delete_classroom(self, classroom_id: int) -> int:
        """Dersliği ID’ye göre siler"""
        return execute("DELETE FROM classrooms WHERE id = %s", [classroom_id])

    def update_classroom(self, classroom_id: int, **kwargs) -> int:
        """Dersliği dinamik olarak günceller"""
        if not kwargs:
            return 0

        fields = []
        values = []
        for key, value in kwargs.items():
            if key == 'rows':
                fields.append(f'"{key}" = %s')
            else:
                fields.append(f"{key} = %s")
            values.append(value)

        sql = f"UPDATE classrooms SET {', '.join(fields)} WHERE id = %s"
        values.append(classroom_id)

        return execute(sql, values)
