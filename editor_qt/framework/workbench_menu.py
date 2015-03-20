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




import framework.menu
import framework.python_console
import framework.about
import framework.dialogs
import framework.util as util
from framework.document import Document
import framework.settings
import os
from PySide.QtCore import *
from PySide.QtGui import *
import copy
from iso15926.graph.graph_document import GraphDocument
from iso15926.io.rdf_graph import RdfDiff

def FindProjectNodesMethod(methodname):
    v = appdata.project
    if not v:
        return
    v = v.selected
    if not v:
        return
    v = util.findcommonmethod(v, methodname)
    return v

def CallProjectNodesMethod(methodname, *t, **kw):
    v = FindProjectNodesMethod(methodname)
    if not v:
        return
    return v(*t, **kw)

def FindViewMethod(methodname):
    v = appdata.active_view

    if not v:
        return

    if getattr(v, 'FindViewMethod'):
        return v.FindViewMethod(methodname)

    return

def CallViewMethod(methodname, *t, **kw):
    v = FindViewMethod(methodname)
    if v:
        return v(*t, **kw)

def FindDocumentMethod(methodname):
    d = appdata.active_document
    if d:
        m = getattr(d, methodname, None)
        if m:
            return m
    return

def CallDocumentMethod(methodname, *t, **kw):
    d = appdata.active_document
    if d:
        m = getattr(d, methodname, None)
        if m:
            return m(*t, **kw)
    return


@public('workbench.menubar')
class xFile:
    vis_label = tm.main.menu_file
    menu_content = 'workbench.menu.file'
    position = 1

@public('workbench.menubar')
class xView:
    vis_label = tm.main.menu_view
    menu_content = 'workbench.menu.view'
    position = 3

@public('workbench.menu.file')
class xProject:
    vis_label = tm.main.menu_project
    menu_content = 'workbench.menu.project'
    menu_sep = True

@public('workbench.menu.file')
class xNew:
    vis_label = tm.main.menu_new
    menu_block = 'workbench.menu.new'

@public('workbench.menu.file')
class xOpen:
    vis_label = tm.main.menu_open
    menu_content = 'workbench.menu.open'

@public('workbench.menu.file')
class xOpenSparql:
    vis_label = tm.main.menu_open_endpoint
    menu_content = 'workbench.menu.openendpoint'
    menu_sep = True

@public('workbench.menu.project')
class xNewProject:
    vis_label = tm.main.menu_new_project
    menu_shortcut = 'Ctrl+Shift+N'
    @staticmethod
    def Do():
        appdata.project.NewProject()

@public('workbench.menu.project')
class xOpenProject:
    vis_label = tm.main.menu_open_project
    menu_shortcut = 'Ctrl+Shift+O'
    @staticmethod
    def Do():
        appdata.project.OpenProject()

@public('workbench.menu.project', 'workbench.contextmenu.project_node')
class xSaveProject:
    vis_label = tm.main.menu_save_project
    @staticmethod
    def Update(action):
        action.setEnabled(appdata.project.CanSaveProject() and not appdata.project.ProjectSaved())

    @staticmethod
    def Do():
        appdata.project.SaveProject()


@public('workbench.menu.project', 'workbench.contextmenu.project_node')
class xSaveProjectAs:
    vis_label = tm.main.menu_save_project_as
    @staticmethod
    def Do():
        appdata.project.SaveProjectAs()

@public('workbench.contextmenu.project_node')
class xProjectAddFolder:
    vis_label = tm.main.menu_project_folder_add
    @staticmethod
    def Do():
        appdata.project.AddFolder(tm.main.project_new_folder)

@public('workbench.menu.project')
class xRecentProjects:
    vis_label = tm.main.menu_recent_projects
    menu_content = True

    @staticmethod
    def Update(action):
        action.setEnabled(bool(appconfig.setdefault('recent_projects', [])))

    @staticmethod
    def Make(menu):
        menu.clear()
        recent = appconfig.setdefault('recent_projects', [])
        def f(menu, v):
            projname, ext = os.path.splitext(os.path.basename(v))
            action = QAction(projname, menu)
            action.triggered.connect(lambda: appdata.project.OpenProjectFile(v))
            action.setStatusTip(v)
            menu.addAction(action)

        for v in reversed(recent):
            f(menu, v)

