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




import weakref
from PySide.QtCore import *
from PySide.QtGui import *
from framework.dialogs import Choice
from itertools import product
from framework.util import CanAcceptFocus, FindFocusTarget, IsChild
import framework.util as util
import framework.menu
import sys

class PropsClient(object):
    def SetProp(self, *t):
        if appdata.propwindow:
            appdata.propwindow.UpdateEntry(*t)

    def ShowProps(self):
        if appdata.propwindow:
            appdata.propwindow.SetClient(self)

    def PropChanged(self, prop, value):
        print prop + ' ' + str(value)

    def RefreshProps(self):
        if appdata.propwindow:
            if appdata.propwindow.GetClient() is self:
                appdata.propwindow.RefreshContent()

    def RefreshPropByIndex(self, i, *t):
        if appdata.propwindow:
            if appdata.propwindow.GetClient() is self:
                appdata.propwindow.RefreshPropByIndex(i, *t)

    def RemovePropByIndex(self, i):
        if appdata.propwindow:
            if appdata.propwindow.GetClient() is self:
                appdata.propwindow.RemovePropByIndex(i)

    def InsertPropByIndex(self, i, *t):
        if appdata.propwindow:
            if appdata.propwindow.GetClient() is self:
                appdata.propwindow.InsertPropByIndex(i, *t)

    def GetPropsContent(self):
        if appdata.propwindow:
            if appdata.propwindow.GetClient() is self:
                return appdata.propwindow.content

    def ClearProps(self):
        if appdata.propwindow.GetClient() is self:
            appdata.propwindow.Clear()

    def SetupProps(self):
        pass

class MultilineList(QWidget):
    pass

class PropEntry:
    def __init__(self, name, value='', prop=None, multiline = False):
        self.name = name
        self.value = value
        self.prop = prop
        self.multiline = multiline

class PropsItemDelegate(QStyledItemDelegate):
    def __init__(self, table):
        QStyledItemDelegate.__init__(self)
        self.table = table
        self.setItemEditorFactory(PropsViewEditorFactory())

class PropLineEdit(QLineEdit):
    style_default = 'PropLineEdit {background-color: #FFFFFF;}'
    style_readonly = 'PropLineEdit {background-color: #F0F0F0;}'

    def __init__(self, table, row, text):
        QLineEdit.__init__(self)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed, QSizePolicy.Label))
        self.table = table
        self.row = row
        self.setText(text)
        self.home(False)        
        self.setFrame(False)

    def setReadOnly(self, readonly):
        QLineEdit.setReadOnly(self, readonly)
        if readonly:
            self.setStyleSheet(self.style_readonly)
        else:
            self.setStyleSheet(self.style_default)

    def focusInEvent(self, evt):
        QLineEdit.focusInEvent(self, evt)
        self.value = self.text()
        self.table.setCurrentIndex(self.table.model().index(self.row, 1))
        if evt.reason() == Qt.OtherFocusReason:
            self.home(False)

    def Deselect(self):
        self.deselect()

    def focusOutEvent(self, evt):
        QLineEdit.focusOutEvent(self, evt)
        self.Apply()

    def Apply(self):
        if self.value != self.text():
            self.value = self.text().encode('utf-8')
            self.table.OnChange(self.row, self.value)

    def keyPressEvent(self, evt):
        key = evt.key()
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            evt.ignore()
        elif key == Qt.Key_Escape:
            self.setText(self.value)
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            self.Apply()
        else:
            QLineEdit.keyPressEvent(self, evt)

class PropComboBox(QComboBox):
    default_style = 'QComboBox:!editable {background-color: #FFFFFF; border: 0px solid #000000}'
    focused_style = 'QComboBox:!editable {background-color: #FFFFFF; border: 1px solid #000000}'

    def __init__(self, table, row, items):
        QComboBox.__init__(self)
        self.table = table
        self.row = row
        self.addItems(items)
        #self.setFocusPolicy(Qt.StrongFocus)
        self.activated[int].connect(lambda x: self.Apply())
        self.setStyleSheet(self.default_style)

    def wheelEvent(self, evt):
        evt.ignore()

    def keyPressEvent(self, evt):
        key = evt.key()
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            evt.ignore()
        elif key == Qt.Key_Escape:
            self.Cancel()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            self.Apply()
        else:
            QComboBox.keyPressEvent(self, evt)

    def focusInEvent(self, evt):
        self.table.setCurrentIndex(self.table.model().index(self.row, 1))
        self.value = self.currentText()
        QComboBox.focusInEvent(self, evt)
        self.setStyleSheet(self.focused_style)

    def focusOutEvent(self, evt):
        QComboBox.focusOutEvent(self, evt)
        self.setStyleSheet(self.default_style)

    def Cancel(self):
        self.setEditText(self.value)
        self.Apply()

    def Apply(self):
        if self.value != self.currentText():
            self.value = self.currentText()
            self.table.OnChange(self.row, self.value)


