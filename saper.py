#!/usr/bin/env python

import sys
import random
import csv
import time

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QIntValidator, QCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, QLabel,
                             QGridLayout, QToolBar, QSizePolicy, QMessageBox,
                             QDialog, QDialogButtonBox, QInputDialog, QLineEdit)

def convert_seconds(seconds: int | str) -> str:
    if type(seconds) == str :
        seconds = int(seconds)
    if seconds < 60 :
        return f'{seconds}s'
    elif seconds < 3600 :
        return f'{seconds // 60}m{seconds % 60}s'
    else :
        return f'{seconds // 3600}h{seconds // 60}m{seconds % 60}s'

class CoverButton(QPushButton):
    """Button that covers field"""
    clicked = Signal(tuple)
    pressed = Signal(tuple)
    released = Signal(tuple)
    right = Signal(tuple)

    def __init__(self, field: tuple, *args, **kwargs) -> None:
        """Button is aware of it's position that is emitted when clicked"""
        super().__init__(*args, **kwargs)
        self.setCheckable(True)
        self.setProperty('field', field)
        self.setProperty('flagged', 0)
        self.setStyleSheet('''
                           * { font-weight: bold; }
                           *[number="1"] { color: blue; }
                           *[number="2"] { color: green; }
                           *[number="3"] { color: red; }
                           *[number="4"] { color: sienna; }
                           *[number="5"] { color: purple; }
                           *[number="6"] { color: goldenrod; }
                           *[number="7"] { color: black; }
                           *[number="8"] { color: magenta; }                           
                           ''')
    
    def mousePressEvent(self, event):
        """Change icon when right-click, send signal when left-click"""
        if event.button() == Qt.MouseButton.RightButton :
            if not self.isChecked() :
                if self.property('flagged'):
                    self.setProperty('flagged', 0)
                else:
                    self.setProperty('flagged', 1)
                self.right.emit(self.property('field'))
        elif event.button() == Qt.MouseButton.LeftButton :
            self.pressed.emit(self.property('field'))
    
    def mouseReleaseEvent(self, event):
        """Emit coordinates of clicked button"""
        if event.button() == Qt.MouseButton.LeftButton :
            self.released.emit(self.property('field'))
            if event.pos() in self.rect():
                self.clicked.emit(self.property('field'))
    
    def mouseMoveEvent(self, event):
        """Sets button up/down according to mouse position"""
        if Qt.MouseButton.LeftButton in app.mouseButtons() :
            if event.pos() in self.rect():
                self.pressed.emit(self.property('field'))
            else:
                self.released.emit(self.property('field'))


class CoverButtonQuestion(CoverButton):
    """Theese modified buttons can be marked with question mark"""
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton :
            if not self.isChecked() :
                match self.property('flagged'):
                    case 0:
                        self.setProperty('flagged', 1)
                    case 1:
                        self.setProperty('flagged', 2)
                    case 2:
                        self.setProperty('flagged', 0)
                self.right.emit(self.property('field'))
        else :
            super().mousePressEvent(event)


