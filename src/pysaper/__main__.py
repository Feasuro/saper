#!/usr/bin/env python
"""Game entry point module"""
import sys

from PyQt6.QtWidgets import QApplication

from window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