class ComboProperty(QStackedWidget):
    def __init__(self, table, row, text, editor = None, data = None):
        QStackedWidget.__init__(self)
        self.table = table
        self.row = row
        self.editor = editor
        self.data = data
        self.text = PropTextEdit(table, row, 1, text)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.text)
        self.addWidget(self.text)
        self.text.setReadOnly(True)
        self.setCurrentIndex(0)

    def ShowEditor(self):
        editor = self.editor(self.table, self.row, self.data)
        editor_apply = editor.Apply
        def ApplyProxy():
            editor_apply()
            self.setCurrentIndex(0)
            self.removeWidget(editor)
            self.table.verticalHeader().setResizeMode(self.row, QHeaderView.ResizeToContents)
            self.table.resizeRowToContents(self.row)
        editor.Apply = ApplyProxy
        self.addWidget(editor)
        self.setCurrentIndex(1)
        self.table.verticalHeader().setResizeMode(self.row, QHeaderView.Interactive)
        self.table.resizeRowToContents(self.row)
        editor.setFocus()

    def Apply(self):
        pass

class PropBoolComboBox(PropComboBox):
    def __init__(self, table, row, value):
        PropComboBox.__init__(self, table, row, ['False', 'True'])
        self.value = value
        self.setCurrentIndex(1 if value else 0)

    def Apply(self):
        current = bool(self.currentIndex())
        if self.value != current:
            self.value = current
            self.table.OnChange(self.row, current)


class PropEditor(object):
    def __init__(self, widget_type):
        self.widget_type = widget_type
        appdata.app.AddEventFilter(self.AppEventFilter)

    def AppEventFilter(self, receiver, evt):
        #block shortcuts
        if evt.type() == QEvent.KeyPress:
            if IsChild(self, receiver):
                while receiver:
                    receiver.keyPressEvent(evt)
                    if evt.isAccepted() or receiver == appdata.propwindow:
                        break
                    receiver = receiver.parent()
            return True

        #block focus by wheel
        if evt.type() == QEvent.Wheel:
            if not receiver.isWindow():
                if isinstance(receiver, QDockWidget):
                    if not IsChild(receiver, self):
                        return True
                elif FindFocusTarget(receiver, Qt.WheelFocus) not in (None, appdata.propwindow):
                    if not IsChild(self, receiver):
                        if IsChild(appdata.propwindow, receiver):
                            we = QWheelEvent(appdata.propwindow.mapFromGlobal(evt.globalPos()), evt.globalPos(), evt.delta(), evt.buttons(),
                               evt.modifiers(), evt.orientation())
                            appdata.propwindow.wheelEvent(we)
                        return True
                elif not IsChild(appdata.propwindow, receiver):
                    return True

        #block focus by click
        if evt.type() == QEvent.MouseButtonPress:
            if not receiver.isWindow():
                if isinstance(receiver, QDockWidget):
                    if not IsChild(receiver, self):
                        return not self.TryApply()
                elif FindFocusTarget(receiver, Qt.ClickFocus) not in (None, appdata.propwindow):
                    if not IsChild(self, receiver):
                        return not self.TryApply()
                elif not IsChild(appdata.propwindow, receiver):
                    return not self.TryApply()

        return False

    def IsValid(self):
        return True

    def TryApply(self):
        appdata.app.RemoveEventFilter(self.AppEventFilter)
        if not self.IsValid():
            if not Choice(tm.main.prop_dict_invalid_promt):
                appdata.topwindow.propsdock.activateWindow()
                self.setFocus()
                appdata.app.AddEventFilter(self.AppEventFilter)
                return False
            self.Reset()
        self.Apply()
        return True

    def focusNextPrevChild(self, next):
        evt = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab if next else Qt.Key_Backtab, Qt.NoModifier)
        self.keyPressEvent(evt)
        if event.isAccepted():
            return True;
        if not self.TryApply():
            return True
        return self.widget_type.focusNextPrevChild(self, next)


from _ordereddict import ordereddict

