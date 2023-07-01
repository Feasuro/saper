#!/usr/bin/env python

import sys
import random
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtCore import pyqtSignal as Signal
#from PyQt6.QtCore import pyqtSlot as Slot
from PyQt6.QtGui import QIcon, QPixmap, QAction, QCursor
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout, QLabel, QToolBar

class CoverButton(QPushButton):
    """ Button that covers field """
    click = Signal(tuple)
    pressed = Signal()

    def __init__(self, field: tuple, *args, **kwargs):
        """ button is aware of it's position that is emitted when clicked """
        super().__init__(*args, **kwargs)
        self.setCheckable(True)
        self.setProperty('active', True)
        self.setProperty('field', field)
        self.setProperty('flagged', False)
    
    def mousePressEvent(self, event):
        if self.property('active') :
            if event.button() == Qt.MouseButton.LeftButton :
                self.pressed.emit()
                print('debug: press l')
            elif event.button() == Qt.MouseButton.RightButton :
                if self.property('flagged'):
                    self.setIcon(QIcon())
                else:
                    self.setIcon(QIcon('./resources/flag.png'))
                self.setProperty('flagged', True)
    
    def mouseReleaseEvent(self, event):
        if self.property('active') :
            if event.button() == Qt.MouseButton.LeftButton :
                self.click.emit(self.property('field'))
                print('debug: click l')
                #print('debug 1', QCursor.pos(), self.hitButton( QCursor.pos() ), self.pos() )
                if self.hitButton( QCursor.pos() ) :
                    print('debug 2')


class Board(QWidget):
    """ Widget that represents the game board """
    lost = Signal()
    won = Signal()
    
    def __init__(self, x, y, bombcount, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.bombcount = bombcount
        self.wincounter = x * y
        #labels that store field contents
        self.populate(x, y)
        self.buttons = {field : CoverButton(field, click=self.uncover) for field in self.fields}
        #make layout and fill with covering buttons
        self.setFixedSize(18 * x, 18 * y)
        layout = QGridLayout()
        layout.setSpacing(0)
        #self.layout.setContentsMargins(0,0,0,0)
        for field in self.buttons:
            self.buttons[field].setFixedSize(QSize(18, 18))
            layout.addWidget(self.buttons[field], *field)
        self.setLayout(layout)
    
    def populate(self, x, y) -> None:
        """ Fills board with numbers (9 stands for mine) """
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
        """ Returns neighbor fields to the given one """
        neighbors = []
        for i in range(field[0]-1, field[0]+2):
            for j in range(field[1]-1, field[1]+2):
                if (i,j) == field:
                    continue
                elif (i,j) in self.fields:
                    neighbors.append((i,j))
        return neighbors
    
    def uncover(self, field) -> bool:
        """ Method reveals content of the field(s) """
        if self.buttons[field].isChecked() : #self.buttons[field].isDown() or
            return False
        self.buttons[field].setChecked(True)
        #uncover a number
        if field in self.numbers :
            self.buttons[field].setText( str(self.fields[field]) )
        #loose when you click a bomb
        elif field in self.bombs :
            self.buttons[field].setIcon( QIcon('./resources/mine.png') )
            self.failure()
        #field in self.empty - recurrent uncovering
        else :
            for f in self.neighborhood(field):
                self.uncover(f)
        #check victory condition
        self.victory()
        return True
    
    def failure(self) -> None:
        """ Show bombs, deactivate fields, and send lost signal """
        for field in self.bombs :
                self.uncover(field)
        for field in self.fields :
            self.buttons[field].setProperty('active', False)
        self.lost.emit()
    
    def victory(self) -> None:
        """ Decrease counter, check condition, deactivate bomb-fields and send win signal """
        self.wincounter -= 1
        if self.wincounter == self.bombcount :
            for field in self.bombs:
                self.buttons[field].setIcon(QIcon('./resources/flag.png'))
                self.buttons[field].setChecked(True)
            self.won.emit()


class MainWindow(QMainWindow):
    """ Provides window interface for playing saper """
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        #size and title bar
        self.setWindowTitle('Saper')
        self.setWindowIcon(QIcon('./resources/mine.png'))
        
        self.ui_setup()
        self.new_game()
    
    def ui_setup(self):
        """ Arranges all window elements. """
        #icons for central button
        self.smiley = QIcon('./resources/smiley.png')
        self.sad = QIcon('./resources/sad.png')
        self.wow = QIcon('./resources/wow.png')
        #action of central button
        self.new = QAction(self.smiley, '&New' , self)
        self.new.triggered.connect(self.new_game)
        #toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        toolbar.addAction(self.new)
        self.addToolBar(toolbar)
        #statusbar
        self.statusbar = self.statusBar()
        self.statuslabel = QLabel('Bombs left')
        self.timer = QLabel('Time:')
        self.statusbar.addPermanentWidget(self.statuslabel)
        self.statusbar.addPermanentWidget(self.timer)
    
    def new_game(self):
        """ Set up for a new game """
        self.new.setIcon(self.smiley)
        self.statuslabel.setText('Bombs left')
        self.playground = Board(10, 10, 10)
        self.playground.lost.connect(self.handle_failure)
        self.playground.won.connect(self.handle_victory)
        self.setCentralWidget(self.playground)
    
    def handle_failure(self):
        """ Communicate failure to the player """
        self.statuslabel.setText('You lost!')
        self.new.setIcon(self.sad)

    def handle_victory(self):
        """ Communicate victory to the player """
        self.statuslabel.setText('Victory!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())