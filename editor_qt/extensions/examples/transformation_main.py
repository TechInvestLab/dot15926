"""Copyright 2012 TechInvestLab.ru dot15926@gmail.com

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

import extensions.examples.example_menu
from iso15926 import EnvironmentContext, GraphDocument
import framework.dialogs
from PySide.QtCore import *
from PySide.QtGui import *
from framework.util import FileBrowseButton
import os
from iso15926 import kb

class SetupTransformationDialog(QDialog):
    vis_label = 'Setup source and destination...'

    msg_source           = 'Source:'
    msg_destionation     = 'Destrination:'

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)

        self.source = FileBrowseButton(self)
        self.destionation = FileBrowseButton(self)

        grid = QGridLayout(self)
        grid.addWidget(QLabel(self.msg_source, self), 0, 0)
        grid.addWidget(self.source, 0, 1)
        grid.addWidget(QLabel(self.msg_destionation, self), 1, 0)
        grid.addWidget(self.destionation, 1, 1)

        self.btn_ok = QPushButton('Ok', self)
        self.btn_ok.setDefault(True)
        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)

        grid.addLayout(layout_btn, 2, 0, 1, 2)

        if self.exec_()==QDialog.Accepted:
            appconfig['paths.trans_sample_source'] = str(self.source.GetPath())
            appconfig['paths.trans_sample_destination'] = str(self.destionation.GetPath())
            appconfig.SaveSettings()

@public('dot15926.menu.example_menu')
class xTransformationMenuItem1:
    vis_label = 'Setup source and destination...'

    @staticmethod
    def Do():
        SetupTransformationDialog()

@public('dot15926.menu.example_menu')
class xTransformationMenuItem2:
    vis_label = 'Do transformation'

    @staticmethod
    def Update(action):
        action.setEnabled(bool(appconfig.get('paths.trans_sample_source') and appconfig.get('paths.trans_sample_destination') and appconfig.get('tablan.trans_sample_script')))

    @staticmethod
    def Do():
        Transformation()

class Transformation:

    def __init__(self):

        self.source_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.trans_sample_source')])
        if not self.source_doc:
            self.source_doc = GraphDocument()
            param = dict(module_name='jord', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf)
            self.source_doc.OpenFiles([appconfig.get('paths.trans_sample_source')], **param)
            appdata.project.AddDocument(self.source_doc)

        self.dest_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.trans_sample_destination')])
        if not self.dest_doc:
            self.dest_doc = GraphDocument()
            param = dict(module_name='new_data', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std_meta, annotations=kb.annotations_rdfs+kb.annotations_meta)
            if os.path.exists(appconfig.get('paths.trans_sample_destination')):
                self.dest_doc.OpenFiles([appconfig.get('paths.trans_sample_destination')], **param)
            else:
                self.dest_doc.NewFile(appconfig.get('paths.trans_sample_destination'), **param)            
            appdata.project.AddDocument(self.dest_doc)

        ready = True

        if not self.source_doc.CanView():
            wizard.Subscribe(self.source_doc, self)
            ready = False

        if not self.dest_doc.CanView():
            wizard.Subscribe(self.dest_doc, self)
            ready = False

        if ready:
            appdata.app.After(self.DoTransformation)

    def W_DocumentStateChanged(self, doc):
        if doc.CanView(): 
            wizard.Unsubscribe(doc, self)

        elif doc.IsUnavailable():
            log('Transformation error: {0} unavailable!\n', doc.name)
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            wizard.Unsubscribe(doc, self)

        if self.source_doc.CanView() and self.dest_doc.CanView():
            appdata.app.After(self.DoTransformation)

    def DoTransformation(self):
        context = EnvironmentContext(None, {})
        context.ExecutePythonFile(os.path.join('extensions','examples','transformation_commands.py'))