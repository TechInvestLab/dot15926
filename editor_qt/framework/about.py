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
import requests
import re
import framework.dialogs

class AboutBox(QDialog):

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)

        self.setWindowTitle('%s %s'%(tm.main.about, appdata.app.vis_label))
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(appdata.app.vis_label, self))
        layout.addWidget(QLabel(tm.main.copyright, self))
        layout.addWidget(QLabel(tm.main.distribution, self))

        text = QLabel('<a href="http://community.livejournal.com/dot15926/profile">%s</a>'%tm.main.community, self)
        text.setTextFormat(Qt.RichText)
        text.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text.setOpenExternalLinks(True)
        layout.addWidget(text)

        button = QPushButton(tm.main.ok, self)
        layout.addWidget(button, 0, Qt.AlignRight)

        button.setDefault(True)
        button.clicked.connect(self.accept)
        self.exec_()


@public('workbench.menu.help')
class xAbout:
    vis_label = tm.main.menu_about
    @staticmethod
    def Do():
        AboutBox()



@public('workbench.menu.help')
class xVersionCheck:
    vis_label = tm.main.version_check
    @staticmethod
    def Do():
        try:
            r = requests.get('http://techinvestlab.ru/editorversioninfo')
            if r.status_code == 200:
                m = re.search(r'(version) (\d+.\d+)', r.content)
                if m != None:
                    version = float(m.group(2))
                    if version > appdata.app_version:
                        if framework.dialogs.Choice(tm.main.update_version_question.format(version)):
                            QDesktopServices.openUrl('http://techinvestlab.ru/dot15926Editor')
                    else:
                        framework.dialogs.Notify(tm.main.latest_version)
            else:
                raise
        except:
            framework.dialogs.Notify(tm.main.version_check_failed)
