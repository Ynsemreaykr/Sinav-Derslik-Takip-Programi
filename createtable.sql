-- =========================
-- ENUM TYPES
-- =========================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_enum') THEN
        CREATE TYPE role_enum AS ENUM ('ADMIN', 'COORDINATOR');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'seat_group_enum') THEN
        CREATE TYPE seat_group_enum AS ENUM ('DOUBLE', 'TRIPLE', 'QUAD');
    END IF;
END$$;

-- =========================
-- TABLES
-- =========================

-- Bölümler
CREATE TABLE IF NOT EXISTS departments (
    id   BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Kullanıcılar (Admin / Bölüm Koordinatörü)
CREATE TABLE IF NOT EXISTS users (
    id             BIGSERIAL PRIMARY KEY,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    role           role_enum    NOT NULL DEFAULT 'COORDINATOR',
    department_id  BIGINT       NULL REFERENCES departments(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_users_dept ON users(department_id);

-- Derslikler (kapasite + oturma düzeni parametreleri)
CREATE TABLE IF NOT EXISTS classrooms (
    id            BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    code          VARCHAR(50)  NOT NULL,          -- ör: 3001
    name          VARCHAR(120) NOT NULL,          -- ör: 301, EDA, Büyük Amfi
    capacity      INT NOT NULL CHECK (capacity > 0),
    rows          INT NOT NULL CHECK (rows > 0),  -- boyuna sıra sayısı
    cols          INT NOT NULL CHECK (cols > 0),  -- enine sütun sayısı
    seat_group    seat_group_enum NOT NULL DEFAULT 'DOUBLE',
    UNIQUE (department_id, code)
);
CREATE INDEX IF NOT EXISTS ix_classrooms_dept_name ON classrooms(department_id, name);

-- Dersler
CREATE TABLE IF NOT EXISTS courses (
    id            BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    code          VARCHAR(50)  NOT NULL,          -- ör: BLM401
    name          VARCHAR(255) NOT NULL,
    instructor    VARCHAR(255),
    grade         INT CHECK (grade IS NULL OR grade BETWEEN 1 AND 5),
    is_elective   BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (department_id, code)
);
CREATE INDEX IF NOT EXISTS ix_courses_dept_grade ON courses(department_id, grade);

-- Öğrenciler
CREATE TABLE IF NOT EXISTS students (
    id            BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    number        VARCHAR(50)  NOT NULL,          -- öğrenci no
    fullname      VARCHAR(200) NOT NULL,
    grade         INT CHECK (grade IS NULL OR grade BETWEEN 1 AND 5),
    UNIQUE (department_id, number)
);
CREATE INDEX IF NOT EXISTS ix_students_name ON students(fullname);
CREATE INDEX IF NOT EXISTS ix_students_dept ON students(department_id);

-- Kayıtlar (öğrenci ↔ ders N–M)
CREATE TABLE IF NOT EXISTS enrollments (
    id         BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id  BIGINT NOT NULL REFERENCES courses(id)  ON DELETE CASCADE,
    UNIQUE (student_id, course_id)
);
CREATE INDEX IF NOT EXISTS ix_enroll_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS ix_enroll_course  ON enrollments(course_id);

-- =========================
-- VIEWS (görüntüleme/arama kolaylığı için)
-- =========================
CREATE OR REPLACE VIEW v_student_courses AS
SELECT s.department_id,
       s.number AS student_no,
       s.fullname,
       c.code   AS course_code,
       c.name   AS course_name
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN courses  c ON c.id = e.course_id;

CREATE OR REPLACE VIEW v_course_students AS
SELECT c.department_id,
       c.code   AS course_code,
       c.name   AS course_name,
       s.number AS student_no,
       s.fullname
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN courses  c ON c.id = e.course_id;
