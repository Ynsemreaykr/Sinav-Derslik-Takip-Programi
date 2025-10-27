# UI/coordinator_dashboard.py
from PyQt5 import QtWidgets, QtCore, QtGui
from models.user import User
from services.db import fetch_all, fetch_one, execute
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
        dept_name = self.get_department_name()
        self.setWindowTitle(f"Koordinator Dashboard - {dept_name}")
        self.setMinimumSize(1000, 700)

        main_layout = QtWidgets.QVBoxLayout()

        top_panel = QtWidgets.QHBoxLayout()

        is_admin_access = "Admin →" in self.user.email
        if is_admin_access:
            welcome_text = f"👑 Admin Erişimi\nBölüm: {dept_name}"
            welcome_style = """
                font-size: 14px; 
                font-weight: bold; 
                padding: 10px;
                background-color: #fff3e0;
                border: 2px solid #FF9800;
                border-radius: 5px;
                color: #E65100;
            """
            logout_text = "🔙 Admin Paneline Dön"
        else:
            welcome_text = f"Hos geldiniz, {self.user.email}\nBolum: {dept_name}"
            welcome_style = "font-size: 14px; font-weight: bold; padding: 10px;"
            logout_text = "🚪 Cikis Yap"
        
        welcome_label = QtWidgets.QLabel(welcome_text)
        welcome_label.setStyleSheet(welcome_style)
        top_panel.addWidget(welcome_label)

        top_panel.addStretch()

        btn_logout = QtWidgets.QPushButton(logout_text)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_logout.clicked.connect(self.logout)
        top_panel.addWidget(btn_logout)
        
        main_layout.addLayout(top_panel)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 8px;
                background: white;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f5f5, stop:1 #e0e0e0);
                color: #555;
                padding: 12px 20px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e8eaf6, stop:1 #c5cae9);
                color: #333;
            }
            QTabBar::tab:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafafa, stop:1 #f0f0f0);
                color: #bbb;
                border: 2px dashed #ddd;
            }
        """)

        self.classroom_tab = self.create_classroom_tab()
        self.tabs.addTab(self.classroom_tab, "🏫 Derslik Yonetimi")

        self.course_tab = self.create_course_tab()
        self.course_tab_index = self.tabs.addTab(self.course_tab, "📚 Ders Listesi Yukle")

        self.student_tab = self.create_student_tab()
        self.student_tab_index = self.tabs.addTab(self.student_tab, "👥 Ogrenci Listesi Yukle")

        self.student_list_tab = self.create_student_list_tab()
        self.student_list_tab_index = self.tabs.addTab(self.student_list_tab, "👨‍🎓 Ogrenci Listesi")

        self.course_list_tab = self.create_course_list_tab()
        self.course_list_tab_index = self.tabs.addTab(self.course_list_tab, "📖 Ders Listesi")

        try:
            self.exam_schedule_tab = self.create_exam_schedule_tab()
            self.exam_schedule_tab_index = self.tabs.addTab(self.exam_schedule_tab, "📅 Sinav Programi Olustur")
        except Exception as e:
            self.exam_schedule_tab_index = None

        try:
            self.seating_plan_tab = self.create_seating_plan_tab()
            self.seating_plan_tab_index = self.tabs.addTab(self.seating_plan_tab, "🪑 Oturma Plani")
        except Exception as e:
            self.seating_plan_tab_index = None

        main_layout.addWidget(self.tabs)

        self.check_classroom_requirement()

        self.setLayout(main_layout)

    def check_classroom_requirement(self):
        """
        Gereksinimleri kontrol et ve tab'leri aktif/pasif yap
        - Derslik kontrolü (tüm tab'ler için)
        - Ders listesi kontrolü (öğrenci ve sınav programı için)
        - Öğrenci listesi kontrolü (sınav programı için)
        """
        try:
            classrooms = fetch_all(
                "SELECT COUNT(*) as count FROM classrooms WHERE department_id = %s",
                [self.user.department_id]
            )
            has_classrooms = classrooms[0]['count'] > 0 if classrooms else False

            courses = fetch_all(
                "SELECT COUNT(*) as count FROM courses WHERE department_id = %s",
                [self.user.department_id]
            )
            has_courses = courses[0]['count'] > 0 if courses else False

            students = fetch_all(
                "SELECT COUNT(*) as count FROM students WHERE department_id = %s",
                [self.user.department_id]
            )
            has_students = students[0]['count'] > 0 if students else False

            if hasattr(self, 'course_tab_index'):
                self.tabs.setTabEnabled(self.course_tab_index, has_classrooms)
            if hasattr(self, 'course_list_tab_index'):
                self.tabs.setTabEnabled(self.course_list_tab_index, has_classrooms)

            can_load_students = has_classrooms and has_courses
            if hasattr(self, 'student_tab_index'):
                self.tabs.setTabEnabled(self.student_tab_index, can_load_students)
            if hasattr(self, 'student_list_tab_index'):
                self.tabs.setTabEnabled(self.student_list_tab_index, can_load_students)

            can_create_exam = has_classrooms and has_courses and has_students
            if hasattr(self, 'exam_schedule_tab_index') and self.exam_schedule_tab_index is not None:
                self.tabs.setTabEnabled(self.exam_schedule_tab_index, can_create_exam)

            exams = fetch_all("""
                SELECT COUNT(*) as count FROM exams e
                JOIN exam_schedules es ON e.schedule_id = es.id
                WHERE es.department_id = %s
            """, [self.user.department_id])
            has_exams = exams[0]['count'] > 0 if exams else False
            
            if hasattr(self, 'seating_plan_tab_index') and self.seating_plan_tab_index is not None:
                self.tabs.setTabEnabled(self.seating_plan_tab_index, has_exams)

            if not has_classrooms:
                if not hasattr(self, '_classroom_warning_shown'):
                    QtWidgets.QMessageBox.information(
                        self,
                        "Bilgilendirme",
                        "Diger islemleri yapabilmek icin once en az bir derslik eklemelisiniz!"
                    )
                    self._classroom_warning_shown = True
            elif has_classrooms and not has_courses:
                if not hasattr(self, '_course_warning_shown'):
                    QtWidgets.QMessageBox.information(
                        self,
                        "Bilgilendirme",
                        "Ogrenci listesi yuklemek icin once Ders Listesi Excel dosyasini yukleyin!\n\n"
                        "Ders yuklendikten sonra 'Ogrenci Yukle' tab'lari aktif olacaktir."
                    )
                    self._course_warning_shown = True
            elif has_classrooms and has_courses and not has_students:
                if not hasattr(self, '_student_warning_shown'):
                    QtWidgets.QMessageBox.information(
                        self,
                        "Bilgilendirme",
                        "Sinav programi olusturmak icin Ogrenci Listesi Excel dosyasini yukleyin!\n\n"
                        "Ogrenci yuklendikten sonra 'Sinav Programi Olustur' tab'i aktif olacaktir."
                    )
                    self._student_warning_shown = True

        except Exception as e:
            pass

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
        main_layout = QtWidgets.QVBoxLayout()

        # Baslik - Kompakt
        title = QtWidgets.QLabel("🏫 Derslik Yonetimi")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            padding: 8px;
            background-color: #3498db;
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        main_layout.addWidget(title)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        search_layout = QtWidgets.QHBoxLayout()
        
        search_label = QtWidgets.QLabel("🔍 Derslik Kodu Ara:")
        search_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.classroom_search_input = QtWidgets.QLineEdit()
        self.classroom_search_input.setPlaceholderText("Ders kodu girin (örnek: D101, A201)...")
        self.classroom_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #3498db;
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #2980b9;
            }
        """)
        self.classroom_search_input.textChanged.connect(self.search_classrooms_live)
        search_layout.addWidget(self.classroom_search_input)
        
        btn_clear_search = QtWidgets.QPushButton("✖ Temizle")
        btn_clear_search.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_clear_search.clicked.connect(lambda: self.classroom_search_input.clear())
        search_layout.addWidget(btn_clear_search)
        
        left_layout.addLayout(search_layout)

        btn_layout = QtWidgets.QHBoxLayout()

        btn_add = QtWidgets.QPushButton("➕ Yeni Derslik Ekle")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_add.clicked.connect(self.add_classroom)
        btn_layout.addWidget(btn_add)

        btn_refresh = QtWidgets.QPushButton("🔄 Tüm Listeyi Göster")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_refresh.clicked.connect(self.refresh_classrooms)
        btn_layout.addWidget(btn_refresh)

        left_layout.addLayout(btn_layout)

        self.classroom_table = QtWidgets.QTableWidget()
        self.classroom_table.setColumnCount(9)
        self.classroom_table.setHorizontalHeaderLabels([
            "ID", "Kod", "Ad", "Kapasite", "Satir", "Sutun", "Sira Yapisi", "Düzenle", "Sil"
        ])
        self.classroom_table.horizontalHeader().setStretchLastSection(True)
        self.classroom_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.classroom_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.classroom_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.classroom_table.setAlternatingRowColors(True)

        self.classroom_table.itemSelectionChanged.connect(self.show_classroom_schema)

        self.classroom_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.classroom_table.customContextMenuRequested.connect(self.classroom_context_menu)

        left_layout.addWidget(self.classroom_table)
        
        splitter.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        schema_title = QtWidgets.QLabel("🗺️ Derslik Görsel Şeması")
        schema_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 8px;
            background-color: #e74c3c;
            color: white;
            border-radius: 5px;
        """)
        schema_title.setAlignment(QtCore.Qt.AlignCenter)
        schema_title.setMaximumHeight(35)
        right_layout.addWidget(schema_title)

        self.classroom_schema_info = QtWidgets.QLabel("Lutfen sol taraftan bir derslik secin...")
        self.classroom_schema_info.setStyleSheet("""
            font-size: 13px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            color: #666;
        """)
        self.classroom_schema_info.setAlignment(QtCore.Qt.AlignCenter)
        right_layout.addWidget(self.classroom_schema_info)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.classroom_schema_widget = QtWidgets.QWidget()
        self.classroom_schema_layout = QtWidgets.QVBoxLayout(self.classroom_schema_widget)
        scroll.setWidget(self.classroom_schema_widget)
        
        right_layout.addWidget(scroll)
        
        splitter.addWidget(right_widget)

        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        widget.setLayout(main_layout)

        self.refresh_classrooms()

        return widget

    def create_course_tab(self):
        """Ders listesi yukleme tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("📚 Ders Listesi Yükleme")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            padding: 8px;
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        info = QtWidgets.QLabel(
            "📄 Excel dosyasını yükleyerek ders listesini sisteme aktarabilirsiniz.\n\n"
            "📋 Excel Formatı: Ders Kodu | Ders Adı | Öğretim Elemanı | Sınıf | Seçmeli Mi"
        )
        info.setStyleSheet("""
            font-size: 13px;
            padding: 15px;
            background-color: #e3f2fd;
            border: 2px solid #2196F3;
            border-radius: 8px;
            color: #1565C0;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QtWidgets.QHBoxLayout()
        
        btn_upload = QtWidgets.QPushButton("📂 Excel Dosyası Seç ve Yükle")
        btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_upload.clicked.connect(self.upload_courses_excel)
        btn_layout.addWidget(btn_upload)
        
        btn_clear = QtWidgets.QPushButton("🗑️ Ders Listesini Temizle")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_clear.clicked.connect(self.clear_courses)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)

        self.course_upload_log = QtWidgets.QTextEdit()
        self.course_upload_log.setReadOnly(True)
        self.course_upload_log.setPlaceholderText("📝 Yükleme bilgileri burada görünecek...")
        self.course_upload_log.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.course_upload_log)

        widget.setLayout(layout)
        return widget

    def create_student_tab(self):
        """Ogrenci listesi yukleme tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("👥 Öğrenci Listesi Yükleme")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            padding: 8px;
            background-color: #FF9800;
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        info = QtWidgets.QLabel(
            "📄 Excel dosyasını yükleyerek öğrenci listesini sisteme aktarabilirsiniz.\n\n"
            "📋 Excel Formatı: Öğrenci No | Ad Soyad | Sınıf | Ders Kodu"
        )
        info.setStyleSheet("""
            font-size: 13px;
            padding: 15px;
            background-color: #fff3e0;
            border: 2px solid #FF9800;
            border-radius: 8px;
            color: #E65100;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QtWidgets.QHBoxLayout()
        
        btn_upload = QtWidgets.QPushButton("📂 Excel Dosyası Seç ve Yükle")
        btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        btn_upload.clicked.connect(self.upload_students_excel)
        btn_layout.addWidget(btn_upload)
        
        btn_clear = QtWidgets.QPushButton("🗑️ Öğrenci Listesini Temizle")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        btn_clear.clicked.connect(self.clear_students)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)

        self.student_upload_log = QtWidgets.QTextEdit()
        self.student_upload_log.setReadOnly(True)
        self.student_upload_log.setPlaceholderText("📝 Yükleme bilgileri burada görünecek...")
        self.student_upload_log.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.student_upload_log)

        widget.setLayout(layout)
        return widget

    def create_student_list_tab(self):
        """Ogrenci listesi tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("👨‍🎓 Öğrenci Listesi ve Arama")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            padding: 8px;
            background-color: #9C27B0;
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        search_layout = QtWidgets.QHBoxLayout()
        
        search_label = QtWidgets.QLabel("🔍 Öğrenci No/Ad Ara:")
        search_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        search_layout.addWidget(search_label)

        self.student_search_input = QtWidgets.QLineEdit()
        self.student_search_input.setPlaceholderText("Kısmi arama yapabilirsiniz (örnek: 210, Ahmet)...")
        self.student_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #9C27B0;
                border-radius: 5px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #7B1FA2;
            }
        """)
        self.student_search_input.textChanged.connect(self.search_students_live)
        search_layout.addWidget(self.student_search_input)

        btn_refresh = QtWidgets.QPushButton("🔄 Tüm Listeyi Göster")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        btn_refresh.clicked.connect(self.show_all_students)
        search_layout.addWidget(btn_refresh)

        layout.addLayout(search_layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #9C27B0;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QSplitter::handle:hover {
                background-color: #7B1FA2;
            }
        """)

        self.student_table = QtWidgets.QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels([
            "ID", "Ogrenci No", "Ad Soyad", "Sinif", "Ders Sayisi"
        ])
        self.student_table.horizontalHeader().setStretchLastSection(True)
        self.student_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.student_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.student_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item:selected {
                background-color: #9C27B0;
                color: white;
            }
            QHeaderView::section {
                background-color: #9C27B0;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.student_table.setAlternatingRowColors(True)
        self.student_table.itemClicked.connect(self.show_student_details)
        splitter.addWidget(self.student_table)

        self.student_detail = QtWidgets.QTextEdit()
        self.student_detail.setReadOnly(True)
        self.student_detail.setPlaceholderText("Bir öğrenci seçin...")
        self.student_detail.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        splitter.addWidget(self.student_detail)

        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter)

        widget.setLayout(layout)

        self.show_all_students()

        return widget

    def create_course_list_tab(self):
        """Ders listesi tab'i"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("📖 Ders Listesi")
        title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            padding: 8px;
            background-color: #00BCD4;
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        self.course_table = QtWidgets.QTableWidget()
        self.course_table.setColumnCount(6)
        self.course_table.setHorizontalHeaderLabels([
            "Ders Kodu", "Ders Adi", "Ogretim Elemani", "Sinif", "Tip", "Ogrenci Sayisi"
        ])
        self.course_table.horizontalHeader().setStretchLastSection(True)
        self.course_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.course_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.course_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item:selected {
                background-color: #00BCD4;
                color: white;
            }
            QHeaderView::section {
                background-color: #00BCD4;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.course_table.setAlternatingRowColors(True)
        self.course_table.itemClicked.connect(self.show_course_students)
        layout.addWidget(self.course_table)

        self.course_students = QtWidgets.QTextEdit()
        self.course_students.setReadOnly(True)
        self.course_students.setPlaceholderText("Bir ders seçin...")
        self.course_students.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.course_students)

        self.refresh_courses()

        widget.setLayout(layout)
        return widget

    def add_classroom(self):
        """Yeni derslik ekle"""
        dialog = AddClassroomDialog(self.user.department_id, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.refresh_classrooms()

    def search_classrooms_live(self):
        """Derslik koduna göre canlı arama (filtreleme)"""
        try:
            search_text = self.classroom_search_input.text().strip().upper()
            
            if not search_text:
                self.refresh_classrooms()
                return

            classrooms = fetch_all("""
                SELECT * FROM classrooms 
                WHERE department_id = %s AND UPPER(code) LIKE %s
                ORDER BY code
            """, [self.user.department_id, f"%{search_text}%"])

            self.classroom_table.setRowCount(len(classrooms))
            
            for row, classroom in enumerate(classrooms):
                self.classroom_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(classroom['id'])))
                self.classroom_table.setItem(row, 1, QtWidgets.QTableWidgetItem(classroom['code']))
                self.classroom_table.setItem(row, 2, QtWidgets.QTableWidgetItem(classroom['name']))
                self.classroom_table.setItem(row, 3, QtWidgets.QTableWidgetItem(str(classroom['capacity'])))
                self.classroom_table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(classroom['rows'])))
                self.classroom_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(classroom['cols'])))

                seat_group_str = classroom['seat_group']
                seat_group_display = {"DOUBLE": "2'li", "TRIPLE": "3'lu", "QUAD": "4'lu"}.get(seat_group_str, seat_group_str)
                self.classroom_table.setItem(row, 6, QtWidgets.QTableWidgetItem(seat_group_display))

                btn_delete = QtWidgets.QPushButton("🗑️")
                btn_delete.setFixedSize(40, 30)
                btn_delete.setStyleSheet("background-color: #ff6b6b; color: white; font-size: 16px;")
                btn_delete.clicked.connect(lambda checked, cid=classroom['id']: self.delete_classroom_by_id(cid))
                self.classroom_table.setCellWidget(row, 7, btn_delete)

            if len(classrooms) == 0:
                self.classroom_schema_info.setText(f"'{search_text}' araması için sonuç bulunamadı!")
                self.classroom_schema_info.setStyleSheet("""
                    font-size: 13px;
                    padding: 10px;
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 5px;
                    color: #856404;
                """)
            else:
                self.classroom_schema_info.setText(f"✓ {len(classrooms)} derslik bulundu")
                self.classroom_schema_info.setStyleSheet("""
                    font-size: 13px;
                    padding: 10px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                    color: #155724;
                """)
                
        except Exception as e:
            pass

    def show_classroom_schema(self):
        """Seçili derslik için görsel şemayı göster (BOŞ)"""
        try:
            selected_rows = self.classroom_table.selectedItems()
            if not selected_rows:
                self.classroom_schema_info.setText("Lutfen bir derslik secin...")
                return

            row = self.classroom_table.currentRow()
            classroom_id = int(self.classroom_table.item(row, 0).text())

            classroom = fetch_all(
                'SELECT * FROM classrooms WHERE id = %s',
                [classroom_id]
            )
            
            if not classroom:
                return
            
            classroom = classroom[0]

            while self.classroom_schema_layout.count():
                item = self.classroom_schema_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            rows = classroom['rows']
            cols = classroom['cols']
            seat_group_str = str(classroom['seat_group']).upper()

            if 'DOUBLE' in seat_group_str or seat_group_str == '2':
                seat_group_val = 2
            elif 'TRIPLE' in seat_group_str or seat_group_str == '3':
                seat_group_val = 3
            elif 'QUAD' in seat_group_str or seat_group_str == '4':
                seat_group_val = 4
            else:
                seat_group_val = 3

            capacity = (rows // seat_group_val) * cols * 2

            self.classroom_schema_info.setText(
                f"📌 {classroom['code']} - {classroom['name']}\n"
                f"Boyut: {rows} x {cols} | Sıra Yapısı: {seat_group_val}'lü | Kapasite: {capacity} öğrenci"
            )
            self.classroom_schema_info.setStyleSheet("""
                font-size: 13px;
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                color: #155724;
            """)

            grid_widget = QtWidgets.QWidget()
            grid_layout = QtWidgets.QGridLayout(grid_widget)
            grid_layout.setSpacing(5)
            
            grid_row_idx = 0
            for row in range(1, rows + 1):
                if (row - 1) > 0 and (row - 1) % seat_group_val == 0:
                    # Koridor satırı ekle
                    for col in range(cols):
                        corridor_label = QtWidgets.QLabel("═ KORİDOR ═")
                        corridor_label.setAlignment(QtCore.Qt.AlignCenter)
                        corridor_label.setStyleSheet("""
                            background-color: #f39c12;
                            color: white;
                            font-weight: bold;
                            font-size: 11px;
                            padding: 5px;
                            border-radius: 3px;
                            min-width: 80px;
                            min-height: 30px;
                        """)
                        grid_layout.addWidget(corridor_label, grid_row_idx, col)
                    grid_row_idx += 1

                for col in range(1, cols + 1):
                    btn = QtWidgets.QPushButton("BOŞ")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ecf0f1;
                            color: #95a5a6;
                            font-size: 10px;
                            padding: 5px;
                            border-radius: 3px;
                            min-width: 80px;
                            min-height: 50px;
                        }
                    """)
                    btn.setEnabled(False)
                    grid_layout.addWidget(btn, grid_row_idx, col - 1)
                
                grid_row_idx += 1
            
            self.classroom_schema_layout.addWidget(grid_widget)
            self.classroom_schema_layout.addStretch()
            
        except Exception as e:
            pass
    
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

                seat_group_str = classroom['seat_group']
                seat_group_display = {"DOUBLE": "2'li", "TRIPLE": "3'lu", "QUAD": "4'lu"}.get(seat_group_str, seat_group_str)
                self.classroom_table.setItem(row, 6, QtWidgets.QTableWidgetItem(seat_group_display))

                btn_edit = QtWidgets.QPushButton("✏️")
                btn_edit.setFixedSize(40, 30)
                btn_edit.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        font-size: 16px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                btn_edit.clicked.connect(lambda checked, cid=classroom['id']: self.edit_classroom_by_id(cid))
                self.classroom_table.setCellWidget(row, 7, btn_edit)

                btn_delete = QtWidgets.QPushButton("🗑️")
                btn_delete.setFixedSize(40, 30)
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #ff6b6b;
                        color: white;
                        font-size: 16px;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #e74c3c;
                    }
                """)
                btn_delete.clicked.connect(lambda checked, cid=classroom['id']: self.delete_classroom_by_id(cid))
                self.classroom_table.setCellWidget(row, 8, btn_delete)

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
        """Derslik duzenle (sag tik menusu)"""
        row = self.classroom_table.currentRow()
        if row >= 0:
            classroom_id = int(self.classroom_table.item(row, 0).text())
            self.edit_classroom_by_id(classroom_id)
    
    def edit_classroom_by_id(self, classroom_id):
        """Derslik ID'sine gore duzenle"""
        try:
            classroom = fetch_one(
                "SELECT * FROM classrooms WHERE id = %s",
                [classroom_id]
            )
            
            if not classroom:
                QtWidgets.QMessageBox.warning(self, "Hata", "Derslik bulunamadi!")
                return

            dialog = EditClassroomDialog(classroom, self)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.refresh_classrooms()
                QtWidgets.QMessageBox.information(self, "Basarili", "Derslik guncellendi!")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Derslik duzenlenemedi: {e}")

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

                count = import_courses_from_excel(file_path, department_id=self.user.department_id)
                
                self.course_upload_log.append(f"Basarili! {count} ders eklendi (Bolum ID: {self.user.department_id}).")

                self.refresh_courses()

                self.check_classroom_requirement()

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

                count = import_students_from_excel(file_path, department_id=self.user.department_id)
                
                self.student_upload_log.append(f"Basarili! {count} ogrenci eklendi (Bolum ID: {self.user.department_id}).")

                self.show_all_students()

                self.check_classroom_requirement()

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
            pass

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
            student = fetch_all("SELECT * FROM students WHERE id = %s", [student_id])
            if not student:
                return
            student = student[0]

            courses = fetch_all("""
                SELECT c.code, c.name, c.instructor
                FROM courses c
                INNER JOIN enrollments sc ON c.id = sc.course_id
                WHERE sc.student_id = %s
                ORDER BY c.code
            """, [student_id])

            detail_html = f"""
            <div style='font-family: Arial; padding: 10px;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                    <h2 style='margin: 0; font-size: 18px;'>👨‍🎓 ÖĞRENCİ DETAYLARI</h2>
                </div>
                
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                    <table style='width: 100%; border-collapse: collapse;'>
                        <tr style='border-bottom: 2px solid #dee2e6;'>
                            <td style='padding: 8px; font-weight: bold; color: #495057;'>Öğrenci No:</td>
                            <td style='padding: 8px; color: #212529;'>{student['number']}</td>
                        </tr>
                        <tr style='border-bottom: 2px solid #dee2e6;'>
                            <td style='padding: 8px; font-weight: bold; color: #495057;'>Ad Soyad:</td>
                            <td style='padding: 8px; color: #212529;'>{student['fullname']}</td>
                        </tr>
                        <tr>
                            <td style='padding: 8px; font-weight: bold; color: #495057;'>Sınıf:</td>
                            <td style='padding: 8px; color: #212529;'>{student['grade']}. Sınıf</td>
                        </tr>
                    </table>
                </div>
                
                <div style='background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #2196F3;'>
                    <h3 style='margin: 0 0 10px 0; font-size: 14px; color: #1976D2;'>
                        📚 Aldığı Dersler ({len(courses)} ders)
                    </h3>
                    <div style='max-height: 200px; overflow-y: auto;'>
            """
            
            if courses:
                detail_html += "<table style='width: 100%; border-collapse: collapse;'>"
                for i, course in enumerate(courses):
                    bg_color = '#ffffff' if i % 2 == 0 else '#f8f9fa'
                    detail_html += f"""
                    <tr style='background-color: {bg_color};'>
                        <td style='padding: 8px; font-weight: bold; color: #2196F3;'>{course['code']}</td>
                        <td style='padding: 8px; color: #212529;'>{course['name']}</td>
                        <td style='padding: 8px; color: #6c757d; font-size: 11px;'>{course['instructor']}</td>
                    </tr>
                    """
                detail_html += "</table>"
            else:
                detail_html += """
                <p style='color: #999; text-align: center; padding: 20px;'>
                    ℹ️ Bu öğrenci henüz ders almamış.
                </p>
                """
            
            detail_html += """
                    </div>
                </div>
            </div>
            """

            self.student_detail.setHtml(detail_html)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Detay yuklenemedi: {e}")

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

                course_type = "Seçmeli" if course['is_elective'] else "Zorunlu"
                self.course_table.setItem(row, 4, QtWidgets.QTableWidgetItem(course_type))

                self.course_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(course['student_count'])))

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

            detail_html = f"""
            <div style='font-family: Arial; padding: 10px;'>
                <div style='background: linear-gradient(135deg, #00BCD4 0%, #0097A7 100%); 
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                    <h2 style='margin: 0; font-size: 18px;'>📖 DERS DETAYLARI</h2>
                </div>
                
                <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                    <table style='width: 100%; border-collapse: collapse;'>
                        <tr style='border-bottom: 2px solid #dee2e6;'>
                            <td style='padding: 8px; font-weight: bold; color: #495057;'>Ders Kodu:</td>
                            <td style='padding: 8px; color: #212529;'>{course_code}</td>
                        </tr>
                        <tr>
                            <td style='padding: 8px; font-weight: bold; color: #495057;'>Ders Adı:</td>
                            <td style='padding: 8px; color: #212529;'>{course_name}</td>
                        </tr>
                    </table>
                </div>
                
                <div style='background-color: #e8f5e9; padding: 12px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                    <h3 style='margin: 0 0 10px 0; font-size: 14px; color: #2E7D32;'>
                        👥 Dersi Alan Öğrenciler ({len(students)} öğrenci)
                    </h3>
                    <div style='max-height: 250px; overflow-y: auto;'>
            """
            
            if students:
                detail_html += "<table style='width: 100%; border-collapse: collapse;'>"
                for i, student in enumerate(students):
                    bg_color = '#ffffff' if i % 2 == 0 else '#f8f9fa'
                    detail_html += f"""
                    <tr style='background-color: {bg_color};'>
                        <td style='padding: 8px; font-weight: bold; color: #4CAF50; width: 120px;'>{student['number']}</td>
                        <td style='padding: 8px; color: #212529;'>{student['fullname']}</td>
                        <td style='padding: 8px; color: #6c757d; font-size: 11px; width: 80px;'>{student['grade']}. Sınıf</td>
                    </tr>
                    """
                detail_html += "</table>"
            else:
                detail_html += """
                <p style='color: #999; text-align: center; padding: 20px;'>
                    ℹ️ Bu dersi alan öğrenci bulunamadı.
                </p>
                """
            
            detail_html += """
                    </div>
                </div>
            </div>
            """

            self.course_students.setHtml(detail_html)

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
                
                # Tab kontrolünü güncelle (Sınav Programı tab'ı pasif olabilir)
                self.check_classroom_requirement()
                
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
                
                # Tab kontrolünü güncelle (Sınav Programı tab'ı pasif olabilir)
                self.check_classroom_requirement()
                
                QtWidgets.QMessageBox.information(self, "Basarili", f"{deleted} ogrenci silindi!")
            except Exception as e:
                self.student_upload_log.append(f"HATA: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Hata", f"Ogrenciler silinemedi: {e}")
    
    def logout(self):
        """Cikis yap veya Admin paneline dön"""
        is_admin_access = "Admin →" in self.user.email
        
        if is_admin_access:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Geri Dön",
                "Admin paneline dönmek istediğinizden emin misiniz?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
        else:
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

        title = QtWidgets.QLabel("SINAV PROGRAMI OLUSTUR")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout()

        general_group = QtWidgets.QGroupBox("📋 1. Genel Bilgiler")
        general_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
            }
        """)
        general_layout = QtWidgets.QFormLayout()
        
        self.exam_name_input = QtWidgets.QLineEdit()
        self.exam_name_input.setPlaceholderText("Orn: 2024-2025 Guz Donemi Vize")
        general_layout.addRow("Program Adi:", self.exam_name_input)
        
        self.exam_type_combo = QtWidgets.QComboBox()
        self.exam_type_combo.addItems(["VIZE", "FINAL", "BUTUNLEME"])
        general_layout.addRow("Sinav Turu:", self.exam_type_combo)
        
        general_group.setLayout(general_layout)
        scroll_layout.addWidget(general_group)

        date_group = QtWidgets.QGroupBox("📅 2. Sinav Tarihleri")
        date_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #FF9800;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #FF9800;
            }
        """)
        date_layout = QtWidgets.QFormLayout()
        
        self.start_date_input = QtWidgets.QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QtCore.QDate.currentDate())
        date_layout.addRow("Baslangic Tarihi:", self.start_date_input)
        
        self.end_date_input = QtWidgets.QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QtCore.QDate.currentDate().addDays(14))
        date_layout.addRow("Bitis Tarihi:", self.end_date_input)

        excluded_days_label = QtWidgets.QLabel("Haric Tutulan Gunler:")
        date_layout.addRow(excluded_days_label)

        self.exclude_monday = QtWidgets.QCheckBox("Pazartesi")
        self.exclude_tuesday = QtWidgets.QCheckBox("Sali")
        self.exclude_wednesday = QtWidgets.QCheckBox("Carsamba")
        self.exclude_thursday = QtWidgets.QCheckBox("Persembe")
        self.exclude_friday = QtWidgets.QCheckBox("Cuma")
        self.exclude_saturday = QtWidgets.QCheckBox("Cumartesi")
        self.exclude_sunday = QtWidgets.QCheckBox("Pazar")
        self.exclude_sunday.setChecked(True)

        exclude_layout1 = QtWidgets.QHBoxLayout()
        exclude_layout1.addWidget(self.exclude_monday)
        exclude_layout1.addWidget(self.exclude_tuesday)
        exclude_layout1.addWidget(self.exclude_wednesday)
        exclude_layout1.addWidget(self.exclude_thursday)
        exclude_layout1.addWidget(self.exclude_friday)

        exclude_layout2 = QtWidgets.QHBoxLayout()
        exclude_layout2.addWidget(self.exclude_saturday)
        exclude_layout2.addWidget(self.exclude_sunday)
        exclude_layout2.addStretch()
        
        exclude_widget = QtWidgets.QWidget()
        exclude_main_layout = QtWidgets.QVBoxLayout(exclude_widget)
        exclude_main_layout.addLayout(exclude_layout1)
        exclude_main_layout.addLayout(exclude_layout2)
        exclude_main_layout.setContentsMargins(0, 0, 0, 0)
        
        date_layout.addRow("", exclude_widget)
        
        date_group.setLayout(date_layout)
        scroll_layout.addWidget(date_group)

        duration_group = QtWidgets.QGroupBox("⏱️ 3. Sinav Sureleri")
        duration_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #9C27B0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #9C27B0;
            }
        """)
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

        constraints_group = QtWidgets.QGroupBox("⚙️ 4. Kisitlar")
        constraints_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #F44336;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #F44336;
            }
        """)
        constraints_layout = QtWidgets.QVBoxLayout()
        
        self.no_overlap_checkbox = QtWidgets.QCheckBox("Sinavlar ayni zamana denk gelmesin")
        self.no_overlap_checkbox.setToolTip("Bu secenek isaretliyse, hicbir ders sinavi ayni anda baslamaz")
        constraints_layout.addWidget(self.no_overlap_checkbox)
        
        constraints_group.setLayout(constraints_layout)
        scroll_layout.addWidget(constraints_group)

        course_selection_group = QtWidgets.QGroupBox("📚 5. Ders Secimi (Programa dahil olmayan dersleri isaretleyin)")
        course_selection_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #00BCD4;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #00BCD4;
            }
        """)
        course_selection_layout = QtWidgets.QVBoxLayout()
        
        self.course_selection_table = QtWidgets.QTableWidget()
        self.course_selection_table.setColumnCount(7)
        self.course_selection_table.setHorizontalHeaderLabels([
            "Haric Tut", "Ders Kodu", "Ders Adi", "Sinif", "Ogrenci Sayisi", "Sinav Suresi (dk)", "Bekleme Suresi (dk)"
        ])
        self.course_selection_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.course_selection_table.setMinimumHeight(400)  # 400px minimum yükseklik

        self.course_selection_table.setColumnWidth(0, 80)
        self.course_selection_table.setColumnWidth(1, 100)
        self.course_selection_table.setColumnWidth(2, 300)
        self.course_selection_table.setColumnWidth(3, 60)
        self.course_selection_table.setColumnWidth(4, 100)
        self.course_selection_table.setColumnWidth(5, 130)
        self.course_selection_table.setColumnWidth(6, 130)

        self.course_selection_table.horizontalHeader().setStretchLastSection(False)
        
        course_selection_layout.addWidget(self.course_selection_table)
        
        btn_refresh_courses = QtWidgets.QPushButton("Dersleri Yenile")
        btn_refresh_courses.clicked.connect(self.load_courses_for_exam)
        course_selection_layout.addWidget(btn_refresh_courses)
        
        course_selection_group.setLayout(course_selection_layout)
        scroll_layout.addWidget(course_selection_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        buttons_layout = QtWidgets.QHBoxLayout()

        btn_create_schedule = QtWidgets.QPushButton("✓ PROGRAMI OLUSTUR")
        btn_create_schedule.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        btn_create_schedule.clicked.connect(self.create_exam_schedule)
        buttons_layout.addWidget(btn_create_schedule)

        self.btn_download_excel = QtWidgets.QPushButton("📥 EXCEL İNDİR")
        self.btn_download_excel.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_download_excel.clicked.connect(self.download_current_schedule_excel)
        self.btn_download_excel.setEnabled(False)
        buttons_layout.addWidget(self.btn_download_excel)
        
        layout.addLayout(buttons_layout)
        
        tab.setLayout(layout)

        self.load_courses_for_exam()
        
        return tab
    
    def load_courses_for_exam(self):
        """Sinav programi icin dersleri yukle"""
        try:
            courses = fetch_all("""
                SELECT c.id, c.code, c.name, c.grade, 
                       COUNT(DISTINCT e.student_id) as student_count
                FROM courses c
                LEFT JOIN enrollments e ON c.id = e.course_id
                WHERE c.department_id = %s
                GROUP BY c.id, c.code, c.name, c.grade
                ORDER BY c.grade, c.code
            """, [self.user.department_id])
            
            self.course_selection_table.setRowCount(len(courses))
            
            for row, course in enumerate(courses):

                checkbox = QtWidgets.QCheckBox()
                checkbox_widget = QtWidgets.QWidget()
                checkbox_layout = QtWidgets.QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(QtCore.Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.course_selection_table.setCellWidget(row, 0, checkbox_widget)

                item_code = QtWidgets.QTableWidgetItem(course['code'])
                item_code.setFlags(item_code.flags() & ~QtCore.Qt.ItemIsEditable)
                self.course_selection_table.setItem(row, 1, item_code)
                
                item_name = QtWidgets.QTableWidgetItem(course['name'])
                item_name.setFlags(item_name.flags() & ~QtCore.Qt.ItemIsEditable)
                self.course_selection_table.setItem(row, 2, item_name)
                
                item_grade = QtWidgets.QTableWidgetItem(str(course['grade']))
                item_grade.setFlags(item_grade.flags() & ~QtCore.Qt.ItemIsEditable)
                self.course_selection_table.setItem(row, 3, item_grade)
                
                item_count = QtWidgets.QTableWidgetItem(str(course['student_count']))
                item_count.setFlags(item_count.flags() & ~QtCore.Qt.ItemIsEditable)
                self.course_selection_table.setItem(row, 4, item_count)

                exam_duration_spinbox = QtWidgets.QSpinBox()
                exam_duration_spinbox.setRange(30, 240)
                exam_duration_spinbox.setValue(self.default_duration_input.value())  # Varsayılan değer
                exam_duration_spinbox.setSuffix(" dk")
                exam_duration_spinbox.setToolTip("Bu dersin sinav suresi")
                self.course_selection_table.setCellWidget(row, 5, exam_duration_spinbox)

                break_spinbox = QtWidgets.QSpinBox()
                break_spinbox.setRange(0, 120)
                break_spinbox.setValue(self.break_duration_input.value())  # Varsayılan değer
                break_spinbox.setSuffix(" dk")
                break_spinbox.setToolTip("Bu dersin sinavindan sonraki bekleme suresi")
                self.course_selection_table.setCellWidget(row, 6, break_spinbox)
        
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

            selected_courses = []
            course_exam_durations = {}  # {course_code: exam_duration}
            course_break_durations = {}  # {course_code: break_duration}
            
            for row in range(self.course_selection_table.rowCount()):
                checkbox_widget = self.course_selection_table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QtWidgets.QCheckBox)
                
                if not checkbox.isChecked():
                    course_code = self.course_selection_table.item(row, 1).text()
                    selected_courses.append(course_code)

                    exam_duration_spinbox = self.course_selection_table.cellWidget(row, 5)
                    if isinstance(exam_duration_spinbox, QtWidgets.QSpinBox):
                        course_exam_durations[course_code] = exam_duration_spinbox.value()

                    break_spinbox = self.course_selection_table.cellWidget(row, 6)
                    if isinstance(break_spinbox, QtWidgets.QSpinBox):
                        course_break_durations[course_code] = break_spinbox.value()
            
            if not selected_courses:
                QtWidgets.QMessageBox.warning(self, "Uyari", "Lutfen en az bir ders secin!")
                return

            constraints = {
                'name': program_name,
                'exam_type': self.exam_type_combo.currentText(),
                'start_date': self.start_date_input.date().toString("yyyy-MM-dd"),
                'end_date': self.end_date_input.date().toString("yyyy-MM-dd"),
                'default_duration': self.default_duration_input.value(),
                'break_duration': self.break_duration_input.value(),
                'course_exam_durations': course_exam_durations,
                'course_break_durations': course_break_durations,
                'no_overlap': self.no_overlap_checkbox.isChecked(),
                'exclude_monday': self.exclude_monday.isChecked(),
                'exclude_tuesday': self.exclude_tuesday.isChecked(),
                'exclude_wednesday': self.exclude_wednesday.isChecked(),
                'exclude_thursday': self.exclude_thursday.isChecked(),
                'exclude_friday': self.exclude_friday.isChecked(),
                'exclude_saturday': self.exclude_saturday.isChecked(),
                'exclude_sunday': self.exclude_sunday.isChecked(),
                'selected_courses': selected_courses
            }

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
            
            success = False
            schedule_id = None
            errors = []
            warnings = []
            
            try:
                progress.setLabelText("Eski sinav programlari siliniyor...")
                try:
                    execute("DELETE FROM exam_schedules WHERE department_id = %s", [self.user.department_id])
                except Exception as e:
                    pass

                from services.exam_scheduler_service import create_exam_schedule
                
                progress.setValue(30)
                progress.setLabelText("Algorit kısıtlar kontrol ediliyor...")
                
                success, schedule_id, errors, warnings = create_exam_schedule(
                    self.user.department_id,
                    constraints
                )
                
                progress.setValue(100)
                
            except Exception as inner_e:
                errors.append(f"Beklenmeyen hata: {str(inner_e)}")
                import traceback
                traceback.print_exc()
            finally:
                progress.close()

            if success:
                msg = f"Sinav programi basariyla olusturuldu!\n\n"
                msg += f"Program ID: {schedule_id}\n"
                msg += f"Ders sayisi: {len(selected_courses)}\n"
                
                if warnings:
                    msg += f"\nUyarilar ({len(warnings)}):\n"
                    for warning in warnings[:5]:
                        msg += f"- {warning}\n"
                
                QtWidgets.QMessageBox.information(self, "Basarili", msg)

                if hasattr(self, 'btn_download_excel'):
                    self.btn_download_excel.setEnabled(True)

                self.check_classroom_requirement()

                if hasattr(self, 'seating_plan_tab_index') and self.seating_plan_tab_index is not None:
                    self.tabs.setCurrentIndex(self.seating_plan_tab_index)
                
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
    
    def create_seating_plan_tab(self):
        """Oturma Planı tab'ı - Tamamen yeni!"""
        tab = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("🪑 OTURMA PLANI")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #9b59b6, stop:1 #8e44ad);
            color: white;
            border-radius: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setMaximumHeight(40)
        main_layout.addWidget(title)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)

        exams_group = QtWidgets.QGroupBox("📝 Sınavlar")
        exams_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #9b59b6;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #9b59b6;
            }
        """)
        exams_layout = QtWidgets.QVBoxLayout()

        btn_refresh = QtWidgets.QPushButton("🔄 Yenile")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-size: 13px;
                padding: 8px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        btn_refresh.clicked.connect(self.load_all_exams)
        exams_layout.addWidget(btn_refresh, alignment=QtCore.Qt.AlignRight)

        self.seating_exams_table = QtWidgets.QTableWidget()
        self.seating_exams_table.setColumnCount(3)
        self.seating_exams_table.setHorizontalHeaderLabels([
            "Sinav Adi", "Gun ve Saat", "Derslikler"
        ])
        self.seating_exams_table.horizontalHeader().setStretchLastSection(True)
        self.seating_exams_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.seating_exams_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.seating_exams_table.setAlternatingRowColors(True)
        self.seating_exams_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget::item:selected {
                background-color: #9b59b6;
                color: white;
            }
            QHeaderView::section {
                background-color: #9b59b6;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        self.seating_exams_table.itemSelectionChanged.connect(self.show_seating_plan_schema)
        
        exams_layout.addWidget(self.seating_exams_table)
        exams_group.setLayout(exams_layout)
        left_layout.addWidget(exams_group)
        
        splitter.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)

        schema_group = QtWidgets.QGroupBox("🗺️ Oturma Şeması")
        schema_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px;
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #e74c3c;
            }
        """)
        schema_layout = QtWidgets.QVBoxLayout()

        self.seating_info_label = QtWidgets.QLabel("Lutfen sol taraftan bir sinav secin...")
        self.seating_info_label.setStyleSheet("""
            font-size: 13px;
            padding: 10px;
            background-color: white;
            border-radius: 5px;
            color: #666;
        """)
        self.seating_info_label.setAlignment(QtCore.Qt.AlignCenter)
        schema_layout.addWidget(self.seating_info_label)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.seating_schema_widget = QtWidgets.QWidget()
        self.seating_schema_layout = QtWidgets.QVBoxLayout(self.seating_schema_widget)
        scroll.setWidget(self.seating_schema_widget)
        
        schema_layout.addWidget(scroll)

        button_layout = QtWidgets.QHBoxLayout()

        self.btn_generate_all_seating = QtWidgets.QPushButton("🚀 TUM SINAVLAR İÇİN OTURMA PLANI OLUŞTUR")
        self.btn_generate_all_seating.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_generate_all_seating.clicked.connect(self.generate_all_seating_plans)
        self.btn_generate_all_seating.setEnabled(False)
        button_layout.addWidget(self.btn_generate_all_seating)
        
        self.btn_generate_seating = QtWidgets.QPushButton("📝 Secili Sinav İçin Olustur")
        self.btn_generate_seating.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_generate_seating.clicked.connect(self.generate_seating_plan)
        self.btn_generate_seating.setEnabled(False)
        button_layout.addWidget(self.btn_generate_seating)
        
        self.btn_export_pdf = QtWidgets.QPushButton("📄 PDF Indir")
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_export_pdf.clicked.connect(self.export_seating_pdf)
        self.btn_export_pdf.setEnabled(False)
        button_layout.addWidget(self.btn_export_pdf)
        
        schema_layout.addLayout(button_layout)
        schema_group.setLayout(schema_layout)
        right_layout.addWidget(schema_group)
        
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        tab.setLayout(main_layout)

        self.load_all_exams()
        
        return tab
    
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

            if hasattr(self, 'exam_schedules_list'):
                self.exam_schedules_list.setRowCount(len(schedules))
                
                for row, schedule in enumerate(schedules):
                    self.exam_schedules_list.setItem(row, 0, QtWidgets.QTableWidgetItem(schedule['name']))
                    self.exam_schedules_list.setItem(row, 1, QtWidgets.QTableWidgetItem(schedule['exam_type']))
                    self.exam_schedules_list.setItem(row, 2, QtWidgets.QTableWidgetItem(str(schedule['start_date'])))
                    self.exam_schedules_list.setItem(row, 3, QtWidgets.QTableWidgetItem(str(schedule['end_date'])))
                    self.exam_schedules_list.setItem(row, 4, QtWidgets.QTableWidgetItem(str(schedule['exam_count'])))

                    btn_export = QtWidgets.QPushButton("📥 İndir")
                    btn_export.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                            border: none;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                    """)
                    btn_export.clicked.connect(lambda checked, sid=schedule['id'], sname=schedule['name']: self.export_schedule_to_excel(sid, sname))
                    self.exam_schedules_list.setCellWidget(row, 5, btn_export)

                    btn_delete = QtWidgets.QPushButton("🗑️ Sil")
                    btn_delete.setStyleSheet("""
                        QPushButton {
                            background-color: #dc3545;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                            border: none;
                        }
                        QPushButton:hover {
                            background-color: #c82333;
                        }
                    """)
                    btn_delete.clicked.connect(lambda checked, sid=schedule['id'], sname=schedule['name']: self.delete_exam_schedule(sid, sname))
                    self.exam_schedules_list.setCellWidget(row, 6, btn_delete)
            
        except Exception as e:
            pass
    
    def show_exam_schedule_details(self):
        """Seçilen sınav programının detaylarını göster"""
        try:
            selected_rows = self.exam_schedules_list.selectedItems()
            if not selected_rows:
                self.exam_details_label.setText("Lutfen bir program secin...")
                self.exam_details_table.setRowCount(0)
                return

            row = self.exam_schedules_list.currentRow()
            program_name = self.exam_schedules_list.item(row, 0).text()

            schedules = fetch_all("""
                SELECT id FROM exam_schedules
                WHERE name = %s AND department_id = %s
            """, [program_name, self.user.department_id])
            
            if not schedules:
                return
            
            schedule_id = schedules[0]['id']

            exams = fetch_all("""
                SELECT e.exam_date, e.start_time, e.end_time,
                       c.code, c.name, c.grade, c.instructor
                FROM exams e
                JOIN courses c ON e.course_id = c.id
                WHERE e.schedule_id = %s
                ORDER BY e.exam_date, e.start_time
            """, [schedule_id])

            self.exam_details_label.setText(
                f"✓ {program_name} - Toplam {len(exams)} sinav"
            )
            self.exam_details_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                color: #155724;
            """)

            self.exam_details_table.setRowCount(len(exams))
            
            turkish_days = {
                'Monday': 'Pazartesi',
                'Tuesday': 'Sali',
                'Wednesday': 'Carsamba',
                'Thursday': 'Persembe',
                'Friday': 'Cuma',
                'Saturday': 'Cumartesi',
                'Sunday': 'Pazar'
            }
            
            for row, exam in enumerate(exams):
                exam_date = exam['exam_date']
                self.exam_details_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(exam_date)))

                from datetime import datetime
                day_name = datetime.strptime(str(exam_date), '%Y-%m-%d').strftime('%A')
                turkish_day = turkish_days.get(day_name, day_name)
                self.exam_details_table.setItem(row, 1, QtWidgets.QTableWidgetItem(turkish_day))

                time_str = f"{exam['start_time']} - {exam['end_time']}"
                self.exam_details_table.setItem(row, 2, QtWidgets.QTableWidgetItem(time_str))

                self.exam_details_table.setItem(row, 3, QtWidgets.QTableWidgetItem(exam['code']))
                self.exam_details_table.setItem(row, 4, QtWidgets.QTableWidgetItem(exam['name']))
                self.exam_details_table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(exam['grade'])))
                self.exam_details_table.setItem(row, 6, QtWidgets.QTableWidgetItem(exam['instructor'] or '-'))
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hata", f"Detaylar gosterilemedi: {e}")
    
    def delete_exam_schedule(self, schedule_id: int, schedule_name: str):
        """Sınav programını sil"""
        try:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Silme Onayı",
                f"'{schedule_name}' programini silmek istediginize emin misiniz?\n\n"
                f"Bu islem geri alinamaz!",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.No:
                return

            execute("DELETE FROM exam_schedules WHERE id = %s", [schedule_id])
            
            QtWidgets.QMessageBox.information(
                self,
                "Basarili",
                f"'{schedule_name}' programi basariyla silindi!"
            )

            self.load_exam_schedules()

            self.exam_details_label.setText("Lutfen bir program secin...")
            self.exam_details_table.setRowCount(0)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Program silinemedi!\n\nHata: {e}"
            )
    
    def export_schedule_to_excel(self, schedule_id: int, schedule_name: str):
        """Sinav programini Excel olarak indir"""
        try:
            from services.exam_export_service import exam_export_service

            default_name = f"{schedule_name.replace(' ', '_')}.xlsx"
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Excel Dosyasini Kaydet",
                default_name,
                "Excel Dosyalari (*.xlsx)"
            )
            
            if not file_path:
                return
            
            result_path = exam_export_service.export_exam_schedule_to_excel(
                schedule_id,
                output_path=file_path
            )
            
            QtWidgets.QMessageBox.information(
                self,
                "Basarili",
                f"Sinav programi Excel dosyasina aktarildi!\n\n"
                f"Dosya: {result_path}\n\n"
                f"Ozellikler:\n"
                f"- Bolum adi baslikta (buyuk harflerle)\n"
                f"- 7 sutun (sadece gerekli bilgiler)\n"
                f"- Ayni tarihler birlestirilmis\n"
                f"- Profesyonel formatlama\n"
                f"- 2 sayfa: Program + Bilgiler"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Excel dosyasi olusturulamadi!\n\nHata: {e}"
            )
    
    def download_current_schedule_excel(self):
        """Mevcut (en son oluşturulan) sınav programını Excel olarak indir"""
        try:
            schedules = fetch_all("""
                SELECT id, name FROM exam_schedules
                WHERE department_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, [self.user.department_id])
            
            if not schedules:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Uyari",
                    "Henuz olusturulmus bir sinav programi yok!"
                )
                return
            
            schedule = schedules[0]
            self.export_schedule_to_excel(schedule['id'], schedule['name'])
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Hata",
                f"Excel indirilemedi!\n\nHata: {e}"
            )

    
    def load_all_exams(self):
        """Tüm sınavları yükle ve tabloda göster"""
        try:
            exams = fetch_all("""
                SELECT e.id, e.exam_date, e.start_time, e.end_time,
                       c.code, c.name as course_name,
                       STRING_AGG(DISTINCT cl.name, ', ') as classrooms,
                       COUNT(DISTINCT sp.id) as seating_count
                FROM exams e
                JOIN courses c ON e.course_id = c.id
                JOIN exam_schedules es ON e.schedule_id = es.id
                LEFT JOIN exam_classrooms ec ON e.id = ec.exam_id
                LEFT JOIN classrooms cl ON ec.classroom_id = cl.id
                LEFT JOIN seating_plans sp ON e.id = sp.exam_id
                WHERE es.department_id = %s
                GROUP BY e.id, c.code, c.name
                ORDER BY e.exam_date, e.start_time
            """, [self.user.department_id])
            
            self.seating_exams_table.setRowCount(len(exams))
            
            turkish_days = {
                'Monday': 'Pazartesi',
                'Tuesday': 'Sali',
                'Wednesday': 'Carsamba',
                'Thursday': 'Persembe',
                'Friday': 'Cuma',
                'Saturday': 'Cumartesi',
                'Sunday': 'Pazar'
            }
            
            for row, exam in enumerate(exams):
                exam_name = f"{exam['code']} - {exam['course_name']}"
                self.seating_exams_table.setItem(row, 0, QtWidgets.QTableWidgetItem(exam_name))

                from datetime import datetime
                exam_date = exam['exam_date']
                day_name = datetime.strptime(str(exam_date), '%Y-%m-%d').strftime('%A')
                turkish_day = turkish_days.get(day_name, day_name)
                datetime_str = f"{exam_date} {turkish_day} {exam['start_time']}-{exam['end_time']}"
                self.seating_exams_table.setItem(row, 1, QtWidgets.QTableWidgetItem(datetime_str))

                classrooms_str = exam['classrooms'] or '-'

                classrooms_item = QtWidgets.QTableWidgetItem(classrooms_str)
                if exam['seating_count'] > 0:
                    classrooms_item.setBackground(QtGui.QColor("#d4edda"))
                    classrooms_item.setForeground(QtGui.QColor("#155724"))
                
                self.seating_exams_table.setItem(row, 2, classrooms_item)

            if len(exams) > 0:
                self.btn_generate_all_seating.setEnabled(True)
            else:
                self.btn_generate_all_seating.setEnabled(False)
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Sinavlar yuklenemedi: {e}")
    
    def show_seating_plan_schema(self):
        """Seçilen sınav için oturma planı şemasını göster"""
        try:
            selected_rows = self.seating_exams_table.selectedItems()
            if not selected_rows:
                self.seating_info_label.setText("Lutfen bir sinav secin...")
                self.btn_generate_seating.setEnabled(False)
                self.btn_export_pdf.setEnabled(False)
                return

            row = self.seating_exams_table.currentRow()
            exam_name = self.seating_exams_table.item(row, 0).text()

            exam_code = exam_name.split(' - ')[0]
            exams = fetch_all("""
                SELECT e.id, c.code, c.name
                FROM exams e
                JOIN courses c ON e.course_id = c.id
                WHERE c.code = %s
                LIMIT 1
            """, [exam_code])
            
            if not exams:
                return
            
            self.selected_exam_id = exams[0]['id']

            seating = fetch_all("""
                SELECT COUNT(*) as count FROM seating_plans WHERE exam_id = %s
            """, [self.selected_exam_id])
            
            has_seating = seating[0]['count'] > 0 if seating else False
            
            if has_seating:
                self.display_seating_schema(self.selected_exam_id)
                self.btn_generate_seating.setEnabled(True)
                self.btn_generate_seating.setText("🔄 Oturma Plani Yenile")
                self.btn_export_pdf.setEnabled(True)
            else:
                self.seating_info_label.setText(
                    f"✓ {exam_name} secildi\n\n"
                    f"Oturma plani henuz olusturulmadi.\n"
                    f"'Oturma Plani Olustur' butonuna tiklayin."
                )
                self.btn_generate_seating.setEnabled(True)
                self.btn_generate_seating.setText("📝 Oturma Plani Olustur")
                self.btn_export_pdf.setEnabled(False)

                while self.seating_schema_layout.count():
                    item = self.seating_schema_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hata", f"Oturma plani gosterilemedi: {e}")
    
    def display_seating_schema(self, exam_id):
        """Oturma planı şemasını görselleştir"""
        try:
            while self.seating_schema_layout.count():
                item = self.seating_schema_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            seating_data = fetch_all("""
                SELECT sp.*, s.number as student_number, s.fullname,
                       cl.id as classroom_id, cl.name as classroom_name, 
                       cl."rows", cl.cols, cl.seat_group
                FROM seating_plans sp
                JOIN students s ON sp.student_id = s.id
                JOIN classrooms cl ON sp.classroom_id = cl.id
                WHERE sp.exam_id = %s
                ORDER BY cl.name, sp.row_number, sp.col_number
            """, [exam_id])
            
            if not seating_data:
                self.seating_info_label.setText("Oturma plani bulunamadi!")
                return

            classrooms = {}
            for seat in seating_data:
                cl_id = seat['classroom_id']
                if cl_id not in classrooms:
                    classrooms[cl_id] = {
                        'name': seat['classroom_name'],
                        'rows': seat['rows'],
                        'cols': seat['cols'],
                        'seat_group': seat['seat_group'],
                        'seats': []
                    }
                classrooms[cl_id]['seats'].append(seat)

            total_students = len(seating_data)
            self.seating_info_label.setText(
                f"✓ Oturma plani mevcut\n"
                f"Toplam: {total_students} ogrenci | {len(classrooms)} derslik"
            )
            self.seating_info_label.setStyleSheet("""
                font-size: 13px;
                padding: 10px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                color: #155724;
            """)

            for cl_id, cl_data in classrooms.items():
                cl_title = QtWidgets.QLabel(f"🏫 {cl_data['name']} ({len(cl_data['seats'])} öğrenci)")
                cl_title.setStyleSheet("""
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    background-color: #3498db;
                    color: white;
                    border-radius: 5px;
                """)
                self.seating_schema_layout.addWidget(cl_title)

                grid_widget = QtWidgets.QWidget()
                grid_layout = QtWidgets.QGridLayout(grid_widget)
                grid_layout.setSpacing(5)

                rows = cl_data['rows']
                cols = cl_data['cols']
                seat_group_str = str(cl_data.get('seat_group', 'TRIPLE')).upper()

                if 'DOUBLE' in seat_group_str or seat_group_str == '2':
                    seat_group_val = 2
                elif 'TRIPLE' in seat_group_str or seat_group_str == '3':
                    seat_group_val = 3
                elif 'QUAD' in seat_group_str or seat_group_str == '4':
                    seat_group_val = 4
                else:
                    seat_group_val = 3

                seat_matrix = {}
                for seat in cl_data['seats']:
                    key = (seat['row_number'], seat['col_number'])
                    seat_matrix[key] = seat

                grid_row_idx = 0
                for row in range(1, rows + 1):
                    if (row - 1) > 0 and (row - 1) % seat_group_val == 0:
                        # Koridor satırı ekle
                        for col in range(cols):
                            corridor_label = QtWidgets.QLabel("═ KORİDOR ═")
                            corridor_label.setAlignment(QtCore.Qt.AlignCenter)
                            corridor_label.setStyleSheet("""
                                background-color: #f39c12;
                                color: white;
                                font-weight: bold;
                                font-size: 11px;
                                padding: 5px;
                                border-radius: 3px;
                                min-width: 80px;
                                min-height: 30px;
                            """)
                            grid_layout.addWidget(corridor_label, grid_row_idx, col)
                        grid_row_idx += 1

                    for col in range(1, cols + 1):
                        seat_key = (row, col)
                        
                        if seat_key in seat_matrix:
                            seat = seat_matrix[seat_key]
                            btn = QtWidgets.QPushButton(f"{seat['student_number']}\n{seat['fullname'][:15]}")
                            btn.setStyleSheet("""
                                QPushButton {
                                    background-color: #27ae60;
                                    color: white;
                                    font-size: 10px;
                                    padding: 5px;
                                    border-radius: 3px;
                                    min-width: 80px;
                                    min-height: 50px;
                                }
                            """)
                        else:
                            btn = QtWidgets.QPushButton("BOŞ")
                            btn.setStyleSheet("""
                                QPushButton {
                                    background-color: #ecf0f1;
                                    color: #95a5a6;
                                    font-size: 10px;
                                    padding: 5px;
                                    border-radius: 3px;
                                    min-width: 80px;
                                    min-height: 50px;
                                }
                            """)
                        
                        btn.setEnabled(False)
                        grid_layout.addWidget(btn, grid_row_idx, col - 1)
                    
                    grid_row_idx += 1
                
                self.seating_schema_layout.addWidget(grid_widget)
                self.seating_schema_layout.addSpacing(20)
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Hata", f"Sema gosterilemedi: {e}")
    
    def generate_seating_plan(self):
        """Seçili sınav için oturma planını oluştur"""
        if not hasattr(self, 'selected_exam_id'):
            QtWidgets.QMessageBox.warning(self, "Uyari", "Lutfen once bir sinav secin!")
            return
        
        progress = None
        try:
            from services.seating_plan_service import generate_seating_plan_for_exam

            progress = QtWidgets.QProgressDialog("Oturma plani olusturuluyor...", None, 0, 100, self)
            progress.setWindowTitle("Lutfen Bekleyin")
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.setValue(30)
            
            success, error_msg, result = generate_seating_plan_for_exam(self.selected_exam_id)
            
            progress.setValue(100)
            
            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Basarili",
                    f"Oturma plani basariyla olusturuldu!\n\n"
                    f"Toplam: {len(result['students'])} ogrenci\n"
                    f"Derslik: {len(result['classrooms'])} adet"
                )
                
                # Şemayı göster
                self.display_seating_schema(self.selected_exam_id)
                self.btn_export_pdf.setEnabled(True)
                self.btn_generate_seating.setText("🔄 Oturma Plani Yenile")

                self.load_all_exams()
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Hata",
                    f"Oturma plani olusturulamadi!\n\n{error_msg}"
                )
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Hata olustu: {e}")
    
    def generate_all_seating_plans(self):
        """Tüm sınavlar için oturma planı oluştur"""
        progress = None
        try:
            exams = fetch_all("""
                SELECT e.id, c.code, c.name
                FROM exams e
                JOIN courses c ON e.course_id = c.id
                JOIN exam_schedules es ON e.schedule_id = es.id
                WHERE es.department_id = %s
                ORDER BY e.exam_date, e.start_time
            """, [self.user.department_id])
            
            if not exams:
                QtWidgets.QMessageBox.warning(self, "Uyari", "Olusturulacak sinav bulunamadi!")
                return

            reply = QtWidgets.QMessageBox.question(
                self,
                "Onay",
                f"Toplam {len(exams)} sinav icin oturma plani olusturulacak.\n\n"
                f"Devam etmek istiyor musunuz?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.No:
                return
            
            from services.seating_plan_service import generate_seating_plan_for_exam

            progress = QtWidgets.QProgressDialog(
                "Tum sinavlar icin oturma planlari olusturuluyor...", 
                "Iptal", 
                0, 
                len(exams), 
                self
            )
            progress.setWindowTitle("Lutfen Bekleyin")
            progress.setWindowModality(QtCore.Qt.WindowModal)
            
            success_count = 0
            failed_exams = []
            
            for i, exam in enumerate(exams):
                if progress.wasCanceled():
                    break
                
                progress.setLabelText(f"Oturma plani olusturuluyor: {exam['code']} - {exam['name']}")
                progress.setValue(i)
                
                success, error_msg, result = generate_seating_plan_for_exam(exam['id'])
                
                if success:
                    success_count += 1
                else:
                    failed_exams.append(f"{exam['code']}: {error_msg}")
            
            progress.setValue(len(exams))

            if success_count == len(exams):
                QtWidgets.QMessageBox.information(
                    self,
                    "Basarili",
                    f"Tum sinavlar icin oturma plani basariyla olusturuldu!\n\n"
                    f"Toplam: {success_count} sinav"
                )
            elif success_count > 0:
                error_list = "\n".join(failed_exams[:5])
                if len(failed_exams) > 5:
                    error_list += f"\n... ve {len(failed_exams) - 5} tane daha"
                
                QtWidgets.QMessageBox.warning(
                    self,
                    "Kismi Basari",
                    f"Oturma planlari kismi olarak olusturuldu.\n\n"
                    f"Basarili: {success_count}/{len(exams)}\n"
                    f"Basarisiz: {len(failed_exams)}\n\n"
                    f"Hatalar:\n{error_list}"
                )
            else:
                error_list = "\n".join(failed_exams[:5])
                if len(failed_exams) > 5:
                    error_list += f"\n... ve {len(failed_exams) - 5} tane daha"
                
                QtWidgets.QMessageBox.critical(
                    self,
                    "Hata",
                    f"Hicbir sinav icin oturma plani olusturulamadi!\n\n"
                    f"Hatalar:\n{error_list}"
                )

            self.load_all_exams()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Hata olustu: {e}")
        finally:
            if progress:
                progress.close()
    
    def export_seating_pdf(self):
        """Oturma planını PDF olarak dışa aktar"""
        try:
            if not hasattr(self, 'selected_exam_id'):
                QtWidgets.QMessageBox.warning(self, "Uyari", "Lutfen once bir sinav secin!")
                return

            exam_info = fetch_all("""
                SELECT c.code, c.name FROM exams e
                JOIN courses c ON e.course_id = c.id
                WHERE e.id = %s
            """, [self.selected_exam_id])
            
            if not exam_info:
                return
            
            default_name = f"Oturma_Plani_{exam_info[0]['code']}.pdf"
            
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "PDF Dosyasini Kaydet",
                default_name,
                "PDF Dosyalari (*.pdf)"
            )
            
            if not file_path:
                return
            
            from services.seating_plan_service import export_seating_plan_to_pdf
            
            success, error_msg = export_seating_plan_to_pdf(self.selected_exam_id, file_path)
            
            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Basarili",
                    f"Oturma plani PDF olarak kaydedildi!\n\n{file_path}"
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Hata",
                    f"PDF olusturulamadi!\n\n{error_msg}"
                )
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"PDF export hatasi: {e}")


class AddClassroomDialog(QtWidgets.QDialog):
    """Derslik ekleme dialogu"""
    def __init__(self, department_id, parent=None):
        super().__init__(parent)
        self.department_id = department_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yeni Derslik Ekle")
        self.setFixedSize(700, 850)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QtWidgets.QLabel("🏫 Yeni Derslik Ekle")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 25px;
            }
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)

        form_widget = QtWidgets.QWidget()
        form_widget.setStyleSheet("background-color: white;")
        form_layout = QtWidgets.QVBoxLayout(form_widget)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(20)

        lbl_code = QtWidgets.QLabel("🏷️ Derslik Kodu")
        lbl_code.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_code)
        
        self.txt_code = QtWidgets.QLineEdit()
        self.txt_code.setPlaceholderText("Örnek: D301, A101")
        self.txt_code.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.txt_code)

        lbl_name = QtWidgets.QLabel("📝 Derslik Adı")
        lbl_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_name)
        
        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.setPlaceholderText("Örnek: 301 Numaralı Derslik")
        self.txt_name.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.txt_name)

        dimensions_layout = QtWidgets.QHBoxLayout()

        rows_widget = QtWidgets.QWidget()
        rows_layout = QtWidgets.QVBoxLayout(rows_widget)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_rows = QtWidgets.QLabel("📏 Boyuna Sıra (Satır)")
        lbl_rows.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        rows_layout.addWidget(lbl_rows)
        
        self.txt_rows = QtWidgets.QLineEdit()
        self.txt_rows.setText("9")
        self.txt_rows.setPlaceholderText("1-50 arası")
        validator = QtGui.QIntValidator(1, 50, self.txt_rows)
        self.txt_rows.setValidator(validator)
        self.txt_rows.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
        """)
        self.txt_rows.textChanged.connect(self.calculate_capacity)
        rows_layout.addWidget(self.txt_rows)
        
        dimensions_layout.addWidget(rows_widget)

        cols_widget = QtWidgets.QWidget()
        cols_layout = QtWidgets.QVBoxLayout(cols_widget)
        cols_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_cols = QtWidgets.QLabel("📐 Enine Sıra (Sütun)")
        lbl_cols.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        cols_layout.addWidget(lbl_cols)
        
        self.txt_cols = QtWidgets.QLineEdit()
        self.txt_cols.setText("7")
        self.txt_cols.setPlaceholderText("1-50 arası")
        validator = QtGui.QIntValidator(1, 50, self.txt_cols)
        self.txt_cols.setValidator(validator)
        self.txt_cols.setStyleSheet("""
            QLineEdit {
                padding: 14px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 25px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
        """)
        self.txt_cols.textChanged.connect(self.calculate_capacity)
        cols_layout.addWidget(self.txt_cols)
        
        dimensions_layout.addWidget(cols_widget)
        
        form_layout.addLayout(dimensions_layout)

        lbl_seat = QtWidgets.QLabel("🪑 Sıra Yapısı")
        lbl_seat.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_seat)
        
        self.combo_seat_group = QtWidgets.QComboBox()
        self.combo_seat_group.addItem("2'li (İkili Sıra)", 2)
        self.combo_seat_group.addItem("3'lü (Üçlü Sıra)", 3)
        self.combo_seat_group.addItem("4'lü (Dörtlü Sıra)", 4)
        self.combo_seat_group.setCurrentIndex(1)  # 3'lu varsayilan
        self.combo_seat_group.setStyleSheet("""
            QComboBox {
                padding: 14px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                min-height: 25px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
        """)
        self.combo_seat_group.currentIndexChanged.connect(self.calculate_capacity)
        form_layout.addWidget(self.combo_seat_group)

        capacity_title = QtWidgets.QLabel("🎯 Sınav Kapasitesi")
        capacity_title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #555;
            margin-top: 10px;
        """)
        capacity_title.setAlignment(QtCore.Qt.AlignCenter)
        form_layout.addWidget(capacity_title)
        
        self.lbl_capacity = QtWidgets.QLabel("42 öğrenci")
        self.lbl_capacity.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #27ae60;
            margin-bottom: 10px;
        """)
        self.lbl_capacity.setAlignment(QtCore.Qt.AlignCenter)
        form_layout.addWidget(self.lbl_capacity)

        self.calculate_capacity()

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        btn_save = QtWidgets.QPushButton("💾 Kaydet")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #229954, stop:1 #1e8449);
            }
        """)
        btn_save.setCursor(QtCore.Qt.PointingHandCursor)
        btn_save.clicked.connect(self.save_classroom)
        btn_layout.addWidget(btn_save)

        btn_cancel = QtWidgets.QPushButton("❌ İptal")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        form_layout.addLayout(btn_layout)

        main_layout.addWidget(form_widget)
        self.setLayout(main_layout)
    
    def calculate_capacity(self):
        """Sınav kapasitesini otomatik hesapla"""
        try:
            rows = int(self.txt_rows.text()) if self.txt_rows.text() else 0
            cols = int(self.txt_cols.text()) if self.txt_cols.text() else 0
            seat_group = self.combo_seat_group.currentData()

            if seat_group == 2:
                capacity = cols * (rows // seat_group)
            else:
                capacity = cols * 2 * (rows // seat_group)

            self.lbl_capacity.setText(f"{capacity} öğrenci")
        except ValueError:
            self.lbl_capacity.setText("0 öğrenci")

    def save_classroom(self):
        """Dersligi kaydet"""
        code = self.txt_code.text().strip()
        name = self.txt_name.text().strip()
        rows = int(self.txt_rows.text()) if self.txt_rows.text() else 0
        cols = int(self.txt_cols.text()) if self.txt_cols.text() else 0
        seat_group = self.combo_seat_group.currentData()

        if not code or not name:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lutfen tum alanlari doldurun!")
            return

        try:
            if seat_group == 2:
                capacity = cols * (rows // seat_group)
            else:
                capacity = cols * 2 * (rows // seat_group)

            seat_group_map = {2: "DOUBLE", 3: "TRIPLE", 4: "QUAD"}
            seat_group_enum = seat_group_map.get(seat_group, "TRIPLE")

            execute("""
                INSERT INTO classrooms (code, name, capacity, "rows", cols, seat_group, department_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [code, name, capacity, rows, cols, seat_group_enum, self.department_id])

            QtWidgets.QMessageBox.information(
                self, 
                "Basarili", 
                f"Derslik eklendi!\n\nHesaplanan Kapasite: {capacity} ogrenci"
            )
            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Derslik eklenemedi: {e}")


