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
import framework.resources
import sys
from framework.tree import Tree, DefaultTreeDelegate, SimpleTreeNodeEditor
from framework.treenode import TreeNode
import framework.util as util
from framework.dialogs import Choice, Notify, SelectFiles
from framework.document import Document
import os
import json
from framework.util import DictDecoder, GetPath
from framework.docinfo import CollectDocInfo, OpenDoc
from framework.view import View
from iso15926.common.all_menu import xPCARDLSparql
from iso15926.kb.dmviews import XSDTypesView, Part2TypesView
from iso15926.graph.graph_view import GraphView
from iso15926.graph.graph_merge import GraphMergeView
from iso15926.graph.graph_document import GraphDocument
from iso15926.patterns.patterns_document import PatternsDocument
import iso15926.kb as kb
from framework.props import PropsClient
import copy

class ProjectTreeDelegate(DefaultTreeDelegate):
    margin = 2
    def __init__(self, tree):
        DefaultTreeDelegate.__init__(self, tree)
        self.imgs = (appdata.resources.GetPixmap("cross_gray"),
                        appdata.resources.GetPixmap("cross_red"),
                        appdata.resources.GetPixmap("dot_gray"),
                        appdata.resources.GetPixmap("dot_red"))

    def closeIconPos(self, option):
        return QPoint(self.tree.viewport().rect().right() - self.imgs[0].width() - self.margin,
                      option.rect.center().y() - self.imgs[0].height()/2)

    def sizeHint(self, option, index):
        size = QStyledItemDelegate.sizeHint(self, option, index)

        item = self.tree.itemFromIndex(index)
        if not item.parent:
            return size

        if item.IconStyle() == -1:
            return size

        indent = self.tree.indentation() if self.tree.rootIsDecorated() else 0
        while item.parent:
            indent += self.tree.indentation()
            item = item.parent

        size.setWidth(max(self.tree.viewport().rect().width()-indent, size.width() + self.imgs[0].width() + self.margin * 2))
        size.setHeight(max(size.height(), self.imgs[0].height() + self.margin * 2))
        return size

    def paint(self, painter, option, index):
        item = self.tree.itemFromIndex(index)
        optv4 = QStyleOptionViewItemV4(option)
        self.initStyleOption(optv4, index)
        style = self.tree.style()

        if item.parent and item.IconStyle() != -1:
            closeButtonRect = self.imgs[0].rect().translated(self.closeIconPos(option))
            optv4.rect.setRight(closeButtonRect.left())
            icon_style = item.IconStyle()
            cursorPos = self.tree.mapFromGlobal(QCursor.pos())
            if closeButtonRect.contains(cursorPos):
                painter.drawPixmap(closeButtonRect.topLeft(), self.imgs[2*icon_style + 1])
            else:
                painter.drawPixmap(closeButtonRect.topLeft(), self.imgs[2*icon_style + 0])

        style.drawControl(QStyle.CE_ItemViewItem, optv4, painter, self.tree)


    def editorEvent(self, event, model, option, index):
        item = self.tree.itemFromIndex(index)
        if item.parent and item.IconStyle() != -1:
            if event.type() == QEvent.MouseMove:
                self.tree.viewport().repaint()

            if event.type() == QEvent.MouseButtonRelease or event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                closeButtonRect = self.imgs[0].rect().translated(self.closeIconPos(option))
                if closeButtonRect.contains(event.pos()):
                    self.tree.itemFromIndex(index).Destroy()
                    return True

        return DefaultTreeDelegate.editorEvent(self, event, model, option, index)


class ProjectVersionConverter:
    version = 2
    @staticmethod
    def Check(projectdata):
        version = projectdata.get('version', 0)
        if version != ProjectVersionConverter.version:
            for i in xrange(version, ProjectVersionConverter.version):
                convert_method = getattr(ProjectVersionConverter, 'Version{0}'.format(i), None)
                if convert_method != None:
                    convert_method(projectdata)

    @staticmethod
    def Version0(projectdata):
        projectdata['properties'] = {}

    @staticmethod
    def Version1(projectdata):
        data = []
        for v in projectdata['data']:
            if isinstance(v, basestring):
                data.append({'type': 'view', 'viewtype': v})
            elif isinstance(v, dict):
                data.append({'type': 'document', 'data': v})
        projectdata['data'] = data




