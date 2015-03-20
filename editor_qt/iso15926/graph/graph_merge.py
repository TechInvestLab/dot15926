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




from collections import defaultdict

from PySide.QtCore import *
from PySide.QtGui import *
from iso15926.graph.graph_document import GraphDocument
import iso15926.kb as kb
import framework.treenode
import iso15926.common.filteredview
import framework.dialogs as dialogs
from iso15926.io.rdf_graph import RdfDiff
from graphlib import expand_uri, compact_uri
from iso15926.io.rdf_base import ObjectTriple, LiteralTriple, DatatypeQuad, curi_tail
import heapq
import iso15926.graph.graph_actions as actions
from framework.document import MultiAction
from iso15926.graph.graph_view import PropertiesNode, RelationshipsNode, MoreNode, GraphNode

NODE_DEFAULT = 0
NODE_CHANGED = 1
NODE_DELETED = 2
NODE_ADDED   = 3

class MergeGraphNode(GraphNode):
    def CanDrop(self, data = None, before=None, after=None):
        return False

class MergePropertiesNode(PropertiesNode):
    def CanDrop(self, data = None, before=None, after=None):
        return False

class BaseNode(framework.treenode.TreeNode):

    def SetNodeMark(self, mark):
        if mark == NODE_DEFAULT:
            self.SetColor(Qt.transparent)
            font = QFont(self.font(0))
            font.setStrikeOut(False)
            self.setFont(0, font)
        elif mark == NODE_CHANGED:
            self.SetColor(QColor("#ADD8E6"))
            font = QFont(self.font(0))
            font.setStrikeOut(False)
            self.setFont(0, font)
        elif mark == NODE_DELETED:
            self.SetColor(Qt.red)
            font = QFont(self.font(0))
            font.setStrikeOut(True)
            self.setFont(0, font)
        elif mark == NODE_ADDED:
            self.SetColor(Qt.green)
            font = QFont(self.font(0))
            font.setStrikeOut(False)
            self.setFont(0, font)
        self.nodemark = mark

    def MakeAction(self):
        if self.nodemark == NODE_DEFAULT or not self.change:
            return

        if self.change[0] and self.change[1]:
            return actions.ChangeProperty(self.doc, self.change[1], self.change[0])
        elif self.change[1]:
            return actions.AddProperty(self.doc, self.change[1])
        elif self.change[0]:
            return actions.RemoveProperty(self.doc, self.change[0])


class LiteralProperty(BaseNode):
    vis_icon = 'iso_literal'

    def __init__(self, parent, key, mark=None, before = None, after = None, change = None):
        BaseNode.__init__(self, parent, before = before, after = after)
        self.change = change
        self.doc = parent.doc
        self.SetNodeMark(mark)
        self.SetPropertyKey(key)

    def GetPropertyUri(self):
        return self.key.p

    def SetPropertyKey(self, key):
        self.key = key
        self.name = self.doc.infGetPropertyName(self.key.p, self.key.p)
        if self.key.p in [prop['uri'] for prop in self.doc.infGetAvailableProperties(self.parent.parent.uri).itervalues()]:
            self.vis_icon = 'iso_annotation'
        self.vis_label = '{0} = "{1}"'.format(self.name, self.key.l)
        self.Refresh()
        self.RefreshProps()

    def SetupProps(self):
        self.SetProp(tm.main.prop_uri, self.key.p)
        self.SetProp(tm.main.prop_name, self.name)
        self.SetProp(tm.main.value, self.key.l, None, True)

    def OnDblClick(self):
        action = self.MakeAction()
        if action:
            self.doc<<action
        return True

def CreateProperty(node, t, mark = None, before=None, after = None, change = None):
    if t.has_literal:
        return LiteralProperty(node, t, mark=mark, before=before, after=after, change = change)
    else:
        return EntityNode(node, t.o, key=t, prefix=node.doc.infGetPropertyName(t.p, t.p)+' = ', mark=mark, before=before, after=after, change = change)


