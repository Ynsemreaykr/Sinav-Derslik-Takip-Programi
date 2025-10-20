from PyQt5 import QtWidgets, QtCore
from UI.login_window import LoginWindow
from UI.admin_dashboard import AdminDashboard
from UI.coordinator_dashboard import CoordinatorDashboard
from models.user import User


class MainWindow(QtWidgets.QMainWindow):
    """
    🧭 Uygulama Ana Penceresi
    - Giriş, dashboard yönlendirme ve çıkış işlemlerini yönetir.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBS Exam Scheduler")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)

        # Mevcut oturumdaki kullanıcı
        self.current_user: User | None = None
        self.dashboard = None
        self.login_window = None

        # İlk olarak giriş ekranını göster
        self.show_login()

        # Pencereyi ortala
        self._center_on_screen()

    # ==========================================================
    # 🔐 GİRİŞ EKRANI
    # ==========================================================
    def show_login(self):
        """Giriş ekranını göster"""
        self.login_window = LoginWindow(on_success=self.open_dashboard)
        self.setCentralWidget(self.login_window)

    # ==========================================================
    # 🧩 DASHBOARD AÇILIŞI
    # ==========================================================
    def open_dashboard(self, user: User):
        """
        Giriş başarılı olduğunda çağrılır.
        Kullanıcı rolüne göre uygun dashboard açılır.
        """
        self.current_user = user

        # Mevcut dashboard’ı temizle
        if self.dashboard:
            self.dashboard.deleteLater()

        # Rol tabanlı yönlendirme
        if user.is_admin():
            self.dashboard = AdminDashboard(user, on_logout=self.handle_logout)
            self.setCentralWidget(self.dashboard)

        elif user.is_coordinator():
            self.dashboard = CoordinatorDashboard(user, on_logout=self.handle_logout)
            self.setCentralWidget(self.dashboard)

        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Erişim Hatası",
                f"Bilinmeyen kullanıcı rolü: {user.role}\nLütfen sistem yöneticisiyle iletişime geçin."
            )
            self.handle_logout()

    # ==========================================================
    # 🚪 ÇIKIŞ / OTURUM KAPATMA
    # ==========================================================
    def handle_logout(self):
        """Kullanıcı çıkış yaptığında login ekranına döner"""
        self.current_user = None

        # Mevcut dashboard’ı kapat
        if self.dashboard:
            self.dashboard.deleteLater()
            self.dashboard = None

        # Login ekranını tekrar göster
        self.show_login()

    # ==========================================================
    # 🖥️ PENCERE MERKEZLEME
    # ==========================================================
    def _center_on_screen(self):
        """Ana pencereyi ekranın ortasına yerleştirir"""
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
