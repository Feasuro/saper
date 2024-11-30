#!/usr/bin/env python
"""Module for handling records in csv database"""

import csv
import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QLabel,
                             QGridLayout, QMessageBox, QInputDialog)

RECORDS_PATH = './records.csv'
FIELDNAMES = ['mode', 'date', 'name', 'time']

def convert_seconds(seconds: int | str) -> str:
    """Present seconds in human readable format"""
    if isinstance(seconds, str) :
        seconds = int(seconds)
    if seconds < 60 :
        return f'{seconds}s'
    elif seconds < 3600 :
        return f'{seconds // 60}m{seconds % 60}s'
    else :
        return f'{seconds // 3600}h{seconds // 60}m{seconds % 60}s'

class Model:
    """Holds best times as sorted lists, synchronizes with csv file
    provides interface to view data in tabular form"""

    def __new__(cls, *args, **kwargs):
        """Creates a singleton object, if it is not created,
        or else returns the previous singleton object"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(Model, cls).__new__(cls)
        return cls.instance

    def __init__(self, path: str=RECORDS_PATH) -> None:
        """Initialize data and sort it"""
        self.path = path
        self.data = {'b': [], 'a': [], 'e': []}
        try:
            self.load()
        except FileNotFoundError:
            self.no_file = True
            self.header = FIELDNAMES
        else:
            self.no_file = False
            self.sort()

    def load(self) -> None:
        """Reads records from file"""
        with open(self.path, 'r', newline='', encoding='utf-8') as records :
            reader = csv.DictReader(records, dialect='unix')
            self.header = reader.fieldnames
            for row in reader:
                row['time'] = int(row['time'])
                self.data[row.pop('mode')].append(row)

    def sort(self) -> None:
        """Sort data by best times"""
        for value in self.data.values():
            value.sort(key=lambda item: item['time'])

    def check_record(self, mode: str, seconds: int) -> bool:
        """Check if given time is the best in given mode"""
        for item in self.data[mode]:
            if item['time'] < seconds:
                return False
        return True

    def add(self, mode: str, name: str, seconds: int) -> None:
        """Add record, sort and synchronize with file"""
        self.data[mode].append({'date': time.strftime('%x'), 'name': name, 'time': seconds})
        self.sort()
        with open(self.path, 'a', newline='', encoding='utf-8') as records :
            writer = csv.DictWriter(records, fieldnames=self.header, dialect='unix')
            if self.no_file:
                writer.writeheader()
            writer.writerow({'mode': mode, 'date': time.strftime('%x'), 'name': name, 'time': seconds})

    def __len__(self) -> int:
        """Return how many rows are present"""
        return max(len(value) for value in self.data.values())

    def item(self, row: int, col: int) -> str:
        """Returns item at given index for presenting data in tabular form"""
        if col < 0: raise IndexError
        elif col < 3: mode = 'b'
        elif col < 6: mode = 'a'
        elif col < 9: mode = 'e'
        else: raise IndexError
        wrapper = lambda x: x
        match col % 3:
            case 0: field = 'date'
            case 1: field = 'name'
            case 2:
                field = 'time'
                wrapper = convert_seconds
        try:
            return wrapper(self.data[mode][row][field])
        except IndexError:
            return ''

class View(QDialog):
    """Dialog window that displays records"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        #title and 'ok' button
        self.setWindowTitle('Best times')
        button = QDialogButtonBox( QDialogButtonBox.StandardButton.Ok )
        button.accepted.connect(self.close)
        model = Model(RECORDS_PATH)
        #layout
        layout = QGridLayout()
        layout.setHorizontalSpacing(20)
        layout.addWidget(QLabel('Beginner'), 0, 0, 1, 3)
        layout.addWidget(QLabel('Advanced'), 0, 3, 1, 3)
        layout.addWidget(QLabel('Expert'), 0, 6, 1, 3)
        for i in range(0, 9):
            layout.addWidget(QLabel(model.header[1:][i % 3].capitalize()), 1, i)
        for row in range(len(model)):
            for col in range(9):
                layout.addWidget(QLabel(model.item(row, col)), row + 2, col)
        layout.addWidget(button, len(model) + 2, 0, 1, 9, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

def show(parent=None) -> None:
    """Shows dialog window with records
    Args:
        parent (MainWindow, optional): Defaults to None.
    """
    model = Model(RECORDS_PATH)
    if model.no_file :
        QMessageBox.information(parent, 'Not found', 'No records have been saved yet.')
    else:
        View(parent).show()

def end_game(parent) -> None:
    """Check if finished game's time should be recorded
    Args:
        parent (MainWindow):
    """
    model = Model(RECORDS_PATH)
    mode = parent.property('mode')
    seconds = parent.seconds
    ok = False
    if model.check_record(mode, seconds):
        name, ok = QInputDialog.getText(parent, 'New record!', 'Your name:')
    if ok:
        model.add(mode, name, seconds)
        show(parent)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    show()
