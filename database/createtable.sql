-- =====================================================
-- Dinamik Sınav Takvimi Oluşturma Sistemi
-- Tüm Tablo Tanımları
-- =====================================================

-- 1. DEPARTMENTS (Bölümler)
-- =====================================================
CREATE TABLE IF NOT EXISTS departments (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE departments IS 'Üniversite bölümleri';
COMMENT ON COLUMN departments.name IS 'Bölüm adı (ör: Bilgisayar Mühendisliği)';

-- 2. USERS (Kullanıcılar)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('ADMIN', 'COORDINATOR')),
    department_id BIGINT REFERENCES departments(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'Sistem kullanıcıları (Admin ve Koordinatörler)';
COMMENT ON COLUMN users.role IS 'Kullanıcı rolü: ADMIN veya COORDINATOR';
COMMENT ON COLUMN users.department_id IS 'Koordinatör ise bağlı olduğu bölüm (Admin için NULL)';

-- 3. CLASSROOMS (Derslikler)
-- =====================================================
CREATE TABLE IF NOT EXISTS classrooms (
    id BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    rows INTEGER NOT NULL CHECK (rows > 0),
    cols INTEGER NOT NULL CHECK (cols > 0),
    seat_group VARCHAR(20) NOT NULL DEFAULT 'TRIPLE' CHECK (seat_group IN ('DOUBLE', 'TRIPLE', 'QUAD')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, code)
);

COMMENT ON TABLE classrooms IS 'Sınav derslikler ve oturma düzenleri';
COMMENT ON COLUMN classrooms.code IS 'Derslik kodu (ör: A101)';
COMMENT ON COLUMN classrooms.capacity IS 'Maksimum öğrenci kapasitesi';
COMMENT ON COLUMN classrooms.rows IS 'Enine sıra sayısı';
COMMENT ON COLUMN classrooms.cols IS 'Boyuna sütun sayısı';
COMMENT ON COLUMN classrooms.seat_group IS 'Oturma düzeni: DOUBLE (2li), TRIPLE (3lü), QUAD (4lü)';

-- 4. COURSES (Dersler)
-- =====================================================
CREATE TABLE IF NOT EXISTS courses (
    id BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    instructor VARCHAR(255),
    grade INTEGER CHECK (grade >= 1 AND grade <= 4),
    is_elective BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, code)
);

COMMENT ON TABLE courses IS 'Bölüm dersleri';
COMMENT ON COLUMN courses.code IS 'Ders kodu (ör: BİL101)';
COMMENT ON COLUMN courses.grade IS 'Sınıf seviyesi (1-4)';
COMMENT ON COLUMN courses.is_elective IS 'Seçmeli ders mi? (true/false)';

-- 5. STUDENTS (Öğrenciler)
-- =====================================================
CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    number VARCHAR(50) NOT NULL UNIQUE,
    fullname VARCHAR(255) NOT NULL,
    grade INTEGER CHECK (grade >= 1 AND grade <= 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE students IS 'Öğrenci bilgileri';
COMMENT ON COLUMN students.number IS 'Öğrenci numarası';
COMMENT ON COLUMN students.grade IS 'Öğrencinin sınıfı (1-4)';

-- 6. STUDENT_COURSES (Öğrenci-Ders İlişkisi - Çoktan Çoğa)
-- =====================================================
CREATE TABLE IF NOT EXISTS student_courses (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

COMMENT ON TABLE student_courses IS 'Öğrencilerin aldığı dersler (çoktan çoğa ilişki)';

-- 7. ENROLLMENTS (Kayıt Dönemleri/Ders Kayıtları)
-- =====================================================
CREATE TABLE IF NOT EXISTS enrollments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    semester VARCHAR(20) NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    grade VARCHAR(5),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DROPPED', 'COMPLETED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id, semester, academic_year)
);

COMMENT ON TABLE enrollments IS 'Öğrencilerin ders kayıtları ve dönem bilgileri';
COMMENT ON COLUMN enrollments.semester IS 'Dönem (GÜZ, BAHAR, YAZ)';
COMMENT ON COLUMN enrollments.academic_year IS 'Akademik yıl (ör: 2023-2024)';
COMMENT ON COLUMN enrollments.grade IS 'Ders notu (AA, BA, BB, vb.)';
COMMENT ON COLUMN enrollments.status IS 'Kayıt durumu: ACTIVE (Aktif), DROPPED (Bırakıldı), COMPLETED (Tamamlandı)';

