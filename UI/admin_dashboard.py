# ui/admin_dashboard.py
from PyQt5 import QtWidgets
from UI.student_view import StudentView

class AdminDashboard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(StudentView(), "Öğrenciler")
        # ileride: tabs.addTab(ClassroomView(), "Derslikler")
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(tabs)
