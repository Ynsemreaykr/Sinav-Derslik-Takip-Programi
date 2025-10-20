from PyQt5 import QtWidgets
from models.user import User
from services.auth_service import create_coordinator
from services.db import fetch_all
from services.excel_service import import_departments


class AdminDashboard(QtWidgets.QWidget):
    """🔹 Admin paneli — tüm sistem yönetimi"""
    def __init__(self, user: User, on_logout=None):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self._build_ui()

    # ==================================================
    # 🧱 ARAYÜZ YAPISI
    # ==================================================
    def _build_ui(self):
        self.setWindowTitle(f"Admin Dashboard - {self.user.email}")
        self.setMinimumSize(900, 600)

        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel(f"👋 Hoş geldiniz, {self.user.email}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Üst butonlar
        btn_layout = QtWidgets.QHBoxLayout()

        self.btn_add_coord = QtWidgets.QPushButton("🧑‍🏫 Bölüm Koordinatörü Ekle")
        self.btn_add_coord.clicked.connect(self._open_add_coord_dialog)
        btn_layout.addWidget(self.btn_add_coord)

        self.btn_list_users = QtWidgets.QPushButton("👥 Kullanıcıları Görüntüle")
        self.btn_list_users.clicked.connect(self._show_users)
        btn_layout.addWidget(self.btn_list_users)

        self.btn_logout = QtWidgets.QPushButton("🚪 Çıkış Yap")
        self.btn_logout.clicked.connect(self._logout)
        btn_layout.addWidget(self.btn_logout)

        layout.addLayout(btn_layout)

        # Bilgi alanı
        self.info_box = QtWidgets.QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlaceholderText("📄 Yapılan işlemler burada görüntülenecek...")
        layout.addWidget(self.info_box)

        self.setLayout(layout)

    # ==================================================
    # 👥 Kullanıcı Listeleme
    # ==================================================
    def _show_users(self):
        """Veritabanındaki tüm kullanıcıları listele"""
        try:
            users = fetch_all("SELECT id, email, role, department_id FROM users ORDER BY id")
            if not users:
                self.info_box.setText("⚠️ Hiç kullanıcı bulunamadı.")
                return

            text = "=== KAYITLI KULLANICILAR ===\n\n"
            for u in users:
                text += f"🆔 ID: {u['id']}\n"
                text += f"📧 E-posta: {u['email']}\n"
                text += f"🎭 Rol: {u['role']}\n"
                text += f"🏛 Bölüm ID: {u['department_id']}\n"
                text += "-" * 40 + "\n"

            self.info_box.setText(text)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenemedi:\n{e}")

    # ==================================================
    # ➕ Koordinatör Ekleme
    # ==================================================
    def _open_add_coord_dialog(self):
        """Yeni koordinatör ekleme ekranı"""
        dialog = AddCoordinatorDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.info_box.append("✅ Yeni koordinatör başarıyla eklendi.\n")

    # ==================================================
    # 🚪 Çıkış
    # ==================================================
    def _logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Çıkış",
            "Çıkış yapmak istiyor musunuz?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes and self.on_logout:
            self.on_logout()


# ==================================================
# 🧑‍🏫 Koordinatör Ekleme Penceresi
# ==================================================
class AddCoordinatorDialog(QtWidgets.QDialog):
    """Yeni bölüm koordinatörü ekleme arayüzü"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("🧩 Yeni Bölüm Koordinatörü Ekle")
        self.setFixedSize(420, 320)

        layout = QtWidgets.QFormLayout()

        # Email alanı
        self.txt_email = QtWidgets.QLineEdit()
        self.txt_email.setPlaceholderText("örnek@university.edu")
        layout.addRow("📧 E-posta:", self.txt_email)

        # Şifre alanı
        self.txt_password = QtWidgets.QLineEdit()
        self.txt_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_password.setPlaceholderText("Minimum 6 karakter")
        layout.addRow("🔑 Şifre:", self.txt_password)

        # Bölüm seçimi
        self.combo_department = QtWidgets.QComboBox()
        self._load_departments()
        layout.addRow("🏛 Bölüm:", self.combo_department)

        # Butonlar
        btn_layout = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("💾 Kaydet")
        btn_save.clicked.connect(self._save)
        btn_cancel = QtWidgets.QPushButton("❌ İptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    # ==================================================
    # 🏛 Bölüm Yükleme
    # ==================================================
    def _load_departments(self):
        try:
            departments = fetch_all("SELECT id, name FROM departments ORDER BY id")
            if not departments:
                # hiç yoksa oluştur
                import_departments()
                departments = fetch_all("SELECT id, name FROM departments ORDER BY id")

            self.combo_department.clear()
            for dept in departments:
                self.combo_department.addItem(dept["name"], dept["id"])

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Bölümler yüklenemedi:\n{e}")

    # ==================================================
    # 💾 Kaydetme İşlemi
    # ==================================================
    def _save(self):
        email = self.txt_email.text().strip()
        password = self.txt_password.text().strip()
        department_id = self.combo_department.currentData()

        if not email or "@" not in email:
            QtWidgets.QMessageBox.warning(self, "Geçersiz Giriş", "Lütfen geçerli bir e-posta girin!")
            return

        if len(password) < 6:
            QtWidgets.QMessageBox.warning(self, "Hatalı Şifre", "Şifre en az 6 karakter olmalıdır!")
            return

        if department_id is None:
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Bir bölüm seçmelisiniz!")
            return

        try:
            success = create_coordinator(email, password, department_id)
            if success:
                QtWidgets.QMessageBox.information(
                    self, "Başarılı", f"Yeni koordinatör eklendi!\n📧 {email}"
                )
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Hata", "Bu e-posta zaten kayıtlı!"
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"İşlem başarısız:\n{e}")
