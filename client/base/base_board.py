from PyQt5.QtWidgets import QMainWindow,QMessageBox,QPushButton,QWidget,QDialog,QLabel,QVBoxLayout,QTextEdit
from PyQt5.QtCore import QRect,Qt
import random
class popMessageBoard(QDialog):
    def __init__(self,parent,text,title='提示'):
        super().__init__(parent)
        self.parent=parent
        self.text=text
        self.title=title
        self.initUI()
    def initUI(self):
        layout_main=QVBoxLayout()
        if type(self.text)==list:
            for i in self.text:
                textWidget=QTextEdit()
                textWidget.resize(300,300)
                textWidget.document().contentsChanged.connect(self.textAreaChanged)
                textWidget.setText(i)
                textWidget.setFocusPolicy(Qt.NoFocus)
                # textWidget.setAlignment(Qt.AlignTop)
                textWidget.setStyleSheet("border:none")
                layout_main.addWidget(textWidget,alignment=Qt.AlignHCenter)
        else:
            textWidget=QTextEdit()
            textWidget.resize(300,300)
            textWidget.document().contentsChanged.connect(self.textAreaChanged)
            textWidget.setText(self.text)
            textWidget.setFocusPolicy(Qt.NoFocus)
            # textWidget.setAlignment(Qt.AlignTop)
            textWidget.setStyleSheet("border:none")
            print(textWidget,id(textWidget))
            layout_main.addWidget(textWidget,alignment=Qt.AlignHCenter)
        yes=QPushButton('确定')
        yes.clicked.connect(self.button_yes)
        layout_main.addWidget(yes,alignment=Qt.AlignHCenter)
        self.setLayout(layout_main)
        # self.setMinimumSize(300,300)
        # self.setMaximumSize(300,300)
        self.setWindowTitle(self.title) 
        self.exec_()
    def textAreaChanged(self):
        sender=self.sender()
        sender.adjustSize()
        print('p:',sender.pageCount(),sender.size())
        sender.setTextWidth(300)
        print('p:',sender.pageCount(),sender.size())
        newWidth=sender.size().width()
        newHeight=sender.size().height()
        edit=sender.parent().parent()
        edit.setFixedWidth(newWidth+20)
        edit.setFixedHeight(newHeight)
        # edit.resize(newWidth,newHeight)
        print('新:',newWidth,newHeight)
    def button_yes(self):
        self.close()


class BaseBoard(QMainWindow):
    def __init__(self,parent=None,topBoard=None):
        super().__init__(parent)
        self.parent=parent
        self.topBoard=topBoard
        self.main_widget=QWidget()
        self.setCentralWidget(self.main_widget)
    def setLayout(self,layout):
        self.main_widget.setLayout(layout)
    def popUpMessage(self,text,title='提示'):
        messageBox=popMessageBoard(self,text,title)
    def layoutAddWidget(self,layout,wight,alignment=Qt.AlignHCenter,size=None):
        if size:
            wight.setFixedWidth(size[0])
            wight.setFixedHeight(size[1])
        layout.addWidget(wight,alignment=alignment)


class DiaBaseBoard(QDialog):
    def __init__(self,parent=None,topBoard=None):
        super().__init__(parent)
        self.parent=parent
        self.topBoard=topBoard

    def popUpMessage(self,text):
        messageBox = QMessageBox(self)
        messageBox.setWindowTitle('提示')
        messageBox.setText(text)
        messageBox.addButton(QPushButton('确定'), QMessageBox.NoRole)
        messageBox.exec_()

    def layoutAddWidget(self,layout,wight,alignment=Qt.AlignHCenter,size=None):
        if size:
            wight.setFixedWidth(size[0])
            wight.setFixedHeight(size[1])
        layout.addWidget(wight,alignment=alignment)