class Board(QWidget):
    """Widget that represents the game board"""
    lost = Signal()
    won = Signal()
    
    def __init__(self, rows, cols, bombcount, question=False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #icons
        self.noicon = QIcon()
        self.flag = QIcon('./resources/flag.png')
        self.flag.addFile('./resources/flag.png', mode=QIcon.Mode.Disabled)
        self.mine = QIcon('./resources/mine.png')
        self.mine.addFile('./resources/mine.png', mode=QIcon.Mode.Disabled)
        self.question = QIcon('./resources/question.png')
        self.question.addFile('./resources/question.png', mode=QIcon.Mode.Disabled)
        #counters
        self.bombcount = bombcount
        self.wincounter = rows * cols
        #make gameboard, layout and fill with covering buttons
        self.fields = {(i,j) : CoverButtonQuestion((i,j)) if question else CoverButton((i,j)) for i in range(rows) for j in range(cols)}
        self.populate()
        layout = QGridLayout()
        layout.setSpacing(0)
        for field in self.fields:
            layout.addWidget(self.fields[field], *field)
        self.setLayout(layout)
    
    def populate(self) -> None:
        """Fills board with numbers (9 stands for mine)"""
        self.bombs = random.sample(sorted(self.fields), self.bombcount)
        self.empty = []
        self.numbers = []
        for field in self.bombs:
            self.fields[field].setProperty('number', 9)
        for field in self.fields:
            if field in self.bombs:
                continue
            else:
                counter = 0
                for f in self.neighborhood(field):
                    if f in self.bombs:
                        counter += 1
                if counter == 0:
                    self.empty.append(field)
                else:
                    self.numbers.append(field)
                self.fields[field].setProperty('number', counter)
    
    def neighborhood(self, field: tuple) -> list:
        """Returns neighbor fields to the given one"""
        neighbors = []
        for i in range(field[0]-1, field[0]+2):
            for j in range(field[1]-1, field[1]+2):
                if (i,j) == field:
                    continue
                elif (i,j) in self.fields:
                    neighbors.append((i,j))
        return neighbors
    
    def fields_to_uncover(self, field: tuple) -> list:
        """Return list of un-checked and un-flagged fields"""
        result = []
        if self.fields[field].isChecked():
            for f in self.neighborhood(field):
                if not self.fields[f].isChecked() and not self.fields[f].property('flagged'):
                    result.append(f)
        else:
            result.append(field)
        return result
    
    def set_icon(self, field) -> None:
        """Set button's icon according to property"""
        match self.fields[field].property('flagged'):
            case 0:
                self.fields[field].setIcon(self.noicon)
            case 1:
                self.fields[field].setIcon(self.flag)
            case 2:
                self.fields[field].setIcon(self.question)
    
    def uncover(self, field) -> bool:
        """Method reveals content of the field(s)"""
        if self.fields[field].isChecked() :
            return False
        self.fields[field].setIcon(self.noicon)
        self.fields[field].setProperty('flagged', 0)
        self.fields[field].setChecked(True)
        #uncover a number
        if field in self.numbers :
            self.fields[field].setText( str(self.fields[field].property('number')) )
        #loose when you click a bomb
        elif field in self.bombs :
            self.failure()
            return True
        #field in self.empty - recurrent uncovering
        else :
            for f in self.neighborhood(field):
                self.uncover(f)
        #check victory condition
        self.victory()
        return True
    
    def mass_uncover(self, field) -> None:
        """Uncovers all non-flagged adjacent fields"""
        for f in self.fields_to_uncover(field):
            self.uncover(f)
    
    def mass_uncover_safe(self, field) -> None:
        """Uncovers non-flagged adjacent fields when adjacent bombs are flagged"""
        self.uncover(field)
        counter = 0
        for f in self.neighborhood(field) :
            if self.fields[f].property('flagged') :
                counter += 1
        if counter == self.fields[field].property('number') :
            for f in self.fields_to_uncover(field) :
                self.uncover(f)
    
    def failure(self) -> None:
        """Show bombs, deactivate fields, and send lost signal"""
        for field in self.bombs :
            self.fields[field].setIcon(self.mine)
            self.fields[field].setChecked(True)
        for field in self.fields :
            if not self.fields[field].isChecked():
                self.fields[field].setEnabled(False)
        self.lost.emit()
    
    def victory(self) -> None:
        """Decrease counter, check condition, deactivate bomb-fields and send win signal"""
        self.wincounter -= 1
        if self.wincounter == self.bombcount :
            for field in self.bombs:
                self.fields[field].setIcon(self.flag)
            for field in self.fields :
                self.fields[field].setEnabled(False)
            self.won.emit()


class MainWindow(QMainWindow):
    """Provides window interface for playing saper"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        #title, icon, timer and defaults
        self.setWindowTitle('Saper')
        self.setWindowIcon(QIcon('./resources/mine.png'))
        self.timerID = 0
        self.size = 20
        self.setProperty('question', False)
        self.setProperty('massuncover', 1)
        #make the window and game
        self.ui_setup()
        self.beginner_mode()
        self.beginner.setChecked(True)
        self.show()
    
    def ui_setup(self) -> None:
        """Arranges all window elements."""
        #icons
        self.smiley = QIcon('./resources/smiley.png')
        self.sad = QIcon('./resources/sad.png')
        self.wow = QIcon('./resources/wow.png')
        self.glasses = QIcon('./resources/glasses.png')
        self.close = QIcon('./resources/exit.png')
        #actions
        self.new = QAction(self.smiley, '&New', self)
        self.new.setShortcut('Ctrl+N')
        self.new.triggered.connect(self.new_game)
        self.beginner = QAction('&Beginner', self)
        self.beginner.setCheckable(True)
        self.beginner.setShortcut('Ctrl+B')
        self.beginner.triggered.connect(self.beginner_mode)
        self.advanced = QAction('&Advanced', self)
        self.advanced.setCheckable(True)
        self.advanced.setShortcut('Ctrl+A')
        self.advanced.triggered.connect(self.advanced_mode)
        self.expert = QAction('&Expert', self)
        self.expert.setCheckable(True)
        self.expert.setShortcut('Ctrl+E')
        self.expert.triggered.connect(self.expert_mode)
        self.custom = QAction('&Custom', self)
        self.custom.setCheckable(True)
        self.custom.setShortcut('Ctrl+C')
        self.custom.triggered.connect(self.custom_mode)
        close = QAction(self.close, '&Exit', self)
        close.setShortcut('Alt+F4')
        close.triggered.connect(app.quit)
        larger = QAction('&Larger', self)
        larger.setShortcut('Ctrl++')
        larger.triggered.connect(self.enlarge)
        smaller = QAction('&Smaller', self)
        smaller.setShortcut('Ctrl+-')
        smaller.triggered.connect(self.zoomout)
        question = QAction('&Question marks', self)
        question.setShortcut('Ctrl+Q')
        question.setCheckable(True)
        question.triggered.connect(self.question_marks)
        self.massuncover = QAction('&Uncovering neighbors', self)
        self.massuncover.setCheckable(True)
        self.massuncover.setChecked(True)
        self.massuncover.setShortcut('Ctrl+U')
        self.massuncover.triggered.connect(self.mass_uncover)
        self.massuncoversafe = QAction('&Safe neighbors uncovering', self)
        self.massuncoversafe.setCheckable(True)
        self.massuncoversafe.setShortcut('Ctrl+S')
        self.massuncoversafe.triggered.connect(self.mass_uncover_safe)
        records = QAction('&Records', self)
        records.setShortcut('Ctrl+R')
        records.triggered.connect(self.show_records)
        #toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        left_spacer = QWidget()
        right_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(left_spacer)
        toolbar.addAction(self.new)
        toolbar.addWidget(right_spacer)
        self.addToolBar(toolbar)
        #statusbar
        self.statusbar = self.statusBar()
        self.clock = QLabel('Time: 0s')
        self.statusbar.addPermanentWidget(self.clock)
        #menubar
        menu = self.menuBar()
        game = menu.addMenu('&Game')
        game.addAction(self.new)
        game.addAction(records)
        game.addSeparator()
        game.addAction(self.beginner)
        game.addAction(self.advanced)
        game.addAction(self.expert)
        game.addAction(self.custom)
        game.addSeparator()
        game.addAction(close)
        options = menu.addMenu('&Options')
        options.addAction(larger)
        options.addAction(smaller)
        options.addSeparator()
        options.addAction(question)
        options.addSeparator()
        options.addAction(self.massuncover)
        options.addAction(self.massuncoversafe)
    
    def new_game(self) -> None:
        """Set up for a new game"""
        self.new.setIcon(self.smiley)
        #be sure that timer is reset and shows 0
        if self.timerID :
            self.killTimer(self.timerID)
            self.timerID = 0
        self.seconds = -1
        self.timerEvent(None)
        #reset bomb counter
        self.bombsleft = self.bombcount
        self.statusbar.showMessage(f'{self.bombsleft} bombs left')
        #game widget
        self.playground = Board(self.rows, self.cols, self.bombcount, question=self.property('question'))
        self.playground.lost.connect(self.handle_failure)
        self.playground.won.connect(self.handle_victory)
        for field in self.playground.fields :
            self.playground.fields[field].pressed.connect(self.handle_mouse_press)
            self.playground.fields[field].released.connect(self.handle_mouse_release)
            self.playground.fields[field].clicked.connect(self.handle_mouse_click)
            self.playground.fields[field].right.connect(self.handle_right_click)
        self.setCentralWidget(self.playground)
    
    def handle_failure(self) -> None:
        """Communicate failure to the player"""
        self.killTimer(self.timerID)
        self.timerID = 0
        self.statusbar.showMessage('You lost!')
        self.new.setIcon(self.sad)

    def handle_victory(self) -> None:
        """Communicate victory to the player, and check record"""
        self.killTimer(self.timerID)
        self.timerID = 0
        self.statusbar.showMessage('Victory!')
        self.new.setIcon(self.glasses)
        #saving best time
        fieldnames = ['mode', 'date', 'name', 'time']
        ok = False
        try:
            with open('./records.csv', 'r+', newline='', encoding='utf-8') as records :
                reader = csv.DictReader(records, dialect='unix')
                for row in reader :
                    if row['mode'] == self.property('mode') and int(row['time']) < self.seconds :
                        break
                else :
                    name, ok = QInputDialog.getText(self, 'New record!', 'Your name:')
                    if ok:
                        writer = csv.DictWriter(records, fieldnames=fieldnames, dialect='unix')
                        writer.writerow({'mode': self.property('mode'), 'date': time.strftime('%x'), 'name': name, 'time': self.seconds})
        except FileNotFoundError:
            name, ok = QInputDialog.getText(self, 'New record!', 'Your name:')
            if ok:
                with open('./records.csv', 'w', newline='', encoding='utf-8') as records :
                    writer = csv.DictWriter(records, fieldnames=fieldnames, dialect='unix')
                    writer.writeheader()
                    writer.writerow({'mode': self.property('mode'), 'date': time.strftime('%x'), 'name': name, 'time': self.seconds})
        finally:
            if ok : self.show_records()
    
    def handle_mouse_press(self, field) -> None:
        """Change icon to wow and press buttons"""
        self.new.setIcon(self.wow)
        for f in self.playground.fields_to_uncover(field):
            self.playground.fields[f].setDown(True)
    
    def handle_mouse_release(self, field) -> None:
        """Change icon back to smiley and un-press buttons"""
        self.new.setIcon(self.smiley)
        for f in self.playground.fields_to_uncover(field):
            self.playground.fields[f].setDown(False)
    
    def handle_mouse_click(self, field) -> None:
        """Start timer on first move and uncover fields"""
        if not self.timerID :
            self.timerID = self.startTimer(1000)
        match self.property('massuncover'):
            case 0:
                self.playground.uncover(field)
            case 1:
                self.playground.mass_uncover(field)
            case 2:
                self.playground.mass_uncover_safe(field)
    
    def handle_right_click(self, field) -> None:
        """Changes icon and informs how many bombs are left"""
        self.playground.set_icon(field)
        flagged = self.playground.fields[field].property('flagged')
        if flagged == 1 :
            self.bombsleft -= 1
        elif ( self.property('question') and flagged == 2 ) or ( not self.property('question') and flagged == 0 ):
            self.bombsleft += 1
        self.statusbar.showMessage(f'{self.bombsleft} bombs left')
    
    def timerEvent(self, event) -> None:
        """Counts elapsed time of a game"""
        self.seconds += 1
        self.clock.setText('Time: ' + convert_seconds(self.seconds))
    
    def beginner_mode(self) -> None:
        """Beginner game setup"""
        self.advanced.setChecked(False)
        self.expert.setChecked(False)
        self.custom.setChecked(False)
        self.rows = 8
        self.cols = 8
        self.bombcount = 10
        self.setProperty('mode', 'b')
        self.new_game()
    
    def advanced_mode(self) -> None:
        """Advanced game setup"""
        self.beginner.setChecked(False)
        self.expert.setChecked(False)
        self.custom.setChecked(False)
        self.rows = 16
        self.cols = 16
        self.bombcount = 40
        self.setProperty('mode', 'a')
        self.new_game()
    
    def expert_mode(self) -> None:
        """Expert game setup"""
        self.beginner.setChecked(False)
        self.advanced.setChecked(False)
        self.custom.setChecked(False)
        self.rows = 16
        self.cols = 30
        self.bombcount = 99
        self.setProperty('mode', 'e')
        self.new_game()
    
    def custom_mode(self) -> None:
        """Custom game setup"""
        dialog = CustomSetupDialog(self)
        if dialog.exec() :
            self.beginner.setChecked(False)
            self.advanced.setChecked(False)
            self.expert.setChecked(False)
            self.setProperty('mode', 'c')
            self.new_game()
        else :
            self.custom.setChecked(False)
    
    def enlarge(self) -> None:
        """Make fields bigger"""
        self.size += 2
        self.update()
    
    def zoomout(self) -> None:
        """Make fields smaller"""
        self.size -= 2
        self.update()
    
    def paintEvent(self, event) -> None:
        """Set fixed sizes of self, fields, fonts and icons"""
        font = self.playground.font()
        font.setPixelSize( int(self.size * 0.7) )
        for field in self.playground.fields:
            self.playground.fields[field].setFixedSize(QSize(self.size, self.size))
            self.playground.fields[field].setIconSize(QSize( int(self.size * 0.8), int(self.size * 0.8) ))
            self.playground.fields[field].setFont(font)
        self.setFixedSize(self.size * self.cols + 18, self.size * self.rows + 106)
        super().paintEvent(event)
    
    def question_marks(self) -> None:
        """Toggle marking fields with question mark"""
        self.setProperty('question', not self.property('question'))
        self.new_game()
    
    def mass_uncover(self) -> None:
        """Toggle option for uncovering neighbors"""
        self.massuncoversafe.setChecked(False)
        if self.property('massuncover') :
            self.setProperty('massuncover', 0)
        if not self.property('massuncover') :
            self.setProperty('massuncover', 1)
        self.new_game()
    
    def mass_uncover_safe(self) -> None:
        """Toggle option for uncovering neighbors - safe version"""
        self.massuncover.setChecked(False)
        if self.property('massuncover') :
            self.setProperty('massuncover', 0)
        if not self.property('massuncover') :
            self.setProperty('massuncover', 2)
        self.new_game()
    
    def show_records(self) -> None:
        """Display window with saved records"""
        try:
            RecordsWindow(self).exec()
        except FileNotFoundError:
            QMessageBox.information(self, 'Not found', 'No records have been saved yet.')


class CustomSetupDialog(QDialog):
    """Dialog window to setup custom rows, columns and bombs count"""
    
    def __init__(self, parent=None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.setWindowTitle('Setup custom mode')
        #standard ok/cancel buttons
        btns = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        buttons = QDialogButtonBox(btns)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.close)
        #input fields with labels
        validator = QIntValidator(0, 5000, self)
        rlabel = QLabel('Rows:')
        rlabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.rows = QLineEdit(str(parent.rows), maxLength=2)
        self.rows.setMaximumWidth(50)
        self.rows.setValidator(validator)
        clabel = QLabel('Columns:')
        clabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cols = QLineEdit(str(parent.cols), maxLength=2)
        self.cols.setMaximumWidth(50)
        self.cols.setValidator(validator)
        blabel = QLabel('Number of bombs:')
        blabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bombcount = QLineEdit(str(parent.bombcount), maxLength=4)
        self.bombcount.setMaximumWidth(50)
        self.bombcount.setValidator(validator)
        #layout
        layout = QGridLayout()
        layout.addWidget(rlabel, 0, 0)
        layout.addWidget(self.rows, 0, 1)
        layout.addWidget(clabel, 1, 0)
        layout.addWidget(self.cols, 1, 1)
        layout.addWidget(blabel, 2, 0)
        layout.addWidget(self.bombcount, 2, 1)
        layout.addWidget(buttons, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
    
    def accept(self) -> None:
        """First check if there's no more bombs than fields, then apply"""
        if int(self.bombcount.text()) < int(self.rows.text()) * int(self.cols.text()):
            self.parent.rows = int(self.rows.text())
            self.parent.cols = int(self.cols.text())
            self.parent.bombcount = int(self.bombcount.text())
            self.done(1)
        else :
            QMessageBox.critical(self, 'Invalid', "Too many bombs for given board dimensions")


class RecordsWindow(QDialog):
    """Dialog window that displays records"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #title and 'ok' button
        self.setWindowTitle('Best times')
        button = QDialogButtonBox( QDialogButtonBox.StandardButton.Ok )
        button.accepted.connect(self.close)
        #layout
        layout = QGridLayout()
        layout.addWidget(QLabel('Beginner'), 0, 0, 1, 3)
        layout.addWidget(QLabel('Advanced'), 0, 3, 1, 3)
        layout.addWidget(QLabel('Expert'), 0, 6, 1, 3)
        for i in range(0, 7, 3):
            layout.addWidget(QLabel('Date'), 1, i)
            layout.addWidget(QLabel('Name'), 1, i+1)
            layout.addWidget(QLabel('Time'), 1, i+2)
        #get records from file
        with open('./records.csv', 'r', newline='', encoding='utf-8') as records :
            reader = csv.DictReader(records, dialect='unix')
            b, a, e = 2, 2, 2
            for row in reader :
                match row['mode']:
                    case 'b':
                        layout.addWidget(QLabel(row['date']), b, 0)
                        layout.addWidget(QLabel(row['name']), b, 1)
                        layout.addWidget(QLabel(convert_seconds(row['time'])), b, 2)
                        b += 1
                    case 'a':
                        layout.addWidget(QLabel(row['date']), a, 3)
                        layout.addWidget(QLabel(row['name']), a, 4)
                        layout.addWidget(QLabel(convert_seconds(row['time'])), a, 5)
                        a += 1
                    case 'e':
                        layout.addWidget(QLabel(row['date']), e, 6)
                        layout.addWidget(QLabel(row['name']), e, 7)
                        layout.addWidget(QLabel(convert_seconds(row['time'])), e, 8)
                        e += 1
        #add button and set layout
        layout.addWidget(button, max(b, a, e), 0, 1, 9, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())