# main.py
import sys
import atexit
from PyQt5 import QtWidgets
from database.connection import init_pool
from database.init_db import initialize_core
from UI.main_window import MainWindow

def initialize_database():
    """Veritabanı bağlantısını başlat ve core seed'leri uygula (departments, default admin)."""
    try:
        init_pool()
        initialize_core()
    except Exception as e:
        sys.exit(1)

def cleanup_on_exit():
    """Program sonlandığında tüm sınav programlarını temizle"""
    try:
        from services.db import execute
        execute("DELETE FROM exam_schedules")
    except Exception as e:
        pass

def main():
    initialize_database()

    atexit.register(cleanup_on_exit)

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
