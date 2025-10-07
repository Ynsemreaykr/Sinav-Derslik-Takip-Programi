# ui/student_view.py
from PyQt5 import QtWidgets
from models.student import Student
from services import student_service as svc

class StudentView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self.load()

    def _build(self):
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ad", "No", "Email"])
        self.name = QtWidgets.QLineEdit(); self.name.setPlaceholderText("Ad Soyad")
        self.no   = QtWidgets.QLineEdit(); self.no.setPlaceholderText("Öğrenci No")
        self.dep  = QtWidgets.QLineEdit(); self.dep.setPlaceholderText("Bölüm ID")
        self.mail = QtWidgets.QLineEdit(); self.mail.setPlaceholderText("E-posta")
        add = QtWidgets.QPushButton("Ekle"); add.clicked.connect(self.add_student)
        refresh = QtWidgets.QPushButton("Yenile"); refresh.clicked.connect(self.load)

        top = QtWidgets.QHBoxLayout()
        for w in (self.name, self.no, self.dep, self.mail, add, refresh):
            top.addWidget(w)

        lay = QtWidgets.QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.table)

    def load(self):
        sts = svc.list_students()
        self.table.setRowCount(0)
        for s in sts:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(s.id)))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(s.name or ""))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(s.student_no or ""))
            self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(s.email or ""))

    def add_student(self):
        s = Student(
            name=self.name.text().strip(),
            student_no=self.no.text().strip(),
            department_id=int(self.dep.text()),
            email=self.mail.text().strip() or None
        )
        svc.create_student(s)
        self.load()
