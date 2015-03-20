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




import iso15926.kb as kb
from framework.document import Document
from iso15926.kb.dmviews import XSDTypesView, Part2TypesView
from iso15926.io.sparql import SparqlConnection
from iso15926.graph.graph_document import GraphDocument
from iso15926.patterns.patterns_document import PatternsDocument
import framework.dialogs
import iso15926
from framework.docinfo import OpenDoc, GetDocSource, NameWithPrefix
from PySide.QtCore import *
from PySide.QtGui import *
import copy

@public('workbench.menubar')
class xBasics:
    vis_label = tm.main.menu_datatypes
    menu_content = 'workbench.menu.iso15926.basics'
    position = 5

@public('workbench.menu.iso15926.basics')
class xXMLView:
    vis_label = tm.main.menu_xmlschema
    @classmethod
    def Do(cls):
        appdata.project.AddView(XSDTypesView)

@public('workbench.menu.iso15926.basics')
class xPart2View:
    vis_label = tm.main.menu_part2
    @classmethod
    def Do(cls):
        appdata.project.AddView(Part2TypesView)

class SimpleOpen:
    params = dict()
    is_new_file = False # True for creating new file
    appconfig_file_path = None # for paths stored in appconfig
    sparql_path = None # for known endpoints
    is_other_sparql = False # True for unknown endpoints
    doctype = None

    @classmethod
    def Do(cls):
        doctype = GraphDocument if not cls.doctype else cls.doctype

        if cls.is_new_file:
            name = framework.dialogs.EnterText(tm.main.new_data_source, tm.main.data_source_name_field)
            if not name:
                return
            doc = doctype()
            doc.NewFile([], name = name, **cls.params)
        elif cls.appconfig_file_path:
            path = cls.appconfig_file_path
            if not appconfig.get(cls.appconfig_file_path).decode('utf-8'):
                path, wildcard = framework.dialogs.SelectFiles(cls.vis_label)
            if not path:
                return
            paths = [path]
            if not Document.VerifyEditablePaths([appconfig.get(v).decode('utf-8') if v.startswith('cfg://') else v for v in paths]):
                return
            doc = doctype()
            doc.OpenFiles(paths, **cls.params)
        elif not cls.sparql_path and not cls.is_other_sparql:
            # unknown file
            paths, wildcard = framework.dialogs.SelectFiles(cls.vis_label, multi=True)
            if not paths:
                return
            if not Document.VerifyEditablePaths(paths):
                return

            for p in list(paths):     
                if paths[0].endswith('.patt'):
                    doc = PatternsDocument()
                    doc.OpenFiles([p], **params)
                    self.AddDocument(doc)
                    paths.remove(p)

            if paths:
                doc = doctype()
                doc.OpenFiles(paths, **cls.params)
        elif cls.sparql_path:
            doc = doctype()
            doc.OpenSparql(SparqlConnection(cls.sparql_path), **cls.params)
        elif cls.is_other_sparql:
            dlg = iso15926.common.dialogs.OpenEndpoint(cls.vis_label)
            if not dlg.connection:
                return
            doc = doctype()
            doc.OpenSparql(dlg.connection, **cls.params)

        appdata.project.AddDocument(doc)

@public('workbench.menu.open')
class xOtherRDL(SimpleOpen):
    vis_label = tm.main.menu_open_rdl
    menu_sep = True
    params = dict(chosen_part2=kb.ns_dm_rds, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs+kb.annotations_meta, roles = kb.roles_std)

@public('workbench.menu.open')
class xPart4(SimpleOpen):
    vis_label = tm.main.menu_open_part4
    vis_help = tm.main.menu_open_part4_help
    appconfig_file_path = 'cfg://part4'
    params = dict(name='Part 4', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_old_part4, roles = kb.roles_std)

@public('workbench.menu.open')
class xPCARDL(SimpleOpen):
    vis_label = tm.main.menu_open_pcardl
    vis_help = tm.main.menu_open_pcardl_help
    appconfig_file_path = 'cfg://pca_rdl'
    params = dict(name='PCA RDL', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf, roles = kb.roles_std)

@public('workbench.menu.open')
class xPart8Templates(SimpleOpen):
    vis_label = tm.main.menu_open_part8
    vis_help = tm.main.menu_open_part8_help
    appconfig_file_path = 'cfg://p7tpl'
    menu_sep = True
    params = dict(name="Proto and initial templates", chosen_part2=kb.ns_dm_part8, module_name="p7tpl", namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf, roles = kb.roles_std)

