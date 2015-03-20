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




from iso15926.tools.environment import EnvironmentContext
from PySide.QtCore import *
from PySide.QtGui import *
import os
from framework.dialogs import Choice

class TestWindow(QDialog):
    vis_label = tm.main.tests_title
    tests_dir = 'tests'

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)

        layout = QVBoxLayout(self)
        box = QGroupBox(tm.main.tests_field, self)

        self.tests_list = QListWidget(box)
        boxlayout = QHBoxLayout(box)
        boxlayout.addWidget(self.tests_list)
        layout.addWidget(box)

        for n in os.listdir(self.tests_dir):
            if n.startswith(".") or not n.endswith('.py'):
                continue

            sp = os.path.splitext(n)
            item = QListWidgetItem(sp[0], self.tests_list)
            item.setCheckState(Qt.Unchecked)

    
        self.btn_prepare = QPushButton(tm.main.prepare, self)
        self.btn_prepare.setToolTip(tm.main.prepare_selected_tests)
        self.btn_prepare.clicked.connect(self.OnPrepare)

        self.btn_run = QPushButton(tm.main.run, self)
        self.btn_run.setToolTip(tm.main.run_selected_tests)
        self.btn_run.clicked.connect(self.OnRun)


        self.btn_sel_all = QPushButton(tm.main.select_all, self)
        self.btn_sel_all.clicked.connect(self.SelectAll)

        self.btn_unsel_all = QPushButton(tm.main.unselect_all, self)
        self.btn_unsel_all.clicked.connect(self.UnselectAll)

        self.btn_cancel = QPushButton(tm.main.cancel, self)
        self.btn_cancel.clicked.connect(self.reject)

        btnlayout = QHBoxLayout()
        btnlayout.addWidget(self.btn_sel_all)
        btnlayout.addWidget(self.btn_unsel_all)
        btnlayout.addStretch()
        btnlayout.addWidget(self.btn_prepare)
        btnlayout.addWidget(self.btn_run)
        btnlayout.addWidget(self.btn_cancel)
        layout.addLayout(btnlayout)

        box = QGroupBox(tm.main.tests_result_field, self)
        self.report = QPlainTextEdit(self)
        boxlayout = QHBoxLayout(box)
        boxlayout.addWidget(self.report)
        layout.addWidget(box)
        self.exec_()

    def SelectAll(self):
        self.tests_list.SetChecked([x for x in xrange(self.tests_list.Count)])

    def UnselectAll(self):
        self.tests_list.SetChecked([])

    def OnPrepare(self):
        if Choice(tm.main.tests_prepare_warning):
            for k in self.tests_list.CheckedStrings:
                self.report.AppendText(tm.main.tests_preparing.format(k))
                locals = {'mode': 'prepare'}
                ec = EnvironmentContext(None, locals)
                ec.ExecutePythonFile(os.path.join(self.tests_dir, k + '.py'))
            self.report.AppendText(tm.main.tests_preparing_done)

    def OnRun(self):
        all_passed = True
        self.report.appendPlainText(tm.main.tests_running)
        count = 0
        passed = 0

        for i in xrange(self.tests_list.count()):
            item = self.tests_list.item(i)
            name = item.text()
            if not item.checkState() == Qt.Checked:
                continue

            count += 1
            locals = {'mode': 'run', 'passed': False}
            ec = EnvironmentContext(None, locals)

            ec.ExecutePythonFile(os.path.join(self.tests_dir, name + '.py'))

            if locals['passed']:
                passed += 1
                self.report.appendPlainText(tm.main.test_passed.format(name))
            else:
                self.report.appendPlainText(tm.main.test_failed.format(name))

        self.report.appendPlainText(tm.main.tests_result)
        self.report.appendPlainText(tm.main.tests_result_info.format(passed, count))


if os.path.exists(TestWindow.tests_dir):
    @public('workbench.menu.help')
    class xTestMenu:
        vis_label = tm.main.menu_tests
        @classmethod
        def Do(cls):
            TestWindow()
