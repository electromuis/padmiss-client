from src.padmiss.gui import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.attemptShow()
    sys.exit(app.exec())