class PropDictEdit(QTableWidget, PropEditor):

    def __init__(self, table, row, value):
        QTableWidget.__init__(self, 0, 3)
        PropEditor.__init__(self, QTableWidget)
        self.row = row
        self.table = table

        self.value = []
        keys = set()
        for v in reversed(value):
            if v[0] not in keys:
                self.value.append(tuple(v))
                keys.add(v[0])
        self.value = self.value[::-1] 

        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.setHorizontalHeaderLabels(['', '', ' '])
        self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.err_icon = appdata.resources.GetPixmap('exclamation-red')
        self.horizontalHeader().setMinimumSectionSize(self.err_icon.width())
        self.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QHeaderView.ResizeToContents)
        self.horizontalHeader().setClickable(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.itemChanged.connect(self.OnItemEdit)
        self.Reset()

        action = QAction(tm.main.menu_copy, self)
        action.setShortcut("Ctrl+C")
        action.activated.connect(self.CopySelected)
        self.addAction(action)

        action = QAction(tm.main.menu_paste, self)
        action.setShortcut("Ctrl+V")
        action.activated.connect(self.Paste)
        self.addAction(action)

        action = QAction(tm.main.menu_cut, self)
        action.setShortcut("Ctrl+X")
        action.activated.connect(self.CutSelected)
        self.addAction(action)

        action = QAction(tm.main.menu_delete, self)
        action.setShortcut("Delete")
        action.activated.connect(self.DeleteSelected)
        self.addAction(action)

    def contextMenuEvent(self, evt):
        menu = QMenu(self)
        menu.addActions(self.actions())
        menu.popup(evt.globalPos())
        evt.accept()

    def GetData(self):
        res = []
        for i in xrange(self.rowCount() - 1):
            r = self.item(i, 1).text().split(' ', 1)
            if len(r) < 2:
                key, value = r[0], ''
            else:
                key, value = r
            res.append((key.encode('utf-8'), value.encode('utf-8')))
        return res

    def IsValid(self):
        self.setCurrentIndex(QModelIndex())
        keys = set()
        for i in xrange(self.rowCount() - 1):
            try:
                r = self.item(i, 1).text().split(' ', 1)
                key, value = r
                if not key or key in keys or not value.strip():
                    return False
                keys.add(key)
            except:
                return False
        return True

    def InsertRow(self, k = '', v = '', row = None):
        self.itemChanged.disconnect(self.OnItemEdit)
        if row == None:
            row = self.rowCount()
        self.setRowCount(row + 1)

        err_item = QTableWidgetItem()
        err_item.setFlags(0)
        self.setItem(row, 0, err_item)

        err = QLabel()
        err.setFixedSize(self.err_icon.size())
        err.setFocusPolicy(Qt.NoFocus)
        self.setCellWidget(row, 0, err)

        value = QTableWidgetItem(' '.join((k, v)).strip())
        self.setItem(row, 1, value)

        btn_item = QTableWidgetItem()
        btn_item.setFlags(0)
        self.setItem(row, 2, btn_item)

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('cross_red'))
        btn.setToolTip(tm.main.console_run)
        btn.clicked.connect(lambda widget = btn: self.OnDelPressed(widget))
        btn.setAutoRaise(True)
        self.setCellWidget(row, 2, btn)

        if not value.text():
            btn.setEnabled(False)
        self.itemChanged.connect(self.OnItemEdit)

    def Reset(self):
        self.setRowCount(0)
        for k, v in self.value:
            self.InsertRow(k, v)

        self.InsertRow()
        self.setCurrentIndex(QModelIndex())

    def OnDelPressed(self, btn):
        for i in xrange(self.rowCount() - 1):
            if btn == self.cellWidget(i, 2):
                self.DeleteRow(i)
                return

    def DeleteSelected(self):
        rows = [item.row() for item in self.selectedItems()]
        for r in sorted(rows, reverse=True):
            if r == (self.rowCount() - 1):
                continue
            self.DeleteRow(r)

    def CutSelected(self):
        self.CopySelected()
        self.DeleteSelected()

    def CopySelected(self):
        text = '\n'.join([item.text().strip() for item in self.selectedItems()])
        util.SetClipboard(text, None)

    def Paste(self):
        try:
            current = self.GetData()
            for l in util.GetClipboard().splitlines():
                r = l.split(' ', 1)
                if len(r) < 2:
                    key, value = r[0], ''
                else:
                    key, value = r
                current.append((key, value))
            self.setRowCount(0)
            for k, v in current:
                self.InsertRow(k, v)
            self.InsertRow()
            self.setCurrentIndex(QModelIndex())
            self.scrollToBottom()
            self.Update()
        except:
            pass

    def DeleteRow(self, row):
        self.removeRow(row)
        self.Update()

    def keyPressEvent(self, evt):
        key = evt.key()
        if key == Qt.Key_Escape:
            if self.state() == QAbstractItemView.EditingState:
                self.closePersistentEditor(self.currentItem())
            else:
                self.Reset()
                self.TryApply()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            if self.state() == QAbstractItemView.EditingState:
                index = self.currentIndex()
                self.currentChanged( index, index )
            else:
                self.TryApply()
        elif key in (Qt.Key_Delete,):
            self.DeleteSelected()
        elif key in (Qt.Key_C,) and evt.modifiers() & Qt.ControlModifier:
            self.CopySelected()
        elif key in (Qt.Key_V,) and evt.modifiers() & Qt.ControlModifier:
            self.Paste()
        elif key in (Qt.Key_X,) and evt.modifiers() & Qt.ControlModifier:
            self.CutSelected()
        else:
            QTableWidget.keyPressEvent(self, evt)

    def OnItemEdit(self, item):
        if item.row() == self.rowCount() - 1:
            self.cellWidget(item.row(), 2).setEnabled(True)
            self.InsertRow('', '')
        elif item.row == self.rowCount() - 2:
            if not item.text():
                self.removeRow(self.rowCount() - 1)
                self.cellWidget(item.row(), 2).setEnabled(False)
        self.Update()

    def Update(self):
        keys = {}
        self.cellWidget(self.rowCount() - 1, 0).setPixmap(None)

        for i in xrange(self.rowCount() - 1):
            try:
                r = self.item(i, 1).text().split(' ', 1)
                key, value = r
                if not value.strip():
                    self.cellWidget(i, 0).setPixmap(self.err_icon)
                else:
                    keys.setdefault(key, []).append(i)
            except:
                self.cellWidget(i, 0).setPixmap(self.err_icon)

        for k, v in keys.iteritems():
            if len(v) > 1:
                for i in v:
                    self.cellWidget(i, 0).setPixmap(self.err_icon)
            else:
                self.cellWidget(v[0], 0).setPixmap(None)

    def focusInEvent(self, evt):
        self.table.setCurrentIndex(self.table.model().index(self.row, 1))
        QTreeWidget.focusInEvent(self, evt)

    def Apply(self):
        data = self.GetData()
        if self.value != data:
            self.value = data
            self.table.OnChange(self.row, self.value)