@public('workbench.contextmenu.project')
class xOpenDataSource:
    vis_label = tm.main.menu_open_view
    @staticmethod
    def Do():
        CallProjectNodesMethod('OpenView')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindProjectNodesMethod('OpenView')))

@public('workbench.menu.file', 'workbench.contextmenu.project', 'workbench.maintoolbar')
class xSave:
    vis_label = tm.main.menu_save
    menu_shortcut = 'Ctrl+S'
    vis_icon = 'disk_blue'

    @staticmethod
    def Do():
        CallDocumentMethod('Save')
    @staticmethod
    def Update(action):
        enabled = bool(CallDocumentMethod('CanSave'))
        action.setEnabled(enabled)
        if enabled:
            fm = appdata.app.fontMetrics()
            width = fm.averageCharWidth() * 80
            text = fm.elidedText(str(CallDocumentMethod('GetName')), Qt.ElideMiddle, width).replace(u'\u2026', '...')
            action.setText('{0} {1}'.format(xSave.vis_label, text))
        else:
            action.setText('{0}'.format(xSave.vis_label))   
            
@public('workbench.menu.file', 'workbench.contextmenu.project')
class xSaveAs:
    vis_label = tm.main.menu_save_as
    msg_save_item_as = tm.main.menu_save_item_as
    menu_shortcut = 'Ctrl+Shift+S'

    @staticmethod
    def Do():
        CallDocumentMethod('SaveAs')
    @staticmethod
    def Update(action):
        enabled = bool(CallDocumentMethod('CanSaveAs'))
        action.setEnabled(enabled)
        if enabled:
            fm = appdata.app.fontMetrics()
            width = fm.averageCharWidth() * 80
            text = fm.elidedText(str(CallDocumentMethod('GetName')), Qt.ElideMiddle, width).replace(u'\u2026', '...')
            action.setText(xSaveAs.msg_save_item_as.format(text))
        else:
            action.setText(xSaveAs.vis_label)   

@public('workbench.menu.file', 'workbench.contextmenu.project', 'workbench.maintoolbar')
class xSaveAll:
    vis_label = tm.main.menu_save_all
    menu_shortcut = 'Ctrl+Alt+S'
    vis_icon = 'disks'

    @staticmethod
    def Do():
        Document.SaveAll()
        if appdata.project.CanSaveProject():
            appdata.project.SaveProject()
        else:
            appdata.project.SaveProjectAs()
    @staticmethod
    def Update(action):
        action.setEnabled(Document.CanSaveAll() or not appdata.project.ProjectSaved())

@public('workbench.menu.file', 'workbench.contextmenu.project')
class xSaveSnapshot:
    vis_label = tm.main.menu_save_snapshot
    menu_shortcut = 'Alt+S'
    menu_sep = True
    @staticmethod
    def Do():
        CallDocumentMethod('SaveSnapshot')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanSaveSnapshot')))

@public('workbench.contextmenu.project')
class xCompareTo:
    vis_label = tm.main.menu_compare_to
    menu_content = True

    @staticmethod
    def Update(action):
        selected = appdata.project.selected[0] if appdata.project.selected else None
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            for it in QTreeWidgetItemIterator(appdata.project):
                viewnode = it.value()
                if hasattr(viewnode, 'doc') and viewnode.doc != None and isinstance(viewnode.doc, GraphDocument) and viewnode is not selected:
                    action.setEnabled(True)
                    return
        action.setEnabled(False)

    @staticmethod
    def Make(menu):
        menu.clear()

        def f(menu, doc):
            fm = appdata.app.fontMetrics()
            width = fm.averageCharWidth() * 80
            text = fm.elidedText(doc.name, Qt.ElideMiddle, width).replace(u'\u2026', '...')
            action = QAction(text, menu)
            action.triggered.connect(lambda: appdata.project.Compare(selected, doc))
            menu.addAction(action)

        selected = appdata.project.selected[0] if appdata.project.selected else None
        docs = set()
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            for it in QTreeWidgetItemIterator(appdata.project):
                viewnode = it.value()
                if hasattr(viewnode, 'doc') and viewnode.doc != None and isinstance(viewnode.doc, GraphDocument) and viewnode is not selected:
                    docs.add(viewnode.doc)

        for d in docs:
            f(menu, d)


