from PyQt5 import QtWidgets, QtGui, QtCore
from services.auth_service import authenticate_user, ensure_default_admin
from models.user import User

class LoginWindow(QtWidgets.QWidget):
    """
     Kullanıcı Giriş Ekranı
    - `on_success`: Giriş başarılı olduğunda çağrılacak callback (örneğin main_window.open_dashboard)
    """
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success
        self.current_user: User | None = None
        self._setup_ui()

        try:
            ensure_default_admin()
        except Exception as e:
            print(f"[WARN] Varsayılan admin oluşturulamadı: {e}")

    def _setup_ui(self):
        self.setWindowTitle("Dinamik Sınav Takvimi - Giriş")

        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.setGeometry(screen_geometry)
        self.showMaximized()

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            }
        """)

        left_widget = QtWidgets.QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setAlignment(QtCore.Qt.AlignCenter)

        lbl_deco = QtWidgets.QLabel("📊\n📚\n🎓")
        lbl_deco.setStyleSheet("""
            font-size: 60px;
            color: rgba(255, 255, 255, 0.3);
            line-height: 1.5;
        """)
        lbl_deco.setAlignment(QtCore.Qt.AlignCenter)
        left_layout.addWidget(lbl_deco)
        
        main_layout.addWidget(left_widget, 1)

        center_widget = QtWidgets.QWidget()
        center_widget.setMaximumWidth(500)
        center_widget.setStyleSheet("background: transparent;")
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setAlignment(QtCore.Qt.AlignCenter)

        form_card = QtWidgets.QWidget()
        form_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 20px;
            }
        """)
        form_card_layout = QtWidgets.QVBoxLayout(form_card)
        form_card_layout.setContentsMargins(50, 40, 50, 40)
        form_card_layout.setSpacing(15)

        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setAlignment(QtCore.Qt.AlignCenter)
        header_layout.setContentsMargins(0, 0, 0, 20)

        lbl_icon = QtWidgets.QLabel("🎓")
        lbl_icon.setAlignment(QtCore.Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 70px;")
        header_layout.addWidget(lbl_icon)

        lbl_title = QtWidgets.QLabel("Dinamik Sınav Takvimi")
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        lbl_title.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #333;
            margin-top: 10px;
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QtWidgets.QLabel("Otomasyon Sistemi")
        lbl_subtitle.setAlignment(QtCore.Qt.AlignCenter)
        lbl_subtitle.setStyleSheet("""
            font-size: 15px;
            color: #666;
            margin-top: 5px;
            margin-bottom: 20px;
        """)
        header_layout.addWidget(lbl_subtitle)
        
        form_card_layout.addLayout(header_layout)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0; max-height: 2px;")
        form_card_layout.addWidget(line)
        form_card_layout.addSpacing(10)

        lbl_login = QtWidgets.QLabel("Giriş Bilgileriniz")
        lbl_login.setAlignment(QtCore.Qt.AlignCenter)
        lbl_login.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #555;
            margin-bottom: 10px;
        """)
        form_card_layout.addWidget(lbl_login)

        lbl_email = QtWidgets.QLabel("📧 E-posta")
        lbl_email.setStyleSheet("font-size: 13px; font-weight: bold; color: #555;")
        form_card_layout.addWidget(lbl_email)
        
        self.txt_email = QtWidgets.QLineEdit()
        self.txt_email.setPlaceholderText("admin@university.edu")
        self.txt_email.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                font-size: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
        """)
        form_card_layout.addWidget(self.txt_email)

        lbl_pass = QtWidgets.QLabel("🔒 Şifre")
        lbl_pass.setStyleSheet("font-size: 13px; font-weight: bold; color: #555;")
        form_card_layout.addWidget(lbl_pass)
        
        self.txt_pass = QtWidgets.QLineEdit()
        self.txt_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Şifrenizi giriniz")
        self.txt_pass.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                font-size: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
        """)
        form_card_layout.addWidget(self.txt_pass)

        self.btn_login = QtWidgets.QPushButton("🔑 Giriş Yap")
        self.btn_login.setStyleSheet("""
            QPushButton {
                padding: 16px;
                font-size: 17px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 10px;
                border: none;
                margin-top: 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6a3d91);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bbd, stop:1 #5d3580);
            }
        """)
        self.btn_login.setCursor(QtCore.Qt.PointingHandCursor)
        self.btn_login.clicked.connect(self._handle_login)
        form_card_layout.addWidget(self.btn_login)

        self.lbl_status = QtWidgets.QLabel("Lütfen giriş bilgilerinizi giriniz")
        self.lbl_status.setStyleSheet("""
            color: #999;
            font-size: 12px;
            margin-top: 10px;
        """)
        self.lbl_status.setAlignment(QtCore.Qt.AlignCenter)
        form_card_layout.addWidget(self.lbl_status)

        lbl_info = QtWidgets.QLabel("ℹ️ Varsayılan: admin@university.edu / admin123")
        lbl_info.setAlignment(QtCore.Qt.AlignCenter)
        lbl_info.setStyleSheet("""
            font-size: 11px;
            color: #666;
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 5px;
            margin-top: 15px;
        """)
        form_card_layout.addWidget(lbl_info)
        
        center_layout.addWidget(form_card)
        main_layout.addWidget(center_widget, 2)

        right_widget = QtWidgets.QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setAlignment(QtCore.Qt.AlignCenter)

        lbl_deco2 = QtWidgets.QLabel("🏫\n📝\n📅")
        lbl_deco2.setStyleSheet("""
            font-size: 60px;
            color: rgba(255, 255, 255, 0.3);
            line-height: 1.5;
        """)
        lbl_deco2.setAlignment(QtCore.Qt.AlignCenter)
        right_layout.addWidget(lbl_deco2)
        
        main_layout.addWidget(right_widget, 1)
        
        self.setLayout(main_layout)

        self.txt_pass.returnPressed.connect(self._handle_login)
        self.txt_email.returnPressed.connect(self._handle_login)

    def _handle_login(self):
        """Giriş butonuna tıklanınca çalışır"""
        email = self.txt_email.text().strip()
        password = self.txt_pass.text().strip()

        if not email or not password:
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Lütfen e-posta ve şifre giriniz.")
            return

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
