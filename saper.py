#!/usr/bin/env python

import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    """Provides graphic interface for playing saper"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        #size and title bar
        self.setWindowTitle('Saper')
        self.setWindowIcon(QIcon('./resources/mine.png'))
        self.setGeometry(100,100,700,500)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())