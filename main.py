import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging
import os
import datetime

log_folder = "logs"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_file = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_path = os.path.join(log_folder, log_file)

logging.basicConfig(filename=log_path, encoding='utf-8', level=logging.DEBUG)
def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()