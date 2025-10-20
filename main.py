# main.py
import sys
from PyQt5 import QtWidgets

from database.connection import init_pool
from database.init_db import initialize_core
from UI.main_window import MainWindow

def initialize_database():
    """Veritabanı bağlantısını başlat ve core seed'leri uygula (departments, default admin)."""
    try:
        print("Veritabani baglantisi baslatiliyor...")
        init_pool()
        print("Baglanti havuzu olusturuldu!")

        print("Cekirdek veriler (departments, admin, exam tables) kontrol ediliyor...")
        initialize_core()
        print("Cekirdek veriler hazir.")
    except Exception as e:
        print(f"Veritabani baslatma hatasi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    # 1) DB'yi bir kez başlat
    initialize_database()

    # 2) GUI başlat
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # 3) Event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
