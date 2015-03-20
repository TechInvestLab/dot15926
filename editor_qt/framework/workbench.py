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
import framework.python_console
import framework.project
import framework.menu
import framework.workbench_menu
import framework.props
import framework.resources
import os
import sys
from framework.tree import Tree
from framework.treenode import TreeNode
from framework.startpage import StartPage

class PopupNotification(QLabel):
    def __init__(self, text, duration = 10000.0):
        QLabel.__init__(self, appdata.topwindow)
        self.move_animation = None
        self.fadeduration = 250.0
        self.moveduration = 100.0
        self.duration = duration + self.fadeduration * 2.0
        self.setStyleSheet('PopupNotification { background-color: qlineargradient( x1:0 y1:0, x2:0 y2:1, stop:0 white, stop:1 gray); color: black; border: 1px solid black;  border-radius: 10px; }')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignCenter)
        fm = self.fontMetrics()

        width = fm.averageCharWidth() * 50
        self.setFixedSize(width, fm.height() * 4)

        log('%s: %s\n'%(tm.main.notification, text))

        for v in text.split():
            r = fm.elidedText(v, Qt.ElideMiddle, width).replace(u'\u2026', '...')
            text = text.replace(v, r)

        self.setText(text)
        self.setToolTip(tm.main.click_to_close)
        self.show()

        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, 'opacity');
        self.animation.setDuration(self.duration)
        self.animation.setStartValue(0.0)
        self.animation.setKeyValueAt(self.fadeduration/self.duration, 0.75)
        self.animation.setKeyValueAt((self.duration - self.fadeduration)/self.duration, 0.75)
        self.animation.setEndValue(0)
        self.animation.finished.connect(lambda: appdata.topwindow.RemoveNotify(self))
        self.animation.start()

    def MoveTo(self, point):
        if not self.move_animation:
            self.move_animation = QPropertyAnimation(self, 'pos');
            self.move_animation.setDuration(self.moveduration)
        else:
            self.move_animation.stop()

        self.move_animation.setStartValue(self.pos())
        self.move_animation.setEndValue(point)
        self.move_animation.start()

    def mousePressEvent(self, evt):
        QLabel.mousePressEvent(self, evt)
        if self.animation.currentTime() < self.duration - self.fadeduration:
            self.animation.setCurrentTime(self.duration - self.fadeduration)

class Workbench(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        appdata.topwindow = self
        self.SetTitle(None)
        #self.statusBar()
        framework.menu.AssignMenuBar(self, 'workbench.menubar')
        self.toolbar = framework.menu.MakeToolBar(self, 'workbench.maintoolbar', 'Toolbar')
        self.toolbar.setObjectName('MainToolbar')
        self.addToolBar(self.toolbar)
        self.setDockNestingEnabled(True)
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        #props window
        self.propsdock = QDockWidget(tm.main.properties, self)
        #pros window steals focus on undock
        self.propsdock.focusNextPrevChild = lambda next: True
        self.propsdock.setObjectName('Properties')
        self.props = framework.props.PropsView(self)
        self.propsdock.setWidget(self.props)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.propsdock)

        #project window
        self.projectdock = QDockWidget(tm.main.project, self)
        self.projectdock.setObjectName('Project')
        self.project = framework.project.ProjectView(self)
        self.projectdock.setWidget(self.project)
        self.projectdock.setWindowFlags(Qt.WindowMaximizeButtonHint)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.projectdock)

        #console
        self.consoledock = QDockWidget(tm.main.console, self)
        self.consoledock.setObjectName('Console')
        self.console = framework.python_console.PythonConsole(self.consoledock)
        self.consoledock.setWidget(self.console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.consoledock, Qt.Horizontal)

        #work area
        self.workarea = QMainWindow(self)
        self.workarea.setWindowFlags(Qt.Widget);
        self.setCentralWidget(self.workarea)
        self.workarea.setTabShape(QTabWidget.Triangular)
        self.workarea.setDockNestingEnabled(True)
        # dummy = QWidget(self.workarea)
        # self.workarea.setCentralWidget(dummy)
        # dummy.hide()

        #start page
        self.startpage = StartPage(self.workarea)
        self.workarea.addDockWidget(Qt.RightDockWidgetArea, self.startpage, Qt.Horizontal)
        self.workarea.setStyleSheet('QTabBar::tab:!selected { color:gray; }')

        #status bar
        self.statusbar = QStatusBar(self)

        def f(evt):
            QStatusBar.moveEvent(self.statusbar, evt)
            self.UpdateNotifications()

        self.statusbar.moveEvent = f
        self.setStatusBar(self.statusbar)

        self.statuses = []
        status_text = QLabel("", self.statusbar)
        status_text.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statuses.append(status_text)
        self.statusbar.addWidget(status_text, 1)

        self.notifications = []

        appdata.app.SetFontSize(appconfig.get('fontsize', 1))

        settings = QSettings("TechInvestLab.ru", "dot15926 application data")
        if settings.contains("screen_number") and settings.contains("window_geometry") and settings.contains("window_state"):
            screen = settings.value("screen_number")
            if QApplication.desktop().screenCount() <= screen:
                screen = -1
            rect = QApplication.desktop().screenGeometry(screen)
            self.move(rect.topLeft())
            self.restoreGeometry(settings.value("window_geometry"))
            self.restoreState(settings.value("window_state"))

        @public.mth
        def f():
            pf = appconfig.get('projectfile', '')
            if pf:
                pf = pf.decode('utf-8')
            appdata.project.OpenProjectFile(pf)
            # else:
            #     appdata.project.NewProject()

    def changeEvent(self, evt):
        if evt.type() == QEvent.ActivationChange:
            if not self.isActiveWindow():
                self.setFocus()
        QMainWindow.changeEvent(self, evt)

    def resizeEvent(self, evt):
        QMainWindow.resizeEvent(self, evt)
        self.UpdateNotifications()

    def SetStatus(self, text):
        if getattr(self, 'statuses', None):
            self.statuses[0].setText(text)

    def AddNotify(self, text, duration = 10000):
        notify = PopupNotification(text, duration)
        notify.move(self.rect().right() - notify.frameGeometry().width(), self.statusbar.pos().y())
        self.notifications.append(notify)
        self.UpdateNotifications()

    def RemoveNotify(self, popup):
        self.notifications.remove(popup)
        popup.close()
        self.UpdateNotifications()

    def UpdateNotifications(self):
        x = self.rect().right()
        y = self.statusbar.pos().y()
        for v in reversed(self.notifications):
            y -= v.frameGeometry().height()
            v.MoveTo(QPoint(x - v.frameGeometry().width(), y))

    def GetStatus(self):
        return self.statuses[0].text()

    def SetTitle(self, text):
        if text:
            self.setWindowTitle('{0} - {1}'.format(text, appdata.app.vis_label))
        else:
            self.setWindowTitle(appdata.app.vis_label)

    def closeEvent(self, evt):
        if not self.project.CloseProject(True):
            evt.ignore()
        else:
            settings = QSettings("TechInvestLab.ru", "dot15926 application data")
            screen = QApplication.desktop().screenNumber(self)
            settings.setValue("screen_number", screen)
            settings.setValue("window_geometry", self.saveGeometry())
            settings.setValue("window_state", self.saveState())
            evt.accept()