import keyword
import re

class PropModulesEdit(QTableWidget, PropEditor):

    def __init__(self, table, row, value):
        QTableWidget.__init__(self, 0, 4)
        PropEditor.__init__(self, QTableWidget)
        self.row = row
        self.table = table
        self.value = value
        self.verticalHeader().setVisible(False)
        self.setHorizontalHeaderLabels([' ', tm.main.key, tm.main.value, ' '])
        self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.err_icon = appdata.resources.GetPixmap('exclamation-red')
        self.horizontalHeader().setMinimumSectionSize(self.err_icon.width())
        self.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setResizeMode(1, QHeaderView.Interactive)
        self.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(3, QHeaderView.ResizeToContents)
        self.horizontalHeader().setClickable(False)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.Reset()

    def GetData(self):
        res = {}
        for i in xrange(self.rowCount() - 1):
            key = self.cellWidget(i, 1).text()
            value = self.cellWidget(i, 2).currentIndex()
            res[self.documents[value - 1]] = key
        return res

    def IsValid(self):
        self.setCurrentIndex(QModelIndex())
        keys = set()
        values = set()
        for i in xrange(self.rowCount() - 1):
            key = self.cellWidget(i, 1).text()
            value  = self.cellWidget(i, 2).currentIndex()
            if not key or key in keys or not re.match("[_A-Za-z][_a-zA-Z0-9]*$",key) or keyword.iskeyword(key):
                return False
            keys.add(key)
            if value == 0 or value in values:
                return False
            values.add(value)
        return True

    def AddRow(self, k = '', v = None):
        row = self.rowCount()
        self.setRowCount(row + 1)

        err_item = QTableWidgetItem()
        err_item.setFlags(0)
        self.setItem(row, 0, err_item)

        err = QLabel()
        err.setFixedSize(self.err_icon.size())
        err.setFocusPolicy(Qt.NoFocus)
        self.setCellWidget(row, 0, err)

        key = QLineEdit(k)
        value = QComboBox()
        value.wheelEvent = lambda evt: evt.ignore()
        value.addItems([''] + [doc.name for doc in self.documents])
        value.setStyleSheet('''QComboBox {border: 0px solid #000000}''')
        if not v:
            value.setCurrentIndex(0)
        else:
            value.setCurrentIndex(1 + self.documents.index(v))

        key.setFrame(False)
        key.home(False)
        value.setFrame(False)

        key.textChanged.connect(lambda value, widget = key: self.OnWidgetEdit(widget))
        value.currentIndexChanged[int].connect(lambda value, widget = value: self.OnWidgetEdit(widget))

        self.setCellWidget(row, 1, key)
        self.setCellWidget(row, 2, value)

        btn_item = QTableWidgetItem()
        btn_item.setFlags(0)
        self.setItem(row, 3, btn_item)

        btn = QToolButton(self)
        btn.setIcon(appdata.resources.GetIcon('cross_red'))
        btn.setToolTip(tm.main.console_run)
        btn.clicked.connect(lambda widget = btn: self.OnDelPressed(widget))
        btn.setAutoRaise(True)
        self.setCellWidget(row, 3, btn)

        if not k and not v:
            btn.setEnabled(False)

    def Reset(self):
        self.documents = [doc for doc in appdata.documents if hasattr(doc, 'idi')]
        self.setRowCount(0)
        self.value = {}
        for doc in self.documents:
            if doc.module_name:
                self.value[doc] = doc.module_name
                self.AddRow(doc.module_name, doc)
        self.AddRow()
        self.setCurrentIndex(QModelIndex())

    def OnDelPressed(self, btn):
        for i in xrange(self.rowCount() - 1):
            if btn == self.cellWidget(i, 3):
                self.DeleteRow(i)
                return

    def DeleteRow(self, row):
        self.removeRow(row)
        self.Update()

    def keyPressEvent(self, evt):
        key = evt.key()
        if key == Qt.Key_Escape:
            self.Reset()
            self.TryApply()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            self.TryApply()
        else:
            QTableWidget.keyPressEvent(self, evt)

    def OnWidgetEdit(self, widget):
        for i, j in product(xrange(self.rowCount()), xrange(1, 3)):
            if widget == self.cellWidget(i, j):
                    row = i
                    break
        else:
            return

        if row == self.rowCount() - 1:
            self.cellWidget(row, 3).setEnabled(True)
            self.AddRow('', '')
        elif row == self.rowCount() - 2:
            key = self.cellWidget(row, 1).text()
            value = self.cellWidget(row, 2).currentIndex()
            if not key and value == 0:
                self.removeRow(self.rowCount() - 1)
                self.cellWidget(row, 3).setEnabled(False)

        self.Update()

    def Update(self):
        keys = {}
        values = {}
        self.cellWidget(self.rowCount() - 1, 0).setPixmap(None)

        for i in xrange(self.rowCount() - 1):
            key = self.cellWidget(i, 1).text()
            keys.setdefault(key, []).append(i)
            value = self.cellWidget(i, 2).currentIndex()
            values.setdefault(value, []).append(i)
            self.cellWidget(i, 0).setPixmap(None)

        for k, v in keys.iteritems():
            if not k or len(v) > 1 or not re.match("[_A-Za-z][_a-zA-Z0-9]*$",k) or keyword.iskeyword(k):
                for i in v:
                    self.cellWidget(i, 0).setPixmap(self.err_icon)

        for k, v in values.iteritems():
            if not k or len(v) > 1:
                for i in v:
                    self.cellWidget(i, 0).setPixmap(self.err_icon)


    def focusInEvent(self, evt):
        self.table.setCurrentIndex(self.table.model().index(self.row, 1))
        QTreeWidget.focusInEvent(self, evt)

    def Apply(self):
        data = self.GetData()
        if self.value != data:
            self.value = data
            for doc in appdata.documents:
                if doc in self.value:
                    doc.module_name = self.value[doc]
                else:
                    doc.module_name = ''
            self.table.OnChange(self.row, self.value)

