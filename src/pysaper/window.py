"""Main window for the game"""

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QIntValidator
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QGridLayout, QToolBar, QSizePolicy, QDialog,
                             QMessageBox, QDialogButtonBox, QLineEdit)

import records
import game

class MainWindow(QMainWindow):
    """Provides window interface for playing saper"""

    def __init__(self) -> None:
        super().__init__()
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
        close.triggered.connect(QApplication.instance().quit)
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
        record = QAction('&Records', self)
        record.setShortcut('Ctrl+R')
        record.triggered.connect(lambda: records.show(self))
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
        gamemenu = menu.addMenu('&Game')
        gamemenu.addAction(self.new)
        gamemenu.addAction(record)
        gamemenu.addSeparator()
        gamemenu.addAction(self.beginner)
        gamemenu.addAction(self.advanced)
        gamemenu.addAction(self.expert)
        gamemenu.addAction(self.custom)
        gamemenu.addSeparator()
        gamemenu.addAction(close)
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
        self.playground = game.Board(self.rows, self.cols, self.bombcount, question=self.property('question'))
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
        records.end_game(self)

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
        self.clock.setText('Time: ' + records.convert_seconds(self.seconds))

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
            self.playground.fields[field].setIconSize(QSize(int(self.size * 0.8), int(self.size * 0.8)))
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


class CustomSetupDialog(QDialog):
    """Dialog window to setup custom rows, columns and bombs count"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
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
