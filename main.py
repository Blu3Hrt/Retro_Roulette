import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging

logging.basicConfig(filename='Main.log', encoding='utf-8', level=logging.DEBUG)
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()