class PropPatternsEdit(QTreeWidget, PropEditor):
    def __init__(self, table, row, value):
        QTreeWidget.__init__(self)
        PropEditor.__init__(self, QTreeWidget)
        self.row = row
        self.table = table
        self.header().setVisible(False)
        self.value = value
        self.itemChanged.connect(self.OnItemChange)
        self.Reset()

    def GetData(self):
        if self.root.data(0, Qt.CheckStateRole) == Qt.Unchecked:
            return {}
        else:
            result = {}
            for i in xrange(self.root.childCount()):
                if self.root.child(i).data(0, Qt.CheckStateRole) != Qt.Unchecked:
                    if self.root.child(i).data(0, Qt.CheckStateRole) == Qt.Checked:
                        result[self.root.child(i).text(0)] = []
                    else:
                        result[self.root.child(i).text(0)] = patterns = []
                        for j in xrange(self.root.child(i).childCount()):
                            if self.root.child(i).child(j).data(0, Qt.CheckStateRole) == Qt.Checked:
                                patterns.append(self.root.child(i).child(j).text(0))
            return result

    def Reset(self):
        self.itemChanged.disconnect(self.OnItemChange)
        self.clear()
        available_patterns = appdata.project.GetPatternsModulesAndNames()

        self.root = QTreeWidgetItem()
        self.root.setText(0, tm.main.all_patterns)
        self.root.setData(0, Qt.CheckStateRole, Qt.Checked)
        self.addTopLevelItem(self.root)

        for module_name, patterns_list in available_patterns.iteritems():
            module_item = QTreeWidgetItem()
            module_item.setText(0, module_name)
            module_item.setData(0, Qt.CheckStateRole, Qt.Checked)
            self.root.addChild(module_item)
            for pattern_name in patterns_list:
                pattern_item = QTreeWidgetItem()
                pattern_item.setText(0, pattern_name)
                if module_name in self.value and (not self.value[module_name] or pattern_name in self.value[module_name]):
                    check = Qt.Checked
                else:
                    check = Qt.Unchecked
                pattern_item.setData(0, Qt.CheckStateRole, check)
                module_item.addChild(pattern_item)
            self.UpdateCheckState(module_item)

        self.itemChanged.connect(self.OnItemChange)
        self.root.setExpanded(True)

    def keyPressEvent(self, evt):
        key = evt.key()
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            evt.ignore()
        elif key == Qt.Key_Escape:
            self.Reset()
            self.TryApply()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            self.TryApply()
        else:
            QTreeWidget.keyPressEvent(self, evt)

    def SetChildrenCheckState(self, item, state):
        for i in xrange(item.childCount()):
            item.child(i).setData(0, Qt.CheckStateRole, state)
            self.SetChildrenCheckState(item.child(i), state)

    def GetChildrenCheckState(self, item):
        states = set()
        for i in xrange(item.childCount()):
            states.add(item.child(i).data(0, Qt.CheckStateRole))
        states = list(states)
        if len(states) == 1:
            return states[0]
        else:
            return Qt.PartiallyChecked

    def UpdateCheckState(self, item):
        if item:
            state = self.GetChildrenCheckState(item)
            item.setData(0, Qt.CheckStateRole, state)
            self.UpdateCheckState(item.parent())

    def OnItemChange(self, item):
        self.itemChanged.disconnect(self.OnItemChange)
        checkstate = item.data(0, Qt.CheckStateRole)
        self.SetChildrenCheckState(item, checkstate)
        self.UpdateCheckState(item.parent())
        self.itemChanged.connect(self.OnItemChange)

    def focusInEvent(self, evt):
        self.table.setCurrentIndex(self.table.model().index(self.row, 1))
        QTreeWidget.focusInEvent(self, evt)

    def Apply(self):
        data = self.GetData()
        if self.value != data:
            self.value = data
            self.table.OnChange(self.row, self.value)

    def contextMenuEvent(self, evt):
        pass


