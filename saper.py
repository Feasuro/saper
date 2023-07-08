#!/usr/bin/env python

import sys
import random
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QCursor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QPushButton, QGridLayout, QLabel,
                             QToolBar, QSizePolicy)

class CoverButton(QPushButton):
    """Button that covers field"""
    click = Signal(tuple)
    right = Signal(int)

    def __init__(self, field: tuple, *args, **kwargs):
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
        if event.button() == Qt.MouseButton.RightButton :
            if not self.isChecked() :
                if self.property('flagged'):
                    self.setIcon(QIcon())
                    self.setProperty('flagged', 0)
                else:
                    self.setIcon(QIcon('./resources/flag.png'))
                    self.setProperty('flagged', 1)
                self.right.emit(self.property('flagged'))
        elif event.button() == Qt.MouseButton.LeftButton :
            self.pressed.emit()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton :
            self.click.emit(self.property('field'))


class CoverButtonQuestion(CoverButton):
    """Theese modified buttons can be marked with question mark"""
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton :
            if not self.isChecked() :
                match self.property('flagged'):
                    case 0:
                        self.setIcon(QIcon('./resources/flag.png'))
                        self.setProperty('flagged', 1)
                    case 1:
                        self.setIcon(QIcon('./resources/question.png'))
                        self.setProperty('flagged', 2)
                    case 2:
                        self.setIcon(QIcon())
                        self.setProperty('flagged', 0)
                self.right.emit(self.property('flagged'))
        else :
            super().mousePressEvent(event)


