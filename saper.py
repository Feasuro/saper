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
    middle = Signal(tuple)
    pressed = Signal()
    right = Signal(bool)

    def __init__(self, field: tuple, *args, **kwargs):
        """button is aware of it's position that is emitted when clicked"""
        super().__init__(*args, **kwargs)
        self.setCheckable(True)
        self.setProperty('field', field)
        self.setProperty('flagged', False)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton :
            self.pressed.emit()
        elif event.button() == Qt.MouseButton.RightButton :
            if not self.isChecked() :
                if self.property('flagged'):
                    self.setIcon(QIcon())
                    self.setProperty('flagged', False)
                else:
                    self.setIcon(QIcon('./resources/flag.png'))
                    self.setProperty('flagged', True)
                self.right.emit(self.property('flagged'))
        elif event.button() == Qt.MouseButton.MiddleButton :
            if self.isChecked() :
                self.pressed.emit()   
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton :
            self.click.emit(self.property('field'))
        if event.button() == Qt.MouseButton.MiddleButton :
            if self.isChecked() :
                self.middle.emit(self.property('field'))


class Board(QWidget):
    """Widget that represents the game board"""
    lost = Signal()
    won = Signal()
    
    def __init__(self, x, y, bombcount, size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.bombcount = bombcount
        self.wincounter = x * y
        self.populate(x, y)
        #make layout and fill with covering buttons
        self.buttons = {field : CoverButton(field, click=self.uncover, middle=self.mass_uncover) for field in self.fields}
        layout = QGridLayout()
        layout.setSpacing(0)
        for field in self.buttons:
            self.buttons[field].setFixedSize(QSize(size, size))
            layout.addWidget(self.buttons[field], *field)
        self.setLayout(layout)
    
    def populate(self, x, y) -> None:
        """Fills board with numbers (9 stands for mine)"""
        self.fields = {(i,j): 0 for i in range(x) for j in range(y)}
        self.bombs = random.sample(sorted(self.fields), self.bombcount)
        self.empty = []
        self.numbers = []
        for f in self.bombs:
            self.fields[f] = 9
        for f in self.fields:
            if f in self.bombs:
                continue
            else:
                counter = 0
                for h in self.neighborhood(f):
                    if h in self.bombs:
                        counter += 1
                if counter == 0:
                    self.empty.append(f)
                else:
                    self.numbers.append(f)
                self.fields[f] = counter
    
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
        if self.buttons[field].isChecked() :
            return False
        self.buttons[field].setIcon(QIcon())
        self.buttons[field].setProperty('flagged', False)
        self.buttons[field].setChecked(True)
        #uncover a number
        if field in self.numbers :
            self.buttons[field].setText( str(self.fields[field]) )
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
        if not self.buttons[field].isChecked() :
            return False
        for f in self.neighborhood(field):
            if not self.buttons[f].property('flagged') :
                self.uncover(f)
        return True
    
    def failure(self) -> None:
        """Show bombs, deactivate fields, and send lost signal"""
        for field in self.bombs :
            self.buttons[field].setIcon( QIcon('./resources/mine.png') )
            self.buttons[field].setChecked(True)
        for field in self.fields :
            self.buttons[field].setEnabled(False)
        self.lost.emit()
    
    def victory(self) -> None:
        """Decrease counter, check condition, deactivate bomb-fields and send win signal"""
        self.wincounter -= 1
        if self.wincounter == self.bombcount :
            for field in self.bombs:
                self.buttons[field].setIcon(QIcon('./resources/flag.png'))
                self.buttons[field].setChecked(True)
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
        close.triggered.connect(self.destroy)
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
    
    def new_game(self):
        """Set up for a new game"""
        #prepare window
        self.setFixedSize(self.size * self.cols + 18, self.size * self.rows + 106)
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
        self.playground = Board(self.rows, self.cols, self.bombcount, self.size)
        self.playground.lost.connect(self.handle_failure)
        self.playground.won.connect(self.handle_victory)
        for field in self.playground.fields :
            self.playground.buttons[field].pressed.connect(self.handle_mouse_press)
            self.playground.buttons[field].click.connect(self.handle_mouse_release)
            self.playground.buttons[field].middle.connect(self.handle_mouse_release)
            self.playground.buttons[field].right.connect(self.message)
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
    
    def handle_mouse_release(self):
        """Change icon to smiley, start timer on first move"""
        if not self.timerID :
            self.timerID = self.startTimer(1000)
        self.new.setIcon(self.smiley)
    
    def message(self, flagged):
        """Informs how many bombs are left"""
        if flagged :
            self.bombsleft -= 1
        else :
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
        self.cols = 8
        self.rows = 8
        self.bombcount = 10
        self.new_game()
    
    def advanced_mode(self):
        self.cols = 16
        self.rows = 16
        self.bombcount = 40
        self.new_game()
    
    def expert_mode(self):
        self.cols = 30
        self.rows = 16
        self.bombcount = 99
        self.new_game()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())