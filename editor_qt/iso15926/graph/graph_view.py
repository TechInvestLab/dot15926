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




from framework.treenode import TreeNode
from iso15926.common.filteredview import FilteredView
from framework.props import PropsClient
import iso15926.kb as kb
from collections import defaultdict
import iso15926.common.dialogs as dialogs
import iso15926.graph.graph_actions as actions
from iso15926.io.rdf_base import ObjectTriple, LiteralTriple, DatatypeQuad, curi_tail
from iso15926.tools.patterns import PatternDict
import framework.util as util
from PySide.QtCore import *
from PySide.QtGui import *
from framework.document import MultiAction

def Command_templates(*t, **d):
    if len(t)>2:
        return

    view = appdata.active_view
    if not view or not getattr(view, 'TemplatesCommand', None):
        return
        
    view.TemplatesCommand(*t, **d)

def Command_show(*t, **d):
    if len(t)>1:
        return

    view = appdata.active_view
    if not view or not getattr(view, 'ShowCommand', None):
        return
        
    view.ShowCommand(*t, **d)

def Command_sparql(*t, **d):
    if len(t)>2:
        return

    view = appdata.active_view
    if not view or not getattr(view, 'SparqlCommand', None):
        return
        
    view.SparqlCommand(*t, **d)

class GraphView(FilteredView):

    msg_filterdesc = tm.main.search_in
    msg_filteroptions = [tm.main.search_in_labels, tm.main.search_in_uri]
    msg_filtermulti = False
    msg_searching_label = tm.main.search_folder
    msg_searching_uri = tm.main.searching_uri
    msg_searching_template_label = tm.main.search_template_folder

    def Seed(self):
        self.provnode = GraphNode(self.wnd_tree, self.document)
        if getattr(self, 'bound_uri', None):
            node = EntityNode(self.provnode, self.bound_uri)
            self.vis_label = node.vis_label
            self.vis_icon  = node.vis_icon
            self.provnode.Expand()

    def Search(self, text):
        if not self.document.CanView():
            return
        text = text.strip()
        if 0 in self.wnd_filter.selection:
            def searchfunc(node):
                self.document.grSearchLabel(text, node)
            lbl = self.msg_searching_label
        else:
            def searchfunc(node):
                self.document.grSearchUriSubstring(text, node)
            lbl = self.msg_searching_uri
        SearchNode(self.provnode, searchfunc, lbl.format(text), search_text = text)
        self.provnode.Expand()

    def SearchUri(self, uri):
        if not self.document.CanView():
            return
        def searchfunc(node):
            self.document.grSearchUri(uri, node)
        SearchNode(self.provnode, searchfunc, self.msg_searching_uri.format(uri), search_text = uri)
        self.provnode.Expand()

    def SearchUriWIP(self, uri):
        if not self.document.CanView():
            return
        def searchfunc(node):
            self.document.grSearchUriWIP(uri, node)
        SearchNode(self.provnode, searchfunc, self.msg_searching_uri.format(uri), search_text = uri)
        self.provnode.Expand()

    def ShowAllCommand(self):
        def searchfunc(node):
            self.document.grSearchAll(node)
        SearchNode(self.provnode, searchfunc, tm.main.found_folder)
        self.provnode.Expand()

    def ShowErrorsCommand(self):
        def searchfunc(node):
            self.document.grSearchErrors(node)
        SearchNode(self.provnode, searchfunc, tm.main.found_folder)
        self.provnode.Expand()

    def ShowCommand(self, *t, **d):
        name = None
        if t:
            name = t[0]

        def finder():
            return appdata.scanner.find(**d)

        ProgSearchNode(self.provnode, finder, name, appdata.environment_manager.latest_console_input)

    def SparqlCommand(self, *t, **d):
        name = tm.main.sparql_query
        if len(t) > 1:
            name = t[0]

        def searchfunc(node):
            self.document.grSparqlQuery(t[-1], node)
        SearchNode(self.provnode, searchfunc, name, sparql_text = t[-1])
        self.provnode.Expand()

    def TemplatesCommand(self, *t, **d):
        text = ''
        if len(t) > 0:
            text = t[-1]

        name = self.msg_searching_template_label.format(text)
        if len(t) > 1:
            name = t[0]

        def searchfunc(node):
            self.document.grFindTemplates(text, node)

        SearchNode(self.provnode, searchfunc, name)
        self.provnode.Expand()

    def CanPaste(self):
        if not self.document.CanEdit():
            return False
        return util.CheckClipboard('application/x-dot15926-graph-records')

    def CanPasteTriples(self):
        if not self.document.CanEdit():
            return False
        return util.CheckClipboard('application/x-dot15926-graph-triples')

    def Paste(self):
        if self.document.CanEdit():
            if util.CheckClipboard('application/x-dot15926-graph-records'):
                data = util.GetClipboard('application/x-dot15926-graph-records')
                if data:
                    self.document<<actions.PasteEntities(self.document, data)

    def PasteTriples(self):
        if self.document.CanEdit():
            if util.CheckClipboard('application/x-dot15926-graph-triples'):
                data = util.GetClipboard('application/x-dot15926-graph-triples')
                if data:
                    self.document<<actions.PasteProperties(self.document, data)

    def CanCopy(self):
        selected = self.wnd_tree.selected
        if not selected:
            return False
        for v in selected:
            if not getattr(v,'GetContent', None):
                return False
        return True

    def CanCut(self):
        if not self.document.CanEdit():
            return False
        selected = self.wnd_tree.selected
        if not selected:
            return False
        for v in selected:
            if not getattr(v,'GetContent', None):
                return False
        return True

    def Copy(self):
        selected = self.wnd_tree.selected
        data     = {}    
        triples  = []
        folders  = data.setdefault('folders', {})
        entities = []

        for v in selected:
            f = getattr(v, 'GetContent', None)
            if f:
                if getattr(v,'is_property', None):                
                    triples += f()
                else:
                    res = f()
                    entities += res
                    if isinstance(v, FolderNode):
                        folders.setdefault(v.vis_label, set()).update(res)

        only_triples = True if triples else False

        entities = set(entities)
        uris = set(entities)
        for v in triples:
            uris.add(v.s)

        for v in entities:
            triples += self.document.grCollectEntityTriples(v, True)

        mime = {}
        if triples:
            data['triples'] = set(triples)
            if not only_triples:
                mime['application/x-dot15926-graph-records'] = data
            mime['application/x-dot15926-graph-triples'] = data

        util.SetClipboard(', '.join(uris), mime)

        notify = tm.main.notify_clipboard
        if not only_triples:
            notify += tm.main.notify_records_copied.format(len(entities))
        notify += tm.main.notify_triples_copied.format(len(triples))
        appdata.topwindow.AddNotify(notify, 2000)


    def Cut(self):
        selected = self.wnd_tree.selected
        data     = {}    
        triples  = []
        folders  = data.setdefault('folders', {})
        entities = []

        for v in selected:
            f = getattr(v, 'GetContent', None)
            if f:
                if getattr(v,'is_property', None):                
                    triples += f()
                else:
                    res = f()
                    entities += res
                    if isinstance(v, FolderNode):
                        folders.setdefault(v.vis_label, set()).update(res)

        only_triples = True if triples else False

        entities = set(entities)
        uris = set(entities)
        for v in triples:
            uris.add(v.s)

        lst = []
        for t in triples:
            lst.append(actions.RemoveProperty(self.document, t))

        for v in entities:
            triples += self.document.grCollectEntityTriples(v, True)

        for uri in entities:
            triples += self.document.grTriplesForSubj(uri)

        self.document<<MultiAction(lst + [actions.RemoveEntity(self.document, uri) for uri in entities])

        mime = {}
        if triples:
            data['triples'] = set(triples)
            if not only_triples:
                mime['application/x-dot15926-graph-records'] = data
            mime['application/x-dot15926-graph-triples'] = data

        util.SetClipboard(', '.join(uris), mime)

        notify = tm.main.notify_clipboard
        if not only_triples:
            notify += tm.main.notify_records_copied.format(len(entities))
        notify += tm.main.notify_triples_copied.format(len(triples))
        appdata.topwindow.AddNotify(notify, 2000)

