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
from extensions.geomtempl.importer import GeomImporter
import iso15926.kb as kb
import framework
from iso15926 import GraphDocument
import framework.dialogs

@public('workbench.menu.tools')
class xGeomImport:
    vis_label = tm.ext.menu_import_geom

    @staticmethod
    def Do():
        SetupImportDialog()

class SetupImportDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.ext.import_geom_title)

        self.proj_ns = QLineEdit(appconfig.get('geom.proj_ns', 'http://example.org/tpl#'), self)

        self.name_uri = QCheckBox(self)
        self.name_uri.setText(tm.ext.uri_for_new_field)
        self.name_uri.setChecked(bool(appconfig.get('geom.uri_from_names', True)))

        grid = QGridLayout(self)
        grid.addWidget(QLabel(tm.ext.ns_for_new_field, self), 0, 0)
        grid.addWidget(self.proj_ns, 0, 1)
        grid.addWidget(self.name_uri, 1, 0, 1, 2)

        self.btn_ok = QPushButton(tm.ext.ok, self)
        self.btn_ok.setDefault(True)
        self.btn_cancel = QPushButton(tm.ext.cancel, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)

        grid.addLayout(layout_btn, 2, 0, 1, 2)

        if self.exec_()==QDialog.Accepted:
            appconfig['geom.proj_ns'] = str(self.proj_ns.text())
            appconfig['geom.uri_from_names'] = self.name_uri.isChecked()
            appconfig.SaveSettings()

            path, wildcard = framework.dialogs.SelectFiles(tm.ext.select_xlsx, multi=False)
            if not path:
                return

            doc_template = GraphDocument()
            doc_template.NewImport([path], GeomImporter, **(dict(chosen_part2=kb.ns_dm_rds, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs_ex, basens=str(self.proj_ns.text()), uri_from_names=self.name_uri.isChecked())))
            appdata.project.AddDocument(doc_template)

