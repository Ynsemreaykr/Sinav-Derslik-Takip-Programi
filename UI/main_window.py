from PyQt5 import QtWidgets
from UI.login_window import LoginWindow
from UI.admin_dashboard import AdminDashboard

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OBS Exam Scheduler")
        self.setGeometry(100, 100, 900, 600)

        # Login ekranını oluştur
        self.login_window = LoginWindow(self.open_dashboard)
        self.setCentralWidget(self.login_window)

    def open_dashboard(self, user):
        """Login başarılı olursa çağrılır."""
        self.dashboard = AdminDashboard()
        self.setCentralWidget(self.dashboard)