class GraphNode(TreeNode):
    vis_icon = 'rdf_ico'
    vis_bold = True

    def __init__(self, parent, doc, suffix = ''):
        TreeNode.__init__(self, parent)
        self.doc = doc
        self.suffix = suffix
        wizard.Subscribe(self.doc, self)
        self.UpdateLabel()

    def CanAddTemplate(self):
        return True

    def DoAddTemplate(self):
        def creator(label_comment_uri):
            if not label_comment_uri:
                return
            label, comment, uri = label_comment_uri
            if not label:
                return

            if not uri:
                uri = uri_gen = self.doc.infGenerateTemplateUri(label)
            else:
                uri_gen = None

            annotations = {}
            if self.doc.annotations_by_name.get('defaultRdsId'):
                annotations[self.doc.annotations_by_name.get('defaultRdsId')] = self.doc.infDefaultRdsIdTemplate(uri_gen)

            self.doc << actions.AddTemplate(self.doc, {'uri': uri, 'name': label, 'comment': comment, 'annotations': annotations})
        dialogs.CreateTemplate(creator)
        return True

    def UpdateLabel(self, suffix = ''):
        if suffix:
            self.suffix = suffix
        self.vis_label = self.doc.GetLabel() + self.suffix
        self.treenode_loading = not self.doc.CanView()
        self.Refresh()

    def OnDestroy(self):
        wizard.Unsubscribe(self.doc, self)
        TreeNode.OnDestroy(self)

    def W_DocumentPropertiesChanged(self, doc):
        for it in QTreeWidgetItemIterator(self.tree):
            if isinstance(it.value(), EntityNode):
                it.value().DoReload()

    def W_DocumentLabelChanged(self, doc):
        self.UpdateLabel()

    def CanDrop(self, data = None, before=None, after=None):
        return self.doc.CanEdit()

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        if data.get('uri'):
            type_uri = data['uri']
        elif data.get('qname'):
            type_uri = self.doc.infExpandQname(data['qname'])
            if not type_uri:
                return False
        else:
            return False
        type_label = data.get('label')
        if not type_label:
            type_label = type_uri
        def creator(label_uri):
            if not label_uri:
                return
            label, uri = label_uri
            if not label:
                label = None

            types = [type_uri]

            if not uri:
                uri = uri_gen = self.doc.infGenerateUri(label)
            else:
                uri_gen = None

            props = []
            if self.doc.annotations_by_name.get('defaultRdsId'):
                props.append(LiteralTriple.of(uri, self.doc.annotations_by_name.get('defaultRdsId'), self.doc.infDefaultRdsId(uri_gen)))

            if data.get('template'):
                types.append(kb.ns_owl+'Thing')
                tpl = self.doc._findTemplate(type_uri)
                if tpl:
                    for v in tpl['roles'].itervalues():
                        if v.get('restricted_by_value'):
                            props.append(ObjectTriple.of(uri, v['uri'], v['type_uri']))
                        if v['is_literal']:
                            props.append(DatatypeQuad.of(uri, v['uri'], '', v['type_uri']))
            self.doc << actions.AddEntity(self.doc, uri, types, label, props)
        dialogs.CreateInstance(creator, type_label)
        return True
    
    def W_EntityCreated(self, doc, obj_uri):
        EntityNode(self, obj_uri)
        self.Expand()

    def W_FolderCreated(self, doc, name, items):
        FolderNode(self, name, items)
        self.Expand()

    def DoReload(self):
        for c in self.children:
            m = getattr(c, 'DoReload', None)
            if m:
                m()

    def ViewType(self):
        return type('', (GraphView,), dict(document=self.doc))

    def OnSelect(self, select):
        if select:
            self.doc.ShowProps()