class PropTextEdit(QTextEdit):
    style_default = 'PropTextEdit {background-color: #FFFFFF;}'
    style_readonly = 'PropTextEdit {background-color: #F0F0F0;}'
    def __init__(self, table, row, col, text):
        QTextEdit.__init__(self)
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.NoFrame)
        self.table = table
        self.row = row
        self.col = col
        self.setPlainText(text)
        self.document().contentsChange.connect(self.UpdateSize)

    def setReadOnly(self, readonly):
        QTextEdit.setReadOnly(self, readonly)
        if readonly and not hasattr(self.parent(), 'ShowEditor'):
            self.setStyleSheet(self.style_readonly)
        else:
            self.setStyleSheet(self.style_default)

    def focusInEvent(self, evt):
        self.table.setCurrentIndex(self.table.model().index(self.row, self.col))
        self.value = self.toPlainText()
        if evt.reason() == Qt.OtherFocusReason:
            self.moveCursor(QTextCursor.Start)
        QTextEdit.focusInEvent(self, evt)

    def Deselect(self):
        c = self.textCursor()
        c.clearSelection()
        self.setTextCursor(c)

    def focusOutEvent(self, evt):
        self.Apply()
        QTextEdit.focusOutEvent(self, evt)

    def Apply(self):
        if self.value != self.toPlainText():
            self.table.OnChange(self.row, self.toPlainText().encode('utf-8'))

    def mouseDoubleClickEvent(self, evt):
        if hasattr(self.parent(), 'ShowEditor') and evt.button() == Qt.LeftButton:
            self.parent().ShowEditor()
            return
        QTextEdit.mouseDoubleClickEvent(self, evt)

    def keyPressEvent(self, evt):
        key = evt.key()
        if hasattr(self.parent(), 'ShowEditor') and key in (Qt.Key_Enter, Qt.Key_Return):
            self.parent().ShowEditor()
        elif key in (Qt.Key_Tab, Qt.Key_Backtab):
            evt.ignore()
        elif key == Qt.Key_Escape:
            self.setPlainText(self.value)
        else:
            QTextEdit.keyPressEvent(self, evt)

    def sizeHint(self):
        m = self.fontMetrics()
        size = self.document().size().toSize()
        if self.col == 0:
            return QSize(self.table.columnWidth(self.col), size.height()+2)
        else:
            return QSize(self.table.columnWidth(self.col), size.height()+2+m.height())

    def UpdateSize(self, *t):
        self.table.resizeRowToContents(self.row)

