from PyQt5 import QtWidgets, QtCore, QtGui
from models.user import User
from services.auth_service import create_coordinator
from services.db import fetch_all
from services.excel_service import import_departments

class AdminDashboard(QtWidgets.QWidget):
    """ Admin paneli — tüm sistem yönetimi"""
    def __init__(self, user: User, on_logout=None, on_dept_access=None):
        super().__init__()
        self.user = user
        self.on_logout = on_logout
        self.on_dept_access = on_dept_access
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle(f"Admin Dashboard - {self.user.email}")
        self.setMinimumSize(1000, 700)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 20, 30, 20)

        title_layout = QtWidgets.QVBoxLayout()
        
        title = QtWidgets.QLabel(f"👋 Hoş geldiniz, {self.user.email}")
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: white;
        """)
        title_layout.addWidget(title)
        
        subtitle = QtWidgets.QLabel("🔹 Admin Yönetim Paneli")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(255, 255, 255, 0.9);
            margin-top: 5px;
        """)
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        btn_logout = QtWidgets.QPushButton("🚪 Çıkış Yap")
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.9);
                color: white;
                padding: 10px 25px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: #f44336;
                border: 2px solid white;
            }
        """)
        btn_logout.setCursor(QtCore.Qt.PointingHandCursor)
        btn_logout.clicked.connect(self._logout)
        header_layout.addWidget(btn_logout)
        
        main_layout.addWidget(header_widget)

        content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        tabs = QtWidgets.QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                border-radius: 8px;
                background: white;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f5f5, stop:1 #e0e0e0);
                color: #333;
                padding: 14px 40px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 180px;
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
        """)

        dept_tab = self._create_department_management_tab()
        tabs.addTab(dept_tab, "🏛️ Bölüm Yönetimi")

        user_tab = self._create_user_management_tab()
        tabs.addTab(user_tab, "👥 Kullanıcı Yönetimi")

        all_students_tab = self._create_all_students_tab()
        tabs.addTab(all_students_tab, "👨‍🎓 Tüm Öğrenciler")

        all_courses_tab = self._create_all_courses_tab()
        tabs.addTab(all_courses_tab, "📚 Tüm Dersler")
        
        content_layout.addWidget(tabs)
        
        main_layout.addWidget(content_widget)
        self.setLayout(main_layout)
    
    def _create_action_card(self, icon, title, description, color, callback):
        """Aksiyon kartı oluştur"""
        card = QtWidgets.QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
            }}
            QWidget:hover {{
                background-color: #f8f9fa;
                border: 3px solid {color};
            }}
        """)
        card.setCursor(QtCore.Qt.PointingHandCursor)
        
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(10)

        lbl_icon = QtWidgets.QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 48px;")
        lbl_icon.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(lbl_icon)

        lbl_title = QtWidgets.QLabel(title)
        lbl_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """)
        lbl_title.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(lbl_title)

        lbl_desc = QtWidgets.QLabel(description)
        lbl_desc.setStyleSheet("""
            font-size: 12px;
            color: #666;
        """)
        lbl_desc.setAlignment(QtCore.Qt.AlignCenter)
        lbl_desc.setWordWrap(True)
        card_layout.addWidget(lbl_desc)

        btn = QtWidgets.QPushButton("Başlat")
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                padding: 10px;
                border-radius: 5px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                opacity: 0.8;
            }}
        """)
        btn.clicked.connect(callback)
        card_layout.addWidget(btn)
        
        return card
    
    def _create_department_management_tab(self):
        """Bölüm yönetimi sekmesi"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info = QtWidgets.QLabel(
            "🏛️ Bir bölüm seçin ve koordinatör olarak o bölümün yönetim paneline erişin.\n"
            "Admin olarak tüm bölümlerin verilerine erişebilir ve düzenleyebilirsiniz."
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

        departments = fetch_all("""
            SELECT DISTINCT d.id, d.name, COUNT(u.id) as coord_count
            FROM departments d
            INNER JOIN users u ON d.id = u.department_id
            WHERE u.role = 'COORDINATOR'
            GROUP BY d.id, d.name
            ORDER BY d.name
        """)
        
        if departments:
            for dept in departments:
                coordinators = fetch_all("""
                    SELECT id, email
                    FROM users
                    WHERE department_id = %s AND role = 'COORDINATOR'
                    ORDER BY email
                """, [dept['id']])
                
                dept_card = QtWidgets.QWidget()
                dept_card.setStyleSheet("""
                    QWidget {
                        background-color: white;
                        border: 3px solid #2196F3;
                        border-radius: 12px;
                    }
                    QWidget:hover {
                        background-color: #f8f9fa;
                        border: 4px solid #2196F3;
                    }
                """)
                
                dept_main_layout = QtWidgets.QVBoxLayout(dept_card)
                dept_main_layout.setContentsMargins(30, 25, 30, 25)
                dept_main_layout.setSpacing(15)

                top_layout = QtWidgets.QHBoxLayout()

                info_layout = QtWidgets.QVBoxLayout()
                info_layout.setSpacing(8)
                
                lbl_name = QtWidgets.QLabel(f"🏛️ {dept['name']}")
                lbl_name.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
                info_layout.addWidget(lbl_name)
                
                lbl_details = QtWidgets.QLabel(f"🧑‍🏫 {dept['coord_count']} Koordinatör")
                lbl_details.setStyleSheet("font-size: 15px; color: #666;")
                info_layout.addWidget(lbl_details)
                
                top_layout.addLayout(info_layout)
                top_layout.addStretch()

                btn_access = QtWidgets.QPushButton("📂 Yönetim Paneline Gir")
                btn_access.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        padding: 15px 30px;
                        border-radius: 8px;
                        border: none;
                        font-weight: bold;
                        font-size: 15px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                btn_access.setCursor(QtCore.Qt.PointingHandCursor)
                btn_access.clicked.connect(lambda checked, d=dept: self._access_department(d))
                top_layout.addWidget(btn_access)
                
                dept_main_layout.addLayout(top_layout)

                if coordinators:
                    separator = QtWidgets.QFrame()
                    separator.setFrameShape(QtWidgets.QFrame.HLine)
                    separator.setFrameShadow(QtWidgets.QFrame.Sunken)
                    separator.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")
                    dept_main_layout.addWidget(separator)

                    coord_header = QtWidgets.QLabel("📋 Bölüm Koordinatörleri:")
                    coord_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #555; margin-top: 5px;")
                    dept_main_layout.addWidget(coord_header)

                    coord_list_layout = QtWidgets.QVBoxLayout()
                    coord_list_layout.setSpacing(8)
                    
                    for coord in coordinators:
                        coord_item = QtWidgets.QWidget()
                        coord_item.setStyleSheet("""
                            QWidget {
                                background-color: #f0f7ff;
                                border: 1px solid #bbdefb;
                                border-radius: 6px;
                                padding: 8px;
                            }
                        """)
                        coord_item_layout = QtWidgets.QHBoxLayout(coord_item)
                        coord_item_layout.setContentsMargins(12, 8, 12, 8)

                        coord_email_label = QtWidgets.QLabel(f"👤 {coord['email']}")
                        coord_email_label.setStyleSheet("font-size: 13px; color: #1565C0; font-weight: 500;")
                        coord_item_layout.addWidget(coord_email_label)
                        
                        coord_item_layout.addStretch()
                        
                        coord_list_layout.addWidget(coord_item)
                    
                    dept_main_layout.addLayout(coord_list_layout)
                
                layout.addWidget(dept_card)
        else:
            no_dept_label = QtWidgets.QLabel(
                "⚠️ Henüz koordinatörü olan bölüm bulunmuyor.\n\n"
                "Koordinatör eklemek için 'Kullanıcı Yönetimi' sekmesine gidin."
            )
            no_dept_label.setStyleSheet("""
                font-size: 14px;
                color: #999;
                padding: 50px;
                text-align: center;
            """)
            no_dept_label.setAlignment(QtCore.Qt.AlignCenter)
            no_dept_label.setWordWrap(True)
            layout.addWidget(no_dept_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_user_management_tab(self):
        """Kullanıcı yönetimi sekmesi"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        btn_layout = QtWidgets.QHBoxLayout()

        btn_add = QtWidgets.QPushButton("➕ Yeni Koordinatör Ekle")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_add.clicked.connect(self._open_add_coord_dialog)
        btn_layout.addWidget(btn_add)
        
        btn_refresh = QtWidgets.QPushButton("🔄 Listeyi Yenile")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        btn_refresh.clicked.connect(self._refresh_users)
        btn_layout.addWidget(btn_refresh)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.user_table = QtWidgets.QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels([
            "ID", "E-posta", "Rol", "Bölüm", "İşlem"
        ])

        self.user_table.setColumnWidth(0, 80)
        self.user_table.setColumnWidth(1, 300)
        self.user_table.setColumnWidth(2, 180)
        self.user_table.setColumnWidth(3, 280)
        self.user_table.setColumnWidth(4, 140)
        
        self.user_table.horizontalHeader().setStretchLastSection(False)
        self.user_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.user_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.user_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 2px solid #ddd;
                border-radius: 8px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 15px 12px;
                font-size: 14px;
            }
            QTableWidget::item:selected {
                background-color: #667eea;
                color: white;
            }
            QHeaderView::section {
                background-color: #667eea;
                color: white;
                padding: 16px;
                border: none;
                font-weight: bold;
                font-size: 15px;
            }
        """)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.verticalHeader().setDefaultSectionSize(55)
        layout.addWidget(self.user_table)

        self._refresh_users()
        
        return widget
    
    def _access_department(self, department):
        """Bölüm yönetim paneline eriş (admin olarak - aynı pencerede)"""
        try:
            from models.user import User, UserRole

            temp_user = User(
                id=self.user.id,
                email=f"Admin → {department['name']}",
                role=UserRole.ADMIN,
                department_id=department['id']
            )

            if self.on_dept_access:
                self.on_dept_access(temp_user)
            else:
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Uyarı", 
                    "Bölüm erişimi callback'i tanımlı değil!"
                )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Bölüme erişilemedi: {e}")
    
    def _refresh_users(self):
        """Kullanıcı tablosunu yenile"""
        try:
            users = fetch_all("""
                SELECT u.id, u.email, u.role, u.department_id, d.name as department_name
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                ORDER BY u.id
            """)
            
            self.user_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.user_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(user['id'])))

                self.user_table.setItem(row, 1, QtWidgets.QTableWidgetItem(user['email']))

                role_text = "👑 Admin" if user['role'] == 'ADMIN' else "🧑‍🏫 Koordinatör"
                role_item = QtWidgets.QTableWidgetItem(role_text)
                role_item.setFont(QtGui.QFont("Arial", 13, QtGui.QFont.Bold))
                if user['role'] == 'ADMIN':
                    role_item.setForeground(QtGui.QColor("#f44336"))
                else:
                    role_item.setForeground(QtGui.QColor("#2196F3"))
                self.user_table.setItem(row, 2, role_item)

                dept_name = user['department_name'] if user['department_name'] else '-'
                self.user_table.setItem(row, 3, QtWidgets.QTableWidgetItem(dept_name))

                if user['role'] == 'COORDINATOR':
                    btn_delete = QtWidgets.QPushButton("Sil")
                    btn_delete.setFixedSize(85, 38)
                    btn_delete.setToolTip(f"'{user['email']}' koordinatörünü sil")
                    btn_delete.setStyleSheet("""
                        QPushButton {
                            background-color: #fff;
                            color: #f44336;
                            border: 2px solid #f44336;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #f44336;
                            color: white;
                        }
                    """)
                    btn_delete.setCursor(QtCore.Qt.PointingHandCursor)
                    btn_delete.clicked.connect(lambda checked, uid=user['id'], email=user['email']: self._delete_user(uid, email))

                    container = QtWidgets.QWidget()
                    container_layout = QtWidgets.QHBoxLayout(container)
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    container_layout.addStretch()
                    container_layout.addWidget(btn_delete)
                    container_layout.addStretch()
                    
                    self.user_table.setCellWidget(row, 4, container)
                else:
                    lbl = QtWidgets.QLabel("-")
                    lbl.setStyleSheet("color: #ddd; font-size: 16px; font-weight: bold;")
                    lbl.setAlignment(QtCore.Qt.AlignCenter)
                    self.user_table.setCellWidget(row, 4, lbl)
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenemedi: {e}")
    
    def _create_all_students_tab(self):
        """Tüm öğrenciler sekmesi (bölüm filtreli)"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        filter_layout = QtWidgets.QHBoxLayout()
        
        lbl_filter = QtWidgets.QLabel("🏛️ Bölüm Filtresi:")
        lbl_filter.setStyleSheet("font-size: 13px; font-weight: bold;")
        filter_layout.addWidget(lbl_filter)
        
        self.student_dept_combo = QtWidgets.QComboBox()
        self.student_dept_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 2px solid #9C27B0;
                border-radius: 5px;
                font-size: 13px;
                min-width: 200px;
            }
        """)
        self.student_dept_combo.addItem("Tüm Bölümler", None)

        departments = fetch_all("SELECT id, name FROM departments ORDER BY name")
        for dept in departments:
            self.student_dept_combo.addItem(dept['name'], dept['id'])
        
        self.student_dept_combo.currentIndexChanged.connect(self._filter_students)
        filter_layout.addWidget(self.student_dept_combo)
        
        filter_layout.addStretch()

        self.student_stats_label = QtWidgets.QLabel("Toplam: 0 öğrenci")
        self.student_stats_label.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 5px 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        """)
        filter_layout.addWidget(self.student_stats_label)
        
        layout.addLayout(filter_layout)

        self.all_students_table = QtWidgets.QTableWidget()
        self.all_students_table.setColumnCount(5)
        self.all_students_table.setHorizontalHeaderLabels([
            "ID", "Öğrenci No", "Ad Soyad", "Sınıf", "Bölüm"
        ])

        self.all_students_table.setColumnWidth(0, 60)
        self.all_students_table.setColumnWidth(1, 120)
        self.all_students_table.setColumnWidth(2, 250)
        self.all_students_table.setColumnWidth(3, 80)
        self.all_students_table.horizontalHeader().setStretchLastSection(True)
        
        self.all_students_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.all_students_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.all_students_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
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
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        self.all_students_table.setAlternatingRowColors(True)
        layout.addWidget(self.all_students_table)

        self._filter_students()
        
        return widget
    
    def _filter_students(self):
        """Öğrencileri bölüme göre filtrele"""
        try:
            dept_id = self.student_dept_combo.currentData()
            
            if dept_id is None:
                students = fetch_all("""
                    SELECT s.id, s.number, s.fullname, s.grade, d.name as department_name
                    FROM students s
                    LEFT JOIN departments d ON s.department_id = d.id
                    ORDER BY d.name, s.number
                """)
            else:
                students = fetch_all("""
                    SELECT s.id, s.number, s.fullname, s.grade, d.name as department_name
                    FROM students s
                    LEFT JOIN departments d ON s.department_id = d.id
                    WHERE s.department_id = %s
                    ORDER BY s.number
                """, [dept_id])
            
            self.all_students_table.setRowCount(len(students))
            
            for row, student in enumerate(students):
                self.all_students_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(student['id'])))
                self.all_students_table.setItem(row, 1, QtWidgets.QTableWidgetItem(student['number']))
                self.all_students_table.setItem(row, 2, QtWidgets.QTableWidgetItem(student['fullname']))
                self.all_students_table.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{student['grade']}. Sınıf"))
                dept_name = student['department_name'] if student['department_name'] else '-'
                self.all_students_table.setItem(row, 4, QtWidgets.QTableWidgetItem(dept_name))

            self.student_stats_label.setText(f"Toplam: {len(students)} öğrenci")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Öğrenciler yüklenemedi: {e}")
    
    def _create_all_courses_tab(self):
        """Tüm dersler sekmesi (bölüm filtreli)"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        filter_layout = QtWidgets.QHBoxLayout()
        
        lbl_filter = QtWidgets.QLabel("🏛️ Bölüm Filtresi:")
        lbl_filter.setStyleSheet("font-size: 13px; font-weight: bold;")
        filter_layout.addWidget(lbl_filter)
        
        self.course_dept_combo = QtWidgets.QComboBox()
        self.course_dept_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 2px solid #00BCD4;
                border-radius: 5px;
                font-size: 13px;
                min-width: 200px;
            }
        """)
        self.course_dept_combo.addItem("Tüm Bölümler", None)

        departments = fetch_all("SELECT id, name FROM departments ORDER BY name")
        for dept in departments:
            self.course_dept_combo.addItem(dept['name'], dept['id'])
        
        self.course_dept_combo.currentIndexChanged.connect(self._filter_courses)
        filter_layout.addWidget(self.course_dept_combo)
        
        filter_layout.addStretch()

        self.course_stats_label = QtWidgets.QLabel("Toplam: 0 ders")
        self.course_stats_label.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 5px 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
        """)
        filter_layout.addWidget(self.course_stats_label)
        
        layout.addLayout(filter_layout)

        self.all_courses_table = QtWidgets.QTableWidget()
        self.all_courses_table.setColumnCount(6)
        self.all_courses_table.setHorizontalHeaderLabels([
            "ID", "Ders Kodu", "Ders Adı", "Öğretim Elemanı", "Sınıf", "Bölüm"
        ])

        self.all_courses_table.setColumnWidth(0, 60)
        self.all_courses_table.setColumnWidth(1, 100)
        self.all_courses_table.setColumnWidth(2, 250)
        self.all_courses_table.setColumnWidth(3, 180)
        self.all_courses_table.setColumnWidth(4, 80)
        self.all_courses_table.horizontalHeader().setStretchLastSection(True)
        
        self.all_courses_table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)
        self.all_courses_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.all_courses_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
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
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        self.all_courses_table.setAlternatingRowColors(True)
        layout.addWidget(self.all_courses_table)

        self._filter_courses()
        
        return widget
    
    def _filter_courses(self):
        """Dersleri bölüme göre filtrele"""
        try:
            dept_id = self.course_dept_combo.currentData()
            
            if dept_id is None:
                courses = fetch_all("""
                    SELECT c.id, c.code, c.name, c.instructor, c.grade, d.name as department_name
                    FROM courses c
                    LEFT JOIN departments d ON c.department_id = d.id
                    ORDER BY d.name, c.code
                """)
            else:
                courses = fetch_all("""
                    SELECT c.id, c.code, c.name, c.instructor, c.grade, d.name as department_name
                    FROM courses c
                    LEFT JOIN departments d ON c.department_id = d.id
                    WHERE c.department_id = %s
                    ORDER BY c.code
                """, [dept_id])
            
            self.all_courses_table.setRowCount(len(courses))
            
            for row, course in enumerate(courses):
                self.all_courses_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(course['id'])))
                self.all_courses_table.setItem(row, 1, QtWidgets.QTableWidgetItem(course['code']))
                self.all_courses_table.setItem(row, 2, QtWidgets.QTableWidgetItem(course['name']))
                instructor = course['instructor'] if course['instructor'] else '-'
                self.all_courses_table.setItem(row, 3, QtWidgets.QTableWidgetItem(instructor))
                grade_text = f"{course['grade']}. Sınıf" if course['grade'] else '-'
                self.all_courses_table.setItem(row, 4, QtWidgets.QTableWidgetItem(grade_text))
                dept_name = course['department_name'] if course['department_name'] else '-'
                self.all_courses_table.setItem(row, 5, QtWidgets.QTableWidgetItem(dept_name))

            self.course_stats_label.setText(f"Toplam: {len(courses)} ders")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Dersler yüklenemedi: {e}")
    
    def _delete_user(self, user_id, email):
        """Kullanıcıyı sil"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Kullanıcı Sil",
            f"'{email}' kullanıcısını silmek istediğinizden emin misiniz?\n\n"
            f"Bu işlem geri alınamaz!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                from services.db import execute
                execute("DELETE FROM users WHERE id = %s", [user_id])
                QtWidgets.QMessageBox.information(self, "Başarılı", f"'{email}' kullanıcısı silindi.")
                self._refresh_users()
                self.info_box.append(f"🗑️ Kullanıcı silindi: {email}\n")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hata", f"Kullanıcı silinemedi: {e}")

    def _show_users(self):
        """Veritabanındaki tüm kullanıcıları listele"""
        try:
            users = fetch_all("""
                SELECT u.id, u.email, u.role, u.department_id, d.name as department_name
                FROM users u
                LEFT JOIN departments d ON u.department_id = d.id
                ORDER BY u.id
            """)
            
            if not users:
                self.info_box.setHtml("""
                    <div style='text-align: center; padding: 50px; color: #999;'>
                        <h2 style='font-size: 48px;'>⚠️</h2>
                        <p style='font-size: 16px;'>Hiç kullanıcı bulunamadı.</p>
                    </div>
                """)
                return

            users_html = """
            <div style='font-family: Arial; padding: 15px;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;'>
                    <h2 style='margin: 0; font-size: 20px;'>👥 KAYITLI KULLANICILAR</h2>
                    <p style='margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;'>
                        Toplam: """ + str(len(users)) + """ kullanıcı
                    </p>
                </div>
            """
            
            for i, u in enumerate(users):
                if u['role'] == 'ADMIN':
                    role_color = '#f44336'
                    role_icon = '👑'
                    role_text = 'Admin'
                else:
                    role_color = '#2196F3'
                    role_icon = '🧑‍🏫'
                    role_text = 'Koordinatör'
                
                dept_name = u['department_name'] if u['department_name'] else 'Atanmamış'
                
                users_html += f"""
                <div style='background-color: white; border: 2px solid #e0e0e0; 
                           border-radius: 8px; padding: 15px; margin-bottom: 15px;'>
                    <div style='display: flex; align-items: center;'>
                        <div style='flex: 1;'>
                            <div style='font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px;'>
                                {role_icon} {u['email']}
                            </div>
                            <table style='width: 100%; font-size: 13px;'>
                                <tr>
                                    <td style='padding: 4px; color: #666; width: 100px;'>ID:</td>
                                    <td style='padding: 4px; font-weight: bold; color: #333;'>{u['id']}</td>
                                </tr>
                                <tr>
                                    <td style='padding: 4px; color: #666;'>Rol:</td>
                                    <td style='padding: 4px;'>
                                        <span style='background-color: {role_color}; color: white; 
                                                    padding: 3px 10px; border-radius: 12px; 
                                                    font-size: 11px; font-weight: bold;'>
                                            {role_text}
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td style='padding: 4px; color: #666;'>Bölüm:</td>
                                    <td style='padding: 4px; color: #333;'>{dept_name}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </div>
                """
            
            users_html += "</div>"
            self.info_box.setHtml(users_html)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenemedi:\n{e}")

    def _open_add_coord_dialog(self):
        """Yeni koordinatör ekleme ekranı"""
        dialog = AddCoordinatorDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self._refresh_users()
            QtWidgets.QMessageBox.information(self, "Başarılı", "✅ Yeni koordinatör başarıyla eklendi.")

    def _logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Çıkış",
            "Çıkış yapmak istiyor musunuz?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes and self.on_logout:
            self.on_logout()


class AddCoordinatorDialog(QtWidgets.QDialog):
    """Yeni bölüm koordinatörü ekleme arayüzü"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("Yeni Bölüm Koordinatörü Ekle")
        self.setFixedSize(600, 520)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QtWidgets.QLabel("🧑‍🏫 Yeni Koordinatör Ekle")
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)

        form_widget = QtWidgets.QWidget()
        form_widget.setStyleSheet("background-color: white;")
        layout = QtWidgets.QVBoxLayout(form_widget)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(25)

        lbl_email = QtWidgets.QLabel("📧 E-posta Adresi")
        lbl_email.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        layout.addWidget(lbl_email)
        
        self.txt_email = QtWidgets.QLineEdit()
        self.txt_email.setPlaceholderText("ornek: koordinator@university.edu")
        self.txt_email.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                font-size: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
        """)
        layout.addWidget(self.txt_email)

        lbl_password = QtWidgets.QLabel("🔒 Şifre")
        lbl_password.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        layout.addWidget(lbl_password)
        
        self.txt_password = QtWidgets.QLineEdit()
        self.txt_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.txt_password.setPlaceholderText("En az 6 karakter uzunlugunda")
        self.txt_password.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                font-size: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: white;
            }
        """)
        layout.addWidget(self.txt_password)

        lbl_dept = QtWidgets.QLabel("🏛️ Bölüm Seçimi")
        lbl_dept.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        layout.addWidget(lbl_dept)
        
        self.combo_department = QtWidgets.QComboBox()
        self.combo_department.setStyleSheet("""
            QComboBox {
                padding: 15px;
                font-size: 15px;
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f9f9f9;
                min-height: 20px;
            }
            QComboBox:focus {
                border: 2px solid #667eea;
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
        self._load_departments()
        layout.addWidget(self.combo_department)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setContentsMargins(0, 20, 0, 0)
        
        btn_save = QtWidgets.QPushButton("💾 Kaydet")
        btn_save.setStyleSheet("""
            QPushButton {
                padding: 15px 40px;
                font-size: 15px;
                font-weight: bold;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border-radius: 10px;
                border: none;
                min-height: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
        """)
        btn_save.setCursor(QtCore.Qt.PointingHandCursor)
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QtWidgets.QPushButton("❌ İptal")
        btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 15px 40px;
                font-size: 15px;
                font-weight: bold;
                background-color: #95a5a6;
                color: white;
                border-radius: 10px;
                border: none;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.setCursor(QtCore.Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)

        main_layout.addWidget(form_widget)
        self.setLayout(main_layout)

    def _load_departments(self):
        try:
            departments = fetch_all("SELECT id, name FROM departments ORDER BY id")
            if not departments:
                import_departments()
                departments = fetch_all("SELECT id, name FROM departments ORDER BY id")

            self.combo_department.clear()
            for dept in departments:
                self.combo_department.addItem(dept["name"], dept["id"])

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"Bölümler yüklenemedi:\n{e}")

    def _save(self):
        email = self.txt_email.text().strip()
        password = self.txt_password.text().strip()
        department_id = self.combo_department.currentData()

        if not email or "@" not in email:
            QtWidgets.QMessageBox.warning(self, "Geçersiz Giriş", "Lütfen geçerli bir e-posta girin!")
            return

        if len(password) < 6:
            QtWidgets.QMessageBox.warning(self, "Hatalı Şifre", "Şifre en az 6 karakter olmalıdır!")
            return

        if department_id is None:
            QtWidgets.QMessageBox.warning(self, "Eksik Bilgi", "Bir bölüm seçmelisiniz!")
            return

        try:
            success, message = create_coordinator(email, password, department_id)
            if success:
                QtWidgets.QMessageBox.information(
                    self, "Başarılı", f"{message}\n\n📧 {email}"
                )
                self.accept()
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Hata", message
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hata", f"İşlem başarısız:\n{e}")
