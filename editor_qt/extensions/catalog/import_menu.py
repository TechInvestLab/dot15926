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
from extensions.catalog.importer import CatalogImporter
import iso15926.kb as kb
from iso15926.graph.graph_document import GraphDocument
from framework.document import Document
import framework


@public('workbench.menu.tools')
class xCatalogDependencies:
    vis_label = tm.ext.menu_catalog
    menu_content = 'workbench.menu.catalog'

@public('workbench.menu.catalog')
class xCatalogDependencies:
    vis_label = tm.ext.menu_setup_catalog

    @staticmethod
    def Do():
        DependenciesDialog()

@public('workbench.menu.catalog')
class xCatalogImport:
    vis_label = tm.ext.menu_import_catalog

    @staticmethod
    def Update(action):
        action.setEnabled(bool(appconfig.get('paths.p7tpl_catalog') and appconfig.get('paths.rdl_catalog') and appconfig.get('catalog.proj_ns')))

    @classmethod
    def Do(cls):
        path, wildcard = framework.dialogs.SelectFiles(cls.vis_label, multi=False)
        if not path:
            return

        doc_rdf = GraphDocument()
        doc_rdf.NewImport([path], CatalogImporter, **(dict(chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf_til)))
        appdata.project.AddDocument(doc_rdf)

from framework.util import FileBrowseButton

class DependenciesDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.ext.setup_catalog_title)

        self.p7tpl = FileBrowseButton(self, appconfig.get('paths.p7tpl_catalog', ''))
        self.pcardl = FileBrowseButton(self, appconfig.get('paths.rdl_catalog', ''))
        self.proj_ns = QLineEdit(appconfig.get('catalog.proj_ns', 'http://example.org/rdl/'), self)

        value = True if appconfig.get('catalog.attr_inheritance', 'True') == 'True' else False

        self.attr_inheritance = QCheckBox(self)
        self.attr_inheritance.setText(tm.ext.attr_inheritance)
        self.attr_inheritance.setChecked(value)

        grid = QGridLayout(self)
        grid.addWidget(QLabel(tm.ext.template_set_field, self), 0, 0)
        grid.addWidget(self.p7tpl, 0, 1)
        grid.addWidget(QLabel(tm.ext.rdl_field, self), 1, 0)
        grid.addWidget(self.pcardl, 1, 1)
        grid.addWidget(QLabel(tm.ext.ns_for_new_field, self), 2, 0)
        grid.addWidget(self.proj_ns, 2, 1)
        grid.addWidget(self.attr_inheritance, 3, 0, 1, 2)

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
            appconfig['paths.p7tpl_catalog'] = str(self.p7tpl.GetPath())
            appconfig['paths.rdl_catalog'] = str(self.pcardl.GetPath())
            appconfig['catalog.proj_ns'] = str(self.proj_ns.text())
            appconfig['catalog.attr_inheritance'] = str(self.attr_inheritance.isChecked())
            appconfig.SaveSettings()