@public('workbench.contextmenu.project')
class xApplyDiff:
    vis_label = tm.main.menu_apply_diff
    @staticmethod
    def Do():
        selected = appdata.project.selected[0] if appdata.project.selected else None
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            path, wildcard = framework.dialogs.SelectFiles('Open diff file...', multi=False)
            if path:
                diff = RdfDiff()
                diff.LoadFromFileProc(path)
                appdata.project.ApplyDiff(selected, diff, os.path.basename(path))

    @staticmethod
    def Update(action):
        selected = appdata.project.selected[0] if appdata.project.selected else None
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            action.setEnabled(True)
            return
        action.setEnabled(False)

@public('workbench.contextmenu.project')
class xApplyInverseDiff:
    vis_label = tm.main.menu_apply_inverse_diff
    @staticmethod
    def Do():
        selected = appdata.project.selected[0] if appdata.project.selected else None
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            path, wildcard = framework.dialogs.SelectFiles('Open diff file...', multi=False)
            if path:
                diff = RdfDiff()
                diff.deletions = diff.ng['insertions']
                diff.insertions = diff.ng['deletions']
                diff.LoadFromFileProc(path)
                appdata.project.ApplyDiff(selected, diff, os.path.basename(path), True)

    @staticmethod
    def Update(action):
        selected = appdata.project.selected[0] if appdata.project.selected else None
        if selected and hasattr(selected, 'doc') and isinstance(selected.doc, GraphDocument) and not getattr(selected.doc, 'doc_connection', None):
            action.setEnabled(True)
            return
        action.setEnabled(False)

@public('workbench.menu.file')
class xStopTask:
    vis_label = tm.main.menu_stop_task
    menu_shortcut = 'Ctrl+B'
    @staticmethod
    def Do():
        appdata.app.worker_thread.Stop(appdata.app.worker_thread.GetCurrentTask())
    @staticmethod
    def Update(action):
        action.setEnabled(appdata.app.worker_thread.GetCurrentTask() != None)

@public('workbench.menu.file', 'workbench.contextmenu.project')
class xReimport:
    vis_label = tm.main.menu_reimport
    menu_shortcut = 'Ctrl+Shift+W'
    @staticmethod
    def Do():
        CallDocumentMethod('Reimport')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanReimport')))

@public('workbench.menu.file')
class xReloadModules:
    vis_label = tm.main.menu_reload_modules
    menu_shortcut = 'Ctrl+Shift+R'
    menu_sep = True
    @staticmethod
    def Do():
        public.reimport()

@public('workbench.menu.file')
class xReloadPatterns:
    vis_label = tm.main.menu_reload_patterns
    menu_shortcut = 'Ctrl+Shift+W'
    menu_sep = True
    @staticmethod
    def Do():
        appdata.project.LoadPatterns()
        for doc in appdata.documents(GraphDocument):
            doc.patterns_env_cached = None
        appdata.environment_manager.GetPatternsEnv(None, force = True)
        appdata.topwindow.AddNotify(tm.main.notify_patterns_reloaded)

@public('workbench.menu.file')
class xSettings:
    vis_label = tm.main.menu_settings
    menu_sep = True
    @staticmethod
    def Do():
        framework.settings.SettingsDialog()

