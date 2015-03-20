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
import os

def SelectFiles(header, multi=False, save=False,  defaultDir = '', defaultFile = '', wildcard = None, wildcard_default = None):
    if not defaultDir:
        defaultDir = appconfig.get('browse_dir', '')

    path = os.path.join(defaultDir, str(defaultFile).translate(None, '\\/:*?"<>|'))

    if save:
        result, wildcard = QFileDialog.getSaveFileName(appdata.topwindow, header, path, wildcard, wildcard_default)
    elif multi:
        result, wildcard = QFileDialog.getOpenFileNames(appdata.topwindow, header, path, wildcard, wildcard_default)
    else:
        result, wildcard = QFileDialog.getOpenFileName(appdata.topwindow, header, path, wildcard, wildcard_default)

    if result:
        if isinstance(result, basestring):
            result = os.path.normpath(result)
            appconfig['browse_dir'] = os.path.dirname(result)
        else:
            for i, v in enumerate(result):
                result[i] = os.path.normpath(v)
            appconfig['browse_dir'] = os.path.dirname(result[0])
        appconfig.SaveSettings()

    return result, wildcard

def SaveAs(defaultFile = '', wildcard = None, wildcard_default = None):
    return SelectFiles(tm.main.save_as, save=True, defaultFile=defaultFile, wildcard=wildcard, wildcard_default=wildcard_default)

def SaveSnapshot(defaultFile = '', wildcard = None, wildcard_default = None):
    return SelectFiles(tm.main.save_snapshot, save=True, defaultFile=defaultFile, wildcard=wildcard, wildcard_default=wildcard_default)

def EnterText(title, prompt):
    text, ok = QInputDialog.getText(appdata.topwindow, title, prompt, flags = Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
    if ok:
        return text
    else:
        return None

def Notify(text):
    QMessageBox.information(appdata.topwindow, tm.main.notification, text)

def Choice(text):
    return QMessageBox.Ok == QMessageBox.question(appdata.topwindow, tm.main.notification, text, QMessageBox.Ok | QMessageBox.Cancel)

class MultilinePropertyDialog(QDialog):
    def __init__(self, label='', ):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(label)

class OkCancelDialog(QDialog):
    def __init__(self, label=''):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(label)

    def keyPressEvent(self, evt):
        QDialog.keyPressEvent(self, evt)
        if evt.key() == Qt.Key_Return or evt.key() == Qt.Key_Enter:
            if evt.modifiers() & Qt.ControlModifier:
                self.accept()
            else:
                widget = QApplication.focusWidget()
                if isinstance(widget, QAbstractButton) and self.isAncestorOf(widget):
                    widget.animateClick()

    def AddButtons(self, layout):
        self.btn_ok = QPushButton(tm.main.ok, self)
        self.btn_cancel = QPushButton(tm.main.cancel, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.setAutoDefault(False)
        self.btn_cancel.setAutoDefault(False)
        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)
        layout.addLayout(layout_btn)

class PopDialog(QDialog):
    def __init__(self, parent, size=None, pos=None, label=''):
        QDialog.__init__(self, parent, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(label)

    def changeEvent(self, evt):
        if evt.type() == QEvent.WindowStateChange:
            if not windowState() & Qt.WindowActive:
                self.Leaving()
                self.accepted()

    def Leaving(self):
        pass

class TextPopDialog(PopDialog):
    def __init__(self, parent, pos, text, callback):
        PopDialog.__init__(self, parent)

        textc = QPlainTextEdit(self)
        self.textctrl = textc
        self.callback = callback
        textc.setFont(parent.font())
        textc.textChanged.connect(self.OnChanged)
        textc.returnPressed.connect(self.OnEnter)
        textc.setText(text)
        self.exec_()

    def OnChanged(self, event):
        textc = self.textctrl
        metrics = textc.fontMetrics()
        size = metrics.size(Qt.TextExpandTab, textc.text()+u'MM')
        size = (size[0], size[1]+4)
        self.setFixedSize(size)
        self.textctrl.setFixedSize(size)

    def OnEnter(self, event):
        if self.callback:
            self.callback(self.textctrl.GetValue())
        self.callback = None
        self.Close()

    def keyPressEvent(self, evt):
        if evt.key() == Qt.Key_Escape:
            evt.accept()
            if self.callback:
                self.callback(None)
            self.callback = None
            self.reject()

    def Leaving(self):
        if self.callback:
            self.callback(None)
        self.callback = None