@public('workbench.menu.open')
class xRecentSources:
    vis_label = tm.main.menu_recent_sources
    menu_content = True

    @staticmethod
    def Update(action):
        enabled = False
        for v in reversed(appconfig.setdefault('recent_sources', [])):
            if not v['info'].get('connection'):
                enabled = True
                break
        action.setEnabled(enabled)

    @staticmethod
    def Make(menu):
        menu.clear()
        recent = appconfig.setdefault('recent_sources', [])
        def f(menu, v):
            action = QAction(NameWithPrefix(v), menu)
            action.triggered.connect(lambda: OpenDoc(v))
            action.setStatusTip(GetDocSource(v))
            menu.addAction(action)

        for v in reversed(recent):
            if not v['info'].get('connection'):
                f(menu, v)
                enabled = True

@public('workbench.menu.openendpoint')
class xOtherSparqlRDL(SimpleOpen):
    vis_label = tm.main.menu_endpoint_open_rdl
    is_other_sparql = True
    menu_sep = True
    params = dict(chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs+kb.annotations_meta, roles = kb.roles_std)

@public('workbench.menu.openendpoint')
class xPCARDLSparql(SimpleOpen):
    vis_label = tm.main.menu_endpoint_open_pcarld
    vis_help = "http://posccaesar.org/endpoint/sparql"
    sparql_path = "http://posccaesar.org/endpoint/sparql"
    params = dict(name='PCA RDL SPARQL', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_sparql, roles = kb.roles_pcardl_sparql)

@public('workbench.menu.openendpoint')
class xIringRdl(SimpleOpen):
    vis_label = tm.main.menu_endpoint_open_iring_rdl
    vis_help = "http://www.iringsandbox.org/repositories/SandboxPt8/query"
    sparql_path = "http://www.iringsandbox.org/repositories/SandboxPt8/query"
    params = dict(name='iRING Sandbox SPARQL', chosen_part2=kb.ns_dm_rds, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs, roles = kb.roles_std)

@public('workbench.menu.openendpoint')
class xIIPTpl(SimpleOpen):
    vis_label = tm.main.menu_open_IIP_templates
    vis_help = "http://posccaesar.org/sandbox/iip/sparql"
    sparql_path = "http://posccaesar.org/sandbox/iip/sparql"
    params = dict(name='IIP Sandbox SPARQL (Templates)', chosen_part2=kb.ns_dm_rds, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs, roles = kb.roles_std)


@public('workbench.menu.openendpoint')
class xTechInvestLab(SimpleOpen):
    vis_label = tm.main.menu_endpoint_open_tilrdl
    vis_help = "http://rdl.techinvestlab.ru:8891/sparql"
    sparql_path = "http://rdl.techinvestlab.ru:8891/sparql"
    params = dict(name='TechInvestLab Sandbox SPARQL', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf_til, roles = kb.roles_std)
    menu_sep = True
    
@public('workbench.menu.openendpoint')
class xRecentSourcesSparql:
    vis_label = tm.main.menu_recent_sources
    menu_content = True

    @staticmethod
    def Update(action):
        enabled = False
        for v in reversed(appconfig.setdefault('recent_sources', [])):
            if v['info'].get('connection'):
                enabled = True
                break
        action.setEnabled(enabled)

    @staticmethod
    def Make(menu):
        menu.clear()
        recent = appconfig.setdefault('recent_sources', [])

        def f(menu, v):
            action = QAction(NameWithPrefix(v), menu)
            action.triggered.connect(lambda: OpenDoc(v))
            action.setStatusTip(GetDocSource(v))
            menu.addAction(action)

        for v in reversed(recent):
            if v['info'].get('connection'):
                f(menu, v)
                enabled = True

@public('workbench.menu.new')
class xNewRDL(SimpleOpen):
    vis_label = tm.main.menu_new_rdl
    is_new_file = True
    params = dict(chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std_meta, annotations=kb.annotations_rdfs+kb.annotations_meta, roles = kb.roles_std)

@public('workbench.menu.new')
class xNewPatterns(SimpleOpen):
    vis_label = tm.main.menu_new_patterns
    is_new_file = True
    doctype = PatternsDocument
    params = dict()

