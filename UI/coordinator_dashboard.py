# UI/coordinator_dashboard.py
from PyQt5 import QtWidgets, QtCore, QtGui
from models.user import User
from services.db import fetch_all, execute
from services.classroom_service import ClassroomService

class CoordinatorDashboard(QtWidgets.QWidget):
    """Bolum koordinatoru dashboard"""
    def __init__(self, user: User, on_logout=None):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.classroom_service = ClassroomService()
        self.setup_ui()

    def setup_ui(self):
        # Bolum adini al
        dept_name = self.get_department_name()
        self.setWindowTitle(f"Koordinator Dashboard - {dept_name}")
        self.setMinimumSize(1000, 700)

        # Ana layout
        main_layout = QtWidgets.QVBoxLayout()

        # Hosgeldin mesaji
        welcome_label = QtWidgets.QLabel(f"Hos geldiniz, {self.user.email}\nBolum: {dept_name}")
        welcome_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(welcome_label)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()

        # Tab 1: Derslik Yonetimi (her zaman aktif)
        self.classroom_tab = self.create_classroom_tab()
        self.tabs.addTab(self.classroom_tab, "Derslik Yonetimi")

        # Tab 2: Ders Listesi Yukleme
        self.course_tab = self.create_course_tab()
        self.course_tab_index = self.tabs.addTab(self.course_tab, "Ders Listesi Yukle")

        # Tab 3: Ogrenci Listesi Yukleme
        self.student_tab = self.create_student_tab()
        self.student_tab_index = self.tabs.addTab(self.student_tab, "Ogrenci Listesi Yukle")

        # Tab 4: Ogrenci Listesi
        self.student_list_tab = self.create_student_list_tab()
        self.student_list_tab_index = self.tabs.addTab(self.student_list_tab, "Ogrenci Listesi")

        # Tab 5: Ders Listesi
        self.course_list_tab = self.create_course_list_tab()
        self.course_list_tab_index = self.tabs.addTab(self.course_list_tab, "Ders Listesi")
        
        # Tab 6: Sinav Programi Olustur
        try:
            self.exam_schedule_tab = self.create_exam_schedule_tab()
            self.exam_schedule_tab_index = self.tabs.addTab(self.exam_schedule_tab, "Sinav Programi Olustur")
        except Exception as e:
            print(f"Sinav programi tab olusturma hatasi: {e}")
            self.exam_schedule_tab_index = None

        main_layout.addWidget(self.tabs)

        # Baslangicta diger tab'leri devre disi birak
        self.check_classroom_requirement()

        # Cikis butonu
        btn_logout = QtWidgets.QPushButton("Cikis Yap")
        btn_logout.clicked.connect(self.logout)
        main_layout.addWidget(btn_logout)

        self.setLayout(main_layout)

    def check_classroom_requirement(self):
        """Derslik girilmeden diger tab'leri devre disi birak"""
        try:
            classrooms = fetch_all(
                "SELECT COUNT(*) as count FROM classrooms WHERE department_id = %s",
                [self.user.department_id]
            )

            has_classrooms = classrooms[0]['count'] > 0 if classrooms else False

            # Derslik yoksa diger tab'leri devre disi birak
            if hasattr(self, 'course_tab_index'):
                self.tabs.setTabEnabled(self.course_tab_index, has_classrooms)
            if hasattr(self, 'student_tab_index'):
                self.tabs.setTabEnabled(self.student_tab_index, has_classrooms)
            if hasattr(self, 'student_list_tab_index'):
                self.tabs.setTabEnabled(self.student_list_tab_index, has_classrooms)
            if hasattr(self, 'course_list_tab_index'):
                self.tabs.setTabEnabled(self.course_list_tab_index, has_classrooms)
            if hasattr(self, 'exam_schedule_tab_index') and self.exam_schedule_tab_index is not None:
                self.tabs.setTabEnabled(self.exam_schedule_tab_index, has_classrooms)

            if not has_classrooms:
                # Uyari mesaji goster (sadece ilk acilista)
                if not hasattr(self, '_classroom_warning_shown'):
                    QtWidgets.QMessageBox.information(
                        self,
                        "Bilgilendirme",
                        "Diger islemleri yapabilmek icin once en az bir derslik eklemelisiniz!"
                    )
                    self._classroom_warning_shown = True

        except Exception as e:
            print(f"Tab kontrol hatasi: {e}")

    def get_department_name(self):
        """Bolum adini al"""
        try:
            result = fetch_all(
                "SELECT name FROM departments WHERE id = %s",
                [self.user.department_id]
            )
            if result:
                return result[0]['name']
        except:
            pass
        return "Bilinmeyen Bolum"

    def create_classroom_tab(self):
        """Derslik yonetimi tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Baslik
        title = QtWidgets.QLabel("Derslik Yonetimi")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Butonlar
        btn_layout = QtWidgets.QHBoxLayout()

        btn_add = QtWidgets.QPushButton("Yeni Derslik Ekle")
        btn_add.clicked.connect(self.add_classroom)
        btn_layout.addWidget(btn_add)

        btn_search = QtWidgets.QPushButton("Derslik Ara")
        btn_search.clicked.connect(self.search_classroom)
        btn_layout.addWidget(btn_search)

        btn_refresh = QtWidgets.QPushButton("Listeyi Yenile")
        btn_refresh.clicked.connect(self.refresh_classrooms)
        btn_layout.addWidget(btn_refresh)

        layout.addLayout(btn_layout)

        # Derslik listesi tablosu
        self.classroom_table = QtWidgets.QTableWidget()
        self.classroom_table.setColumnCount(8)
        self.classroom_table.setHorizontalHeaderLabels([
            "ID", "Kod", "Ad", "Kapasite", "Satir", "Sutun", "Sira Yapisi", "Sil"
        ])
        self.classroom_table.horizontalHeader().setStretchLastSection(True)
        self.classroom_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.classroom_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        # Sag tik menu
        self.classroom_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.classroom_table.customContextMenuRequested.connect(self.classroom_context_menu)

        layout.addWidget(self.classroom_table)

        widget.setLayout(layout)

        # Derslikleri yukle
        self.refresh_classrooms()

        return widget

    def create_course_tab(self):
        """Ders listesi yukleme tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Ders Listesi Yukleme")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        info = QtWidgets.QLabel(
            "Excel dosyasini yukleyerek ders listesini sisteme aktarabilirsiniz.\n"
            "Excel formatı: Ders Kodu | Ders Adi | Ogretim Elemani"
        )
        layout.addWidget(info)

        # Butonlar
        btn_layout = QtWidgets.QHBoxLayout()
        
        btn_upload = QtWidgets.QPushButton("Excel Dosyasi Sec ve Yukle")
        btn_upload.clicked.connect(self.upload_courses_excel)
        btn_layout.addWidget(btn_upload)
        
        btn_clear = QtWidgets.QPushButton("Ders Listesini Temizle")
        btn_clear.setStyleSheet("background-color: #ff6b6b; color: white;")
        btn_clear.clicked.connect(self.clear_courses)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)

        self.course_upload_log = QtWidgets.QTextEdit()
        self.course_upload_log.setReadOnly(True)
        self.course_upload_log.setPlaceholderText("Yukleme bilgileri burada gorunecek...")
        layout.addWidget(self.course_upload_log)

        widget.setLayout(layout)
        return widget

    def create_student_tab(self):
        """Ogrenci listesi yukleme tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Ogrenci Listesi Yukleme")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        info = QtWidgets.QLabel(
            "Excel dosyasini yukleyerek ogrenci listesini sisteme aktarabilirsiniz.\n"
            "Excel formatı: Ogrenci No | Ad Soyad | Sinif | Ders Kodu"
        )
        layout.addWidget(info)

        # Butonlar
        btn_layout = QtWidgets.QHBoxLayout()
        
        btn_upload = QtWidgets.QPushButton("Excel Dosyasi Sec ve Yukle")
        btn_upload.clicked.connect(self.upload_students_excel)
        btn_layout.addWidget(btn_upload)
        
        btn_clear = QtWidgets.QPushButton("Ogrenci Listesini Temizle")
        btn_clear.setStyleSheet("background-color: #ff6b6b; color: white;")
        btn_clear.clicked.connect(self.clear_students)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)

        self.student_upload_log = QtWidgets.QTextEdit()
        self.student_upload_log.setReadOnly(True)
        self.student_upload_log.setPlaceholderText("Yukleme bilgileri burada gorunecek...")
        layout.addWidget(self.student_upload_log)

        widget.setLayout(layout)
        return widget

    def create_student_list_tab(self):
        """Ogrenci listesi tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Ogrenci Listesi ve Arama")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Arama kutusu
        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(QtWidgets.QLabel("Ogrenci No/Ad Ara:"))

        self.student_search_input = QtWidgets.QLineEdit()
        self.student_search_input.setPlaceholderText("Kismi arama yapabilirsiniz (ornek: 210, Ahmet)...")
        self.student_search_input.textChanged.connect(self.search_students_live)
        search_layout.addWidget(self.student_search_input)

        btn_refresh = QtWidgets.QPushButton("Tum Listeyi Goster")
        btn_refresh.clicked.connect(self.show_all_students)
        search_layout.addWidget(btn_refresh)

        layout.addLayout(search_layout)

        # Ogrenci listesi tablosu
        self.student_table = QtWidgets.QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels([
            "ID", "Ogrenci No", "Ad Soyad", "Sinif", "Ders Sayisi"
        ])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.student_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.student_table.itemClicked.connect(self.show_student_details)
        layout.addWidget(self.student_table)

        # Detay alani
        self.student_detail = QtWidgets.QTextEdit()
        self.student_detail.setReadOnly(True)
        self.student_detail.setPlaceholderText("Bir ogrenci secin...")
        self.student_detail.setMaximumHeight(200)
        layout.addWidget(self.student_detail)

        widget.setLayout(layout)

        # Baslangicta tum ogrencileri goster
        self.show_all_students()

        return widget

    def create_course_list_tab(self):
        """Ders listesi tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("Ders Listesi")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Ders listesi tablosu
        self.course_table = QtWidgets.QTableWidget()
        self.course_table.setColumnCount(6)
        self.course_table.setHorizontalHeaderLabels([
            "Ders Kodu", "Ders Adi", "Ogretim Elemani", "Sinif", "Tip", "Ogrenci Sayisi"
        ])
        self.course_table.horizontalHeader().setStretchLastSection(True)
        self.course_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.course_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.course_table.itemClicked.connect(self.show_course_students)
        layout.addWidget(self.course_table)

        # Dersi alan ogrenciler
        self.course_students = QtWidgets.QTextEdit()
        self.course_students.setReadOnly(True)
        self.course_students.setPlaceholderText("Bir ders secin...")
        layout.addWidget(self.course_students)

        # Dersleri yukle
        self.refresh_courses()

        widget.setLayout(layout)
        return widget

    # Derslik islemleri
    def add_classroom(self):
        """Yeni derslik ekle"""
        dialog = AddClassroomDialog(self.user.department_id, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_classrooms()

    def search_classroom(self):
        """Derslik ara ve gorsellestir"""
        classroom_id, ok = QtWidgets.QInputDialog.getText(
            self,
            "Derslik Ara",
            "Derslik ID girin:"
        )

        if ok and classroom_id:
            try:
                result = fetch_all(
                    "SELECT * FROM classrooms WHERE id = %s AND department_id = %s",
                    [classroom_id, self.user.department_id]
                )

                if result:
                    classroom = result[0]
                    # Gorsellestirme dialogu
                    dialog = ClassroomVisualizationDialog(classroom, self)
                    dialog.exec_()
                else:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Bulunamadi",
                        "Derslik bulunamadi!"
                    )
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", str(e))

    def refresh_classrooms(self):
        """Derslikleri yenile"""
        try:
            classrooms = fetch_all(
                "SELECT * FROM classrooms WHERE department_id = %s ORDER BY id",
                [self.user.department_id]
            )

            self.classroom_table.setRowCount(len(classrooms))

            for row, classroom in enumerate(classrooms):
                self.classroom_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(classroom['id'])))
                self.classroom_table.setItem(row, 1, QtWidgets.QTableWidgetItem(classroom['code']))
                self.classroom_table.setItem(row, 2, QtWidgets.QTableWidgetItem(classroom['name']))
                self.classroom_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(classroom['capacity'])))
                self.classroom_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(classroom['rows'])))
                self.classroom_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(classroom['cols'])))

                # Enum'u integer'a cevir
                seat_group_str = classroom['seat_group']
                seat_group_display = {"DOUBLE": "2'li", "TRIPLE": "3'lu", "QUAD": "4'lu"}.get(seat_group_str, seat_group_str)
                self.classroom_table.setItem(row, 6, QtWidgets.QTableWidgetItem(seat_group_display))

                # Sil butonu ekle
                btn_delete = QtWidgets.QPushButton("🗑️")
                btn_delete.setFixedSize(40, 30)
                btn_delete.setStyleSheet("background-color: #ff6b6b; color: white; font-size: 16px;")
                btn_delete.clicked.connect(lambda checked, cid=classroom['id']: self.delete_classroom_by_id(cid))
                self.classroom_table.setCellWidget(row, 7, btn_delete)

            # Tab'leri kontrol et - derslik varsa diger tab'leri aktif et
            self.check_classroom_requirement()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Derslikler yuklenemedi: {e}")

    def classroom_context_menu(self, position):
        """Derslik sag tik menusu"""
        menu = QtWidgets.QMenu()

        edit_action = menu.addAction("Duzenle")
        delete_action = menu.addAction("Sil")
        visualize_action = menu.addAction("Gorsellestir")

        action = menu.exec_(self.classroom_table.viewport().mapToGlobal(position))

        if action == edit_action:
            self.edit_classroom()
        elif action == delete_action:
            self.delete_classroom()
        elif action == visualize_action:
            self.visualize_classroom()

    def edit_classroom(self):
        """Derslik duzenle"""
        row = self.classroom_table.currentRow()
        if row >= 0:
            classroom_id = int(self.classroom_table.item(row, 0).text())
            # TODO: Duzenle dialogu
            QtWidgets.QMessageBox.information(self, "Bilgi", "Duzenleme ozelligi yakinda eklenecek!")

    def delete_classroom(self):
        """Derslik sil (sag tik menusu)"""
        row = self.classroom_table.currentRow()
        if row >= 0:
            classroom_id = int(self.classroom_table.item(row, 0).text())
            self.delete_classroom_by_id(classroom_id)

    def delete_classroom_by_id(self, classroom_id):
        """Derslik ID'sine gore sil"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Silme Onay",
            "Bu dersligi silmek istediginizden emin misiniz?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                execute("DELETE FROM classrooms WHERE id = %s", [classroom_id])
                self.refresh_classrooms()
                QtWidgets.QMessageBox.information(self, "Basarili", "Derslik silindi!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", f"Derslik silinemedi: {e}")

    def visualize_classroom(self):
        """Derslik gorsellestir"""
        row = self.classroom_table.currentRow()
        if row >= 0:
            classroom_id = int(self.classroom_table.item(row, 0).text())
            try:
                result = fetch_all("SELECT * FROM classrooms WHERE id = %s", [classroom_id])
                if result:
                    dialog = ClassroomVisualizationDialog(result[0], self)
                    dialog.exec_()
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", str(e))

    # Excel yukleme islemleri
    def upload_courses_excel(self):
        """Ders listesi Excel yukle"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Excel Dosyasi Sec",
            "",
            "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            try:
                from services.excel_service import import_courses_from_excel

                self.course_upload_log.append(f"Dosya yukleniyor: {file_path}")
                self.course_upload_log.append(f"Hedef bolum: {self.user.department_id}")
                
                # ÖNEMLİ: Koordinatörün bölüm ID'sini geçiyoruz!
                count = import_courses_from_excel(file_path, department_id=self.user.department_id)
                
                self.course_upload_log.append(f"Basarili! {count} ders eklendi (Bolum ID: {self.user.department_id}).")

                # Ders listesini yenile
                self.refresh_courses()

            except Exception as e:
                self.course_upload_log.append(f"HATA: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Hata", f"Excel yuklenemedi: {e}")

    def upload_students_excel(self):
        """Ogrenci listesi Excel yukle"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Excel Dosyasi Sec",
            "",
            "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            try:
                from services.excel_service import import_students_from_excel

                self.student_upload_log.append(f"Dosya yukleniyor: {file_path}")
                self.student_upload_log.append(f"Hedef bolum: {self.user.department_id}")
                
                # ÖNEMLİ: Koordinatörün bölüm ID'sini geçiyoruz!
                count = import_students_from_excel(file_path, department_id=self.user.department_id)
                
                self.student_upload_log.append(f"Basarili! {count} ogrenci eklendi (Bolum ID: {self.user.department_id}).")
                
                # Öğrenci listesini yenile
                self.show_all_students()

            except Exception as e:
                self.student_upload_log.append(f"HATA: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Hata", f"Excel yuklenemedi: {e}")

    # Ogrenci arama ve listeleme
    def show_all_students(self):
        """Tum ogrencileri goster"""
        try:
            students = fetch_all("""
                SELECT s.*, COUNT(sc.course_id) as course_count
                FROM students s
                LEFT JOIN enrollments sc ON s.id = sc.student_id
                WHERE s.department_id = %s
                GROUP BY s.id
                ORDER BY s.number
            """, [self.user.department_id])

            self.populate_student_table(students)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Ogrenciler yuklenemedi: {e}")

    def search_students_live(self):
        """Canli arama - her karakter giriste"""
        search_text = self.student_search_input.text().strip()

        if not search_text:
            self.show_all_students()
            return

        try:
            # Bastan itibaren arama - LIKE 'text%'
            # Ornek: '2' yazilinca 2, 21, 210 gelir ama 12 gelmez
            students = fetch_all("""
                SELECT s.*, COUNT(sc.course_id) as course_count
                FROM students s
                LEFT JOIN enrollments sc ON s.id = sc.student_id
                WHERE s.department_id = %s 
                  AND (s.number LIKE %s OR s.fullname ILIKE %s)
                GROUP BY s.id
                ORDER BY s.number
            """, [self.user.department_id, f"{search_text}%", f"%{search_text}%"])

            self.populate_student_table(students)

        except Exception as e:
            print(f"Arama hatasi: {e}")

    def populate_student_table(self, students):
        """Ogrenci tablosunu doldur"""
        self.student_table.setRowCount(len(students))

        for row, student in enumerate(students):
            self.student_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(student['id'])))
            self.student_table.setItem(row, 1, QtWidgets.QTableWidgetItem(student['number']))
            self.student_table.setItem(row, 2, QtWidgets.QTableWidgetItem(student['fullname']))
            self.student_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{student['grade']}. Sinif"))
            self.student_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(student['course_count'])))

    def show_student_details(self, item):
        """Ogrenci detaylarini goster"""
        row = item.row()
        student_id = int(self.student_table.item(row, 0).text())

        try:
            # Ogrenci bilgilerini al
            student = fetch_all("SELECT * FROM students WHERE id = %s", [student_id])
            if not student:
                return
            student = student[0]

            # Ogrencinin aldigi dersleri al
            courses = fetch_all("""
                SELECT c.code, c.name, c.instructor
                FROM courses c
                INNER JOIN enrollments sc ON c.id = sc.course_id
                WHERE sc.student_id = %s
                ORDER BY c.code
            """, [student_id])

            # Detay metni olustur
            detail_text = f"=== OGRENCI DETAYLARI ===\n\n"
            detail_text += f"Ogrenci No: {student['number']}\n"
            detail_text += f"Ad Soyad: {student['fullname']}\n"
            detail_text += f"Sinif: {student['grade']}\n\n"
            detail_text += f"Aldigi Dersler ({len(courses)} ders):\n"
            detail_text += "-" * 50 + "\n"

            if courses:
                for course in courses:
                    detail_text += f"• {course['code']} - {course['name']}\n"
                    detail_text += f"  Ogretim Elemani: {course['instructor']}\n\n"
            else:
                detail_text += "Bu ogrenci henuz ders almamis.\n"

            self.student_detail.setText(detail_text)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Detay yuklenemedi: {e}")

    # Ders listesi
    def refresh_courses(self):
        """Dersleri yenile"""
        try:
            courses = fetch_all("""
                SELECT c.*, COUNT(sc.student_id) as student_count
                FROM courses c
                LEFT JOIN enrollments sc ON c.id = sc.course_id
                WHERE c.department_id = %s
                GROUP BY c.id
                ORDER BY c.grade, c.code
            """, [self.user.department_id])

            self.course_table.setRowCount(len(courses))

            for row, course in enumerate(courses):
                self.course_table.setItem(row, 0, QtWidgets.QTableWidgetItem(course['code']))
                self.course_table.setItem(row, 1, QtWidgets.QTableWidgetItem(course['name']))
                self.course_table.setItem(row, 2, QtWidgets.QTableWidgetItem(course['instructor']))
                self.course_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(course['grade'])))

                # Zorunlu/Seçmeli
                course_type = "Seçmeli" if course['is_elective'] else "Zorunlu"
                self.course_table.setItem(row, 4, QtWidgets.QTableWidgetItem(course_type))

                # Öğrenci sayısı
                self.course_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(course['student_count'])))

                # Satır rengi - seçmeli dersler mavi, zorunlu dersler yeşil
                if course['is_elective']:
                    for col in range(6):
                        self.course_table.item(row, col).setBackground(QtGui.QColor(230, 240, 255))  # Açık mavi
                else:
                    for col in range(6):
                        self.course_table.item(row, col).setBackground(QtGui.QColor(230, 255, 230))  # Açık yeşil

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Dersler yuklenemedi: {e}")

    def show_course_students(self, item):
        """Dersi alan ogrencileri goster"""
        row = item.row()
        course_code = self.course_table.item(row, 0).text()
        course_name = self.course_table.item(row, 1).text()

        try:
            # Dersi alan ogrencileri al
            students = fetch_all("""
                SELECT s.number, s.fullname, s.grade
                FROM students s
                INNER JOIN enrollments sc ON s.id = sc.student_id
                INNER JOIN courses c ON sc.course_id = c.id
                WHERE c.code = %s AND c.department_id = %s
                ORDER BY s.number
            """, [course_code, self.user.department_id])

            # Metin olustur
            text = f"Secili Ders: {course_code} - {course_name}\n\n"
            text += f"Dersi Alan Ogrenciler ({len(students)} ogrenci):\n"
            text += "=" * 60 + "\n\n"

            if students:
                for student in students:
                    text += f"{student['number']} - {student['fullname']} ({student['grade']}. Sinif)\n"
            else:
                text += "Bu dersi alan ogrenci bulunamadi.\n"

            self.course_students.setText(text)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", str(e))

    def clear_courses(self):
        """Ders listesini temizle"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Onay",
            "Tum dersleri silmek istediginizden emin misiniz?\n\n"
            "Bu islem geri alinamaz!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                deleted = execute("DELETE FROM courses WHERE department_id = %s", [self.user.department_id])
                self.course_upload_log.append(f"Basarili! {deleted} ders silindi.")
                self.refresh_courses()
                QtWidgets.QMessageBox.information(self, "Basarili", f"{deleted} ders silindi!")
            except Exception as e:
                self.course_upload_log.append(f"HATA: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Hata", f"Dersler silinemedi: {e}")
    
    def clear_students(self):
        """Ogrenci listesini temizle"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Onay",
            "Tum ogrencileri silmek istediginizden emin misiniz?\n\n"
            "Bu islem geri alinamaz!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                deleted = execute("DELETE FROM students WHERE department_id = %s", [self.user.department_id])
                self.student_upload_log.append(f"Basarili! {deleted} ogrenci silindi.")
                self.show_all_students()
                QtWidgets.QMessageBox.information(self, "Basarili", f"{deleted} ogrenci silindi!")
            except Exception as e:
                self.student_upload_log.append(f"HATA: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Hata", f"Ogrenciler silinemedi: {e}")
    
    def logout(self):
        """Cikis yap"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Cikis",
            "Cikis yapmak istediginizden emin misiniz?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.on_logout:
                self.on_logout()
    
    def create_exam_schedule_tab(self):
        """Sinav Programi Olustur tab'i"""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        
        # Baslik
        title = QtWidgets.QLabel("SINAV PROGRAMI OLUSTUR")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        
        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()
        
        # === 1. SINAV PROGRAMI GENEL BILGILERI ===
        general_group = QtWidgets.QGroupBox("1. Genel Bilgiler")
        general_layout = QtWidgets.QFormLayout()
        
        self.exam_name_input = QtWidgets.QLineEdit()
        self.exam_name_input.setPlaceholderText("Orn: 2024-2025 Guz Donemi Vize")
        general_layout.addRow("Program Adi:", self.exam_name_input)
        
        self.exam_type_combo = QtWidgets.QComboBox()
        self.exam_type_combo.addItems(["VIZE", "FINAL", "BUTUNLEME"])
        general_layout.addRow("Sinav Turu:", self.exam_type_combo)
        
        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)
        
        # === 2. TARIH ARALIGI ===
        date_group = QtWidgets.QGroupBox("2. Sinav Tarihleri")
        date_layout = QtWidgets.QFormLayout()
        
        self.start_date_input = QtWidgets.QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QtCore.QDate.currentDate())
        date_layout.addRow("Baslangic Tarihi:", self.start_date_input)
        
        self.end_date_input = QtWidgets.QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QtCore.QDate.currentDate().addDays(14))
        date_layout.addRow("Bitis Tarihi:", self.end_date_input)
        
        # Haric tutulan gunler
        excluded_days_label = QtWidgets.QLabel("Haric Tutulan Gunler:")
        date_layout.addRow(excluded_days_label)
        
        self.exclude_saturday = QtWidgets.QCheckBox("Cumartesi")
        self.exclude_sunday = QtWidgets.QCheckBox("Pazar")
        self.exclude_sunday.setChecked(True)
        
        exclude_layout = QtWidgets.QHBoxLayout()
        exclude_layout.addWidget(self.exclude_saturday)
        exclude_layout.addWidget(self.exclude_sunday)
        date_layout.addRow("", exclude_layout)
        
        date_group.setLayout(date_layout)
        scroll_layout.addWidget(date_group)
        
        # === 3. SINAV SURELERI ===
        duration_group = QtWidgets.QGroupBox("3. Sinav Sureleri")
        duration_layout = QtWidgets.QFormLayout()
        
        self.default_duration_input = QtWidgets.QSpinBox()
        self.default_duration_input.setRange(30, 240)
        self.default_duration_input.setValue(75)
        self.default_duration_input.setSuffix(" dk")
        duration_layout.addRow("Varsayilan Sinav Suresi:", self.default_duration_input)
        
        self.break_duration_input = QtWidgets.QSpinBox()
        self.break_duration_input.setRange(0, 60)
        self.break_duration_input.setValue(15)
        self.break_duration_input.setSuffix(" dk")
        duration_layout.addRow("Bekleme Suresi:", self.break_duration_input)
        
        duration_group.setLayout(duration_layout)
        scroll_layout.addWidget(duration_group)
        
        # === 4. KISITLAR ===
        constraints_group = QtWidgets.QGroupBox("4. Kisitlar")
        constraints_layout = QtWidgets.QVBoxLayout()
        
        self.no_overlap_checkbox = QtWidgets.QCheckBox("Sinavlar ayni zamana denk gelmesin")
        self.no_overlap_checkbox.setToolTip("Bu secenek isaretliyse, hicbir ders sinavi ayni anda baslamaz")
        constraints_layout.addWidget(self.no_overlap_checkbox)
        
        constraints_group.setLayout(constraints_layout)
        scroll_layout.addWidget(constraints_group)
        
        # === 5. DERS SECIMI ===
        course_selection_group = QtWidgets.QGroupBox("5. Ders Secimi (Programa dahil olmayan dersleri isaretleyin)")
        course_selection_layout = QtWidgets.QVBoxLayout()
        
        self.course_selection_table = QtWidgets.QTableWidget()
        self.course_selection_table.setColumnCount(5)
        self.course_selection_table.setHorizontalHeaderLabels(["Haric Tut", "Ders Kodu", "Ders Adi", "Sinif", "Ogrenci Sayisi"])
        self.course_selection_table.horizontalHeader().setStretchLastSection(True)
        self.course_selection_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        course_selection_layout.addWidget(self.course_selection_table)
        
        btn_refresh_courses = QtWidgets.QPushButton("Dersleri Yenile")
        btn_refresh_courses.clicked.connect(self.load_courses_for_exam)
        course_selection_layout.addWidget(btn_refresh_courses)
        
        course_selection_group.setLayout(course_selection_layout)
        scroll_layout.addWidget(course_selection_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # === PROGRAM OLUSTUR BUTONU ===
        btn_create_schedule = QtWidgets.QPushButton("PROGRAMI OLUSTUR")
        btn_create_schedule.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_create_schedule.clicked.connect(self.create_exam_schedule)
        layout.addWidget(btn_create_schedule)
        
        # === OLUŞTURULAN PROGRAMLAR LİSTESİ ===
        programs_group = QtWidgets.QGroupBox("Olusturulan Sinav Programlari")
        programs_layout = QtWidgets.QVBoxLayout()
        
        self.exam_schedules_table = QtWidgets.QTableWidget()
        self.exam_schedules_table.setColumnCount(6)
        self.exam_schedules_table.setHorizontalHeaderLabels([
            "Program Adi", "Tur", "Baslangic", "Bitis", "Sinav Sayisi", "İslem"
        ])
        self.exam_schedules_table.horizontalHeader().setStretchLastSection(True)
        self.exam_schedules_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        programs_layout.addWidget(self.exam_schedules_table)
        programs_group.setLayout(programs_layout)
        layout.addWidget(programs_group)
        
        tab.setLayout(layout)
        
        # Dersleri ve programlari yukle
        self.load_courses_for_exam()
        self.load_exam_schedules()
        
        return tab
    
    def load_courses_for_exam(self):
        """Sinav programi icin dersleri yukle"""
        try:
            courses = fetch_all("""
                SELECT c.id, c.code, c.name, c.grade, 
                       COUNT(DISTINCT sc.student_id) as student_count
                FROM courses c
                LEFT JOIN student_courses sc ON c.id = sc.course_id
                WHERE c.department_id = %s
                GROUP BY c.id
                ORDER BY c.grade, c.code
            """, [self.user.department_id])
            
            self.course_selection_table.setRowCount(len(courses))
            
            for row, course in enumerate(courses):
                # Checkbox
                checkbox = QtWidgets.QCheckBox()
                checkbox_widget = QtWidgets.QWidget()
                checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.course_selection_table.setCellWidget(row, 0, checkbox_widget)
                
                # Ders bilgileri
                self.course_selection_table.setItem(row, 1, QtWidgets.QTableWidgetItem(course['code']))
                self.course_selection_table.setItem(row, 2, QtWidgets.QTableWidgetItem(course['name']))
                self.course_selection_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(course['grade'])))
                self.course_selection_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(course['student_count'])))
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Dersler yuklenemedi: {e}")
    
    def create_exam_schedule(self):
        """Sinav programini olustur"""
        try:
            # Validasyon
            program_name = self.exam_name_input.text().strip()
            if not program_name:
                QtWidgets.QMessageBox.warning(self, "Uyari", "Lutfen program adi girin!")
                return
            
            # Secilen dersleri al (haric tutulmayanlar)
            selected_courses = []
            for row in range(self.course_selection_table.rowCount()):
                checkbox_widget = self.course_selection_table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QtWidgets.QCheckBox)
                
                if not checkbox.isChecked():  # Haric tutulmamis
                    course_code = self.course_selection_table.item(row, 1).text()
                    selected_courses.append(course_code)
            
            if not selected_courses:
                QtWidgets.QMessageBox.warning(self, "Uyari", "Lutfen en az bir ders secin!")
                return
            
            # Kisitlari topla
            constraints = {
                'name': program_name,
                'exam_type': self.exam_type_combo.currentText(),
                'start_date': self.start_date_input.date().toString("yyyy-MM-dd"),
                'end_date': self.end_date_input.date().toString("yyyy-MM-dd"),
                'default_duration': self.default_duration_input.value(),
                'break_duration': self.break_duration_input.value(),
                'no_overlap': self.no_overlap_checkbox.isChecked(),
                'exclude_saturday': self.exclude_saturday.isChecked(),
                'exclude_sunday': self.exclude_sunday.isChecked(),
                'selected_courses': selected_courses
            }
            
            # Progress dialog göster
            progress = QtWidgets.QProgressDialog(
                "Sinav programi olusturuluyor...", 
                None, 
                0, 
                100, 
                self
            )
            progress.setWindowTitle("Lutfen Bekleyin")
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setValue(10)
            
            # Sinav programi olustur
            from services.exam_scheduler_service import create_exam_schedule
            
            progress.setValue(30)
            progress.setLabelText("Algorit kısıtlar kontrol ediliyor...")
            
            success, schedule_id, errors, warnings = create_exam_schedule(
                self.user.department_id,
                constraints
            )
            
            progress.setValue(100)
            progress.close()
            
            # Sonuçları göster
            if success:
                msg = f"Sinav programi basariyla olusturuldu!\n\n"
                msg += f"Program ID: {schedule_id}\n"
                msg += f"Ders sayisi: {len(selected_courses)}\n"
                
                if warnings:
                    msg += f"\nUyarilar ({len(warnings)}):\n"
                    for warning in warnings[:5]:
                        msg += f"- {warning}\n"
                
                QtWidgets.QMessageBox.information(self, "Basarili", msg)
                
                # Program listesini yenile
                self.load_exam_schedules()
                
            else:
                error_msg = "Sinav programi olusturulamadi!\n\nHatalar:\n"
                for error in errors:
                    error_msg += f"- {error}\n"
                
                if warnings:
                    error_msg += f"\nUyarilar:\n"
                    for warning in warnings[:5]:
                        error_msg += f"- {warning}\n"
                
                QtWidgets.QMessageBox.critical(self, "Hata", error_msg)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Program olusturulamadi: {e}")
    
    def load_exam_schedules(self):
        """Olusturulan sinav programlarini yukle ve tabloda goster"""
        try:
            schedules = fetch_all("""
                SELECT es.id, es.name, es.exam_type, es.start_date, es.end_date,
                       es.created_at, COUNT(DISTINCT e.id) as exam_count
                FROM exam_schedules es
                LEFT JOIN exams e ON es.id = e.schedule_id
                WHERE es.department_id = %s
                GROUP BY es.id
                ORDER BY es.created_at DESC
            """, [self.user.department_id])
            
            # Tabloda göster (eğer tablo widget'ı varsa)
            if hasattr(self, 'exam_schedules_table'):
                self.exam_schedules_table.setRowCount(len(schedules))
                
                for row, schedule in enumerate(schedules):
                    self.exam_schedules_table.setItem(row, 0, QtWidgets.QTableWidgetItem(schedule['name']))
                    self.exam_schedules_table.setItem(row, 1, QtWidgets.QTableWidgetItem(schedule['exam_type']))
                    self.exam_schedules_table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(schedule['start_date'])))
                    self.exam_schedules_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(schedule['end_date'])))
                    self.exam_schedules_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(schedule['exam_count'])))
                    
                    # Export butonu
                    btn_export = QtWidgets.QPushButton("Excel İndir")
                    btn_export.setStyleSheet("background-color: #28a745; color: white; padding: 5px;")
                    btn_export.clicked.connect(lambda checked, sid=schedule['id'], sname=schedule['name']: self.export_schedule_to_excel(sid, sname))
                    self.exam_schedules_table.setCellWidget(row, 5, btn_export)
            
            # Konsola da yazdır
            print(f"\n[SINAV PROGRAMLARI]")
            for schedule in schedules:
                print(f"  - {schedule['name']} ({schedule['exam_type']}): {schedule['exam_count']} sinav")
            
        except Exception as e:
            print(f"Sinav programlari yuklenemedi: {e}")
    
    def export_schedule_to_excel(self, schedule_id: int, schedule_name: str):
        """Sinav programini Excel olarak indir"""
        try:
            from services.exam_export_service import exam_export_service
            
            # Kayıt yeri seç
            default_name = f"{schedule_name.replace(' ', '_')}.xlsx"
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Excel Dosyasini Kaydet",
                default_name,
                "Excel Dosyalari (*.xlsx)"
            )
            
            if not file_path:
                return  # Kullanıcı iptal etti
            
            # Export et
            print(f"\n[EXCEL EXPORT BASLATILIYOR]")
            print(f"   Schedule ID: {schedule_id}")
            print(f"   Dosya: {file_path}")
            
            result_path = exam_export_service.export_exam_schedule_to_excel(
                schedule_id,
                output_path=file_path
            )
            
            QtWidgets.QMessageBox.information(
                self,
                "Basarili",
                f"Sinav programi Excel dosyasina aktarildi!\n\n"
                f"Dosya: {result_path}\n\n"
                f"Dosya 5 sayfa icerir:\n"
                f"1. Sinav Programi (Detayli Liste)\n"
                f"2. Program Bilgileri\n"
                f"3. Gun Bazli Ozet\n"
                f"4. Sinif Bazli Ozet\n"
                f"5. Derslik Bazli Ozet"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Excel dosyasi olusturulamadi!\n\nHata: {e}"
            )


