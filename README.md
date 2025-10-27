# 🎓 Dinamik Sınav Takvimi ve Oturma Planı Oluşturma Sistemi

### *(OBS Exam Scheduler — Python + PyQt5 + PostgreSQL)*

---

## 📘 Proje Özeti

Bu proje, üniversitelerdeki sınav planlama sürecini otomatikleştirmek amacıyla geliştirilmiş **masaüstü tabanlı bir yönetim sistemi**dir.

Sistem, **bölüm koordinatörlerinin** ders, öğrenci ve derslik bilgilerini yönetmesine; bu bilgilere dayanarak **çakışmasız sınav takvimi** oluşturmasına ve **oturma planlarını** otomatik üretmesine olanak tanır.

Uygulama, **Python (PyQt5)** arayüzü, **PostgreSQL** veritabanı ve **modüler katmanlı mimarisi** ile geliştirilmiştir.

Tüm işlemler GUI üzerinden yönetilir ve sonuçlar **Excel (.xlsx)** veya **PDF (.pdf)** biçiminde dışa aktarılabilir.

---

## 🚀 Temel Özellikler

✅ **Admin Paneli**
- Bölüm yönetimi
- Koordinatör ekleme / silme
- Tüm bölümleri görüntüleme

✅ **Koordinatör Paneli**
- Derslik yönetimi (kapasite, sıra düzeni, oturma tipi)
- Ders ve öğrenci listelerini **Excel**'den yükleme
- Sınav tarihleri aralığını seçip **otomatik sınav takvimi oluşturma**
- **Çakışma çözümü** ve **derslik ataması** algoritması
- Öğrencilere göre **oturma planı (PDF)** oluşturma
- Excel biçiminde **sınav programı dışa aktarımı**

✅ **Veritabanı (PostgreSQL)**
- 11 ilişkili tablo (departments, users, classrooms, courses, students, exams, seating_plans, vb.)
- Güçlü referans bütünlüğü (FK, CHECK, INDEX)
- Hash'lenmiş şifreler, kullanıcı rolleri (Admin / Coordinator)

✅ **Teknik Yapı**
- Katmanlı mimari: `database/`, `models/`, `services/`, `UI/`, `utils/`
- `psycopg2` bağlantı havuzu
- `dataclasses` tabanlı model mimarisi
- Excel: `pandas` + `openpyxl`
- PDF: `ReportLab`

---

## 🧠 Sistem Mimarisi
```
┌────────────────────────┐
│     UI Layer           │ → PyQt5 (MainWindow, AdminDashboard, CoordinatorDashboard)
└────────────────────────┘
           ↓
┌────────────────────────┐
│   Service Layer        │ → ExamScheduler, ExcelService, SeatingPlanGenerator
└────────────────────────┘
           ↓
┌────────────────────────┐
│    Model Layer         │ → dataclass modelleri (Course, Student, Exam, vb.)
└────────────────────────┘
           ↓
┌────────────────────────┐
│   Database Layer       │ → PostgreSQL (createtable.sql, connection pool)
└────────────────────────┘
```

---

## 🖥️ Ekran Görselleri

> `screenshots/` klasörüne şu görselleri ekleyebilirsiniz:
> - `login_screen.png` → Giriş ekranı
> - `admin_dashboard.png` → Admin paneli
> - `coordinator_dashboard.png` → Koordinatör paneli
> - `exam_schedule.png` → Sınav takvimi örneği
> - `seating_plan.png` → Oturma planı PDF görünümü

## 🖥️ Ekran Görselleri

### Giriş Ekranı
![Login Screen](https://github.com/user-attachments/assets/c44f3f61-4ba4-4133-9faa-36c0ce113008)

### Koordinatör Paneli
![Coordinator Dashboard](https://github.com/user-attachments/assets/35e5d629-65b4-49ce-a8d9-5e865c9e34ca)

### Sınav Takvimi
![Exam Schedule](https://github.com/user-attachments/assets/af509cda-0078-46f0-a0ca-8a8dadf028e9)

---

## ⚙️ Kurulum ve Çalıştırma

### 1️⃣ Gerekli bağımlılıkları yükle
```bash
pip install -r requirements.txt
```

`requirements.txt` içinde temel kütüphaneler: `PyQt5`, `psycopg2`, `pandas`, `openpyxl`, `reportlab`, `python-dotenv`

### 2️⃣ PostgreSQL Veritabanını oluştur
```sql
CREATE DATABASE obs_exam_scheduler;
```

### 3️⃣ Ortam değişkenlerini tanımla

Proje kök dizinine `.env` dosyası ekleyin:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=obs_exam_scheduler
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### 4️⃣ Tabloları oluştur
```bash
psql -U postgres -d obs_exam_scheduler -f database/createtable.sql
```

### 5️⃣ Uygulamayı çalıştır
```bash
python main.py
```

---

## 🧩 Kullanıcı Bilgileri

Varsayılan yönetici hesabı:
```
Email: admin@university.edu
Şifre: admin123
```

---

## 📦 Dizin Yapısı
```
YazLab1/
│
├── main.py
├── .env
├── requirements.txt
│
├── database/
│   ├── connection.py
│   ├── db.py
│   ├── init_db.py
│   ├── table_manager.py
│   └── createtable.sql
│
├── models/
│   ├── base_model.py
│   ├── course.py
│   ├── student.py
│   ├── exam.py
│   ├── exam_schedule.py
│   └── user.py
│
├── services/
│   ├── exam_scheduler.py
│   ├── excel_service.py
│   ├── seating_plan_generator.py
│   └── auth_service.py
│
├── UI/
│   ├── main_window.py
│   ├── login_window.py
│   ├── admin_dashboard.py
│   └── coordinator_dashboard.py
│
└── utils/
    ├── helpers.py
    └── constants.py
```

---

## 🧠 Akış Diyagramı
```
Kullanıcı Girişi
    ↓
Rol Kontrolü (Admin / Coordinator)
    ↓
Veritabanı bağlantısı ve tablo kontrolü
    ↓
Derslik + Ders + Öğrenci Excel yükleme
    ↓
Sınav Takvimi Oluştur
    ↓
Çakışma Çözümü & Derslik Ataması
    ↓
Oturma Planı Oluştur (PDF)
    ↓
Excel ve PDF Dışa Aktarım
```

---

## 👥 Katkı Sağlayanlar

- **Yunus Emre Ayıker ve Enes ÜLKÜ** – Backend & Veritabanı Tasarımı
- **Yunus Emre Ayıker** – Arayüz (PyQt5) & UI/UX
- **Yunus Emre Ayıker** – Excel & PDF Modülleri
- **Enes ÜLKÜ** – Test & Raporlama

---

## 🌐 İletişim

📧 `enes107148@gmail.com`  
💻 **Proje:** [GitHub Repository Linkini Buraya Yaz](https://github.com/kullanici-adi/repo-adi)

---

## 📝 Notlar

- PostgreSQL şifrenizi `.env` dosyasına göre düzenleyin
- Ekran görüntülerini `screenshots/` klasörüne ekleyin
- Katkı sağlayan isimleri ve GitHub linkini güncelleyin
