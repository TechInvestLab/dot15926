"""
 .15925 Editor
Copyright 2014 TechInvestLab.ru dot15926@gmail.com

.15925 Editor is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

.15925 Editor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with .15925 Editor.
"""





from PySide.QtCore import *
from PySide.QtGui import *
import framework.resources
import framework.util as util
from framework.dialogs import SelectFiles
import re

expr = re.compile(r'\[\d\d:\d\d:\d\d.\d\d\d\d\d\d\]: ')

def dummy(v):
    pass

class Console(QWidget):
    tab_length      = 3
    vis_label       = tm.main.console

    def __init__(self, parent, inputprocessor=dummy, fileprocessor=dummy):
        QWidget.__init__(self, parent)
        self.showtimestamps = False
        self.inputprocessor = inputprocessor
        self.fileprocessor = fileprocessor

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.splitter = QSplitter(Qt.Vertical, self)
        layout.addWidget(self.splitter)

        self.toppanel    = QWidget(self.splitter)
        layout           = QVBoxLayout(self.toppanel)
        layout.setContentsMargins(0,0,0,0)
        self.log         = QPlainTextEdit(self.toppanel)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.bottompanel = QWidget(self.splitter)

        self.splitter.addWidget(self.toppanel)
        self.splitter.addWidget(self.bottompanel)

        layout = QVBoxLayout(self.bottompanel)
        layout.setContentsMargins(0,0,0,0)

        self.input = QPlainTextEdit(self.bottompanel)
        layout.addWidget(self.input)

        btnlayout = QHBoxLayout()

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('media_play_green'))
        btn.setToolTip(tm.main.console_run)
        btn.clicked.connect(self.EnterText)
        btn.setAutoRaise(True)
        btnlayout.addWidget(btn)

        shortcut = QShortcut(self.input)
        shortcut.setKey("Ctrl+Return")
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(btn.animateClick)

        shortcut = QShortcut(self.input)
        shortcut.setKey("Ctrl+Enter")
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(btn.animateClick)

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('nav_up_green'))
        btn.setToolTip(tm.main.console_prev_cmd)
        btn.clicked.connect(self.HistoryPrev)
        btn.setAutoRaise(True)
        btn.setAutoRepeat(True)
        btnlayout.addWidget(btn)

        shortcut = QShortcut(self.input)
        shortcut.setKey("Ctrl+Up")
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(btn.animateClick)

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('nav_down_green'))
        btn.setToolTip(tm.main.console_next_cmd)
        btn.clicked.connect(self.HistoryNext)
        btn.setAutoRaise(True)
        btn.setAutoRepeat(True)
        btnlayout.addWidget(btn)

        shortcut = QShortcut(self.input)
        shortcut.setKey("Ctrl+Down")
        shortcut.setContext(Qt.WidgetShortcut)
        shortcut.activated.connect(btn.animateClick)

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('document_triangle_green'))
        btn.setToolTip(tm.main.console_run_file)
        btn.clicked.connect(self.OnRunFile)
        btn.setAutoRaise(True)
        btn.setAutoRepeat(True)
        btnlayout.addWidget(btn)

        btnlayout.addStretch(1)
        layout.addLayout(btnlayout)

        self.input.keyPressEvent = self.OnKeyPress

        try:
            with open('input.log', 'rb') as f:
                self.history = f.read().split('\r\n')
        except:
            self.history = []
        self.inhistory = 0

    def OnRunFile(self):
        if self.fileprocessor:
            path, wildcard = SelectFiles('Run file...', multi=False)
            if path:
                self.fileprocessor(path)

    def OnKeyPress(self, event):
        key = event.key()
        if key == Qt.Key_Tab:
            cursor = self.input.textCursor()
            start = cursor.selectionStart()
            end   = cursor.selectionEnd()
            cursor.setPosition(start)
            block_start = cursor.block()
            cursor.setPosition(end)
            block_end = cursor.block()
            if block_start != block_end:
                while True:
                    cursor.setPosition(block_start.position())
                    cursor.insertText(''.ljust(self.tab_length))
                    if block_start == block_end:
                        break
                    block_start = block_start.next()
            else:
                self.input.textCursor().insertText(''.ljust(self.tab_length))
            event.accept()
            return
        if key == Qt.Key_Backtab:
            cursor = self.input.textCursor()
            if not cursor.hasSelection():
                for i in range(self.tab_length):
                    cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
                    selectedText = cursor.selectedText()
                    if selectedText.strip() == '':
                        cursor.removeSelectedText()
                    else:
                        break
            else:
                start = cursor.selectionStart()
                end   = cursor.selectionEnd()
                cursor.setPosition(start)
                block_start = cursor.block()
                cursor.setPosition(end)
                block_end = cursor.block()
                if block_start != block_end:
                    while True:
                        cursor.setPosition(block_start.position())
                        text = block_start.text()
                        count = len(text) - len(text.lstrip())
                        to_remove = self.tab_length if count >= self.tab_length else count
                        for i in range(to_remove):
                            cursor.deleteChar()
                        if block_start == block_end:
                            break
                        block_start = block_start.next()
            event.accept()
            return
        QPlainTextEdit.keyPressEvent(self.input,  event)

    def HistoryNext(self):
        p = self.inhistory+1
        if p<0:
            self.inhistory = p
            self.input.setPlainText(self.history[self.inhistory])
            self.input.moveCursor(QTextCursor.End)
        elif p==0:
            self.inhistory = p
            self.input.setPlainText("")
            self.input.moveCursor(QTextCursor.End)

    def HistoryPrev(self):
        p = self.inhistory-1
        if p+len(self.history)>=0:
            self.inhistory = p
            self.input.setPlainText(self.history[self.inhistory])
            self.input.moveCursor(QTextCursor.End)

    def EnterText(self):
        text = self.input.toPlainText()
        if text=="":
            return
        self.input.clear()
        self.history.append(text)
        self.inhistory = 0
        with open('input.log', 'ab') as f:
            f.write((u'\r\n%s'%text).encode('utf-8'))
        log(u'>>> %s\n'%text)
        self.inputprocessor(text)

    def AddText(self, text):
        self.log.moveCursor(QTextCursor.End)

        tf = self.log.currentCharFormat()
        if text.startswith('Notification:'):
            tf.setForeground(QBrush(Qt.blue))
        else:
            tf.setForeground(QBrush(Qt.black))
        self.log.setCurrentCharFormat(tf)

        self.log.insertPlainText(text)
        self.log.ensureCursorVisible()