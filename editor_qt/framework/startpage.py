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
import sys
from framework.docinfo import GetDocSource, OpenDoc, NameWithPrefix
from framework.view import View

class StartPage(View):
    vis_label = tm.main.startpage

    def __init__(self, parent):
        View.__init__(self, parent)

        self.SetTitle(self.vis_label)
        frame = QFrame(self)

        img = appdata.resources_dir + '/images/grid.png'
        frame.setStyleSheet('background-image: url({0})'.format(img))
        self.text = QTextBrowser(frame)
        self.text.setStyleSheet('border: 0;')
        self.text.anchorClicked.connect(self.OnLinkClicked)
        self.text.highlighted[str].connect(self.OnLinkHighlighted)
        self.text.setOpenLinks(False)
        self.text.contextMenuEvent = lambda evt: evt.accept()
        layout = QHBoxLayout(frame)
        layout.addWidget(self.text)
        layout.setContentsMargins(0,0,0,0)
        self.setWidget(frame)
        self.Refresh()

    def Refresh(self):
        self.recent_projects_list = appconfig.setdefault('recent_projects', [])
        recent_projects = str()
        for idx in xrange(len(self.recent_projects_list)-1, -1, -1):
            projname, ext = os.path.splitext(os.path.basename(self.recent_projects_list[idx]))
            recent_projects += '<a href="project|{0}|{1}">{2}</a><br>'.format(idx, self.recent_projects_list[idx], projname) 

        self.recent_sources_list = appconfig.setdefault('recent_sources', [])
        recent_sources = str()
        for idx in xrange(len(self.recent_sources_list)-1, -1, -1):
            v = self.recent_sources_list[idx]
            recent_sources += '<a href="source|{0}|{1}">{2}</a><br>'.format(idx, GetDocSource(v), NameWithPrefix(v))  

        self.text.setHtml('''
            <html>
            <body style = "font-size: large">
            <h1>.15926 Editor</h1>
            <h3>{0}</h3>
            <br>
            {1}
            <h3>{2}</h3>
            <br>
            {3}
            </body>
            </html>
            '''.format(tm.main.startpage_recent_projects, recent_projects, tm.main.startpage_recent_sources, recent_sources))

    def OnLinkClicked(self, url):
        params = url.toString().split('|')
        if params[0] == 'project':
            appdata.project.OpenProjectFile(self.recent_projects_list[int(params[1])])
        elif params[0] == 'source':
            doc = OpenDoc(self.recent_sources_list[int(params[1])])
            if doc:
                appdata.project.AddDocument(doc)

    def OnLinkHighlighted(self, url):
        if url:
            self.setToolTip('{0}'.format(url.split('|')[-1]))
        else:
            self.setToolTip('')
