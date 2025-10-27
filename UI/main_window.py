from PyQt5 import QtWidgets, QtCore
from UI.login_window import LoginWindow
from UI.admin_dashboard import AdminDashboard
from UI.coordinator_dashboard import CoordinatorDashboard
from models.user import User

class MainWindow(QtWidgets.QMainWindow):
    """
     Uygulama Ana Penceresi
    - Giriş, dashboard yönlendirme ve çıkış işlemlerini yönetir.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dinamik Sinav Takvimi Olusturma Sistemi")

        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        self.setGeometry(screen_geometry)

        self.setMinimumSize(1024, 768)

        self.current_user: User | None = None
        self.dashboard = None
        self.login_window = None

        self.show_login()

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
            self.dashboard = AdminDashboard(
                user, 
                on_logout=self.handle_logout,
                on_dept_access=self.open_department_as_admin
            )
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

    def open_department_as_admin(self, temp_user: User):
        """Admin bölüm yönetimine erişir (aynı pencerede)"""
        if not hasattr(self, 'original_admin_user'):
            self.original_admin_user = self.current_user

        if self.dashboard:
            self.dashboard.deleteLater()
        
        self.dashboard = CoordinatorDashboard(
            temp_user, 
            on_logout=self.return_to_admin
        )
        self.setCentralWidget(self.dashboard)
    
    def return_to_admin(self):
        """Koordinatör panelinden admin paneline geri dön"""
        if hasattr(self, 'original_admin_user'):

            if self.dashboard:
                self.dashboard.deleteLater()
            
            self.dashboard = AdminDashboard(
                self.original_admin_user,
                on_logout=self.handle_logout,
                on_dept_access=self.open_department_as_admin
            )
            self.setCentralWidget(self.dashboard)

            delattr(self, 'original_admin_user')
        else:
            self.handle_logout()

    def handle_logout(self):
        """Kullanıcı çıkış yaptığında login ekranına döner"""
        self.current_user = None

        if self.dashboard:
            self.dashboard.deleteLater()
            self.dashboard = None

        if hasattr(self, 'original_admin_user'):
            delattr(self, 'original_admin_user')

        self.show_login()

    def _center_on_screen(self):
        """Ana pencereyi ekranın ortasına yerleştirir"""
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
