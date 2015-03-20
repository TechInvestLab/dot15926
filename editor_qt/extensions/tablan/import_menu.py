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

from PySide.QtCore import *
from PySide.QtGui import *
from framework.util import FileBrowseButton
from extensions.tablan.importer import TabLanImporter
import iso15926.kb as kb
import framework

from iso15926 import GraphDocument

from framework.document import Document
import framework.dialogs

@public('workbench.menu.tools')
class xCatalogDependencies:
    vis_label = tm.ext.menu_tablan
    menu_content = 'workbench.menu.tablan'

@public('workbench.menu.tablan')
class xTabLanDependencies:
    vis_label = tm.ext.menu_setup_tablan

    @staticmethod
    def Do():
        DependenciesDialog()

@public('workbench.menu.tablan')
class xTabLanImport:
    vis_label = tm.ext.menu_import_tablan

    @staticmethod
    def Update(action):
        action.setEnabled(bool(appconfig.get('paths.p7tpl_tablan') and appconfig.get('paths.rdl_tablan') and appconfig.get('tablan.proj_ns')))

    @classmethod
    def Do(cls):
        path, wildcard = framework.dialogs.SelectFiles(cls.vis_label, multi=False)
        if not path:
            return

        doc_rdf = GraphDocument()
        doc_rdf.NewImport([path], TabLanImporter, **(dict(chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf_til)))
        appdata.project.AddDocument(doc_rdf)


class DependenciesDialog(QDialog):
    vis_label = 'Setup TabLan dependencies...'
    msg_p7tpl =  "Template set:"
    msg_pcardl = "RDL:"
    msg_ns    = "Namespace for new entities:"

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.ext.setup_tablan_title)

        self.p7tpl = FileBrowseButton(self, appconfig.get('paths.p7tpl_tablan', ''))
        self.pcardl = FileBrowseButton(self, appconfig.get('paths.rdl_tablan', ''))
        self.proj_ns = QLineEdit(appconfig.get('tablan.proj_ns', 'http://example.org/rdl/'), self)

        grid = QGridLayout(self)
        grid.addWidget(QLabel(tm.ext.template_set_field, self), 0, 0)
        grid.addWidget(self.p7tpl, 0, 1)
        grid.addWidget(QLabel(tm.ext.rdl_field, self), 1, 0)
        grid.addWidget(self.pcardl, 1, 1)
        grid.addWidget(QLabel(tm.ext.ns_for_new_field, self), 2, 0)
        grid.addWidget(self.proj_ns, 2, 1)

        self.btn_ok = QPushButton(tm.ext.ok, self)
        self.btn_ok.setDefault(True)
        self.btn_cancel = QPushButton(tm.ext.cancel, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)

        grid.addLayout(layout_btn, 4, 0, 1, 2)

        if self.exec_()==QDialog.Accepted:
            appconfig['paths.p7tpl_tablan'] = str(self.p7tpl.GetPath())
            appconfig['paths.rdl_tablan'] = str(self.pcardl.GetPath())
            appconfig['tablan.proj_ns'] = str(self.proj_ns.text())
            appconfig.SaveSettings()