class EntityNode(BaseNode):

    treenode_show_as_nonempty = True
    treenode_track_first_access = True
    show_numrel = 1000

    def __init__(self, parent, uri, key=None, prefix='', reason_uris=set(), suffix='', mark=None, before = None, after = None, change = None):
        BaseNode.__init__(self, parent, before = before, after = after)
        self.change = change
        self.doc = parent.doc
        self.uri = uri
        self.key = key
        self.prefix = prefix
        self.suffix = suffix
        self.reason_uris = reason_uris
        self.names = []
        self.properties = {}
        self.relationships = []
        self.reasonnodes = []
        self.propnode = None
        self.relnode = None

        diff = self.tree.view.diff
        other = self.tree.view.other
        wizard.Subscribe((self.doc, self.uri), self)
        if other: 
            if self.uri in diff.blanks:
                wizard.Subscribe((other, diff.blanks[self.uri]), self)
            else:
                wizard.Subscribe((other, self.uri), self)

        self.doc.grNeedProperties(self.uri)
        self.UpdateProperties()
        self.SetNodeMark(mark)
        self.Refresh()

    def GetPropertyUri(self):
        if self.key:
            return self.key.p
        return None

    def GetResolvableUri(self):
        return self.uri

    def OnDestroy(self):
        diff = self.tree.view.diff
        other = self.tree.view.other
        if other: 
            if self.uri in diff.blanks:
                wizard.Unsubscribe((other, diff.blanks[self.uri]), self)
            else:
                wizard.Unsubscribe((other, self.uri), self)
        wizard.Unsubscribe((self.doc, self.uri), self)
        BaseNode.OnDestroy(self)


    def OnFirstAccess(self):
        self.doc.grNeedRelationships(self.uri)
        for v in self.reason_uris:
            self.reasonnodes.append(EntityNode(self, v, prefix='reason: '))
        self.propnode = MergePropertiesNode(self)
        self.relnode = RelationshipsNode(self)
        self.UpdateProperties()
        self.UpdateRelationships()

    def W_EntityDestroyed(self, doc, obj_uri):
        diff = self.tree.view.diff
        diff.UpdateEntity(self.uri)
        self.UpdateProperties()
        self.RefreshProps()

    def W_EntityPropertiesChanged(self, doc, obj_uri, prop_new = None, prop_old =None):
        if self.propnode:
            if prop_old and prop_new and prop_old.has_literal and prop_new.has_literal:
                node = self.properties.pop(prop_old, None)
                if node:
                    self.properties[prop_new] = node
                    node.SetPropertyKey(prop_new)
                else:
                    self.properties[prop_new] = LiteralProperty(self.propnode, prop_new)

        diff = self.tree.view.diff
        diff.UpdateEntity(self.uri)
        self.UpdateProperties()
        self.RefreshProps()

    def W_EntityRelationshipsChanged(self, doc, obj_uri):
        self.UpdateRelationships()

    def UpdateProperties(self):
        props = set(self.doc.grTriplesForSubj(self.uri))

        diff = self.tree.view.diff

        props_del = set(diff.deletions.grTriplesForSubj(self.uri)) & props
        props_add = set(diff.insertions.grTriplesForSubj(self.uri)) - props
            
        if not props_del and not props_add:
            self.SetNodeMark(NODE_DEFAULT)
        elif not props-props_del and not props_add:
            self.SetNodeMark(NODE_DELETED)
        elif not props and props_add:
            self.SetNodeMark(NODE_ADDED)
        elif props_del or props_add:
            self.SetNodeMark(NODE_CHANGED)

        if self.propnode:
            for t in props:
                if t not in self.properties:
                    self.properties[t] = CreateProperty(self.propnode, t)
                else:
                    self.properties[t].SetNodeMark(NODE_DEFAULT)

            for t in props_add:
                if t not in self.properties:
                    self.properties[t] = CreateProperty(self.propnode, t, NODE_ADDED, change = (None, t))
                else:
                    self.properties[t].change = (None, t)
                    self.properties[t].SetNodeMark(NODE_ADDED)

            for key, node in self.properties.items():
                if key not in props | props_add:
                    if node:
                        node.Destroy()
                    del self.properties[key]

            self.propnode.Sort()

            props_chn = set()

            for k, v in self.properties.iteritems():
                if k in props_del:
                    v.SetNodeMark(NODE_DELETED)
                    v.change = (k, None)
                    for t in props_add:
                        if k.p == t.p and t not in props_chn:
                            v.change = (k, t)
                            self.properties[t].change = (k, t)
                            self.propnode.RemoveChild(self.properties[t])
                            self.propnode.InsertChild(self.propnode.IndexOf(v)+1, self.properties[t])
                            props_chn.add(t)

            self.propnode.Refresh()

        name, tp_label, icon = self.doc.infGetEntityVisual(self.uri, triples = props | props_add)
        
        if isinstance(name, list):
            self.names = name
            name = ', '.join(name)
        else:
            self.names = []

        if tp_label:
            self.vis_label = self.prefix+name+' : '+tp_label+self.suffix
        else:
            self.vis_label = self.prefix+name+self.suffix

        self.vis_icon = icon
        self.Refresh()

    def MoreRelationships(self):
        if self.relmorenode:
            self.relmorenode.Destroy()
            self.relmorenode = None

        diff = self.tree.view.diff
        rels_del = set(diff.deletions.grTriplesForObj(self.uri))
        rels_add = set(diff.insertions.grTriplesForObj(self.uri))-set(self.doc.grTriplesForObj(self.uri))

        idx = -1
        for idx in xrange(self.relshown, min(len(self.relationships), self.relshown+self.show_numrel)):
            t = self.relationships[idx]
            node = EntityNode(self.relnode, t.s, key = t, prefix = '{0} for '.format(curi_tail(t[1])))
            if t in rels_del:
                node.SetNodeMark(NODE_DELETED)
            elif t in rels_add:
                node.SetNodeMark(NODE_ADDED)

        relshown = idx + 1
        if relshown < len(self.relationships):
            self.relmorenode = MoreNode(self.relnode, self.MoreRelationships)
        elif self.relshown == 0:
                self.relnode.Sort()
        
        self.relshown = relshown
        self.relnode.Refresh()

    def UpdateRelationships(self):
        if not self.relnode:
            return
        
        self.relnode.DestroyChildren()
        self.relmorenode = None

        diff = self.tree.view.diff
        self.relationships = list(self.doc.grTriplesForObj(self.uri)) + list(diff.insertions.grTriplesForObj(self.uri))
        self.relnode.items_count = len(self.relationships)
        self.relshown = 0
        self.MoreRelationships()

    def ViewType(self):
        return appdata.environment_manager.FindViewType(self.doc, self.uri)

    def SetupProps(self):
        if self.doc.name:
            self.SetProp(tm.main.source_name, self.doc.name)
        if self.key:
            self.SetProp(tm.main.prop_uri, self.key.p)
            pn = self.doc.infGetPropertyName(self.key.p)
            if pn:
                self.SetProp(tm.main.prop_name, pn)
        self.SetProp(tm.main.uri, self.uri)
        for n in self.names:
            self.SetProp(tm.main.name, n)
        for k in self.properties.iterkeys():
            if k.has_object:
                continue
            pn = self.doc.infGetPropertyName(k.p, default=k.p)
            self.SetProp(pn, k.l, None, True)

    def CanReload(self):
        return True

    def DoReload(self):
        if self.treenode_track_first_access:
            return
        diff = self.tree.view.diff
        diff.UpdateEntity(self.uri)
        self.DestroyChildren()
        self.properties = {}
        self.relationships = {}
        self.propnode = None
        self.relnode = None
        self.OnFirstAccess()

    def OnDblClick(self):
        if getattr(self, 'change', None):
            action = self.MakeAction()
            if action:
                self.doc<<action
        else:
            lst = []
            props = set(self.doc.grTriplesForSubj(self.uri))
            diff = self.tree.view.diff
            props_del = set(diff.deletions.grTriplesForSubj(self.uri)) & props
            props_add = set(diff.insertions.grTriplesForSubj(self.uri)) - props
            for t in props_del:
                lst.append(actions.RemoveProperty(self.doc, t))
            for t in props_add:
                lst.append(actions.AddProperty(self.doc, t))
            self.doc<<MultiAction(lst)
        return True

