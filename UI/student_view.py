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

        self.current_user: User | None = None
        self.dashboard = None
        self.login_window = None

        self.show_login()

        self._center_on_screen()

    def show_login(self):
        """Giriş ekranını göster"""
        self.login_window = LoginWindow(on_success=self.open_dashboard)
        self.setCentralWidget(self.login_window)

    def open_dashboard(self, user: User):
        """
        Giriş başarılı olduğunda çağrılır.
        Kullanıcı rolüne göre uygun dashboard açılır.
        """
        self.current_user = user

        if self.dashboard:
            self.dashboard.deleteLater()

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

    def handle_logout(self):
        """Kullanıcı çıkış yaptığında login ekranına döner"""
        self.current_user = None

        if self.dashboard:
            self.dashboard.deleteLater()
            self.dashboard = None

        self.show_login()

    def _center_on_screen(self):
        """Ana pencereyi ekranın ortasına yerleştirir"""
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
