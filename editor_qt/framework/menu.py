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

class Menu(QMenu):
    def __init__(self, parent = None):
        QMenu.__init__(self, parent)
        self.aboutToShow.connect(self.OnAboutToShow)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.UpdateActions)
        self.timer.start(200)

    def OnAboutToShow(self):
        if getattr(self, 'make', None):
            self.make(self)
        self.UpdateActions()

    def UpdateActions(self):
        actions = self.actions()
        for v in actions:
            if getattr(v, 'update', None):
                v.update(v)

class ToolBar(QToolBar):
    def __init__(self, title, parent = None):
        QToolBar.__init__(self, title, parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateActions)
        self.timer.start(200)

    def updateActions(self):
        actions = self.actions()
        for v in actions:
            if getattr(v, 'update', None):
                v.update(v)

def AddMenuItem(menu, item, need_sep=False):
    block = getattr(item, 'menu_block', None)

    if block:
        if not menu.isEmpty():
            menu.addSeparator()
        for i in public.all(block):
            AddMenuItem(menu, i)
        return getattr(item, 'menu_sep', False)

    if need_sep:
        menu.addSeparator()

    sep = getattr(item, 'menu_sep', False)
    part = getattr(item, 'menu_part', None)
    if part:
        for i in public.all(part):
            AddMenuItem(menu, i)
        return sep

    content = getattr(item, 'menu_content', None)

    if content:
        submenu = Menu(menu)

        init = getattr(item, 'Init', None)
        if init:
            init(submenu)

        make = getattr(item, 'Make', None)
        if make:
            submenu.make = make

        InitAction(item, submenu.menuAction())
        menu.addMenu(submenu)
        MakeMenu(submenu, content)
        return sep

    action = QAction(menu)
    InitAction(item, action)
    menu.addAction(action)

    return sep


def InitAction(item, action):
    label = getattr(item, 'vis_label', item.__name__)
    action.setText(label)

    shortcut = getattr(item, 'menu_shortcut', None)
    if shortcut:
        action.setShortcut(shortcut)

    checkable = getattr(item, 'menu_check', False)

    help = getattr(item, 'vis_help', '')
    action.setStatusTip(help)

    do = getattr(item, 'Do', None)
    update = getattr(item, 'Update', None)

    if do:
        if checkable:
            action.setCheckable(True)
            action.triggered[bool].connect(do)
        else:
            action.triggered.connect(do)

    if update:
        action.update = update

    action.setIconVisibleInMenu(False)

    return action

def MakeActions(path, parent):
    actions = []
    for i in public.all(path):
        action = QAction(parent)
        InitAction(i, action)
        actions.append(action)

    return actions

def MakeMenu(menu, path):
    need_sep = False
    for i in public.all(path):
        need_sep = AddMenuItem(menu, i, need_sep)
    return menu

def AssignMenuBar(owner, path):
    bar = owner.menuBar()
    if bar:
        bar.clear()
    else:
        bar = QMenuBar()

    list = public.all(path)
    list = sorted(list, cmp=lambda x,y: getattr(x, 'position', -1) - getattr(y, 'position', -1) )

    for m in list:
        content = getattr(m, 'menu_content')
        menu_items = public.all(content)
        if public.all(content):
            label = getattr(m, 'vis_label', m.__name__)
            menu = Menu(bar)
            init = getattr(m, 'Init', None)
            if init:
                init(menu)
            menu.setTitle(label)
            bar.addMenu(menu)
            MakeMenu(menu, content)

    owner.setMenuBar(bar)

def MakeTool(owner, toolbar, item):

    label = getattr(item, 'vis_label', item.__name__)
    icon = appdata.resources.GetIcon(getattr(item, 'vis_icon', 'error'))

    sep = getattr(item, 'tool_sep', False)

    if sep:
        toolbar.addSeparator()

    action = QAction(icon, label, toolbar)
    checkable = getattr(item, 'menu_check', False)
    do = getattr(item, 'Do', None)
    update = getattr(item, 'Update', None)
    if do:
        if checkable:
            action.setCheckable(True)
            action.triggered[bool].connect(do)
        else:
            action.triggered.connect(do)

    if update:
        action.update = update

    toolbar.addAction(action)

def MakeToolBar(owner, path, title):
    tb = ToolBar(title, owner)
    for m in public.all(path):
        MakeTool(owner, tb, m)
    return tb
