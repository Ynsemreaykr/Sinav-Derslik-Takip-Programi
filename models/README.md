# Models - Class Hiyerarşisi

Bu klasör projenin veri modellerini içerir.

## Ana Modeller

### 1. BaseModel
- Tüm modellerin temel sınıfı
- `id` alanı içerir

### 2. User (Kullanıcı)
- **Roller**: Admin, Bölüm Koordinatörü
- **Alanlar**: email, password_hash, role, department_id
- **Metodlar**: is_admin(), is_coordinator()

### 3. Department (Bölüm)
- **Alanlar**: name
- 5 aktif bölüm: Bilgisayar Müh., Yazılım Müh., Elektrik Müh., Elektronik Müh., İnşaat Müh.

### 4. Course (Ders)
- **Alanlar**: code, name, instructor, department_id, grade, is_elective, exam_duration
- Zorunlu/Seçmeli bilgisi
- Hangi sınıfa ait olduğu

### 5. Student (Öğrenci)
- **Alanlar**: number, fullname, department_id, grade, courses
- Aldığı dersler listesi

### 6. Classroom (Derslik)
- **Alanlar**: code, name, capacity, rows, cols, seat_group, department_id
- **Sıra Yapısı**: 2'li, 3'lü, 4'lü
- **Metodlar**: get_total_seats(), is_capacity_sufficient()

### 7. Exam (Sınav)
- **Türler**: Vize, Final, Bütünleme
- **Alanlar**: course_id, exam_type, exam_date, start_time, duration, classroom_id

### 8. SeatingPlan (Oturma Planı)
- **Alanlar**: exam_id, student_id, classroom_id, row_number, col_number, seat_number
- Her öğrencinin sınav sırasındaki yeri

### 9. ExamSchedule (Sınav Programı)
- **Kısıtlar**: ExamScheduleConstraints
- **Alanlar**: exams, constraints, created_at
- **Metodlar**: add_exam(), get_exams_by_date(), get_exams_by_course()

## Enum Türleri

### UserRole
- ADMIN
- COORDINATOR

### ExamType
- MIDTERM (Vize)
- FINAL (Final)
- MAKEUP (Bütünleme)

### SeatGroup
- TWO (2'li)
- THREE (3'lü)
- FOUR (4'lü)

## Kullanım

```python
from models.user import User, UserRole
from models.course import Course
from models.classroom import Classroom

# User oluşturma
user = User(
    email="admin@university.edu",
    role=UserRole.ADMIN
)

# Course oluşturma
course = Course(
    code="BLM101",
    name="Programlama I",
    instructor="Prof. Dr. Ali Veli",
    grade=1,
    is_elective=False
)

# Classroom oluşturma
classroom = Classroom(
    code="3001",
    name="301",
    capacity=42,
    rows=9,
    cols=7,
    seat_group=SeatGroup.THREE
)
```