class PropsViewEditorFactory(QItemEditorFactory):
    def createEditor(self, type, parent):
        if type != unicode:
            return QItemEditorFactory.createEditor(self, type, parent)
        return QPlainTextEdit(parent)

class PropsView(QTableWidget):
    msg_property = tm.main.property
    msg_value = tm.main.value

    def __init__(self, parent):
        QTableWidget.__init__(self, 0, 2, parent)
        appdata.propwindow = self
        self.setHorizontalHeaderLabels([self.msg_property, self.msg_value])
        self.horizontalHeader().setMinimumSectionSize(60)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(True)
        self.client = None
        self.content = []
        self.delegate = PropsItemDelegate(self)
        self.setItemDelegateForColumn(1, self.delegate)
        self.itemChanged.connect(self.OnItemChanged)
        self.need_refresh = False
        self.refreshing = False
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setClickable(False)
        header.sectionResized.connect(self.OnHeaderSectionResized)
        self.currentCellChanged.connect(self.OnCellChanged)
        self.setTextElideMode(Qt.ElideNone)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)

    def OnHeaderSectionResized(self, idx, oldsize, newsize):
        if idx == 0:
            avail = self.horizontalHeader().width() - self.horizontalHeader().minimumSectionSize()
            if newsize > avail:
                self.horizontalHeader().resizeSection (0, avail)

    def resizeEvent(self, evt):
        QTableWidget.resizeEvent(self, evt)
        newsize = self.horizontalHeader().sectionSize(0)
        avail = self.horizontalHeader().width() - self.horizontalHeader().minimumSectionSize()
        if newsize > avail and avail >= self.horizontalHeader().minimumSectionSize():
            self.horizontalHeader().resizeSection (0, avail)

    def OnCellChanged(self, row, col, prev_row, prev_col):
        w = self.cellWidget(row, col)
        prev_w = self.cellWidget(prev_row, prev_col)
        if prev_w and getattr(prev_w, 'Deselect', None):
            prev_w.Deselect()

    def RefreshPropByIndex(self, i, *t):
        self.content[i] = PropEntry(*t)
        self.FillEntry(i)

    def RemovePropByIndex(self, i):
        del self.content[i]
        self.removeRow(i)

    def InsertPropByIndex(self, i, *t):
        self.content.insert(i, PropEntry(*t))
        self.insertRow(i)
        self.FillEntry(i)

    def RefreshContent(self):
        if self.need_refresh:
            return
        self.need_refresh = True
        @public.mth
        def f():
            self.need_refresh = False
            if self.client():
                self.content = []
                self.client().SetupProps()
                self.RefreshPropsInternal()
            else:
                self.Clear()

    def Clear(self):
        self.setRowCount(0)
        self.content = []

    def SetClient(self, client):
        if not self.client or self.client() is not client:
            self.client = weakref.ref(client, self.OnClientDestroy)
            self.RefreshContent()

    def GetClient(self):
        if self.client:
            return self.client()
        return None

    def OnClientDestroy(self, client):
        if self.client and self.client() is client:
            self.Clear()

    def FillEntry(self, i):
        entry = self.content[i]
        widget = self.cellWidget(i, 0)
        if not widget:
            widget = PropTextEdit(self, i, 0, entry.name)
            p = widget.palette()
            p.setColor(QPalette.Base, QColor(0xF0F0F0));
            widget.setPalette(p)
            widget.setReadOnly(True)
            self.setCellWidget(i, 0, widget)
        else:
            widget.setPlainText(entry.name)

        if isinstance(entry.value, basestring):
            if entry.multiline:
                widget = PropTextEdit(self, i, 1, entry.value)
            else:
                widget = PropLineEdit(self, i, entry.value)
            if not entry.prop:
                widget.setReadOnly(True)
            self.setCellWidget(i, 1, widget)
        elif isinstance(entry.value, tuple):
            widget = ComboProperty(self, i, entry.value[0], entry.value[1], entry.value[2])
            self.setCellWidget(i, 1, widget)
        elif isinstance(entry.value, list):
            widget = PropComboBox(self, i, entry.value)
            self.setCellWidget(i, 1, widget)            
        elif isinstance(entry.value, bool):
            widget = PropBoolComboBox(self, i, entry.value)
            self.setCellWidget(i, 1, widget)
        else:
            self.setCellWidget(i, 1, None)
            value = self.item(i, 1)
            if not value:
                value = QTableWidgetItem()
                self.setItem(i, 1, value)
            if not entry.prop:
                value.setBackground(QBrush(QColor(0xF0F0F0)))
                value.setFlags(value.flags() & ~Qt.ItemIsEditable)
            else:
                value.setBackground(QBrush(QColor(0xFFFFFF)))
                value.setFlags(value.flags() | Qt.ItemIsEditable)
            value.setData(Qt.EditRole, entry.value)

    def RefreshPropsInternal(self):
        row_count = len(self.content)
        self.setRowCount(row_count)
        self.refreshing = True
        for i in xrange(row_count):
            self.FillEntry(i)
        self.refreshing = False

    def UpdateEntry(self, *t):
        self.content.append(PropEntry(*t))

    def moveCursor(self, cursorAction, modifiers):
        if cursorAction not in (self.CursorAction.MoveNext, self.CursorAction.MovePrevious):
            return self.currentIndex()

        index = self.currentIndex()
        if not index.isValid():
            return self.currentIndex()

        while True:    
            i = QTableWidget.moveCursor(self, cursorAction, modifiers)
            if cursorAction == QAbstractItemView.MoveNext and index.row() > i.row():
                widget = self.cellWidget(index.row(), index.column())
                if widget:
                    widget.Apply()
                item = self.itemFromIndex(index)
                if item:
                    self.editItem(item)
                return index
            if cursorAction == QAbstractItemView.MovePrevious and index.row() < i.row():
                widget = self.cellWidget(index.row(), index.column())
                if widget:
                    widget.Apply()
                item = self.itemFromIndex(index)
                if item:
                    self.editItem(item)
                return index
            if self.IsItemEditable(i):
                return i
            if index == i:
                return i
            self.setCurrentIndex(i)

    def IsItemEditable(self, index):
        widget = self.cellWidget(index.row(), index.column())
        if widget:
            if getattr(widget, 'isReadOnly', None):
                return not widget.isReadOnly()
            return True
        item = self.itemFromIndex(index)
        if item:
            return item.flags() & Qt.ItemIsEditable
        return False

    def keyPressEvent(self, evt):
        QTableWidget.keyPressEvent(self, evt)
        if evt.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            evt.accept()

    def OnItemChanged(self, item):
        if self.refreshing or item.column() != 1:
            return

        value = item.data(Qt.EditRole)
        if isinstance(value, basestring):
            value = value.strip()
            self.refreshing = True
            item.setData(Qt.EditRole, value)
            self.refreshing = False

        self.OnChange(item.row(), value)

    def OnChange(self, row, value):

        if not self.client or not self.client() or row >= len(self.content):
            return
        entry = self.content[row]

        if not entry.prop:
            return

        if isinstance(value, basestring):
            value = value.strip()

        self.client().PropChanged(entry.prop, value)