#---------------------------------------------------------

class ProjectFolderNode(TreeNode):
    vis_icon = 'folder'
    vis_label = 'Folder'
    treenode_editable = True

    def __init__(self, parent, name = '', tag = None):
        for c in parent.children:
            if not isinstance(c, ProjectFolderNode):
                before = c
                break
        else:
            before = None
        TreeNode.__init__(self, parent, before = before)
        self.vis_label = name
        self.tag = tag
        appdata.project.UpdateProject()
        self.Refresh()

    def CreateEditor(self, tree):
        editor = SimpleTreeNodeEditor(tree, self.vis_label)
        return editor

    def CommitData(self, editor):
        self.vis_label = editor.GetText().strip()
        appdata.project.UpdateProject()
        self.Refresh()
        return True

    def IconStyle(self):
        return 0

    def CanDrop(self, data = None, before=None, after=None):
        if 'projectnode' in data:
            return True
        elif 'paths' in data:
            return True
        return False

    def Drop(self, data, before=None, after=None):
        if 'projectnode' in data:
            for it in QTreeWidgetItemIterator(appdata.project):
                node = it.value()
                if hash(node) == data['projectnode']:
                    node.parent.RemoveChild(node)
                    @public.mth
                    def f():
                        self.AddChild(node)
                        self.Expand()
                    return True
        elif 'paths' in data:
            self.tree.OpenPaths(data['paths'], self)
            return True
        return False

    def OnDestroy(self):
        appdata.project.UpdateProject()
        TreeNode.OnDestroy(self)


class ProjectRootNode(ProjectFolderNode):
    vis_icon = 'project_ico'
    treenode_editable = False

    def __init__(self, parent):
        ProjectFolderNode.__init__(self, parent)

    def OnSelect(self, select):
        if select:
            appdata.project.ShowProps()
            appdata.active_document = appdata.project

#---------------------------------------------------------

from props import PropPatternsEdit, PropDictEdit, PropModulesEdit

class ProjectPropertyChange():
    
    def __init__(self, prop, value):
        self.prop = prop
        self.value = value

    def Redo(self):
        self.old_value = getattr(appdata.project, self.prop, None)
        if self.old_value == self.value:
            return False
        setattr(appdata.project, self.prop, copy.copy(self.value))
        for doc in appdata.documents:
            doc.UpdateProps({})
        appdata.project.RefreshProps()
        appdata.project.UpdateProject()
        return True

    def Undo(self):
        setattr(appdata.project, self.prop, copy.copy(self.old_value))
        for doc in appdata.documents:
            doc.UpdateProps({})
        appdata.project.RefreshProps()
        appdata.project.UpdateProject()