class MoreNode(TreeNode):
    treenode_show_as_nonempty = False
    vis_icon = 'more'
    vis_label = tm.main.more_link
    def __init__(self, parent, callback):
        TreeNode.__init__(self, parent)
        self.callback = callback
        self.Refresh()

    def OnDblClick(self):
        self.callback()
        return True

class FolderNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    show_num = 1000
    vis_label = 'Folder'

    def __init__(self, parent, label = None, items = None, makefunc = None):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.label = label
        if self.label:
            self.vis_label = self.label
            wizard.Subscribe((self.doc, self.label), self)
        if makefunc:
            self.MakeItem = makefunc
        self.ResetFolder(items)

    def MakeItem(self, items, idx):
        val = items[idx]
        EntityNode(self, val)
        return True

    def ResetFolder(self, items, length = None):
        self.DestroyChildren()
        self.items = items if items else []
        self.items_count = length if length else len(self.items)
        self.morenode = None
        self.idx = 0
        if self.items:
            self.ShowMore()
        else:
            self.Refresh()

    def ShowMore(self):
        oldmorenode = self.morenode
        self.morenode = None

        self.tree.expanded.disconnect(self.tree.OnItemExpanded)

        shown = 0
        idx = -1
        for idx in xrange(self.idx, self.items_count):
            if self.MakeItem(self.items, idx):
                shown += 1
                if shown == self.show_num:
                    self.morenode = MoreNode(self, self.ShowMore)
                    break
        else:
            if self.idx == 0:
                self.Sort()

        self.tree.expanded.connect(self.tree.OnItemExpanded)  

        if oldmorenode:
            oldmorenode.Destroy()

        self.idx = idx + 1
        self.Refresh()

    def OnDestroy(self):
        if self.label:
            wizard.Unsubscribe((self.doc, self.label), self)

    def GetContent(self):
        return self.items

    def DoDelete(self):
        self.Destroy()

    def CanReload(self):
        return True

    def DoReload(self):
        self.DestroyChildren()
        self.ShowMore()

    def W_FolderDestroyed(self, doc, name):
        self.Destroy()