@public('workbench.menu.file')
class xClose:
    vis_label = tm.main.menu_exit
    menu_shortcut = 'Alt+X'
    @staticmethod
    def Do():
        appdata.topwindow.close()

@public('workbench.contextmenu.project', 'workbench.contextmenu.project_actions')
class xOpenDataSourceNewView:
    vis_label = tm.main.menu_open_new_view
    menu_shortcut = 'F10'
    @staticmethod
    def Do():
        CallProjectNodesMethod('NewView')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindProjectNodesMethod('NewView')))

@public('workbench.menubar')
class xEdit:
    vis_label = tm.main.menu_edit
    menu_content = 'workbench.menu.edit'
    position = 2

    @staticmethod
    def Init(menu):
        appdata.app.focusChanged.connect(lambda old, new: menu.UpdateActions())


@public('workbench.menubar')
class xSearch:
    vis_label = tm.main.menu_search
    menu_content = 'workbench.menu.search'
    position = 2

    @staticmethod
    def Init(menu):
        appdata.app.focusChanged.connect(lambda old, new: menu.UpdateActions())

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xUndo:
    vis_label = tm.main.menu_undo
    vis_icon = 'undo'
    menu_shortcut = 'Ctrl+Z'
    tool_sep = True
    @staticmethod
    def Do():
        CallDocumentMethod('Undo')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanUndo')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xRedo:
    vis_label = tm.main.menu_redo
    vis_icon = 'redo'
    menu_shortcut = 'Ctrl+Y'
    menu_sep = True
    @staticmethod
    def Do():
        CallDocumentMethod('Redo')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanRedo')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xCopy:
    vis_label = tm.main.menu_copy
    menu_shortcut = 'Ctrl+C'
    vis_icon = 'copy'
    tool_sep = True
    @staticmethod
    def Do():
        if CallViewMethod('CanCopy'):
            CallViewMethod('Copy')

    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('CanCopy')))

@public('workbench.menu.edit', 'workbench.menu.element')
class xCopyText:
    vis_label = tm.main.menu_copy_text
    menu_shortcut = 'Ctrl+Shift+C'
    @staticmethod
    def Do():
        if CallViewMethod('CanCopyText'):
            CallViewMethod('CopyText')

    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('CanCopyText')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xCut:
    vis_label = tm.main.menu_cut
    menu_shortcut = 'Ctrl+X'
    vis_icon = 'cut'
    @staticmethod
    def Do():
        if CallViewMethod('CanCut'):
            CallViewMethod('Cut')

    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('CanCut')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xPaste:
    vis_label = tm.main.menu_paste
    menu_shortcut = 'Ctrl+V'
    vis_icon = 'paste'
    @staticmethod
    def Do():
        if CallViewMethod('CanPaste'):
            CallViewMethod('Paste')

    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('CanPaste')))

@public('workbench.menu.edit', 'workbench.menu.element', 'workbench.menu.element')
class xPaste2:
    vis_label = tm.main.paste_as_triples
    menu_shortcut = 'Ctrl+Shift+V'
    menu_sep = True
    @staticmethod
    def Do():
        if CallViewMethod('CanPasteTriples'):
            CallViewMethod('PasteTriples')

    @staticmethod
    def Update(action):
        if not FindViewMethod('CanPasteTriples'):
            action.setVisible(False)
        else:
            action.setVisible(True)
        action.setEnabled(bool(CallViewMethod('CanPasteTriples')))


@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xInsert:
    vis_label = tm.main.menu_insert
    vis_icon = 'element_add'
    menu_shortcut = 'Insert'
    @staticmethod
    def Do():
        CallViewMethod('DoAdd')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanEdit')) and bool(FindViewMethod('DoAdd')))

@public('workbench.menu.edit', 'workbench.menu.element')
class xInsert2:
    vis_label = tm.main.menu_insert2
    menu_shortcut = 'Shift+Insert'
    @staticmethod
    def Do():
        CallViewMethod('DoAddTemplate')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallDocumentMethod('CanEdit')) and bool(CallViewMethod('CanAddTemplate')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xDelete:
    vis_label = tm.main.menu_delete
    vis_icon = 'element_delete'
    menu_shortcut = 'Delete'
    @staticmethod
    def Do():
        CallViewMethod('DoDelete')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindViewMethod('DoDelete')))

