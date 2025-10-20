from PyQt5 import QtWidgets, QtGui, QtCore
from services.auth_service import authenticate_user, ensure_default_admin
from models.user import User


class LoginWindow(QtWidgets.QWidget):
    """
    🔐 Kullanıcı Giriş Ekranı
    - `on_success`: Giriş başarılı olduğunda çağrılacak callback (örneğin main_window.open_dashboard)
    """
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success
        self.current_user: User | None = None
        self._setup_ui()

        # Varsayılan admini kontrol et / oluştur
        try:
            ensure_default_admin()
        except Exception as e:
            print(f"[WARN] Varsayılan admin oluşturulamadı: {e}")

    # ==========================================================
    # 🧱 ARAYÜZ TASARIMI
    # ==========================================================
    def _setup_ui(self):
        self.setWindowTitle("OBS Exam Scheduler - Giriş")
        self.setFixedSize(420, 260)
        self.setStyleSheet("""
            QLabel { font-size: 14px; }
            QLineEdit { padding: 6px; font-size: 13px; }
            QPushButton {
                padding: 8px; font-size: 14px;
                background-color: #2E8B57; color: white; border-radius: 6px;
            }
            QPushButton:hover { background-color: #3CB371; }
        """)

        # Başlık
        lbl_title = QtWidgets.QLabel("📘 OBS Exam Scheduler Giriş")
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size:18px; font-weight:bold; margin-bottom:15px;")

        # Form alanları
        lbl_email = QtWidgets.QLabel("E-posta:")
        self.txt_email = QtWidgets.QLineEdit()
        self.txt_email.setPlaceholderText("örnek: admin@university.edu")

        lbl_pass = QtWidgets.QLabel("Şifre:")
        self.txt_pass = QtWidgets.QLineEdit()
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Şifrenizi giriniz")

        # Giriş butonu
        self.btn_login = QtWidgets.QPushButton("🔑 Giriş Yap")
        self.btn_login.clicked.connect(self._handle_login)

        # Alt bilgi
        self.lbl_status = QtWidgets.QLabel("Lütfen e-posta ve şifrenizi giriniz.")
        self.lbl_status.setStyleSheet("color: gray; font-size: 12px; margin-top: 5px;")
        self.lbl_status.setAlignment(QtCore.Qt.AlignCenter)

        # Layout
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(lbl_email, self.txt_email)
        form_layout.addRow(lbl_pass, self.txt_pass)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(lbl_title)
        main_layout.addSpacing(10)
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.btn_login)
        main_layout.addWidget(self.lbl_status)
        self.setLayout(main_layout)

        # Enter tuşuna basıldığında login çalışsın
        self.txt_pass.returnPressed.connect(self._handle_login)
        self.txt_email.returnPressed.connect(self._handle_login)

    # ==========================================================
    # 🔐 GİRİŞ İŞLEMİ
    # ==========================================================
    def _handle_login(self):
        """Giriş butonuna tıklanınca çalışır"""
        email = self.txt_email.text().strip()
        password = self.txt_pass.text().strip()

        if not email or not password:
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Lütfen e-posta ve şifre giriniz.")
            return

        # Veritabanında doğrulama
        user = authenticate_user(email, password)
        if user:
            self.current_user = user
            QtWidgets.QMessageBox.information(
                self,
                "Giriş Başarılı",
                f"Hoş geldiniz, {user.email}\nRol: {user.role.value}"
            )

            if self.on_success:
                self.on_success(user)
                self.close()
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "Hatalı Giriş",
                "E-posta veya şifre yanlış!\n\nVarsayılan giriş bilgisi:\nadmin@university.edu / admin123"
            )
            self.lbl_status.setText("❌ Giriş başarısız. Lütfen tekrar deneyin.")