class ProjectView(Tree, PropsClient):
    UseDragAndDrop = True
    popup_menu = 'workbench.contextmenu.project'
    project_menu = 'workbench.contextmenu.project_node'
    autosave_file = os.path.join(appdata.app_dir, 'autosave.15926')
    project_props = ['patterns_filter', 'annotations', 'roles']
    temp_node = None
    patterns_dir = 'patterns'

    def __init__(self, parent):
        Tree.__init__(self, parent)
        self.setMouseTracking(True)
        appdata.project = self
        self.closing = False
        self.update_requested = False
        self.root = ProjectRootNode(self)
        self.ResetProject()
        self.root.Expand()
        self.setItemDelegate(ProjectTreeDelegate(self))
        self.projectfile = None
        self.header().setStretchLastSection(False)
        self.header().setResizeMode(QHeaderView.ResizeToContents)
        self.horizontalScrollBar().valueChanged.connect(lambda value: self.viewport().repaint())
        self.addActions(framework.menu.MakeActions('workbench.contextmenu.project_actions', self))
        self.changed = False
        self.projectdata = self.CurrentProjectData()
        self.autosavedata = None
        self.docs = []
        # keep model
        self.model = self.model()
        #self.model.rowsInserted.connect(self.OnRowsInserted)

    def GetPatternsModulesAndNames(self):
        result = {}
        for doc in appdata.documents(PatternsDocument):
            result[doc.name] = doc.patterns.keys()
        return result

    def LoadPatterns(self):
        for v in self.root.children:
            if isinstance(v, ProjectFolderNode) and v.tag == 'patterns':
                folder = v
                break
        else:
            folder = self.AddFolder(tm.main.patterns_folder, 'patterns')

        for n in os.listdir(appconfig.get('cfg://patterns')):
            if n.startswith(".") or not n.endswith('.patt'):
                continue

            path = os.path.join('cfg://patterns', n)
            for doc in appdata.documents(PatternsDocument):
                if GetPath(path) in doc.paths:
                    break
            else:
                self.OpenPaths([path], folder)


    def AddFolder(self, name = '', tag = None):
        return ProjectFolderNode(self.root, name, tag)

    # def OnRowsInserted(self, parent, start, end):
    #     @public.mth
    #     def f():
    #         self.model.rowsInserted.disconnect(self.OnRowsInserted)
    #         self.SortProject()
    #         self.model.rowsInserted.connect(self.OnRowsInserted)

    # def SortProject(self):

    #     def f(node):
    #         items = node.TakeChildren()
    #         folders = []
    #         views = []
    #         for i in items:
    #             if isinstance(i, ProjectFolderNode):
    #                 folders.append((i.vis_label, i))
    #             else:
    #                 if getattr(i, 'doc', None) != None:
    #                     views.append((i.doc.name, i ))
    #                 else:
    #                     views.append((i.vis_label, i ))

    #         for _, i in sorted(folders, key = lambda x: x[0].lower()):
    #             node.AddChild(i)
    #             f(i)

    #         for _, i in sorted(views, key = lambda x: x[0].lower()):
    #             node.AddChild(i)   

    #     f(self.root)

    def CanUndo(self):
        return self.his_index>0

    def CanRedo(self):
        return self.his_index<len(self.his_entries)

    def Undo(self):
        if self.CanUndo():
            self.his_index -= 1
            action = self.his_entries[self.his_index]
            action.Undo()

    def Redo(self):
        if self.CanRedo():
            action = self.his_entries[self.his_index]
            action.Redo()
            self.his_index += 1

    def Edit(self, action):
        if not action.Redo():
            return
        if self.his_index<len(self.his_entries):
            self.his_entries = self.his_entries[:self.his_index]
        self.his_entries.append(action)
        self.his_index += 1

    def ResetProject(self):
        self.his_entries = []
        self.his_index = 0
        self.patterns_filter = {}
        available_patterns = self.GetPatternsModulesAndNames()
        self.patterns_filter['patterns_samples.patt'] = []
        self.annotations = copy.copy(kb.annotations_rdfs)
        self.roles = copy.copy(kb.roles_std)

    def contextMenuEvent(self, evt):
        menu = framework.menu.Menu(self)
        if self.GetSelectedNode() is self.root:
            framework.menu.MakeMenu(menu, self.project_menu)
        else:
            framework.menu.MakeMenu(menu, self.popup_menu)
        menu.popup(evt.globalPos())

    def SetupProps(self):
        self.SetProp(tm.main.location, self.projectfile)

        have_enabled = False
        have_disabled = False
        for module_name, patterns_list in self.GetPatternsModulesAndNames().iteritems():
            for name in patterns_list:
                if (module_name in self.patterns_filter) and (not self.patterns_filter[module_name] or name in self.patterns_filter[module_name]):
                    have_enabled = True
                else:
                    have_disabled = True

        pf_status = tm.main.prop_status_none
        if have_enabled and have_disabled:
            pf_status = tm.main.prop_status_custom
        elif have_enabled:
            pf_status = tm.main.prop_status_default

        self.SetProp(tm.main.patterns_filter, (pf_status,
                                               PropPatternsEdit, self.patterns_filter) , 'patterns_filter')

        self.SetProp(tm.main.annotations, (', '.join([name for name, uri in self.annotations]),
                                               PropDictEdit, self.annotations) , 'annotations')

        self.SetProp(tm.main.roles, (', '.join([name for name, uri in self.roles]),
                                               PropDictEdit, self.roles) , 'roles')
        self.SetProp(tm.main.module_names, (', '.join([doc.module_name for doc in appdata.documents(GraphDocument) if doc.module_name]),
                                               PropModulesEdit, None) , 'modules')

    def PropChanged(self, prop, value):
        if prop != 'modules':
            self.Edit(ProjectPropertyChange(prop, value))
        else:
            wizard.W_ProjectModulesChanged()
            self.RefreshProps()
            self.UpdateProject()

    def decodeMime(self, mimeData):
        if mimeData.hasUrls():
            paths = [os.path.normpath(url.toLocalFile()) for url in mimeData.urls()]
            return {'paths': paths}
        return Tree.decodeMime(self, mimeData)

    def dragEnterEvent(self, event):
        Tree.dragEnterEvent(self, event)
        if not event.isAccepted():
            mimeData = event.mimeData()
            data = self.decodeMime(mimeData)
            if data and 'paths' in data:
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        Tree.dragMoveEvent(self, event)
        if not event.isAccepted():
            mimeData = event.mimeData()
            data = self.decodeMime(mimeData)
            if data and 'paths' in data:
                event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        Tree.dragLeaveEvent(self, event)
        if not event.isAccepted():
            evt.accept()

    def OpenPaths(self, paths, node):
        for p in paths:
            if p.endswith('.15926'):
                self.OpenProjectFile(p)
                return

        if not Document.VerifyEditablePaths(paths):
            return

        unresolved = []
        for p in paths:
            if p.endswith('.patt'):
                doc = PatternsDocument()
                doc.OpenFiles([p], {})
                self.AddDocument(doc, node)
            else:
                unresolved.append(p)

        if unresolved:
            doc = GraphDocument()
            params = dict(chosen_part2=kb.ns_dm_rds, namespaces=kb.namespaces_std, annotations=kb.annotations_rdfs+kb.annotations_meta, roles = kb.roles_std)
            doc.OpenFiles(unresolved, **params)
            self.AddDocument(doc, node)

    def dropEvent(self, event):
        Tree.dropEvent(self, event)
        if not event.isAccepted():
            mimeData = event.mimeData()
            data = self.decodeMime(mimeData)
            if data and 'paths' in data:
                self.OpenPaths(data['paths'], self.root)
                event.accept()

    def NewProject(self):
        if self.CloseProject():
            self.ResetProject()
            self.LoadPatterns()
            self.projectdata = self.CurrentProjectData()
            if 'projectfile' in appconfig:
                del appconfig['projectfile']
                appconfig.SaveSettings()        
            self.RefreshProps()
            self.UpdateProject()

    def CloseProject(self, exit = False):
        changed_data = []
        if self.changed:
            text = tm.main.current_project
            if self.projectfile:
                projname, ext = os.path.splitext(os.path.basename(self.projectfile))
                text += ' ' + projname
            changed_data.append(text)
        changed_data += [doc.name for doc in appdata.documents if doc.doc_state==doc.state_changed]
        if changed_data:
            if exit:
                if not Choice(tm.main.unsaved_data_exit.format('\n'.join(changed_data))):
                    return False
            else:
                if not Choice(tm.main.unsaved_data_close.format('\n'.join(changed_data))):
                    return False

        self.closing = True

        self.DeleteAutosave()

        if self.projectfile:
            self.UpdateRecentProjects()

        self.projectfile = None
        self.root.DestroyChildren(True)

        self.closing = False
        return True

    def UpdateRecentProjects(self):
        recent_projects = appconfig.setdefault('recent_projects', [])
        recent = [v for v in recent_projects if v != self.projectfile]
        recent.append(self.projectfile)
        recent = recent[-5:]
        appconfig['recent_projects'] = recent
        appconfig.SaveSettings()
        if appdata.topwindow and getattr(appdata.topwindow, 'startpage', None):
            appdata.topwindow.startpage.Refresh()

    def DeleteAutosave(self):
        if self.autosavedata:
            self.autosavedata = None
            if self.projectfile:
                fdir, fname = os.path.split(self.projectfile)
                if os.path.exists(os.path.join(fdir, '.$' + fname)):
                    os.remove(os.path.join(fdir, '.$' + fname))
            elif os.path.exists(self.autosave_file):
                os.remove(self.autosave_file)

    def LoadProject(self, projectdata):
        for k, v in projectdata['properties'].iteritems():
            setattr(self, k, v)
        def loader(data, node):
            for v in data:
                if v['type'] == 'folder':
                    loader(v['data'], ProjectFolderNode(node, v['name'], v['tag']))
                elif v['type'] == 'view':
                    for viewtype in public.all("dot15926.viewtypes"):
                        if viewtype.__name__ == v['viewtype']:
                            self.AddView(viewtype, node)
                elif v['type'] == 'document':
                    doc = OpenDoc(v['data'], self.projectfile)
                    if doc:
                        appdata.project.AddDocument(doc, node)

        loader(projectdata['data'], self.root)
        self.LoadPatterns()

    def LoadProjectFromFile(self, filename):
        autosavefile = None

        if filename:
            fdir, fname = os.path.split(filename)
            if os.path.exists(os.path.join(fdir, '.$' + fname)):
                if Choice(tm.main.project_autosave_found):
                    autosavefile = os.path.join(fdir, '.$' + fname)
                else:
                    os.remove(os.path.join(fdir, '.$' + fname))

            if not autosavefile and not os.path.exists(filename):
                Notify(tm.main.project_not_found.format(filename))
                self.projectfile = None
            else:       
                self.projectfile = filename
        else:
            if os.path.exists(self.autosave_file):
                if Choice(tm.main.project_autosave_found):
                    autosavefile = self.autosave_file
                else:
                    os.remove(self.autosave_file)
            if not autosavefile:
                self.NewProject()
                return

        autosavefailed = False
        projectfailed = False

        if autosavefile:
            try:
                with open(autosavefile, 'r') as f:
                    projectdata = json.load(f, 'utf-8', object_hook = DictDecoder())
                ProjectVersionConverter.Check(projectdata)
                self.LoadProject(projectdata)
                self.autosavedata = projectdata
            except:
                log.exception()
                autosavefailed = True

        if self.projectfile:
            try:
                with open(self.projectfile, 'r') as f:
                    projectdata = json.load(f, 'utf-8', object_hook = DictDecoder())
                ProjectVersionConverter.Check(projectdata)
                if not autosavefile or autosavefailed:
                    self.LoadProject(projectdata)
                self.projectdata = projectdata
            except:
                log.exception()
                projectfailed = True

        if autosavefailed:
            if projectfailed:
                Notify(tm.main.project_autosave_failed)
                self.projectfile = None
            else:
                Notify('%s\n%s'%(tm.main.project_autosave_failed, tm.main.project_autosave_skipped))
        elif projectfailed:
            Notify(tm.main.project_load_failed)
            self.projectfile = None

        if appconfig.get('projectfile') != self.projectfile:
            appconfig['projectfile'] = self.projectfile
            appconfig.SaveSettings()
        self.RefreshProps()
        self.UpdateProject()

    def UpdateProject(self):
        if self.update_requested or self.closing:
            return
        self.update_requested = True
        @public.mth
        def f():
            self.update_requested = False
            current = self.CurrentProjectData()
            self.changed = self.projectdata != current
            if self.changed:
                if self.autosavedata != current:
                    if self.projectfile:
                        fdir, fname = os.path.split(self.projectfile)
                        autosavefile = os.path.join(fdir, '.$' + fname)
                    else:
                        autosavefile = self.autosave_file
                    try:
                        with open(autosavefile, 'w') as f:
                            json.dump(current, f, 'utf-8', ensure_ascii=False)
                        self.autosavedata = current
                    except:
                        self.autosavedata = None
            else:
                self.DeleteAutosave()
            self.UpdateTopWindowTitle()

    def CurrentProjectData(self, base_path = None):
        if not base_path:
            base_path = self.projectfile
        projectdata = {}

        projectdata['version'] = ProjectVersionConverter.version
        projectdata['properties'] = dict([(v, getattr(self, v)) for v in self.project_props])
        
        def saver(parent):
            data = []
            for node in parent.children:
                if isinstance(node, ProjectNode):
                    doc = node.doc
                    if doc != None:
                        docinfo = CollectDocInfo(doc, base_path)
                        if docinfo:
                            data.append({'type': 'document', 'data': docinfo})
                    elif node.viewtype != None:
                        data.append({'type': 'view', 'viewtype': node.viewtype.__name__})
                elif isinstance(node, ProjectFolderNode):
                    data.append({'type': 'folder', 'name': node.vis_label, 'tag': node.tag, 'data': saver(node)})
            return data

        projectdata['data'] = saver(self.root)
        return projectdata

    def ProjectSaved(self):
        return self.projectfile and not self.changed

    def CanSaveProject(self):
        return self.projectfile != None

    def SaveProjectToFile(self, filename):
        docs = set()
        for it in QTreeWidgetItemIterator(self):
            node = it.value()
            if isinstance(node, ProjectNode):
                if node.doc != None:
                    docs.add(node.doc)
        for doc in docs:
            doc.UpdatePropsState(True)

        try:
            projectdata = self.CurrentProjectData(filename)
            with open(filename, 'w') as f:
                json.dump(projectdata, f, 'utf-8', ensure_ascii=False)
            self.DeleteAutosave()
            if self.projectfile and self.projectfile != filename:
                self.UpdateRecentProjects()
            self.projectfile = filename
            self.projectdata = projectdata
        except:
            Notify(tm.main.project_not_accessible)
            self.projectfile = None
        finally:
            if appconfig.get('projectfile') != self.projectfile:
                appconfig['projectfile'] = self.projectfile
                appconfig.SaveSettings()
            self.RefreshProps()
            self.UpdateProject()

    def SaveProject(self):
        if not self.projectfile:
            return
        self.SaveProjectToFile(self.projectfile)

    def UpdateTopWindowTitle(self):
        if self.projectfile:
            projname, ext = os.path.splitext(os.path.basename(self.projectfile))
            if self.changed:
                appdata.topwindow.SetTitle('*'+projname)
                self.root.vis_label = '*'+projname
            else:
                appdata.topwindow.SetTitle(projname)
                self.root.vis_label = projname
            self.root.vis_tooltip = self.projectfile
        else:
            if self.changed:
                appdata.topwindow.SetTitle('*')
                self.root.vis_label = '*'+tm.main.default_project_name
            else:
                appdata.topwindow.SetTitle(None)
                self.root.vis_label = tm.main.default_project_name
            self.root.vis_tooltip = None
        self.root.Refresh()

    def OpenProject(self):
        if self.projectfile:
            defDir = os.path.dirname(self.projectfile)
        else:
            defDir = './'
        path, wildcard = SelectFiles(tm.main.open_project, multi = False, defaultDir = defDir, wildcard = tm.main.project_wildcard)
        if not path:
            return
        self.OpenProjectFile(path)

    def OpenProjectFile(self, path):
        if self.CloseProject():
            self.LoadProjectFromFile(path)

    def SaveProjectAs(self):
        path, wildcard = SelectFiles(tm.main.save_project_as, save = True, wildcard = tm.main.project_wildcard)
        if not path or not Document.VerifyEditablePaths([path]):
            return
        self.SaveProjectToFile(path)

    def ProjectTreeChanged(self):
        if self.projectfile:
            appdata.app.After(self.SaveProject)

    def focusInEvent(self, event):
        Tree.focusInEvent(self, event)
        node = self.GetSelectedNode()
        if node and isinstance(node, ProjectNode):
            appdata.active_document = node.doc
        else:
            appdata.active_document = None

    def NewView(self, viewtype, show = True, tabify = True, source = None):
        if not viewtype:
            return
        if not source:
            source = self.root
            if appdata.active_view and getattr(appdata.active_view, 'viewnode', None):
                if isinstance(appdata.active_view.viewnode.parent, ProjectNode):
                    source = appdata.active_view.viewnode.parent
                else:
                    source = appdata.active_view.viewnode

        node = ProjectNode(source, viewtype)
        if source is not self:
            source.Expand()
        return node.OpenView(show, tabify)

    def AddDocument(self, doc, folder = None):
        if folder:
            return ProjectNode(folder, doc.viewtype)
        return ProjectNode(self.root, doc.viewtype)

    def AddView(self, viewtype, folder = None):
        if folder:
            return ProjectNode(folder, viewtype)
        return ProjectNode(self.root, viewtype)
        
    def RemoveView(self, view):
        view.viewnode.Destroy()

    def AsyncOpenView(self, t, s):
        @public.mth
        def f():
            self.NewView(t, show = False, source = s)

    def FindUri(self, uri):
        @public.wth('Searching...')
        def f1():
            endpoints = False
            found = False
            for viewnode in self.root.children:
                if hasattr(viewnode, 'doc') and viewnode.doc != None and getattr(viewnode.doc, 'doc_connection', None) != None:
                    if isinstance(viewnode.doc, GraphDocument):
                        endpoints = True
                        res = viewnode.doc._grSearchUri(uri)
                        if res:
                            found = True
                            t = type('', (viewnode.viewtype,), dict(bound_uri = uri))
                            self.AsyncOpenView(t, viewnode)

            if not endpoints:
                @public.mth
                def f5():
                    appdata.topwindow.AddNotify(tm.main.notify_no_endpoints_in_project)
            elif not found:
                @public.mth
                def f4():
                    appdata.topwindow.AddNotify(tm.main.notify_uri_not_found%uri)
    
    def FindUriWIP(self, uri):
        found = False
        for viewnode in self.root.children:
            if hasattr(viewnode, 'doc') and viewnode.doc != None and getattr(viewnode.doc, 'doc_connection', None) != None:
                if viewnode.doc.doc_connection.uri == xPCARDLSparql.sparql_path:
                    found = True
                    break

        if not found:
            xPCARDLSparql.Do()

        @public.wth('Searching...')
        def f1():
            found = False
            for viewnode in self.root.children:
                if hasattr(viewnode, 'doc') and viewnode.doc != None and isinstance(viewnode.doc, GraphDocument) and getattr(viewnode.doc, 'doc_connection', None) != None:
                    if viewnode.doc.doc_connection.uri == "http://posccaesar.org/endpoint/sparql":
                        res = viewnode.doc._grSearchUriWIP(uri)
                        if res:
                            found = True
                            t = type('', (viewnode.viewtype,), dict(bound_uri = res[uri]))
                            self.AsyncOpenView(t, viewnode)
                            
            if not found:
                @public.mth
                def f3():
                    appdata.topwindow.AddNotify(tm.main.notify_uri_not_found%uri)

    def W_ResultsAvailable(self, res_id, result_set, status = None):
        res_list = list(result_set)
        if len(res_list) == 1:
            appdata.project.NewView(type('', (res_id[1].viewtype,),dict(bound_uri = res_list[0])), show = False, source = res_id[1])
        wizard.Unsubscribe(res_id, self)

    def Compare(self, node, other):
        label = tm.main.compare_to%other.name
        t = type('', (GraphMergeView,), dict(vis_label = label, document = node.doc, other = other))
        self.NewView(t, source = node)

    def ApplyDiff(self, node, diff, diffname, inverse = False):
        if inverse:
            label = tm.main.inverse_diff_to%(diffname, node.doc.name)
        else:
            label = tm.main.diff_to%(diffname, node.doc.name)
        t = type('', (GraphMergeView,), dict(vis_label = label, document = node.doc, diff = diff))
        self.NewView(t, source = node)