@public('workbench.menu.edit', 'workbench.maintoolbar', 'workbench.menu.element')
class xReloadItem:
    vis_label = tm.main.menu_reload
    vis_icon = 'refresh'
    menu_shortcut = 'F5'

    @staticmethod
    def Do():
        CallViewMethod('DoReload')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('CanReload')))

@public('workbench.menu.edit')
class xUUID:
    vis_label = tm.main.menu_gen_uuid
    menu_shortcut = 'Alt+U'

    @staticmethod
    def Do():
        res = CallDocumentMethod('infGenerateUUID')
        util.SetClipboard(res)
        appdata.topwindow.AddNotify(tm.main.notify_gen_uuid%res)

    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindDocumentMethod('infGenerateUUID')))

@public('workbench.menu.search', 'workbench.maintoolbar', 'workbench.menu.element')
class xSearchEndpoints:
    vis_label = tm.main.menu_search_endpoints
    vis_icon = 'data_find'
    menu_shortcut = 'F4'
    tool_sep = True
    @staticmethod
    def Do():
        uri = CallViewMethod('GetResolvableUri')
        appdata.project.FindUri(uri)
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('GetResolvableUri')))

@public('workbench.menu.search', 'workbench.maintoolbar', 'workbench.menu.element')
class xSearchEndpointsWIP:
    vis_label = tm.main.menu_search_endpoints_wip
    vis_icon = 'data_find_wip'
    menu_shortcut = 'F7'
    @staticmethod
    def Do():
        uri = CallViewMethod('GetResolvableUri')
        appdata.project.FindUriWIP(uri)
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('GetResolvableUri')))

@public('workbench.menu.search', 'workbench.maintoolbar', 'workbench.menu.element')
class xOpenUrl:
    vis_label = tm.main.menu_open_uri
    vis_icon = 'environment_view'
    menu_shortcut = 'F6'
    @staticmethod
    def Do():
        uri = CallViewMethod('GetResolvableUri')
        if uri.startswith('http://') or uri.startswith('https://'):
            QDesktopServices.openUrl(uri)
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('GetResolvableUri')))

@public('workbench.menu.search', 'workbench.maintoolbar', 'workbench.menu.element')
class xOpenUrlProp:
    vis_label = tm.main.menu_open_property_uri
    vis_icon = 'environment_view2'
    @staticmethod
    def Do():
        uri = CallViewMethod('GetPropertyUri')
        if uri.startswith('http://') or uri.startswith('https://'):
            QDesktopServices.openUrl(uri)
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('GetPropertyUri') != None))

@public('workbench.menu.search', 'workbench.maintoolbar')
class xAllEntities:
    vis_label = tm.main.menu_all_entities
    vis_icon = 'iso_group_find'

    @staticmethod
    def Do():
        CallViewMethod('ShowAllCommand')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindViewMethod('ShowAllCommand')))

@public('workbench.menu.search', 'workbench.maintoolbar')
class xAllTemplates:
    vis_label = tm.main.menu_all_templates
    vis_icon = 'find_tpl'

    @staticmethod
    def Do():
        CallViewMethod('TemplatesCommand', '')
    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindViewMethod('TemplatesCommand')))

@public('workbench.menu.search')
class xWrongEntities:
    vis_label = tm.main.menu_entities_with_errors

    @staticmethod
    def Do():
        CallViewMethod('ShowErrorsCommand')

    @staticmethod
    def Update(action):
        action.setEnabled(bool(FindViewMethod('ShowErrorsCommand')))

