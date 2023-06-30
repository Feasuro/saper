#!/usr/bin/env python

import sys
import random
from PyQt6.QtCore import QSize
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtCore import pyqtSlot as Slot
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout, QLabel, QToolBar

class Button(QPushButton):
    """ Button that covers field """
    click = Signal(tuple)

    def __init__(self, field, *args, **kwargs):
        """ button is aware of it's position that is emitted when clicked """
        super().__init__(*args, **kwargs)
        self.setProperty('field', field)
        self.clicked.connect(self.on_click)

    @Slot()
    def on_click(self):
        self.click.emit(self.property('field'))


class Board(QWidget):
    """ Widget that represents the game board """
    lost = Signal()
    won = Signal()
    
    def __init__(self, x, y, bombcount, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.bombcount = bombcount
        self.wincounter = 0
        #labels that store field contents
        self.field = {(i,j): QLabel() for i in range(x) for j in range(y)}
        for f in self.field:
            self.field[f].setProperty('covered', True)
            self.wincounter += 1
        self.populate()
        #make layout and fill with covering buttons
        self.setFixedSize(18 * x, 18 * y)
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        for f in self.field:
            self.field[f].setFixedSize(QSize(18, 18))
            self.layout.addWidget(Button(f, click=self.uncover), f[0], f[1])
        self.setLayout(self.layout)
    
    def populate(self) -> None:
        """ Fills board with mines and numbers """
        self.bombs = random.sample(sorted(self.field), self.bombcount)
        self.empty = []
        for f in self.bombs:
            self.field[f].setPixmap(QPixmap('./resources/mine.png').scaled(18, 18))
        for f in self.field:
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
                    self.field[f].setText(str(counter))
    
    def neighborhood(self, f: tuple) -> list:
        """ Returns neighbor fields to the given one """
        neighbors = []
        for i in range(f[0]-1, f[0]+2):
            for j in range(f[1]-1, f[1]+2):
                if (i,j) == f:
                    continue
                elif (i,j) in self.field:
                    neighbors.append((i,j))
        return neighbors
    
    def uncover(self, field) -> bool:
        """ Method reveals content of the field(s) """
        if not self.field[field].property('covered'):
            return False

        button = self.layout.itemAtPosition(*field).widget()
        self.layout.removeWidget(button)
        self.layout.addWidget(self.field[field], *field)
        self.field[field].setProperty('covered', False)
        #recurrent uncovering
        if field in self.empty:
            for f in self.neighborhood(field):
                self.uncover(f)
        #loose when you click a bomb
        if field in self.bombs:
            self.failure()
        #check victory condition
        self.victory()
        return True
    
    def failure(self) -> None:
        """ Show bombs, deactivate fields, and send lost signal """
        for f in self.bombs:
                self.uncover(f)
        for f in self.field:
            if self.field[f].property('covered') == True:
                self.layout.itemAtPosition(*f).widget().setFlat(True)
        self.lost.emit()
    
    def victory(self) -> None:
        """ Decrease counter, check condition, deactivate bomb-fields and send win signal """
        self.wincounter -= 1
        if self.wincounter == self.bombcount :
            for f in self.bombs:
                self.layout.itemAtPosition(*f).widget().setFlat(True)
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