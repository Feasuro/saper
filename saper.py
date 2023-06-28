#!/usr/bin/env python

import sys
import random
from PyQt6.QtCore import QSize
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtCore import pyqtSlot as Slot
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout, QLabel

class Button(QPushButton):
    """Button that covers field"""
    click = Signal(tuple)

    def __init__(self, field, *args, **kwargs):
        """button is aware of it's position that is emitted when clicked"""
        super().__init__(*args, **kwargs)
        self.setProperty('field', field)
        self.clicked.connect(self.on_click)

    @Slot()
    def on_click(self):
        self.click.emit(self.property('field'))


class Board(QWidget):
    """Widget that represents the game board"""
    
    def __init__(self, x, y, bombcount, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.wincounter = 0
        self.field = {(i,j): QLabel() for i in range(x) for j in range(y)}
        for f in self.field:
            self.field[f].setProperty('covered', True)
            self.wincounter += 1
        self.populate(bombcount)
        
        self.setFixedSize(18 * x, 18 * y)
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        for f in self.field:
            #self.field[f].setFixedSize(QSize(18, 18))
            self.layout.addWidget(Button(f, click=self.uncover), f[0], f[1])
            #self.layout.addWidget(self.field[*f], *f)
            #sygnałki
            #self.layout.itemAtPosition(*f).widget().clicked.connect(self.on_click)
        self.setLayout(self.layout)
    
    def populate(self, bombcount):
        """Fills board with mines and numbers"""
        self.bombs = random.sample(sorted(self.field), bombcount)
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
                    self.field[f].setText(str(counter)) #poprawić kolory
    
    def neighborhood(self, f: tuple) -> list:
        """Returns neighbor fields to the given one"""
        neighbors = []
        for i in range(f[0]-1, f[0]+2):
            for j in range(f[1]-1, f[1]+2):
                if (i,j) == f:
                    continue
                elif (i,j) in self.field:
                    neighbors.append((i,j))
        return neighbors
    
    def uncover(self, field) -> bool:
        """Method reveals content of the field(s)"""
        if not self.field[field].property('covered'):
            return False
        #print('click!', field)
        button = self.layout.itemAtPosition(*field).widget()
        self.layout.removeWidget(button)
        #button.deleteLater()
        #del button
        #self.layout.replaceWidget(old, self.field[field])
        self.layout.addWidget(self.field[field], *field)
        self.field[field].setProperty('covered', False)
        
        if field in self.empty:
            for f in self.neighborhood(field):
                self.uncover(f)
        
        if field in self.bombs:
            #print('You Lost!') #to be continued
            for f in self.bombs:
                self.uncover(f)
                #self.layout.itemAtPosition(*f).widget().click
        wincounter -= 1
        return True


class MainWindow(QMainWindow):
    """Provides graphic interface for playing saper"""
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        #size and title bar
        self.setWindowTitle('Saper')
        self.setWindowIcon(QIcon('./resources/mine.png'))
        #self.setGeometry(100,100,700,500)
        
        self.playground = Board(10, 10, 10)
        self.setCentralWidget(self.playground)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())