class EditClassroomDialog(QtWidgets.QDialog):
    """Derslik duzenleme dialogu"""
    def __init__(self, classroom, parent=None):
        super().__init__(parent)
        self.classroom = classroom
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Derslik Düzenle")
        self.setFixedSize(550, 650)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QtWidgets.QLabel("✏️ Derslik Düzenle")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 25px;
            }
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)

        form_widget = QtWidgets.QWidget()
        form_widget.setStyleSheet("background-color: white;")
        form_layout = QtWidgets.QVBoxLayout(form_widget)
        form_layout.setContentsMargins(40, 30, 40, 30)
        form_layout.setSpacing(20)

        lbl_code = QtWidgets.QLabel("🏷️ Derslik Kodu")
        lbl_code.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_code)
        
        self.txt_code = QtWidgets.QLineEdit()
        self.txt_code.setText(self.classroom['code'])
        self.txt_code.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #f39c12;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.txt_code)

        lbl_name = QtWidgets.QLabel("📝 Derslik Adı")
        lbl_name.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_name)
        
        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.setText(self.classroom['name'])
        self.txt_name.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #f39c12;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.txt_name)

        dimensions_layout = QtWidgets.QHBoxLayout()

        rows_widget = QtWidgets.QWidget()
        rows_layout = QtWidgets.QVBoxLayout(rows_widget)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_rows = QtWidgets.QLabel("📏 Boyuna Sıra (Satır)")
        lbl_rows.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        rows_layout.addWidget(lbl_rows)
        
        self.txt_rows = QtWidgets.QLineEdit()
        self.txt_rows.setText(str(self.classroom['rows']))
        self.txt_rows.setPlaceholderText("1-50 arası")
        validator = QtGui.QIntValidator(1, 50, self.txt_rows)
        self.txt_rows.setValidator(validator)
        self.txt_rows.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #f39c12;
                background-color: white;
            }
        """)
        self.txt_rows.textChanged.connect(self.calculate_capacity)
        rows_layout.addWidget(self.txt_rows)
        
        dimensions_layout.addWidget(rows_widget)

        cols_widget = QtWidgets.QWidget()
        cols_layout = QtWidgets.QVBoxLayout(cols_widget)
        cols_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_cols = QtWidgets.QLabel("📐 Enine Sıra (Sütun)")
        lbl_cols.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        cols_layout.addWidget(lbl_cols)
        
        self.txt_cols = QtWidgets.QLineEdit()
        self.txt_cols.setText(str(self.classroom['cols']))
        self.txt_cols.setPlaceholderText("1-50 arası")
        validator = QtGui.QIntValidator(1, 50, self.txt_cols)
        self.txt_cols.setValidator(validator)
        self.txt_cols.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid #f39c12;
                background-color: white;
            }
        """)
        self.txt_cols.textChanged.connect(self.calculate_capacity)
        cols_layout.addWidget(self.txt_cols)
        
        dimensions_layout.addWidget(cols_widget)
        
        form_layout.addLayout(dimensions_layout)

        lbl_seat = QtWidgets.QLabel("🪑 Sıra Yapısı")
        lbl_seat.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        form_layout.addWidget(lbl_seat)
        
        self.combo_seat_group = QtWidgets.QComboBox()
        self.combo_seat_group.addItem("2'li (İkili Sıra)", 2)
        self.combo_seat_group.addItem("3'lü (Üçlü Sıra)", 3)
        self.combo_seat_group.addItem("4'lü (Dörtlü Sıra)", 4)

        seat_group_map = {"DOUBLE": 2, "TRIPLE": 3, "QUAD": 4}
        current_seat_group = seat_group_map.get(self.classroom['seat_group'], 3)
        if current_seat_group == 2:
            self.combo_seat_group.setCurrentIndex(0)
        elif current_seat_group == 3:
            self.combo_seat_group.setCurrentIndex(1)
        else:
            self.combo_seat_group.setCurrentIndex(2)
        
        self.combo_seat_group.setStyleSheet("""
            QComboBox {
                padding: 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            QComboBox:focus {
                border: 2px solid #f39c12;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                margin-right: 10px;
            }
        """)
        self.combo_seat_group.currentIndexChanged.connect(self.calculate_capacity)
        form_layout.addWidget(self.combo_seat_group)

        capacity_container = QtWidgets.QWidget()
        capacity_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d4edda, stop:1 #c3e6cb);
                border: 3px solid #27ae60;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        capacity_layout = QtWidgets.QVBoxLayout(capacity_container)
        capacity_layout.setContentsMargins(15, 15, 15, 15)
        
        capacity_title = QtWidgets.QLabel("🎯 Sınav Kapasitesi")
        capacity_title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #155724;
        """)
        capacity_title.setAlignment(QtCore.Qt.AlignCenter)
        capacity_layout.addWidget(capacity_title)
        
        self.lbl_capacity = QtWidgets.QLabel("")
        self.lbl_capacity.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #155724;
        """)
        self.lbl_capacity.setAlignment(QtCore.Qt.AlignCenter)
        capacity_layout.addWidget(self.lbl_capacity)
        
        form_layout.addWidget(capacity_container)

        self.calculate_capacity()

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        btn_save = QtWidgets.QPushButton("💾 Güncelle")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e67e22, stop:1 #d35400);
            }
        """)
        btn_save.setCursor(QtCore.Qt.PointingHandCursor)
        btn_save.clicked.connect(self.update_classroom)
        btn_layout.addWidget(btn_save)

        btn_cancel = QtWidgets.QPushButton("❌ İptal")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        form_layout.addLayout(btn_layout)

        main_layout.addWidget(form_widget)
        self.setLayout(main_layout)
    
    def calculate_capacity(self):
        """Sınav kapasitesini otomatik hesapla"""
        try:
            rows = int(self.txt_rows.text()) if self.txt_rows.text() else 0
            cols = int(self.txt_cols.text()) if self.txt_cols.text() else 0
            seat_group = self.combo_seat_group.currentData()

            if seat_group == 2:
                capacity = cols * (rows // seat_group)
            else:
                capacity = cols * 2 * (rows // seat_group)

            self.lbl_capacity.setText(f"{capacity} öğrenci")
        except ValueError:
            self.lbl_capacity.setText("0 öğrenci")

    def update_classroom(self):
        """Dersligi guncelle"""
        code = self.txt_code.text().strip()
        name = self.txt_name.text().strip()
        rows = int(self.txt_rows.text()) if self.txt_rows.text() else 0
        cols = int(self.txt_cols.text()) if self.txt_cols.text() else 0
        seat_group = self.combo_seat_group.currentData()

        if not code or not name:
            QtWidgets.QMessageBox.warning(self, "Hata", "Lutfen tum alanlari doldurun!")
            return

        try:
            if seat_group == 2:
                capacity = cols * (rows // seat_group)
            else:
                capacity = cols * 2 * (rows // seat_group)

            seat_group_map = {2: "DOUBLE", 3: "TRIPLE", 4: "QUAD"}
            seat_group_enum = seat_group_map.get(seat_group, "TRIPLE")

            execute("""
                UPDATE classrooms 
                SET code = %s, name = %s, capacity = %s, "rows" = %s, cols = %s, seat_group = %s
                WHERE id = %s
            """, [code, name, capacity, rows, cols, seat_group_enum, self.classroom['id']])

            self.accept()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Derslik guncellenemedi: {e}")


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

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)

        viz_widget = QtWidgets.QWidget()
        viz_layout = QtWidgets.QGridLayout()
        viz_layout.setSpacing(5)

        rows = self.classroom['rows']
        cols = self.classroom['cols']

        seat_group_str = self.classroom['seat_group']
        seat_group_map = {"DOUBLE": 2, "TRIPLE": 3, "QUAD": 4}
        seat_group = seat_group_map.get(seat_group_str, 3)

        seat_num = 1
        for row in range(rows):
            for col in range(cols):
                seat = QtWidgets.QPushButton(str(seat_num))
                seat.setFixedSize(40, 40)

                if (col % seat_group) == 0:
                    seat.setStyleSheet("background-color: #90EE90;")
                elif (col % seat_group) == 1:
                    seat.setStyleSheet("background-color: #87CEEB;")
                else:
                    seat.setStyleSheet("background-color: #FFB6C1;")

                viz_layout.addWidget(seat, row, col)
                seat_num += 1

        viz_widget.setLayout(viz_layout)
        scroll.setWidget(viz_widget)
        layout.addWidget(scroll)

        btn_close = QtWidgets.QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)