class Board(QWidget):
    """Widget that represents the game board"""
    lost = Signal()
    won = Signal()
    
    def __init__(self, x, y, bombcount, question=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.bombcount = bombcount
        self.wincounter = x * y
        #make gameboard, layout and fill with covering buttons
        self.fields = {(i,j) : CoverButtonQuestion((i,j)) if question else CoverButton((i,j)) for i in range(x) for j in range(y)}
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
    
    def uncover(self, field) -> bool:
        """Method reveals content of the field(s)"""
        if self.fields[field].isChecked() :
            return False
        self.fields[field].setIcon(QIcon())
        self.fields[field].setProperty('flagged', 0)
        self.fields[field].setChecked(True)
        #uncover a number
        if field in self.numbers :
            self.fields[field].setText( str(self.fields[field].property('number')) )
        #loose when you click a bomb
        elif field in self.bombs :
            self.failure()
        #field in self.empty - recurrent uncovering
        else :
            for f in self.neighborhood(field):
                self.uncover(f)
        #check victory condition
        self.victory()
        return True
    
    def mass_uncover(self, field) -> bool:
        """Uncovers all non-flagged adjacent fields"""
        if not self.fields[field].isChecked() :
            return False
        for f in self.neighborhood(field):
            if not self.fields[f].property('flagged') :
                self.uncover(f)
        return True
    
    def failure(self) -> None:
        """Show bombs, deactivate fields, and send lost signal"""
        for field in self.bombs :
            self.fields[field].setIcon( QIcon('./resources/mine.png') )
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
                self.fields[field].setIcon(QIcon('./resources/flag.png'))
                self.fields[field].setChecked(True)
            self.won.emit()


class MainWindow(QMainWindow):
    """Provides window interface for playing saper"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        #title, icon and timer
        self.setWindowTitle('Saper')
        self.setWindowIcon(QIcon('./resources/mine.png'))
        self.timerID = 0
        self.size = 20
        self.setProperty('question', False)
        
        self.ui_setup()
        self.beginner_mode()
        self.show()
    
    def ui_setup(self):
        """Arranges all window elements."""
        #icons
        self.smiley = QIcon('./resources/smiley.png')
        self.sad = QIcon('./resources/sad.png')
        self.wow = QIcon('./resources/wow.png')
        self.glasses = QIcon('./resources/glasses.png')
        self.close = QIcon('./resources/exit.png')
        #actions
        self.new = QAction(self.smiley, '&New' , self)
        self.new.setShortcut('Ctrl+N')
        self.new.triggered.connect(self.new_game)
        beginner = QAction('&Beginner', self)
        beginner.setShortcut('Ctrl+B')
        beginner.triggered.connect(self.beginner_mode)
        advanced = QAction('&Advanced', self)
        advanced.setShortcut('Ctrl+A')
        advanced.triggered.connect(self.advanced_mode)
        expert = QAction('&Expert', self)
        expert.setShortcut('Ctrl+E')
        expert.triggered.connect(self.expert_mode)
        custom = QAction('&Custom', self)
        custom.setShortcut('Ctrl+C')
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
        game.addSeparator()
        game.addAction(beginner)
        game.addAction(advanced)
        game.addAction(expert)
        game.addAction(custom)
        game.addSeparator()
        game.addAction(close)
        options = menu.addMenu('&Options')
        options.addAction(larger)
        options.addAction(smaller)
        options.addSeparator()
        options.addAction(question)
    
    def new_game(self):
        """Set up for a new game"""
        self.new.setIcon(self.smiley)
        #be sure that timer is reset and shows 0
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
            self.playground.fields[field].click.connect(self.handle_mouse_release)
            self.playground.fields[field].right.connect(self.message)
        self.setCentralWidget(self.playground)
    
    def handle_failure(self):
        """Communicate failure to the player"""
        self.killTimer(self.timerID)
        self.statusbar.showMessage('You lost!')
        self.new.setIcon(self.sad)

    def handle_victory(self):
        """Communicate victory to the player"""
        self.killTimer(self.timerID)
        self.statusbar.showMessage('Victory!')
        self.new.setIcon(self.glasses)
    
    def handle_mouse_press(self):
        """Change icon to wow"""
        self.new.setIcon(self.wow)
    
    def handle_mouse_release(self, field):
        """Change icon to smiley, start timer on first move"""
        if not self.timerID :
            self.timerID = self.startTimer(1000)
        self.new.setIcon(self.smiley)
        if self.playground.fields[field].isChecked() :
            self.playground.mass_uncover(field)
        else :
            self.playground.uncover(field)
    
    def message(self, flagged):
        """Informs how many bombs are left"""
        if flagged == 1 :
            self.bombsleft -= 1
        elif ( self.property('question') and flagged == 2 ) or ( not self.property('question') and flagged == 0 ):
            self.bombsleft += 1
        self.statusbar.showMessage(f'{self.bombsleft} bombs left')
    
    def timerEvent(self, event):
        """Counts elapsed time of a game"""
        self.seconds += 1
        if self.seconds < 60 :
            self.clock.setText(f'Time: {self.seconds}s')
        elif self.seconds < 3600 :
            self.clock.setText(f'Time: {self.seconds // 60}m{self.seconds % 60}s')
        else :
            self.clock.setText(f'Time: {self.seconds // 3600}h{self.seconds // 60}m{self.seconds % 60}s')
    
    def beginner_mode(self):
        """Beginner game setup"""
        self.cols = 8
        self.rows = 8
        self.bombcount = 10
        self.new_game()
    
    def advanced_mode(self):
        """Advanced game setup"""
        self.cols = 16
        self.rows = 16
        self.bombcount = 40
        self.new_game()
    
    def expert_mode(self):
        """Expert game setup"""
        self.cols = 30
        self.rows = 16
        self.bombcount = 99
        self.new_game()
    
    def enlarge(self):
        """Make fields bigger"""
        self.size += 2
        self.update()
    
    def zoomout(self):
        """Make fields smaller"""
        self.size -= 2
        self.update()
    
    def paintEvent(self, event):
        """Set fixed size of fields and self"""
        font = self.playground.font()
        font.setPixelSize( int(self.size * 0.7) )
        for field in self.playground.fields:
            self.playground.fields[field].setFixedSize(QSize(self.size, self.size))
            self.playground.fields[field].setIconSize(QSize( int(self.size * 0.8), int(self.size * 0.8) ))
            self.playground.fields[field].setFont(font)
        self.setFixedSize(self.size * self.cols + 18, self.size * self.rows + 106)
        super().paintEvent(event)
    
    def question_marks(self):
        self.setProperty('question', not self.property('question'))
        self.new_game()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())