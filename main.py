# main.py
import sys
from PyQt5 import QtWidgets
from database.connection import init_pool
from UI.main_window import MainWindow

def main():
    init_pool()
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