#---------------------------------------------------------

class ProjectNode(TreeNode):

    def __init__(self, parent, viewtype):
        TreeNode.__init__(self, parent)
        self.view      = None
        self.viewtype  = type(viewtype.__name__, (viewtype, ), dict(viewnode = self))
        self.doc       = viewtype.document
        self.vis_icon  = 'blank_ico'

        if self.doc:
            self.vis_icon = self.doc.GetIcon()
            self.doc.AddClient(self)
            wizard.Subscribe(self.doc, self)
            if self.doc.doc_owner is None:
                self.doc.doc_owner = self
                wizard.Subscribe(self.doc, self)
        elif self.viewtype:
            if hasattr(self.viewtype, 'vis_icon'):
                self.vis_icon = self.viewtype.vis_icon
                
        self.UpdateLabel()
        if self.parent is appdata.project.root:
            appdata.project.RefreshProps()
            appdata.project.UpdateProject()

    def IconStyle(self):
        if self.doc and self.doc.doc_state == self.doc.state_changed:
            return 1
        return 0

    def GetInfoString(self):
        info = ''
        if self.doc:
            if len(self.doc.paths)>0:
                info += '{0}\n'.format(', '.join(self.doc.paths))
            elif hasattr(self.doc, 'import_source'):
                info += '{0}\n'.format(', '.join(self.doc.import_source))

            module_name = getattr(self.doc, 'module_name', '')
            if module_name != '':
                info += 'Module name: {0}\n'.format(module_name)

        return info

    def W_DocumentPropertiesChanged(self, doc):
        if self.doc.props_changed:
            self.vis_italic = True
        else:
            self.vis_italic = False
        self.Refresh()
        if self.parent is appdata.project.root:
            appdata.project.UpdateProject()

    def W_DocumentStateChanged(self, doc):
        if self.doc.props_changed:
            self.vis_italic = True
        else:
            self.vis_italic = False
        self.Refresh()
        if self.parent is appdata.project.root:
            appdata.project.UpdateProject()

    def W_DocumentLabelChanged(self, doc):
        self.UpdateLabel()

    def CanEdit(self):
        return self.parent is appdata.project.root

    def BeginEdit(self):
        if self.doc:
            self.EditText(self.doc.name, self.OnTextEdited)

    def OnTextEdited(self, text):
        if self.doc:
            self.doc.name = text

    def SetLabel(self, label):
        if isinstance(self.parent, ProjectFolderNode):
            self.vis_label = label

        elif self.view != None:
            self.vis_label = self.view.GetLabel()
            if getattr(self.view, 'document', None) != None and not issubclass(self.viewtype, GraphMergeView):
               self.vis_label = '{0} ({1})'.format(self.view.GetLabel(), self.view.document.name)
            self.vis_icon = self.view.GetIcon()
        else:
            self.vis_label = label

        self.vis_tooltip = '{0}\n{1}'.format(self.vis_label, self.GetInfoString())

        if self.view != None :
            self.view.SetTitle(label)

        self.Refresh()

    def UpdateLabel(self):
        if self.view:
            self.SetLabel(self.view.GetLabel())
        elif self.doc:
            self.SetLabel(self.doc.label)
        elif self.viewtype:
            self.SetLabel(self.viewtype.vis_label)
        else:
            self.SetLabel('Empty')

    def IsDestroyAllowed(self):
        if self.doc and self.doc.doc_owner is self and self.doc.doc_state==self.doc.state_changed:
            if not Choice(tm.main.unsaved_documents.format(self.doc.name)):
                return False
        return True

    def OnDestroy(self):
        if self.doc:
            wizard.Unsubscribe(self.doc, self)
            self.doc.RemoveClient(self)
            self.doc.ClearProps()
            if self.doc.doc_owner is self:
                self.doc.doc_owner = None
                for v in self.doc.doc_clients.copy():
                    if type(v) == ProjectNode and v in self.doc.doc_clients:
                        v.Destroy()
                 
        if self.view:
            self.view.OnDestroy()
            self.view.close()
            self.view.deleteLater()
            self.view = None

        if isinstance(self.parent, ProjectFolderNode):
            appdata.project.UpdateProject()
        TreeNode.OnDestroy(self)

    def NewView(self):
        if self.view:
            if self.view.IsSeeable():
                appdata.project.NewView(self.viewtype, tabify = False, source = self.parent if isinstance(self.parent, ProjectNode) else self)
            else:
                self.OpenView(tabify = False, readd = True)
        else:
            self.OpenView(tabify = False)

    def OpenView(self, show = True, tabify = True, readd = False):
        if not self.view:
            self.view = self.viewtype(appdata.topwindow.workarea)
            self.view.viewnode = self
            self.UpdateLabel()

        if show:
            if self.view.isHidden() or readd:
                if appdata.active_view != None and tabify:
                    appdata.topwindow.workarea.tabifyDockWidget(appdata.active_view, self.view)
                else:
                    count = 1
                    for v in appdata.topwindow.workarea.findChildren(View):
                        if v.IsSeeable() and not v.isFloating():
                            count += 1

                    width = appdata.topwindow.workarea.width()/count
                    self.view.setMinimumWidth(width)
                    appdata.topwindow.workarea.addDockWidget(Qt.RightDockWidgetArea, self.view, Qt.Horizontal)
                    @public.mth
                    def f():
                        self.view.setMinimumWidth(0)

                self.view.show()
            self.view.raise_()
            self.view.SetActive()
        else:
            self.view.hide()
        return self.view

    def OnSelect(self, select):
        if select:
            if self.doc and not issubclass(self.viewtype, GraphMergeView):
                self.doc.ShowProps()
                appdata.active_document = self.doc
            else:
                self.ShowProps()
        else:
            appdata.active_document = None

    def SetupProps(self):
        self.SetProp(tm.main.name, self.vis_label)

    def OnDblClick(self):
        self.OpenView()
        return True

    def OnMiddleDown(self):
        self.NewView()
        return True

    def Drag(self):
        return dict(projectnode = hash(self))

