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

import framework.util as util
from framework.view import View
from framework.tree import Tree

class SearchBox(QFrame):
    def __init__(self, parent, target, text, filter_cb, search_cb, options = None, multi = False, ):
        QFrame.__init__(self, parent)
        self.setStyleSheet('SearchBox {border: 2px solid gray;  border-radius: 4px; background-color: white}')
        self.filter_cb = filter_cb
        self.search_cb = search_cb
        self.target = target
        self.searchbutton = QToolButton(self)
        self.searchbutton.setIcon(appdata.resources.GetIcon('view'))
        self.searchbutton.setAutoRaise(True)
        self.searchbutton.setStyleSheet('border: 0px')
        self.searchbutton.clicked.connect(self.OnSearch)
        self.lineedit = QLineEdit(self)
        self.lineedit.returnPressed.connect(self.OnSearch)
        self.lineedit.textChanged.connect(self.OnText)
        self.lineedit.setFrame(False)
        self.lineedit.setStyleSheet('border: 0px')
        layout = QHBoxLayout(self)
        layout.addWidget(self.lineedit)
        layout.addWidget(self.searchbutton)

        self.text = text
        self.multi = multi
        self.selection = set()
        self.ololo = []
        if options:
            self.options = []
            self.menu = QMenu(self)
            for i, v in enumerate(options):
                action = QWidgetAction(self.menu)
                checkBox = QCheckBox(v, self.menu)
                action.setDefaultWidget(checkBox)
                checkBox.clicked[bool].connect(lambda state, idx = i: self.OnOptionChanged(idx, state))
                self.options.append(action)
                self.menu.addAction(action)

            self.OnOptionChanged(0, True)
            self.optbutton = QToolButton(self)
            self.optbutton.setIcon(appdata.resources.GetIcon('navigate_down'))
            self.optbutton.setText(tm.main.search_type)
            self.optbutton.setAutoRaise(True)
            self.optbutton.setStyleSheet('border: 0px')
            self.optbutton.clicked.connect(self.OnOptions)
            self.optbutton.setToolTip(tm.main.search_type)
            layout.addWidget(self.optbutton)
        else:
            self.UpdateHints(text)
        layout.setContentsMargins(0,0,0,0)


    @property
    def value(self):
        return self.lineedit.text()

    @value.setter
    def value(self, value):
        self.lineedit.setText(value)

    def UpdateHints(self, text):
        self.lineedit.setPlaceholderText(text)
        self.searchbutton.setText(text)
        self.searchbutton.setToolTip(text)

    def OnOptionChanged(self, idx, checked):
        texts = []
        for i, v in enumerate(self.options):
            if i == idx:
                if checked or not self.multi:
                    v.defaultWidget().setChecked(True)
                    self.selection.add(i)
                else:
                    if len(self.selection) <= 1:
                        v.defaultWidget().setChecked(True)
                    else:
                        self.selection.discard(i)
                        v.defaultWidget().setChecked(False)

            elif not self.multi:
                self.selection.discard(i)
                v.defaultWidget().setChecked(False)

            if v.defaultWidget().isChecked():
                texts.append(v.defaultWidget().text())

        self.UpdateHints(self.text + ', '.join(texts))

    def OnOptions(self):
        self.menu.popup(self.optbutton.mapToGlobal(QPoint(0,self.optbutton.frameGeometry().height())))

    def OnSearch(self):
        if self.search_cb:
            self.search_cb(self.lineedit.text())
        self.lineedit.setText('')
        self.target.setFocus()

    def OnText(self):
        if self.filter_cb:
            self.filter_cb(self.lineedit.text())

class FilteredView(View):

    msg_filterdesc  = tm.main.filter
    document        = None
    bound_uri       = None
    msg_filteroptions = None
    msg_filtermulti = False

    @property
    def selected(self):
        return self.wnd_tree.selected

    def FindViewMethod(self, methodname):
        if not self.wnd_tree.hasFocus() and not appdata.topwindow.menuBar().hasFocus():
            return

        if getattr(self, methodname, None):
            return getattr(self, methodname)

        v = self.selected
        if not v:
            return

        return util.findcommonmethod(v, methodname)

    def __init__(self, parent):
        View.__init__(self, parent)
        self.UpdateLabel(self.GetLabel())

        widget = QWidget(self)

        layout = QVBoxLayout(widget)

        self.wnd_tree = Tree(widget)
        if not self.bound_uri:
            self.wnd_filter = SearchBox(widget, self.wnd_tree, self.msg_filterdesc, self.Filter, self.Search, self.msg_filteroptions, self.msg_filtermulti)
            layout.addWidget(self.wnd_filter)

        self.setFocusProxy(self.wnd_tree)
        self.wnd_tree.view = self
        layout.addWidget(self.wnd_tree)
        layout.setContentsMargins(0,5,0,0)

        self.destroyed.connect(self.OnDestroy)
        self.setWidget(widget)
        self.Seed()

    def GetIcon(self):
        if not self.bound_uri and self.document != None:
            return self.document.GetIcon()
        if getattr(self, 'vis_icon', None) != None:
            return self.vis_icon
        else:
            return 'blank_ico'

    def GetLabel(self):
        if getattr(self, 'vis_label', None) != None:
            return self.vis_label
        elif self.document:
            return self.document.GetLabel()
        else:
            return tm.main.view

    def UpdateLabel(self, label):
        self.SetTitle(label)

    def OnDestroy(self):
        self.wnd_tree.clear()
        appdata.views.discard(self)

    # override

    def Seed(self):
        pass

    def Filter(self, value):
        pass

    def Search(self, value):
        pass

    def CanCopyText(self):
        if self.wnd_tree.selected:
            return True
        return False

    def CopyText(self):
        selected = self.wnd_tree.selected_sorted
        lines    = []
        for v in selected:
            line = ''
            p = v.parent
            indent  = 0
            while p:
                indent += 1
                p = p.parent
            line += v.text(0)
            lines.append((indent, line))

        if lines:
            min_indent = sorted(lines)[0][0]
            text = '\n'.join(['\t'*(i-min_indent)+l for i, l in lines])
        else:
            text = ''
        util.SetClipboard(text, None)