from PyQt5 import QtWidgets
from services.db import fetch_one


class LoginWindow(QtWidgets.QWidget):
    """
    Basit kullanıcı giriş ekranı.
    on_success parametresi: giriş başarılı olduğunda çalışacak fonksiyon.
    (örnek: main_window içindeki open_dashboard fonksiyonu)
    """
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("OBS Exam Scheduler - Giriş")
        self.setFixedSize(400, 250)

        # --- Etiketler ve giriş alanları ---
        lbl_title = QtWidgets.QLabel("OBS Exam Scheduler Giriş")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")

        lbl_email = QtWidgets.QLabel("E-posta:")
        self.txt_email = QtWidgets.QLineEdit()
        self.txt_email.setPlaceholderText("örnek: admin@obs.local")

        lbl_pass = QtWidgets.QLabel("Şifre:")
        self.txt_pass = QtWidgets.QLineEdit()
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_pass.setPlaceholderText("şifrenizi giriniz")

        # --- Giriş butonu ---
        self.btn_login = QtWidgets.QPushButton("Giriş Yap")
        self.btn_login.clicked.connect(self.handle_login)

        # --- Layout oluştur ---
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(lbl_email, self.txt_email)
        form_layout.addRow(lbl_pass, self.txt_pass)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(lbl_title)
        main_layout.addSpacing(15)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.btn_login)
        self.setLayout(main_layout)

    # ===============================================================
    #  GİRİŞ BUTONUNA TIKLANINCA ÇALIŞAN FONKSİYON
    # ===============================================================
    def handle_login(self):
        email = self.txt_email.text().strip()
        password = self.txt_pass.text().strip()

        if not email or not password:
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Lütfen e-posta ve şifre giriniz.")
            return

        # --- Veritabanı kontrolü ---
        sql = "SELECT id, email, role FROM users WHERE email = %s AND password = %s"
        user = fetch_one(sql, [email, password])

        if user:
            QtWidgets.QMessageBox.information(self, "Giriş Başarılı", f"Hoş geldin {user['email']}!")
            if self.on_success:
                self.on_success(user)
        else:
            QtWidgets.QMessageBox.critical(self, "Hatalı Giriş", "E-posta veya şifre yanlış!")