class SearchNode(FolderNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    show_num = 1000
    msg_error = tm.main.endpoint_search_error

    def __init__(self, parent, searchfunc, label, search_text = None, sparql_text = None):
        FolderNode.__init__(self, parent, label)
        self.doc = parent.doc
        self.searchfunc = searchfunc
        self.vis_label = label
        self.sparql_text = sparql_text
        self.search_text = search_text
        wizard.Subscribe(self, self)
        self.DoReload()
        self.SetCurrent()

    def GetContent(self):
        return self.items

    def GetItemsCount(self):
        return len(self.items)

    def OnDestroy(self):
        wizard.Unsubscribe(self, self)
        FolderNode.OnDestroy(self)

    def W_ResultsAvailable(self, res_id, result_set, status = None):
        if status:
            self.vis_label = '[{0}] {1}'.format(status, self.vis_label)
        self.treenode_loading = False
        self.ResetFolder(list(result_set))

    def DoDelete(self):
        self.Destroy()

    def CanReload(self):
        return True

    def DoReload(self):
        self.DestroyChildren()
        self.treenode_loading = True
        self.Refresh()
        self.searchfunc(self)

    def SetupProps(self):
        if self.search_text:
            self.SetProp(tm.main.search_text, self.search_text)
        if self.sparql_text:
            self.SetProp(tm.main.sparql_text, self.sparql_text)

import heapq

class EntityNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_track_first_access = True
    show_numrel = 1000

    def __init__(self, parent, uri, key=None, prefix='', reason_uris=set(), suffix='', is_prop = False, reason_pattern = None):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.uri = uri
        self.key = key
        self.prefix = prefix
        self.suffix = suffix
        self.is_property = is_prop
        self.reason_uris = reason_uris
        self.reason_pattern = reason_pattern
        self.names = set()
        self.properties = {}
        self.relationships = []
        self.propnode = None
        self.relnode = None
        self.patternsnode = None
        self.rolesnode = None
        self.supertemplatenode = None
        wizard.Subscribe((self.doc, self.uri), self)
        self.doc.grNeedProperties(self.uri)
        self.UpdateProperties()
        self.Refresh()

    def CanAddTemplate(self):
        return self.doc.grIsTemplate(self.uri)

    def DoAddTemplate(self):
        def creator(label_comment_uri):
            if not label_comment_uri:
                return

            label, comment, uri = label_comment_uri

            if not label:
                return

            if not uri:
                uri = uri_gen = self.doc.infGenerateTemplateUri(label)
            else:
                uri_gen = None

            annotations = {}
            if self.doc.annotations_by_name.get('defaultRdsId'):
                annotations[self.doc.annotations_by_name.get('defaultRdsId')] = self.doc.infDefaultRdsIdTemplate(uri_gen)

            self.doc << actions.AddTemplate(self.doc, {'uri': uri, 'name': label, 'comment':comment, 'supertemplate': self.uri, 'annotations': annotations})
        tpl = self.doc.grTemplateGetDesc(self.uri)
        dialogs.CreateTemplate(creator, supertemplate=tpl['name'])
        return True

    def GetContent(self):
        if self.is_property:
            return [self.key]
        return [self.uri]

    def GetPropertyUri(self):
        if self.key:
            return self.key.p
        return None

    def GetResolvableUri(self):
        return self.uri

    def OnDestroy(self):
        wizard.Unsubscribe((self.doc, self.uri), self)
        TreeNode.OnDestroy(self)

    def OnFirstAccess(self):
        self.doc.grNeedRelationships(self.uri)

        if self.reason_pattern or self.reason_uris:
            pattern_reason_node = PatternResultNode(self, tm.main.reason)
            for v in self.reason_pattern:
                if v[1]:
                    if getattr(v[1], 'has_literal', False):
                        PatternsLiteralNode(pattern_reason_node, v[1], prefix = '{0}: '.format(v[0]))
                    else:
                        EntityNode(pattern_reason_node, v[1], prefix = '{0}: '.format(v[0]))
            for v in self.reason_uris:
                EntityNode(pattern_reason_node, v)

        if not appconfig.get('show_simple', False):
            if appconfig.get('show_properties', True):
                self.propnode = PropertiesNode(self)
            if appconfig.get('show_relationships', True):
                self.relnode = RelationshipsNode(self)
            if appconfig.get('show_patterns', True) and getattr(self.doc, 'doc_connection', None) is None:
                self.patternsnode = PatternsNode(self)

        self.UpdateProperties()
        self.UpdateRelationships()
        self.UpdatePatterns()
        self.UpdateSimplePatterns()
        self.UpdateTemplate()

    def W_EntityDestroyed(self, doc, obj_uri):
        self.Destroy()

    def W_EntityPropertiesChanged(self, doc, obj_uri, prop_new = None, prop_old =None):

        if prop_old and prop_new and prop_old.has_literal and prop_new.has_literal:
            if self.propnode:
                node = self.properties.pop(prop_old, None)
                if node:
                    self.properties[prop_new] = node
                    node.SetPropertyKey(prop_new)
                else:
                    self.properties[prop_new] = LiteralProperty(self.propnode, prop_new)
                    
            props = self.GetPropsContent()
            if props:
                name_idx = None
                for i, v in enumerate(props):
                    if v.prop == prop_old:
                        self.RefreshPropByIndex(i, v.name, prop_new.v, prop_new, True)
                        break
        else:
            self.RefreshProps()

        self.UpdateProperties()

    def W_EntityRelationshipsChanged(self, doc, obj_uri):
        self.UpdateTemplate()
        self.UpdateRelationships()

    def UpdateProperties(self):
        props = self.doc.grTriplesForSubj(self.uri)

        for t in props:
            if self.properties.get(t):
                continue
            if self.propnode:
                if t.has_literal:
                    self.properties[t] = LiteralProperty(self.propnode, t)
                else:
                    self.properties[t] = EntityNode(self.propnode, t.o, key=t, prefix=self.doc.infGetPropertyName(t.p, t.p)+' = ', is_prop = True)
            else:
                self.properties[t] = False

        for key, node in self.properties.items():
            if key not in props:
                if node:
                    node.Destroy()
                del self.properties[key]

        if self.propnode:
            verify = self.doc.infVerifyEntity(self.uri)
            self.propnode.vis_icon2 = None
            self.propnode.vis_tooltip = None
            if verify:
                if None in verify:
                    self.propnode.vis_icon2 = 'warning_small' if verify[None][0] < 2 else 'error_small'
                    self.propnode.vis_tooltip = verify[None][1]

            for k, v in self.properties.iteritems():
                if v:
                    if verify and k in verify:
                        v.vis_icon2 = 'warning_small' if verify[k][0] < 2 else 'error_small'
                        v.vis_tooltip = verify[k][1]
                    else:
                        v.vis_icon2 = None
                        v.vis_tooltip = None
                    v.Refresh()

            self.propnode.Sort()
            self.propnode.Refresh()

        name, tp_label, icon  = self.doc.infGetEntityVisual(self.uri)

        if isinstance(name, list):
            self.names = name
            name = ', '.join(name)
        else:
            self.names = []

        props = self.GetPropsContent()
        if props:
            name_idx = 2
            name_copy = list(self.names)
            idx = 0
            for v in props:
                if v.name == tm.main.name and v.prop == None:
                    if name_copy:
                        self.RefreshPropByIndex(idx, tm.main.name, name_copy.pop(0))
                        name_idx = idx
                    else:
                        self.RemovePropByIndex(idx)
                        idx -= 1
                idx += 1
            for i, n in enumerate(name_copy):
                self.InsertPropByIndex(name_idx+i+1, tm.main.name, n)

        if tp_label:
            self.vis_label = self.prefix+name+' : '+tp_label+self.suffix
        else:
            self.vis_label = self.prefix+name+self.suffix
        self.vis_icon = icon
        self.Refresh()

    def UpdateTemplate(self):
        if self.treenode_track_first_access:
            return
        if self.doc.grIsTemplate(self.uri):
            if not self.rolesnode:
                self.rolesnode = RolesNode(self)
                self.RemoveChild(self.rolesnode)
                self.InsertChild(0, self.rolesnode)
            else:
                self.rolesnode.Update()
            sup = self.doc.grTemplateGetSuper(self.uri)
            if sup:
                if not self.supertemplatenode or self.supertemplatenode.uri != sup:
                    if self.supertemplatenode:
                        self.supertemplatenode.Destroy()
                    self.supertemplatenode = EntityNode(self, sup)
                    self.RemoveChild(self.supertemplatenode)
                    self.InsertChild(0, self.supertemplatenode)
            elif self.supertemplatenode:
                self.supertemplatenode.Destroy()
        else:
            if self.rolesnode:
                self.rolesnode.Destroy()
                self.rolesnode = None
            if self.supertemplatenode:
                self.supertemplatenode.Destroy()
                self.supertemplatenode = None

    def UpdateRelationships(self):
        if not self.relnode:
            return
        newrels = self.doc.grTriplesForObj(self.uri)
        self.relationships = list(newrels)
        self.relnode.ResetFolder(self.relationships)

    def UpdateSimplePatterns(self):
        if not appconfig.get('show_simple', False) or getattr(self.doc, 'doc_connection', None):
            return
        self.DestroyChildren()
        patterns_env = appdata.environment_manager.GetPatternsEnv(self.doc, appdata.project.patterns_filter)
        patterns = patterns_env.get(self.uri, self.doc)
        gnodes = {}
        for pat, results in patterns.iteritems():
            sign = patterns_env.get_signature(pat)
            for k, res in results.IterResults():
                reasons = results.GetReasons(k)

                self_count = 0
                for v in res:
                    if v[1] == self.uri:
                        self_count += 1

                for v in res:
                    if v[1] == self.uri and self_count == 1:
                        continue
                    if v[0] not in sign:
                        continue

                    pre = '%s '%sign[v[0]]['inverse_title']
                    if getattr(v[1], 'has_literal', False):
                        for node in self.children:
                            if isinstance(node, PatternsLiteralNode) and node.prefix == pre and node.value == v[1]:
                                break
                        else:
                            PatternsLiteralNode(self, v[1], prefix = pre, reason_pattern=res, reason_uris = reasons)
                    else:
                        for node in self.children:
                            if isinstance(node, EntityNode) and node.prefix == pre and node.uri == v[1]:
                                break
                        else:
                            EntityNode(self, v[1], prefix = pre, reason_pattern=res, reason_uris = reasons)
        self.Sort()
        self.Refresh()

    def UpdatePatterns(self):
        if self.patternsnode is None:
            return
        self.patternsnode.DestroyChildren()
        patterns_env = appdata.environment_manager.GetPatternsEnv(self.doc, appdata.project.patterns_filter)
        patterns = patterns_env.get(self.uri, self.doc)
        gnodes = {}
        for pat, results in patterns.iteritems():
            sign = patterns_env.get_signature(pat)
            for k, res in results.IterResults():
                reasons = results.GetReasons(k)

                self_count = 0
                for v in res:
                    if v[1] == self.uri:
                        self_count += 1

                for v in res:
                    if v[1] == self.uri and self_count == 1:
                        continue
                    if v[0] not in sign:
                        continue
                    if sign[v[0]] in gnodes:
                        grnode = gnodes[sign[v[0]]]['inverse_title']
                    else:
                        grnode = PatternsGroupNode(self.patternsnode, sign[v[0]]['inverse_title'])
                        gnodes[sign[v[0]]['inverse_title']] = grnode
                    if getattr(v[1], 'has_literal', False):
                        found = None
                        for node in grnode.children:
                            if isinstance(node, PatternsLiteralNode) and node.value == v[1]:
                                found = node
                                break
                        if not found:
                            PatternsLiteralNode(grnode, v[1], reason_pattern=res, reason_uris = reasons)
                    else:
                        found = None
                        for node in grnode.children:
                            if isinstance(node, EntityNode) and node.uri == v[1]:
                                found = node
                                break
                        if not found:
                            EntityNode(grnode, v[1], reason_pattern=res, reason_uris = reasons)
                    grnode.Sort()
                    grnode.Refresh()
        self.patternsnode.Refresh()

    def DoDelete(self):
        if not self.doc.CanEdit():
            return
        if self.key:
            self.doc << actions.RemoveProperty(self.doc, self.key)
        else:
            self.doc << actions.RemoveEntity(self.doc, self.uri)

    def Drag(self):
        if self.doc.grIsTemplate(self.uri):
            return dict(uri=self.uri, template = True)
        return dict(uri=self.uri)

    def CanDrop(self, data = None, before=None, after=None):
        return self.key and self.doc.CanEdit()

    def Drop(self, data, before=None, after=None):
        if not self.key or not self.doc.CanEdit():
            return False
        if data.get('uri'):
            uri = data['uri']
        elif data.get('qname'):
            uri = self.doc.infExpandQname(data['qname'])
        else:
            return False

        self.doc << actions.ChangeProperty(self.doc, self.key.with_o(uri), self.key)
        return True

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
            self.SetProp(pn, k.l, k, True)

    def PropChanged(self, prop, value):
        if prop in self.properties:
            self.doc << actions.ChangeProperty(self.doc, prop.with_l(value), prop)

    def CanReload(self):
        return True

    def DoReload(self):
        if self.treenode_track_first_access:
            return
        self.DestroyChildren()
        self.properties = {}
        self.relationships = {}
        self.propnode = None
        self.relnode = None
        self.patternsnode = None
        self.rolesnode = None
        self.supertemplatenode = None
        self.OnFirstAccess()

class PropertiesNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    vis_label = tm.main.properties

    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc

    def GetContent(self):
        return [self.parent.uri]

    def CanDrop(self, data = None, before=None, after=None):
        if not self.doc.CanEdit():
            return False

        if data.get('template') == True:
            return False

        if not data.get('uri') and not data.get('qname'):
            return False

        return True

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False

        if data.get('template') == True:
            return False

        if 'qname' in data:
            uri = self.doc.infExpandQname(data['qname'])
        elif 'uri' in data:
            uri = data['uri']
        else:
            return False

        props = {}
        roles = self.doc.infGetAvailableProperties(self.parent.uri)
        if not roles:
            return False
        for r in roles.itervalues():
            if not r['is_literal']:
                props[r['name']] = r

        def creator(prop_obj):
            if not prop_obj:
                return
            prop, obj = prop_obj
            if not prop or not obj:
                return
            p = props[prop]['uri']
            self.doc << actions.AddProperty(self.doc, ObjectTriple.of(self.parent.uri, p, uri))

        if 'qname' in data:
            dialogs.AddAsProperty(creator, uri, ['rdf:type'])
        else:
            dialogs.AddAsProperty(creator, uri, props.keys())

        return False

    def DoAdd(self):
        roles = self.doc.infGetAvailableProperties(self.parent.uri)
        if not roles:
            return
        props = {}
        for r in roles.itervalues():
            if r['is_literal']:
                props[r['name']] = r

        def creator(prop_value):
            if not prop_value:
                return
            prop, value = prop_value
            if not prop or not value:
                return
            p = props[prop]['uri']
            datatype = props[prop].get('type_uri')
            if datatype:
                k = DatatypeQuad.of(self.parent.uri, p, value, datatype)
            else:
                k = LiteralTriple.of(self.parent.uri, p, value)
            self.doc << actions.AddProperty(self.doc, k)
        dialogs.AddProperty(creator, props.keys())

class RelationshipsNode(FolderNode):
    treenode_show_as_nonempty = True
    vis_icon = 'iso_group'
    vis_label = tm.main.relationships
    def __init__(self, parent):
        FolderNode.__init__(self, parent)

    def MakeItem(self, items, idx):
        t = items[idx]
        propname = self.doc.infGetPropertyName(t.p, self.doc.infMakeQname(t.p, default=t.p))
        EntityNode(self, t.s, prefix = '{0} for '.format(propname))
        return True

    def GetContent(self):
        return [t.s for t in self.items]


class PatternsNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    vis_label = tm.main.patterns
    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
    def CanReload(self):
        return True
    def DoReload(self):
        self.parent.UpdatePatterns()

class PatternsGroupNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    def __init__(self, parent, name):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.vis_label = name


class LiteralProperty(TreeNode):
    vis_icon = 'iso_literal'
    is_property = True

    def __init__(self, parent, key):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.SetPropertyKey(key)

    def GetContent(self):
        return [self.key]

    def GetPropertyUri(self):
        if self.key:
            return self.key.p
        return None

    def SetPropertyKey(self, key):
        self.key = key
        self.name = self.doc.infGetPropertyName(self.key.p, self.key.p)
        if (kb.split_uri(self.key.p)[0] in kb.part2_all_ns and kb.split_uri(self.key.p)[1] in kb.part2_object_properties) or (self.key.p in [prop['uri'] for prop in self.doc.infGetAvailableProperties(self.parent.parent.uri).itervalues()]):
            self.vis_icon = 'iso_annotation'
        self.vis_label = '{0} = "{1}"'.format(self.name, self.key.l)
        self.Refresh()
        self.RefreshProps()

    def DoDelete(self):
        self.doc << actions.RemoveProperty(self.doc, self.key)

    def SetupProps(self):
        self.SetProp(tm.main.prop_uri, self.key.p)
        self.SetProp(tm.main.prop_name, self.name)
        self.SetProp(tm.main.value, self.key.l, 'value', True)

    def PropChanged(self, prop, value):
        if prop=='value':
            self.doc << actions.ChangeProperty(self.doc, self.key.with_l(value), self.key)

class PatternsLiteralNode(TreeNode):
    vis_icon = 'iso_annotation'

    def __init__(self, parent, value, prefix = '', reason_uris=set(), reason_pattern = None):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.value = value
        self.prefix = prefix
        self.reason_uris = reason_uris
        self.reason_pattern = reason_pattern
        self.vis_label = self.prefix + '"{0}"'.format(self.value)
        if self.reason_pattern or self.reason_uris:
            pattern_reason_node = PatternResultNode(self, tm.main.reason)
            for v in self.reason_pattern:
                if v[1]:
                    if getattr(v[1], 'has_literal', False):
                        PatternsLiteralNode(pattern_reason_node, v[1], prefix = '{0}: '.format(v[0]))
                    else:
                        EntityNode(pattern_reason_node, v[1], prefix = '{0}: '.format(v[0]))
            for v in self.reason_uris:
                EntityNode(pattern_reason_node, v)
        self.Refresh()

    def SetupProps(self):
        self.SetProp('Value', self.value, True)

class ProgSearchNode(FolderNode):
    treenode_show_as_nonempty = True
    treenode_show_count = True
    vis_icon = 'iso_group'
    msg_found = tm.main.found_folder
    msg_found_for = tm.main.found_for_folder
    show_num = 1000

    def __init__(self, parent, finder, name=None, console_text=None):
        FolderNode.__init__(self, parent)
        self.doc = parent.doc
        self.name = name
        self.console_text = console_text
        if self.name:
            self.vis_label = self.msg_found_for.format(self.name)
        else:
            self.vis_label = self.msg_found
        self.finder = finder
        self.DoReload()
        self.SetCurrent()

    def DoDelete(self):
        self.Destroy()

    def CanReload(self):
        return True

    def DoReload(self):
        try:
            self.DestroyChildren()
            self.ResetFolder(None)
            self.treenode_loading = True
            self.Refresh()
            self.parent.Expand()

            items = self.finder()

            if self.name:
                appdata.console_locals[self.name] = items

            if isinstance(items, PatternDict):
                self.ResetFolder(items, items.ResultsCount())
            else:
                items = list(items)

                treest = False
                for ent in items:
                    if len(ent.split('|'))==2:
                        treest = True
                        break

                if treest:
                    dd = defaultdict(lambda: set())
                    for ent in items:
                        tt = ent.split('|')
                        if len(tt)!=2:
                            EntityNode(self, ent, prefix=tm.main.found_prefix)
                            continue
                        dd[tt[1]].add(tt[0])
                    for (k, v) in dd.iteritems():
                        nn = EntityNode(self, k, prefix=tm.main.group_prefix, suffix = ' ({0})'.format(len(v)))
                        for a in v:
                            EntityNode(nn, a, prefix=tm.main.found_prefix)
                    self.Sort()
                else:
                    self.ResetFolder(items)

        finally:
            self.treenode_loading = False
            self.Refresh()

    def GetContent(self):
        if isinstance(self.items, list):
            return [v.split('|')[-1] for v in self.items]
        return None

    def MakeItem(self, items, idx):
        if isinstance(items, PatternDict):
            r = items.GetResult(idx)
            prn = PatternResultNode(self, tm.main.patterns_result.format(idx+1))
            for v in r:
                if getattr(v[1], 'has_literal', False):
                    PatternsLiteralNode(prn, v[1], prefix = '{0}: '.format(v[0]))
                else:
                    EntityNode(prn, v[1], prefix = '{0}: '.format(v[0]))
            prn.Expand()
            return True
        else:
            return FolderNode.MakeItem(self, items, idx)

    def SetupProps(self):
        if self.name:
            self.SetProp(tm.main.name, self.name)
        if self.console_text:
            self.SetProp(tm.main.console_text, self.console_text)

class PatternResultNode(TreeNode):
    treenode_show_count = False
    vis_icon            = 'iso_group'
    def __init__(self, parent, label):
        TreeNode.__init__(self, parent)
        self.vis_label = label
        self.doc = parent.doc
        self.Refresh()

class RolesNode(TreeNode):
    treenode_show_count = True
    vis_label = tm.main.roles
    vis_icon = 'iso_group'

    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.uri = parent.uri
        self.Update()

    def W_EntityPropertiesChanged(self, doc, obj_uri, prop_new = None, prop_old =None):
        self.Update()

    def W_TemplateRolesChanged(self, doc, tpl_uri, role_name=None):
        self.Update()

    def OnDestroy(self):
        wizard.UnsubscribeAll(self)
        TreeNode.OnDestroy(self)

    def Update(self):
        wizard.UnsubscribeAll(self)
        subscribe_uris = set()
        for t in self.doc.grCollectEntityTriples(self.uri, True):
            subscribe_uris.add(t.s)
        for s in subscribe_uris:
            wizard.Subscribe((self.doc, s), self)

        roles = self.doc.grGetTemplateRoles(self.uri)
        found = set()

        for c in self.children:
            if c.role['name'] in roles:
                c.Update(roles[c.role['name']])
                found.add(c.role['name'])
            else:
                c.Destroy()

        for r in roles.viewkeys() - found:
            RoleNode(self, roles[r])
        self.Sort()
        self.Refresh()

    def DoAdd(self):
        def creator(label_comment_uri):
            if not label_comment_uri:
                return
            label, comment, uri = label_comment_uri
            if not label:
                return

            if not uri:
                uri = uri_gen = self.doc.infGenerateTemplateRoleUri(label)
            else:
                uri_gen = None

            annotations = {}
            if self.doc.annotations_by_name.get('defaultRdsId'):
                annotations[self.doc.annotations_by_name.get('defaultRdsId')] = self.doc.infDefaultRdsIdTemplate(uri_gen)

            self.doc << actions.AddTemplateRole(self.doc, self.uri, {'name': label, 'comment': comment, 'uri': uri, 'type_uri': kb.ns_xsd+'string', 'is_literal': True, 'annotations': annotations})
            self.Expand()
        dialogs.AddRole(creator)

class RoleNode(TreeNode):

    def __init__(self, parent, role):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.uri = parent.uri
        self.restriction_node = None
        self.Update(role)

    def Update(self, role):
        self.role = role
        type_uri = self.role['type_uri']
        if not self.restriction_node or self.restriction_node.uri != type_uri:
            if self.restriction_node:
                self.restriction_node.Destroy()
            self.restriction_node = EntityNode(self, type_uri)
        self.doc.grNeedProperties(type_uri)
        self.doc.grNeedProperties(self.role['uri'])
        restricted_by_value = self.role.get('restricted_by_value', False)
        type_label, type_icon = self.doc.infGetRestrictionNameAndIcon(type_uri, restricted_by_value)
        if restricted_by_value:
            self.vis_label = '{0}. {1} = {2}'.format(self.role['index'], self.role['name'], type_label)
        else:
            self.vis_label = '{0}. {1} : {2}'.format(self.role['index'], self.role['name'], type_label)
        self.vis_icon = type_icon
        self.type_label = type_label
        self.Refresh()

    def GetResolvableUri(self):
        return self.role['type_uri']

    def SetupProps(self):
        self.SetProp(tm.main.index, str(self.role['index']))
        self.SetProp(tm.main.uri, self.role['uri'])
        self.SetProp(tm.main.name, self.role['name'], 'name')
        self.SetProp(tm.main.comment, self.role['comment'], 'comment', True)
        if self.role['annotations']:
            for k, v in self.role['annotations'].iteritems():
                ann_name = k
                prop = self.doc.props_by_uri.get(k)
                if prop:
                    ann_name = prop['name']
                self.SetProp(ann_name, v, None, True)
        self.SetProp(tm.main.restriction, self.type_label)
        self.SetProp(tm.main.restricted_by_value, self.role.get('restricted_by_value', False), 'restricted_by_value')

    def PropChanged(self, prop, value):
        if not self.doc.CanEdit():
            return False
        if prop == 'name':
            role_name = self.role['name']
            self.role[prop] = value
            self.doc << actions.ChangeTemplateRoleName(self.doc, self.uri, role_name, value)
        else:
            self.role[prop] = value
            self.doc << actions.UpdateTemplateRole(self.doc, self.uri, self.role)

    def CanDrop(self, data = None, before=None, after=None):
        return self.doc.CanEdit()

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False

        rolename = data.get('rolename')
        if rolename:
            uri = data.get('templateuri')

            if not rolename or not uri or uri != self.uri:
                return False

            node = None
            for c in self.parent.children:
                if c.role['name'] == rolename:
                    node = c

            if not node:
                return False

            wasindex = node.role['index']
            newindex = self.role['index']

            if newindex < 0:
                newindex = 0

            roles = self.doc.grGetTemplateRoles(self.uri)
            maxindex = max([v['index'] for v in roles.itervalues()])

            if newindex > maxindex:
                newindex = maxindex

            alst = []

            for v in roles.itervalues():
                if v['index'] == wasindex:
                    alst.append(actions.ChangeTemplateRoleIndex(self.doc, self.uri, v['name'], newindex))
                elif v['index'] >= newindex and v['index'] <= wasindex:
                    alst.append(actions.ChangeTemplateRoleIndex(self.doc, self.uri, v['name'], v['index']+1))
                elif v['index'] >= wasindex and v['index'] <= newindex:
                    alst.append(actions.ChangeTemplateRoleIndex(self.doc, self.uri, v['name'], v['index']-1))

            self.tree.UnselectAll()
            self.doc << MultiAction(alst)
            return True

        type_uri = data.get('uri')
        if not type_uri:
            qname = data.get('qname')
            if qname:
                type_uri = self.doc.infExpandQname(qname)
        if not type_uri:
            return False

        self.role['type_uri'] = type_uri
        self.role['is_literal'] = type_uri.startswith(kb.ns_xsd)
        self.doc << actions.UpdateTemplateRole(self.doc, self.uri, self.role)
        return True

    def Drag(self):
        return dict(uri = self.role['uri'], templateuri = self.uri, rolename = self.role['name'])

    def DoDelete(self):
        self.Unselect()
        self.doc << actions.DeleteTemplateRole(self.doc, self.uri, self.role['name'])

    def ViewType(self):
        return appdata.environment_manager.FindViewType(self.doc, self.role['uri'])