class GraphMergeView(iso15926.common.filteredview.FilteredView):

    diff = None
    document = None
    other = None
    vis_label = None
    show_num = 1000

    def __init__(self, parent):
        wizard.Subscribe(self.document, self)
        if self.other:
            wizard.Subscribe(self.other, self)

        self.filter_params = None
        self.show_changed = True
        self.show_added   = True
        self.show_deleted = True
        self.text = ''
        self.morenode = None
        self.shown = 0
        self.pnode = None
        self.seeding = False
        iso15926.common.filteredview.FilteredView.__init__(self, parent)

        widget = self.widget()
        layout = widget.layout()

        tb = QToolBar('', widget)

        action = tb.addAction(appdata.resources.GetIcon('element_warning'), tm.main.changed)
        action.setCheckable(True)
        action.triggered[bool].connect(self.OnChangedFilter)
        action.setChecked(True)

        action = tb.addAction(appdata.resources.GetIcon('element_add'), tm.main.added)
        action.setCheckable(True)
        action.triggered[bool].connect(self.OnAddedFilter)
        action.setChecked(True)

        action = tb.addAction(appdata.resources.GetIcon('element_delete'), tm.main.deleted)
        action.setCheckable(True)
        action.triggered[bool].connect(self.OnDeletedFilter)
        action.setChecked(True)        

        tb.addSeparator()

        action = tb.addAction(appdata.resources.GetIcon('checks'), tm.main.accept_all)
        action.triggered.connect(self.OnAcceptAll)

        action = tb.addAction(appdata.resources.GetIcon('disk_green'), tm.main.save_diff)
        action.triggered.connect(self.SaveDiff)

        action = tb.addAction(appdata.resources.GetIcon('disk_blue_ok'), tm.main.save_filtered_diff)
        action.triggered.connect(self.SaveFilteredDiff)

        layout.insertWidget(0, tb)

    def OnAcceptAll(self):
        if len(self.subjects) > 1000:
            if dialogs.Choice(tm.main.apply_diff_warning):
                self.pnode.DestroyChildren()
                for v in self.subjects:
                    for t in self.diff.deletions.grTriplesForSubj(expand_uri(v)):
                        t.deletefrom(self.document)
                    for t in self.diff.insertions.grTriplesForSubj(expand_uri(v)):
                        t.insertto(self.document)
                self.document.ChangeState(self.document.state_changed)
                self.Seed()
            return

        lst = []
        for v in self.subjects:
            for t in self.diff.deletions.grTriplesForSubj(expand_uri(v)):
                lst.append(actions.RemoveProperty(self.document, t))
            for t in self.diff.insertions.grTriplesForSubj(expand_uri(v)):
                lst.append(actions.AddProperty(self.document, t))

        self.document<<MultiAction(lst)

    def SaveDiff(self):
        path, wildcard = dialogs.SelectFiles(tm.main.save_diff_as_title, save = True)
        if not path:
            return
        self.diff.SaveToFileProc(path)

    def SaveFilteredDiff(self):
        path, wildcard = dialogs.SelectFiles(tm.main.save_filtered_diff_as_title, save = True)

        if not path:
            return

        new_diff = RdfDiff()
        for v in self.subjects:
            uri = expand_uri(v)
            for t in self.diff.deletions.grTriplesForSubj(uri):
                t.insertto(new_diff.deletions)
            for t in self.diff.insertions.grTriplesForSubj(uri):
                t.insertto(new_diff.insertions)

        new_diff.SaveToFileProc(path)

    def W_EntityCreated(self, doc, uri):
        self.diff.UpdateEntity(uri)

    def W_EntityDestroyed(self, doc, uri):
        self.diff.UpdateEntity(uri)

    def W_EntityPropertiesChanged(self, doc, uri, prop_new = None, prop_old =None):
        self.diff.UpdateEntity(uri)

    def Search(self, value):
        self.text = value
        self.Seed()

    def OnChangedFilter(self, enabled):
        self.show_changed = enabled
        self.shown = 0
        self.Seed()

    def OnAddedFilter(self, enabled):
        self.show_added = enabled
        self.shown = 0
        self.Seed()

    def OnDeletedFilter(self, enabled):
        self.show_deleted = enabled
        self.shown = 0
        self.Seed()

    def ShowCommand(self, *t, **d):
        if not self.seeding:
            self.filter_params = d
            self.Seed()
        else:
            log(tm.main.diff_is_busy_msg)

    def Seed(self):
        self.setEnabled(False)
        self.seeding = True
        if not self.pnode:
            self.pnode = MergeGraphNode(self.wnd_tree, self.document)
        self.pnode.treenode_loading = True
        self.pnode.Refresh()
        self.pnode.DestroyChildren()
        self.shown = 0

        @public.wth(tm.main.searching_in_diff, self.document)
        def f1():
            if not self.diff and self.other:
                self.diff = RdfDiff()
                try:
                    self.diff.CompareProc(self.document, self.other)
                except:
                    log.exception()

            other = GraphDocument()
            self.diff.MakeLocalDiff(other, self.document)
            other.UpdateNamespacesFromLoad()
            props_source = self.other if self.other else self.document
            props = {}
            for k in type(self.document).doc_params:
                v = getattr(props_source, k, None)
                if v != None:
                    props[k] = v
            other.UpdateProps(props)

            all_subj = self.diff.deletions.ks.viewkeys() | self.diff.insertions.ks.viewkeys()
            new_subj = self.diff.insertions.ks.viewkeys() - self.document.ks.viewkeys()
            del_subj = self.diff.deletions.ks.viewkeys() - other.ks.viewkeys()
            chn_subj = all_subj - new_subj - del_subj

            self.subjects = []
            if self.show_changed:
                self.subjects += list(chn_subj)
            if self.show_added:
                self.subjects += list(new_subj)
            if self.show_deleted:
                self.subjects += list(del_subj)

            if self.text:
                res_doc = self.document._grSearchLabel(self.text)
                res_other = other._grSearchLabel(self.text)

                self.subjects =  list((res_doc | res_other) & set([expand_uri(uri) for uri in self.subjects]))
                self.subjects = [compact_uri(uri) for uri in self.subjects]

            if self.filter_params:
                env = appdata.environment_manager.GetWorkEnvironment(self.document, include_scanner=True)
                res_doc = env['scanner']._find(**self.filter_params)
                env = appdata.environment_manager.GetWorkEnvironment(other, include_scanner=True)
                res_other = env['scanner']._find(**self.filter_params)

                self.subjects =  list((res_doc | res_other) & set([expand_uri(uri) for uri in self.subjects]))
                self.subjects = [compact_uri(uri) for uri in self.subjects]
                self.filter_params = None


            count_all = len(all_subj)
            count_filtered = len(self.subjects)

            @public.mth
            def f2():
                self.ShowEntities()
                self.pnode.treenode_loading = False
                self.pnode.UpdateLabel(' [{1}/{2}]'.format(self.document.GetLabel(), count_filtered, count_all))
                self.setEnabled(True)
                self.seeding = False

    def ShowEntities(self):
        if self.morenode:
            self.morenode.Destroy()
            self.morenode = None

        idx = self.shown-1
        for idx in xrange(self.shown, min(len(self.subjects), self.shown+self.show_num)):
            uri = expand_uri(self.subjects[idx])
            node = EntityNode(self.pnode, uri)

        self.shown = idx + 1
        if self.shown < len(self.subjects):
            self.morenode = MoreNode(self.pnode, self.ShowEntities)

        self.pnode.Expand()