class AddClassroomDialog(QtWidgets.QDialog):
    """Derslik ekleme dialogu"""
    def __init__(self, department_id, parent=None):
        super().__init__(parent)
        self.department_id = department_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Derslik Ekle")
        self.setFixedSize(400, 400)

        layout = QtWidgets.QFormLayout()

        # Derslik kodu
        self.txt_code = QtWidgets.QLineEdit()
        self.txt_code.setPlaceholderText("ornek: 3001")
        layout.addRow("Derslik Kodu:", self.txt_code)

        # Derslik adi
        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.setPlaceholderText("ornek: 301")
        layout.addRow("Derslik Adi:", self.txt_name)

        # Kapasite
        self.spin_capacity = QtWidgets.QSpinBox()
        self.spin_capacity.setRange(1, 500)
        self.spin_capacity.setValue(42)
        layout.addRow("Kapasite:", self.spin_capacity)

        # Satir sayisi
        self.spin_rows = QtWidgets.QSpinBox()
        self.spin_rows.setRange(1, 50)
        self.spin_rows.setValue(9)
        layout.addRow("Boyuna Sira (Satir):", self.spin_rows)

        # Sutun sayisi
        self.spin_cols = QtWidgets.QSpinBox()
        self.spin_cols.setRange(1, 50)
        self.spin_cols.setValue(7)
        layout.addRow("Enine Sira (Sutun):", self.spin_cols)

        # Sira yapisi
        self.combo_seat_group = QtWidgets.QComboBox()
        self.combo_seat_group.addItem("2'li", 2)
        self.combo_seat_group.addItem("3'lu", 3)
        self.combo_seat_group.addItem("4'lu", 4)
        self.combo_seat_group.setCurrentIndex(1)  # 3'lu varsayilan
        layout.addRow("Sira Yapisi:", self.combo_seat_group)

        # Butonlar
        btn_layout = QtWidgets.QHBoxLayout()

        btn_save = QtWidgets.QPushButton("Kaydet")
        btn_save.clicked.connect(self.save_classroom)
        btn_layout.addWidget(btn_save)

        btn_cancel = QtWidgets.QPushButton("Iptal")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addRow(btn_layout)

        self.setLayout(layout)

    def save_classroom(self):
        """Dersligi kaydet"""
        code = self.txt_code.text().strip()
        name = self.txt_name.text().strip()
        capacity = self.spin_capacity.value()
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()
        seat_group = self.combo_seat_group.currentData()

        if not code or not name:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lutfen tum alanlari doldurun!")
            return

        try:
            # Integer'i enum'a cevir
            seat_group_map = {2: "DOUBLE", 3: "TRIPLE", 4: "QUAD"}
            seat_group_enum = seat_group_map.get(seat_group, "TRIPLE")

            execute("""
                INSERT INTO classrooms (code, name, capacity, rows, cols, seat_group, department_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [code, name, capacity, rows, cols, seat_group_enum, self.department_id])

            QtWidgets.QMessageBox.information(self, "Basarili", "Derslik eklendi!")
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Derslik eklenemedi: {e}")


class ClassroomVisualizationDialog(QtWidgets.QDialog):
    """Derslik gorsellestirme dialogu"""
    def __init__(self, classroom, parent=None):
        super().__init__(parent)
        self.classroom = classroom
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Derslik: {self.classroom['name']}")
        self.setMinimumSize(600, 500)

        layout = QtWidgets.QVBoxLayout()

        # Bilgiler
        info = f"""
        Derslik Kodu: {self.classroom['code']}
        Derslik Adi: {self.classroom['name']}
        Kapasite: {self.classroom['capacity']}
        Satir x Sutun: {self.classroom['rows']} x {self.classroom['cols']}
        Sira Yapisi: {self.classroom['seat_group']}'lu
        """

        info_label = QtWidgets.QLabel(info)
        info_label.setStyleSheet("font-size: 12px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info_label)

        # Gorsellestirme alani
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)

        viz_widget = QtWidgets.QWidget()
        viz_layout = QtWidgets.QGridLayout()
        viz_layout.setSpacing(5)

        # Koltukları olustur
        rows = self.classroom['rows']
        cols = self.classroom['cols']

        # Enum'u integer'a cevir
        seat_group_str = self.classroom['seat_group']
        seat_group_map = {"DOUBLE": 2, "TRIPLE": 3, "QUAD": 4}
        seat_group = seat_group_map.get(seat_group_str, 3)

        seat_num = 1
        for row in range(rows):
            for col in range(cols):
                seat = QtWidgets.QPushButton(str(seat_num))
                seat.setFixedSize(40, 40)

                # Renk kodlama (grup bazinda)
                if (col % seat_group) == 0:
                    seat.setStyleSheet("background-color: #90EE90;")  # Yesil
                elif (col % seat_group) == 1:
                    seat.setStyleSheet("background-color: #87CEEB;")  # Mavi
                else:
                    seat.setStyleSheet("background-color: #FFB6C1;")  # Pembe

                viz_layout.addWidget(seat, row, col)
                seat_num += 1

        viz_widget.setLayout(viz_layout)
        scroll.setWidget(viz_widget)
        layout.addWidget(scroll)

        # Kapat butonu
        btn_close = QtWidgets.QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)