-- 8. EXAM_SCHEDULES (Sınav Programları)
-- =====================================================
CREATE TABLE IF NOT EXISTS exam_schedules (
    id BIGSERIAL PRIMARY KEY,
    department_id BIGINT NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    exam_type VARCHAR(50) NOT NULL CHECK (exam_type IN ('VİZE', 'FİNAL', 'BÜTÜNLEME')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    default_duration INTEGER NOT NULL DEFAULT 75,
    break_duration INTEGER NOT NULL DEFAULT 15,
    no_overlap BOOLEAN NOT NULL DEFAULT false,
    excluded_days TEXT,
    excluded_courses TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_date >= start_date)
);

COMMENT ON TABLE exam_schedules IS 'Sınav programı genel bilgileri';
COMMENT ON COLUMN exam_schedules.exam_type IS 'Sınav türü: VİZE, FİNAL, BÜTÜNLEME';
COMMENT ON COLUMN exam_schedules.default_duration IS 'Varsayılan sınav süresi (dakika)';
COMMENT ON COLUMN exam_schedules.break_duration IS 'Sınavlar arası mola süresi (dakika)';
COMMENT ON COLUMN exam_schedules.no_overlap IS 'Öğrencilerin aynı anda birden fazla sınavı olmasın mı?';
COMMENT ON COLUMN exam_schedules.excluded_days IS 'Hariç tutulan günler (JSON)';
COMMENT ON COLUMN exam_schedules.excluded_courses IS 'Hariç tutulan dersler (JSON)';

-- 9. EXAMS (Sınavlar)
-- =====================================================
CREATE TABLE IF NOT EXISTS exams (
    id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL REFERENCES exam_schedules(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration INTEGER NOT NULL,
    student_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schedule_id, course_id)
);

COMMENT ON TABLE exams IS 'Her bir sınavın detayları';
COMMENT ON COLUMN exams.student_count IS 'Sınava girecek öğrenci sayısı';

-- 10. EXAM_CLASSROOMS (Sınav-Derslik İlişkisi - Çoktan Çoğa)
-- =====================================================
CREATE TABLE IF NOT EXISTS exam_classrooms (
    id BIGSERIAL PRIMARY KEY,
    exam_id BIGINT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    classroom_id BIGINT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    allocated_seats INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, classroom_id)
);

COMMENT ON TABLE exam_classrooms IS 'Bir sınav birden fazla derslikte yapılabilir';
COMMENT ON COLUMN exam_classrooms.allocated_seats IS 'Bu dersliğe atanan öğrenci sayısı';

-- 11. SEATING_PLANS (Oturma Planları)
-- =====================================================
CREATE TABLE IF NOT EXISTS seating_plans (
    id BIGSERIAL PRIMARY KEY,
    exam_id BIGINT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    classroom_id BIGINT NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    col_number INTEGER NOT NULL,
    seat_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, student_id),
    UNIQUE(exam_id, classroom_id, row_number, col_number, seat_position)
);

COMMENT ON TABLE seating_plans IS 'Sınavlarda öğrencilerin oturma düzeni';
COMMENT ON COLUMN seating_plans.seat_position IS 'Sırada kaçıncı koltukta (1, 2, 3 veya 4)';

-- =====================================================
-- İndeksler (Performans için)
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_classrooms_department ON classrooms(department_id);
CREATE INDEX IF NOT EXISTS idx_courses_department ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department_id);
CREATE INDEX IF NOT EXISTS idx_students_number ON students(number);
CREATE INDEX IF NOT EXISTS idx_student_courses_student ON student_courses(student_id);
CREATE INDEX IF NOT EXISTS idx_student_courses_course ON student_courses(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_semester ON enrollments(semester, academic_year);
CREATE INDEX IF NOT EXISTS idx_exam_schedules_department ON exam_schedules(department_id);
CREATE INDEX IF NOT EXISTS idx_exams_schedule ON exams(schedule_id);
CREATE INDEX IF NOT EXISTS idx_exams_course ON exams(course_id);
CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(exam_date);
CREATE INDEX IF NOT EXISTS idx_exam_classrooms_exam ON exam_classrooms(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_classrooms_classroom ON exam_classrooms(classroom_id);
CREATE INDEX IF NOT EXISTS idx_seating_plans_exam ON seating_plans(exam_id);
CREATE INDEX IF NOT EXISTS idx_seating_plans_student ON seating_plans(student_id);
CREATE INDEX IF NOT EXISTS idx_seating_plans_classroom ON seating_plans(classroom_id);

-- =====================================================
-- Tetikleyiciler (updated_at otomatik güncelleme)
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Her tablo için trigger oluştur
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('departments', 'users', 'classrooms', 'courses', 'students', 'enrollments', 'exam_schedules')
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', t, t);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I 
                       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$;