@public('workbench.menu.view', 'workbench.maintoolbar', 'workbench.menu.element')
class xNavigate:
    tool_sep = True
    vis_label = tm.main.menu_open_new_view
    vis_icon = 'window_new'
    menu_shortcut = 'F12'
    menu_sep = True
    @staticmethod
    def Do():
        appdata.project.NewView(CallViewMethod('ViewType'), tabify=False)
    @staticmethod
    def Update(action):
        action.setEnabled(bool(CallViewMethod('ViewType')))

@public('workbench.menu.view')
class xPropertiesNodes:
    vis_label = tm.main.menu_view_properties_nodes
    menu_check = True

    @staticmethod
    def Update(action):
        action.setChecked(appconfig.get('show_properties', True))

    @staticmethod
    def Do():
        appconfig['show_properties'] = not appconfig.get('show_properties', True)
        if appconfig['show_properties']:
            appconfig['show_simple'] = False
        appconfig.SaveSettings()

@public('workbench.menu.view')
class xRelationshipsNodes:
    vis_label = tm.main.menu_view_relationships_nodes
    menu_check = True

    @staticmethod
    def Update(action):
        action.setChecked(appconfig.get('show_relationships', True))

    @staticmethod
    def Do():
        appconfig['show_relationships'] = not appconfig.get('show_relationships', True)
        if appconfig['show_relationships']:
            appconfig['show_simple'] = False
        appconfig.SaveSettings()


@public('workbench.menu.view')
class xPatternsNodes:
    vis_label = tm.main.menu_view_patterns_nodes
    menu_shortcut = 'Ctrl+P'
    menu_check = True

    @staticmethod
    def Update(action):
        action.setChecked(appconfig.get('show_patterns', True))

    @staticmethod
    def Do():
        appconfig['show_patterns'] = not appconfig.get('show_patterns', True)
        if appconfig['show_patterns']:
            appconfig['show_simple'] = False
        appconfig.SaveSettings()

@public('workbench.menu.view')
class xSimpleView:
    vis_label = tm.main.menu_simple_view
    menu_shortcut = 'Ctrl+l'
    menu_check = True
    menu_sep  = True

    @staticmethod
    def Update(action):
        action.setChecked(appconfig.get('show_simple', False))

    @staticmethod
    def Do():
        appconfig['show_simple'] = not appconfig.get('show_simple', False)
        if appconfig['show_simple']:
            appconfig['show_patterns'] = False
            appconfig['show_properties'] = False
            appconfig['show_relationships'] = False
        else:
            appconfig['show_patterns'] = True
            appconfig['show_properties'] = True
            appconfig['show_relationships'] = True
        appconfig.SaveSettings()

@public('workbench.menu.view')
class xConsole:
    vis_label = tm.main.menu_view_python_console
    menu_shortcut = 'Ctrl+`'

    vis_icon = 'console'
    tool_sep  = True
    menu_check = True

    @staticmethod
    def Update(action):
        if getattr(appdata.topwindow, 'consoledock', None):
            action.setChecked(appdata.topwindow.consoledock.isVisible())

    @staticmethod
    def Do(checked):
        if checked:
            appdata.topwindow.consoledock.show()
        else:
            appdata.topwindow.consoledock.hide()

@public('workbench.menu.view')
class xProjectView:
    vis_label = tm.main.menu_view_project
    menu_shortcut = 'Ctrl+T'

    tool_sep  = True
    menu_check = True

    @staticmethod
    def Update(action):
        action.setChecked(appdata.topwindow.projectdock.isVisible())

    @staticmethod
    def Do(checked):
        if checked:
            appdata.topwindow.projectdock.show()
        else:
            appdata.topwindow.projectdock.hide()

@public('workbench.menu.view')
class xPropertiesView:
    vis_label = tm.main.menu_view_properties
    menu_shortcut = 'Ctrl+G'

    tool_sep  = True
    menu_check = True
    menu_sep = True

    @staticmethod
    def Update(action):
        action.setChecked(appdata.topwindow.propsdock.isVisible())

    @staticmethod
    def Do(checked):
        if checked:
            appdata.topwindow.propsdock.show()
        else:
            appdata.topwindow.propsdock.hide()

