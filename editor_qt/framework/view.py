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


class TitleBar(QFrame):
    def __init__(self, parent):
        QFrame.__init__(self, parent)
        self.SetActive(False)
        self.title = QLabel(tm.main.title, self)
        self.title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        self.btn = QToolButton(self)
        self.btn.setIconSize(QSize(10,10))
        self.btn.setIcon(appdata.app.style().standardIcon(QStyle.SP_TitleBarNormalButton))
        self.btn.setText(tm.main.close)
        self.btn.setDefaultAction
        self.btn.clicked.connect(lambda: parent.setFloating(True))
        self.btn.setAutoRaise(True)

        btn2 = QToolButton(self)
        btn2.setIconSize(QSize(10,10))
        btn2.setIcon(appdata.app.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        btn2.setText(tm.main.close)
        btn2.clicked.connect(parent.close)
        btn2.setAutoRaise(True)

        layout = QHBoxLayout(self)
        layout.addSpacing(5)
        layout.addWidget(self.title)
        layout.addWidget(self.btn)
        layout.addWidget(btn2)
        layout.setContentsMargins(0,0,0,0)

    def SetActive(self, active):
        if active:
            self.setStyleSheet('QLabel{color: white;} TitleBar {background: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 MidnightBlue, stop:1 LightBlue);}')
        else:
            self.setStyleSheet('QLabel{color: black;} TitleBar {background: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 gray , stop:1 white);}')

class View(QDockWidget):
    """Base class for view.

    Attributes:
        document: Document associated with this view.
    """
    document = None
    vis_icon = 'blank_ico'
    def __init__(self, parent):
        QDockWidget.__init__(self, parent)
        self.setWindowTitle(tm.main.empty)
        self._dragged = False
        self.installEventFilter(self)
        self.setTitleBarWidget(TitleBar(self))
        self.topLevelChanged.connect(self.OnDockState)
        self.visibilityChanged.connect(self.OnVisibilityChanged)
        self.viewnode = None
        self.seeable = False
        #elf.focusPolicy(Qt.ClickFocus)

    def changeEvent(self, evt):
        if evt.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.setFocus()
        QDockWidget.changeEvent(self, evt)

    def IsSeeable(self):
        return self.seeable 

    def OnDockState(self, undock):
        if undock:
            self.titleBarWidget().btn.hide()
        else:
            self.titleBarWidget().btn.show()

    def focusNextPrevChild(self, next):
        if not self._dragged:
            return QDockWidget.focusNextPrevChild(self, next)
        return True

    def OnVisibilityChanged(self, visible):
        self.seeable = visible
        if visible:
            if appdata.active_view != self and appdata.active_view and appdata.active_view._dragged:
                return
            self.SetActive()

    def SetTitle(self, title):
        self.titleBarWidget().title.setText(title)
        self.setWindowTitle(title)

    def AddChild(self, obj):
        if obj and obj.isWidgetType():
            obj.installEventFilter(self)

        for v in obj.children():
            self.AddChild(v)

    def RemoveChild(self, obj):
        if obj and obj.isWidgetType():
            obj.removeEventFilter(self)

        for v in obj.children():
            self.RemoveChild(v)

    def eventFilter(self, obj, evt):
        if evt.type() == QEvent.ChildAdded:
            self.AddChild(evt.child())
        elif evt.type() == QEvent.ChildRemoved:
            self.RemoveChild(evt.child())
        elif evt.type() == QEvent.MouseButtonPress:
            if obj == self.titleBarWidget() and evt.button() == Qt.LeftButton:
                self._dragged = True
            self.SetActive()
        elif evt.type() == QEvent.MouseButtonRelease:
            self._dragged = False
        elif evt.type() == QEvent.FocusIn:
            self.SetActive(False) #child already focused
        return QDockWidget.eventFilter(self, obj, evt)

    def SetActive(self, focus = True):
        if self.viewnode:
            self.viewnode.Select()
            if self.viewnode.doc:
                appdata.active_document = self.viewnode.doc
            else:
                appdata.active_document = None

        if appdata.active_view == self:
            return

        if appdata.active_view != None:
            appdata.active_view.titleBarWidget().SetActive(False)
            if self.isFloating():
                appdata.topwindow.setFocus(Qt.OtherFocusReason)

        if focus:
            self.setFocus(Qt.OtherFocusReason)

        self.titleBarWidget().SetActive(True)
        appdata.active_view = self

    def Highlight(self):
        pass

    def closeEvent(self, evt):
        evt.accept()
        if appdata.active_view == self:
            appdata.active_view = None
            for v in appdata.topwindow.workarea.findChildren(View):
                if v != self and v.IsSeeable():
                    v.SetActive(True)
                    break

    def GetIcon(self):
        return self.vis_icon

    def FindViewMethod(self, methodname):
        pass

    def GetTitle():
        """Returns label for view"""
        return ""

    def OnDestroy(self):
        pass
