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
import framework.appconfig
import os
import framework.dialogs
import sys
from framework.util import FileBrowseButton
import site

class Settings_PathsPage(QWidget):

    msg_part4  = tm.main.settings_part4
    msg_pcardl = tm.main.settings_pcardl
    msg_p7tpl  = tm.main.settings_p7tpl

    def __init__(self, parent):
        QWidget.__init__(self, parent)

        box = QGroupBox(tm.main.py_search_paths, self)
        self.pypath = QPlainTextEdit(box)
        self.pypath.setPlainText(os.pathsep.join(appconfig.get('sys.path', [])))

        layout = QVBoxLayout(self)
        layout.addWidget(box)

        box_layout = QVBoxLayout(box)
        box_layout.addWidget(self.pypath)

        box = QGroupBox(tm.main.settings_common_file_paths, self)

        self.part4_path = FileBrowseButton(box, appconfig.get('cfg://part4', ''))
        self.pcardl_path = FileBrowseButton(box, appconfig.get('cfg://pca_rdl', ''))
        self.p7tpl_path = FileBrowseButton(box, appconfig.get('cfg://p7tpl', ''))

        grid = QGridLayout(box)
        grid.addWidget(QLabel(self.msg_part4, self), 0, 0)
        grid.addWidget(self.part4_path, 0, 1)
        grid.addWidget(QLabel(self.msg_pcardl, self), 1, 0)
        grid.addWidget(self.pcardl_path, 1, 1)
        grid.addWidget(QLabel(self.msg_p7tpl, self), 2, 0)
        grid.addWidget(self.p7tpl_path, 2, 1)
        
        layout.addWidget(box)

    def Apply(self):
        newpaths = self.pypath.toPlainText().split(os.pathsep)
        sys.path = appdata.path
        for v in newpaths:
            site.addsitedir(v.encode(sys.getfilesystemencoding()))
        appconfig['sys.path'] = newpaths
        appconfig['cfg://part4'] = str(self.part4_path.GetPath())
        appconfig['cfg://pca_rdl'] = str(self.pcardl_path.GetPath())
        appconfig['cfg://p7tpl'] = str(self.p7tpl_path.GetPath())

        appconfig.SaveSettings()

        return False

class Settings_GeneralPage(QWidget):


    def __init__(self, parent):
        QWidget.__init__(self, parent)

        box = QGroupBox(tm.main.settings_enabled_extensions, self)

        extensions_dict = appconfig.get('extensions', {})

        self.extensions = QListWidget(self)

        for k, v in extensions_dict.iteritems():
            item = QListWidgetItem(k, self.extensions)

            if v:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

            self.extensions.addItem(item)

        layout = QVBoxLayout(self)

        layout.addWidget(box)
        layout_box = QVBoxLayout(box)
        layout_box.addWidget(self.extensions)

        self.languages = QComboBox(self)
        current_lang = appconfig.get('language', 'en')
        for code, lang in tm._get_languages():
            self.languages.addItem(QIcon(), lang)
            if code == current_lang:
                self.languages.setCurrentIndex(self.languages.count()-1)

        grid = QGridLayout()
        grid.addWidget(QLabel(tm.main.language, self), 0, 0)
        grid.addWidget(self.languages, 0, 1)

        layout.addLayout(grid)

    def Apply(self):
        extensions_dict = appconfig.get('extensions', {})
        changed = False

        for i in xrange(self.extensions.count()):
            item = self.extensions.item(i)
            name = item.text()
            checked = item.checkState() == Qt.Checked
            if extensions_dict[name] != checked:
                changed = True
                extensions_dict[name] = checked

        if tm._get_languages()[self.languages.currentIndex()][0] != appconfig.get('language', 'en'):
            appconfig['language'] = tm._get_languages()[self.languages.currentIndex()][0]
            changed = True

        appconfig.SaveSettings()
        return changed

class SettingsDialog(QDialog):

    vis_label = tm.main.settings
    msg_restart_required = tm.main.settings_restart_required

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)

        notebook = QTabWidget(self)
       
        layout = QVBoxLayout(self)
        layout.addWidget(notebook)

        self.btn_ok = QPushButton(tm.main.ok, self)
        self.btn_ok.setDefault(True)
        self.btn_cancel = QPushButton(tm.main.cancel, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)
        layout.addLayout(layout_btn)
        
        notebook.addTab(Settings_GeneralPage(notebook), tm.main.general)
        notebook.addTab(Settings_PathsPage(notebook), tm.main.paths)

        if self.exec_()==QDialog.Accepted:
            restart_needed = False
            for i in xrange(notebook.count()):
                if notebook.widget(i).Apply():
                    restart_needed = True
            if restart_needed:
                framework.dialogs.Notify(self.msg_restart_required)

class PatternsSelection(QDialog):
    vis_label = tm.main.settings
    
    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)
        