@public('workbench.menu.view')
class xStartPage:
    vis_label = tm.main.menu_view_start_page

    tool_sep  = True
    menu_check = True
    menu_sep = True

    @staticmethod
    def Update(action):
        action.setChecked(appdata.topwindow.startpage.isVisible())

    @staticmethod
    def Do(checked):
        if checked:
            appdata.topwindow.startpage.show()
            appdata.topwindow.startpage.raise_()
        else:
            appdata.topwindow.startpage.hide()

@public('workbench.menu.view')
class xViewToolbar:
    vis_label = tm.main.menu_view_toolbar

    tool_sep  = True
    menu_check = True
    menu_sep = True

    @staticmethod
    def Update(action):
        action.setChecked(appdata.topwindow.toolbar.isVisible())

    @staticmethod
    def Do(checked):
        if checked:
            appdata.topwindow.toolbar.show()
            appdata.topwindow.toolbar.raise_()
        else:
            appdata.topwindow.toolbar.hide()

@public('workbench.menu.view')
class xFont:
    vis_label = tm.main.menu_font_size
    menu_content = 'workbench.menu.fontsize'

@public('workbench.menu.fontsize')
class xFontSizeBlock(object):
    menu_block = 'workbench.menu.fontsizeblock'
    menu_sep = True

class xFontSizeBase(object):
    menu_check = True

    @classmethod
    def Update(cls, action):
        action.setChecked(cls.fontsize == appconfig.get('fontsize', 1.0))

    @classmethod
    def Do(cls):
        appdata.app.SetFontSize(cls.fontsize)


for i in xrange(25, 225, 25):
    if i == 100:
        t = type('xFont{0}'.format(i), (xFontSizeBase,), dict(menu_shortcut = 'Ctrl+0', vis_label= '{0}%'.format(i), fontsize=float(i)/100.0))
    else:
        t = type('xFont{0}'.format(i), (xFontSizeBase,), dict(vis_label= '{0}%'.format(i), fontsize=float(i)/100.0))
    public('workbench.menu.fontsizeblock')(t)

@public('workbench.menu.fontsize')
class xIncreaseFontSize(object):
    menu_shortcut = 'Ctrl+='
    vis_label = '+10%'
    @classmethod
    def Do(cls):
        appdata.app.SetFontSize(appconfig.get('fontsize', 1.0) + 0.1)

@public('workbench.menu.fontsize')
class xDecreaseFontSize(object):
    menu_shortcut = 'Ctrl+-'
    vis_label = '-10%'
    @classmethod
    def Do(cls):
        appdata.app.SetFontSize(appconfig.get('fontsize', 1.0) - 0.1)

@public('workbench.menubar')
class xHelp:
    vis_label = tm.main.menu_help
    menu_content = 'workbench.menu.help'
    position = 100

@public('workbench.menubar')
class xTools:
    vis_label = tm.main.menu_extensions
    menu_content = 'workbench.menu.tools'
    position = 99

def _find_doc_path():
    docpath = os.path.join('..', 'documentation')
    if os.path.exists(docpath):
        return docpath
    import _winreg
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\TechInvestLab.ru\\dot15926 application data', 0, _winreg.KEY_READ)
        if key:
            docpath, tp = _winreg.QueryValueEx(key, 'documentation_path')
            if os.path.exists(docpath):
                return docpath
    except:
        pass
    return None

class DocumentationDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.main.doc_not_found_title)

        link = 'http://techinvestlab.ru/15926EditorDocumentation'
        link_txt = '<a href="%s">%s</a>'%(link, link)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tm.main.doc_not_found_body))
        text = QLabel(link_txt, self)
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
class xDocumentation:
    vis_label = tm.main.documentation
    @staticmethod
    def Do():
        docpath = _find_doc_path()
        if docpath:
            os.startfile(docpath)
        else:
            DocumentationDialog()

@public('workbench.maintoolbar')
class xConsole2(xConsole):
    pass
