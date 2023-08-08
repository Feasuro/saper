import random

from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QPushButton, QGridLayout

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
    
    def mousePressEvent(self, event) -> None:
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
    
    def mouseReleaseEvent(self, event) -> None:
        """Emit coordinates of clicked button"""
        if event.button() == Qt.MouseButton.LeftButton :
            self.released.emit(self.property('field'))
            if event.pos() in self.rect():
                self.clicked.emit(self.property('field'))
    
    def mouseMoveEvent(self, event) -> None:
        """Sets button up/down according to mouse position"""
        if Qt.MouseButton.LeftButton in event.buttons() :
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