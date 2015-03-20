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
from framework.tree import Tree, DefaultTreeDelegate, TreeEditor
from framework.treenode import TreeNode
from iso15926.common.filteredview import FilteredView
import iso15926.patterns.patterns_actions as actions
from iso15926.patterns.patterns_actions import GenPartName
from framework.props import PropPatternsEdit, PropDictEdit, PropModulesEdit
from framework.util import HashableDict
import iso15926.kb as kb
from framework.document import MultiAction
import framework.util as util
from framework.util import IsUri, IsPyVariable
import copy
from iso15926.kb.dmviews import XSDTypesView, Part2TypesView

class PatternsView(FilteredView):

    msg_filterdesc = tm.main.search_in
    msg_filteroptions = [tm.main.search_in_labels, tm.main.search_in_comments, tm.main.search_in_mapping]
    msg_filtermulti = True

    def Search(self, value):
        self.Seed()

    def Seed(self):
        self.wnd_tree.Clear()
        self.provnode = PatternsDocNode(self.wnd_tree, self.document)

        if self.bound_uri:
            PatternNode(self.provnode, self.document.patterns[self.bound_uri])
        else:
            fi = self.wnd_filter.value.lower().strip()
            shown = set()
            if 0 in self.wnd_filter.selection:
                for k, v in self.document.patterns.iteritems():
                    if fi in k.lower():
                        shown.add(k)
                        PatternNode(self.provnode, v)

            if fi:
                if 1 in self.wnd_filter.selection:
                    for k, v in self.document.patterns.iteritems():
                        if k in shown:
                            continue
                        if fi in v.get('comment', '').lower():
                            shown.add(k)
                            PatternNode(self.provnode, v)

                if 2 in self.wnd_filter.selection:
                    for k, v in self.document.patterns.iteritems():
                        if k in shown:
                            continue
                        found = set()
                        for o in v['options']:
                            for p in o['parts']:
                                for m in p.itervalues():
                                    if isinstance(m, basestring):
                                        if fi in m.lower():
                                            found.add(o)
                                            break
                                    else:
                                        for e in m:
                                            if fi in e.lower():
                                                found.add(o)
                                                break
                                        else:
                                            continue
                                        break
                        if found:
                            node = PatternNode(self.provnode, v)
                            node.Expand()
                            shown.add(k)
                            for c in node.children:
                                if hasattr(c, 'option') and c.option in found:
                                    c.Expand()
                            
        self.provnode.Sort()
        self.provnode.Expand()
        self.provnode.Update()

    def CanPaste(self):
        if not self.document.CanEdit():
            return False
        selected = self.wnd_tree.selected

        if util.CheckClipboard('application/x-dot15926-patterns'):
            if not selected or (len(selected) == 1 and selected[0] is self.provnode):
                return True
        elif util.CheckClipboard('application/x-dot15926-pattern-options'):
            if selected:
                if all(isinstance(x, PatternNode) for x in selected):
                    return True
        elif util.CheckClipboard('application/x-dot15926-pattern-parts'):
            if selected:
                if all(isinstance(x, PatternOptionEntryNode) for x in selected):
                    return True

    def Paste(self):
        if not self.document.CanEdit():
            return

        selected = self.wnd_tree.selected
        if util.CheckClipboard('application/x-dot15926-patterns'):
            if not selected or (len(selected) == 1 and selected[0] is self.provnode):
                lst = []
                data = util.GetClipboard('application/x-dot15926-patterns')
                for v in data:
                    lst.append(actions.DocumentModifyPatterns(self.document, v, new=False))
                self.document<<MultiAction(lst)

        elif util.CheckClipboard('application/x-dot15926-pattern-options'):
            if selected:
                if all(isinstance(x, PatternNode) for x in selected):
                    lst = []
                    data = util.GetClipboard('application/x-dot15926-pattern-options')
                    for x in selected:
                        for v in data:
                            lst.append(actions.DocumentModifyPatternOptions(x.pattern, v, new=False))
                    self.document<<MultiAction(lst)


        elif util.CheckClipboard('application/x-dot15926-pattern-parts'):
            if selected:
                if all(isinstance(x, PatternOptionEntryNode) for x in selected):
                    lst = []
                    data = util.GetClipboard('application/x-dot15926-pattern-parts')
                    for x in selected:
                        for v in data:
                            lst.append(actions.DocumentModifyPatternOptionParts(x.option, v))
                    self.document<<MultiAction(lst)


    def CanCopy(self):
        selected = self.wnd_tree.selected
        if not selected:
            return False

        if all(isinstance(x, PatternNode) for x in selected):
            return True

        if all(isinstance(x, PatternOptionEntryNode) for x in selected):
            return True

        if all(isinstance(x, PatternOptionPartNode) for x in selected):
            return True            

        return False

    def CanCut(self):
        if not self.document.CanEdit():
            return False
        selected = self.wnd_tree.selected
        if not selected:
            return False

        if all(isinstance(x, PatternNode) for x in selected):
            return True

        if all(isinstance(x, PatternOptionEntryNode) for x in selected):
            return True

        if all(isinstance(x, PatternOptionPartNode) for x in selected):
            return True            

        return False


    def Copy(self):
        selected = self.wnd_tree.selected

        if not selected:
            return

        if all(isinstance(x, PatternNode) for x in selected):
            data = []
            for v in selected:
                data.append(v.pattern)
            util.SetClipboard('', {'application/x-dot15926-patterns': data})

        if all(isinstance(x, PatternOptionEntryNode) for x in selected):
            data = []
            for v in selected:
                data.append(v.option)
            util.SetClipboard('', {'application/x-dot15926-pattern-options': data})

        if all(isinstance(x, PatternOptionPartNode) for x in selected):
            data = []
            for v in selected:
                data.append(v.part)
            util.SetClipboard('', {'application/x-dot15926-pattern-parts': data})        

    def Cut(self):
        selected = self.wnd_tree.selected

        if not selected:
            return

        if all(isinstance(x, PatternNode) for x in selected):
            data = []
            lst = []
            for v in selected:
                data.append(v.pattern)
                lst.append(actions.DocumentModifyPatterns(self.document, v.pattern, True))
            util.SetClipboard('', {'application/x-dot15926-patterns': data})
            self.document<<MultiAction(lst)

        if all(isinstance(x, PatternOptionEntryNode) for x in selected):
            data = []
            lst = []
            for v in selected:
                data.append(v.option)
                lst.append(actions.DocumentModifyPatternOptions(v.pattern, v.option, True))
            util.SetClipboard('', {'application/x-dot15926-pattern-options': data})
            self.document<<MultiAction(lst)

        if all(isinstance(x, PatternOptionPartNode) for x in selected):
            data = []
            lst = []
            for v in selected:
                data.append(v.part)
                lst.append(actions.DocumentModifyPatternOptionParts(v.option, v.part, True))
            util.SetClipboard('', {'application/x-dot15926-pattern-parts': data})
            self.document<<MultiAction(lst)

class PatternsDocNode(TreeNode):
    vis_icon = 'patterns_doc'
    vis_bold = True

    def __init__(self, parent, doc):
        TreeNode.__init__(self, parent)
        self.doc = doc
        wizard.Subscribe(self.doc, self)
        self.Update()

    def OnDestroy(self):
        wizard.Unsubscribe(self.doc, self)
        TreeNode.OnDestroy(self)

    def W_PatternAdded(self, doc, pattern, new = False):
        node = PatternNode(self, pattern)
        if new:
            node.Edit()

    def OnSelect(self, select):
        if select:
            self.doc.ShowProps()

    def CanReload(self):
        return True

    def Update(self):
        self.vis_label = self.doc.GetLabel() + ' [{0}/{1}]'.format(len(self.children), len(self.doc.patterns))
        self.Refresh()

    def DoReload(self):
        for c in self.children:
            m = getattr(c, 'DoReload', None)
            if m:
                m()

    def DoAdd(self):
        i = 0
        while True:
            name_gen = 'UnnamedPattern%i'%i
            if name_gen not in self.doc.patterns:
                break
            i += 1

        pattern = HashableDict({
          'name': name_gen,
          'comment': '',
          'signature': {},
          'options': []
        })

        self.doc << actions.DocumentModifyPatterns(self.doc, pattern)


class PatternNameEditor(TreeEditor):
    def __init__(self, parent, description):
        TreeEditor.__init__(self, parent)
        self.lineedit = QLineEdit()
        self.layout().insertWidget(0, self.lineedit)
        self.layout().insertWidget(1, QLabel(description))
        self.setFocusProxy(self.lineedit)

    def SetText(self, txt):
        self.lineedit.setText(txt)

    def GetText(self):
        return self.lineedit.text().encode('utf-8')

class PatternNode(TreeNode):
    treenode_show_as_nonempty = True
    treenode_track_first_access = True
    treenode_editable = True
    vis_icon = 'pattern_ico'

    def __init__(self, parent, pattern):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.pattern = pattern
        wizard.Subscribe(self.pattern, self)
        self.Update()

    def OnFirstAccess(self):
        self.signaturenode = PatternSignatureNode(self)
        for option in self.pattern['options']:
            PatternOptionEntryNode(self, option)

    def CanReload(self):
        return True

    def DoReload(self):
        for c in self.children:
            m = getattr(c, 'DoReload', None)
            if m:
                m()

    def CreateEditor(self, tree):
        editor = PatternNameEditor(tree, tm.main.name)
        editor.SetText(self.pattern['name'])
        return editor

    def CommitData(self, editor):
        if not editor.GetText().strip():
            return False
        self.doc << actions.DocumentChangePatternName(self.doc, self.pattern, editor.GetText().strip())
        return True

    def W_PatternDeleted(self, pattern):
        self.Destroy()

    def OnDestroy(self):
        wizard.Unsubscribe(self.pattern, self)
        TreeNode.OnDestroy(self)

    def W_PatternNameChanged(self, pattern):
        self.Update()

    # def W_PatternSignatureChanged(self, pattern):
    #     self.Update()

    def W_PatternOptionAdded(self, pattern, option, new = False):
        idx = self.pattern['options'].index(option)
        before = None
        after  = None
        if idx + 1 < len(self.pattern['options']):
            before = self.pattern['options'][idx + 1]
        if idx > 0:
            after = self.pattern['options'][idx - 1]
        
        for i in self.children[1:]:
            if i.option == before:
                node = PatternOptionEntryNode(self, option, before = i)
                break
            elif i.option == after:
                node = PatternOptionEntryNode(self, option, after = i)
                break
        else:
            node = PatternOptionEntryNode(self, option)
        if new:
            node.Edit()

    def Update(self):
        self.RefreshProps()
        self.vis_label = self.pattern['name']
        self.Refresh()

    def SetupProps(self):
        self.SetProp(tm.main.pattern_name, self.pattern['name'], 'name')
        self.SetProp(tm.main.comment, self.pattern.get('comment', ''), 'comment', True)

    def PropChanged(self, prop, value):
        if prop == 'name':
            self.doc << actions.DocumentChangePatternName(self.doc, self.pattern, value)
        else:
            self.doc << actions.DocumentChangePatternProperty(self.doc, self.pattern, prop, value)
            self.RefreshProps()

    def DoAdd(self):
        self.Expand()
        option = HashableDict({'parts': []})
        self.doc << actions.DocumentModifyPatternOptions(self.pattern, option)

    def DoDelete(self):
        self.doc << actions.DocumentModifyPatterns(self.doc, self.pattern, True)

    def Drag(self):
        return dict(pattern=self.pattern['name'])

    def ViewType(self):
        return type('', (PatternsView,), dict(document=self.doc, bound_uri = self.pattern['name']))

class PatternSignatureNode(TreeNode):
    vis_label = tm.main.pattern_signature
    vis_icon = 'gears'
    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.pattern = parent.pattern
        wizard.Subscribe(self.pattern, self)
        for role in self.pattern['signature'].iterkeys():
            PatternSignatureItem(self, role)
        self.Refresh()

    def OnDestroy(self):
        wizard.Unsubscribe(self.pattern, self)

    def W_PatternSignatureChanged(self, pattern, role, old_role):
        for r in self.children:
            if r.role == old_role:
                if not role:
                    r.Destroy()
                else:
                    r.role = role
                    r.Update()
                break
        else:
            PatternSignatureItem(self, role)

    def DoAdd(self):
        node = PatternSignatureItem(self, '')
        self.Expand()
        node.Edit()
        return True

class PattternSignatureEditor(TreeEditor):

    def __init__(self, parent, roles, value):
        TreeEditor.__init__(self, parent)
        
        self.role = QComboBox(self)
        self.setFocusProxy(self.role)

        self.value = QLineEdit(self)

        self.role.setEditable(True)

        layout = QGridLayout()
        layout.setContentsMargins(QMargins())
        layout.setSpacing(0)
        layout.addWidget(self.role, 0, 0)
        layout.addWidget(QLabel(tm.main.role), 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setContentsMargins(0,0,0,0)
        self.layout().insertLayout(0, layout)

        #initialize
        self.role.addItems(roles)
        self.value.setText(value)

    def GetRoleAndValue(self):
        return self.role.currentText().encode('utf-8'), self.value.text().encode('utf-8')


class PatternSignatureItem(TreeNode):
    treenode_editable = True
    vis_icon = 'iso_literal'

    def __init__(self, parent, role):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.pattern = parent.pattern
        self.role = role
        self.Update()

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if self.IsSelected():
            for o in self.pattern['options']:
                wizard.W_HighlightPatternRole(o, self._role, False)
        self._role = value
        if self.IsSelected():
            for o in self.pattern['options']:
                wizard.W_HighlightPatternRole(o, self._role, True)

    def OnSelect(self, select):
        for o in self.pattern['options']:
            wizard.W_HighlightPatternRole(o, self.role, select)
        TreeNode.OnSelect(self, select)

    def CreateEditor(self, tree):
        editor = PatternNameEditor(tree, tm.main.name)
        editor.SetText(self.role)
        return editor

    def CommitData(self, editor):
        if not editor.GetText().strip():
            return False
        self.doc << actions.DocumentChangePatternName(self.doc, self.pattern, editor.GetText().strip())
        return True

    def Highlight(self, enable):
        if enable:
            self.SetColor(QColor("#99FF22"))
        else:
            self.SetColor(Qt.transparent)

    def DoAdd(self):
        pass

    def DoDelete(self):
        self.doc << actions.DocumentChangePatternSignature(self.pattern, None, None, self.role)

    def Update(self):
        self.vis_label = ''
        if self.role:
            self.vis_label = self.role
        self.Refresh()

    def CreateEditor(self, tree):
        editor = PatternNameEditor(tree, tm.main.name)
        editor.SetText(self.role)
        return editor

    def RejectData(self, editor):
        if not self.role:
            self.Destroy()

    def CommitData(self, editor):
        role = editor.GetText().strip()

        if not role:
            return False

        if not IsPyVariable(role):
            return False

        if role in self.pattern['signature'] and self.pattern['signature'][self.role] != self.pattern['signature'][role]:
            return

        self.PropChanged('name', role)
        return True

    def SetupProps(self):
        self.SetProp(tm.main.role, self.role, 'name')
        if self.role in self.pattern['signature']:
            desc = self.pattern['signature'][self.role]
            self.SetProp(tm.main.inverse_title, desc['inverse_title'], 'inverse_title')
            self.SetProp(tm.main.comment, desc.get('comment', ''), 'comment', True)

    def PropChanged(self, prop, value):
        if prop == 'name':
            data = copy.deepcopy(self.pattern['signature'])
            if self.role and self.role in data:
                desc = data[self.role]
                del data[self.role]
            else:
                desc = HashableDict({'comment': '',
                                      'inverse_title': ''})
            self.doc << actions.DocumentChangePatternSignature(self.pattern, value, desc, self.role)
        else:
            data = copy.deepcopy(self.pattern['signature'])
            desc = data[self.role]
            desc[prop] = value
            self.doc << actions.DocumentChangePatternSignature(self.pattern, self.role, desc, self.role)
        self.RefreshProps()

class PatternOptionEntryNode(TreeNode):
    treenode_editable = True
    vis_icon = 'option_ico'

    def __init__(self, parent, option, before = None, after = None):
        TreeNode.__init__(self, parent, before, after)
        self.doc = parent.doc
        self.pattern = parent.pattern
        self.option = option
        wizard.Subscribe(self.option, self)
        self.Update()
        for part in self.option['parts']:
            PatternOptionPartNode(self, part)

    def CanReload(self):
        return True

    def DoReload(self):
        for c in self.children:
            m = getattr(c, 'DoReload', None)
            if m:
                m()

    def Drag(self):
        if 'name' in self.option:
            return dict(pattern = '%s.%s'%(self.pattern['name'], self.option['name']))

    def W_HighlightPatternRole(self, option, role, enable):
        for r in self.parent.signaturenode.children:
            if r.role == role:
                r.Highlight(enable)

        for p in self.children:
            if 'self' in p.part and p.part['self'] == role:
                p.Highlight(enable)
            for r in p.children:
                if r.role == role:
                    r.Highlight(enable)

    def CreateEditor(self, tree):
        editor = PatternNameEditor(tree, tm.main.name)
        editor.SetText(self.option.get('name', tm.main.unnamed_option))
        return editor

    def CommitData(self, editor):
        if editor.GetText().strip() != tm.main.unnamed_option:
            self.doc << actions.DocumentChangePatternOptionName(self.pattern, self.option, editor.GetText().strip())
        else:
            self.doc << actions.DocumentChangePatternOptionName(self.pattern, self.option, '')
        return True

    def OnDestroy(self):
        wizard.Unsubscribe(self.option, self)
        TreeNode.OnDestroy(self)

    def W_PatternOptionDeleted(self, option):
        self.Destroy()

    def W_PatternOptionChanged(self, option):
        self.Update()

    def W_PatternOptionPartIndexChanged(self, option, part):
        for i in self.children:
            if i.part == part:
                self.RemoveChild(i)
                break
        else:
            return

        self.InsertChild(self.option['parts'].index(part), i)
        for i in self.children:
            i.Update()


    def W_PatternOptionPartAdded(self, option, part):
        for i in self.children:
            if i.part == part:
                for r in i.children:
                    r.Update()
                i.Update()
                return

        idx = self.option['parts'].index(part)
        before = None
        after  = None
        if idx + 1 < len(self.option['parts']):
            before = self.option['parts'][idx + 1]
        elif idx > 0:
            after = self.option['parts'][idx - 1]

        if before != None or after != None:
            for i in self.children:
                i.Update()
                if i.part == before:
                    PatternOptionPartNode(self, part, before = i)
                elif i.part == after:
                    PatternOptionPartNode(self, part, after = i)
        else:
            PatternOptionPartNode(self, part)

        for i in self.children:
            i.Update()

        self.Expand()

    def W_PatternOptionPartDeleted(self, option, part):
        for i in self.children:
            if i.part == part:
                i.Destroy()
            else:
                i.Update()

    def Update(self):
        name = self.option.get('name')
        if name:
            self.vis_label = name
            self.SetTextColor(Qt.black)
        else:
            self.vis_label = tm.main.unnamed_option
            self.SetTextColor(Qt.gray)
        self.Refresh()

    def DoAdd(self):
        part = HashableDict({'self': GenPartName(self.option)})
        self.doc << actions.DocumentModifyPatternOptionParts(self.option, part)

    def DoDelete(self):
        self.doc << actions.DocumentModifyPatternOptions(self.pattern, self.option, True)

    def SetupProps(self):
        name = self.option.get('name', '')
        self.SetProp(tm.main.option_name, name, 'name')

    def PropChanged(self, prop, value):
        if prop == 'name':
            self.doc << actions.DocumentChangePatternOptionName(self.pattern, self.option, value)

    def CanDrop(self, data = None, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        elif data.get('uri'):
            return True
        elif data.get('qname'):
            qname = data['qname']
            if qname.startswith('part2:'):
                return True
        elif data.get('pattern'):
            return True
        elif data.get('patternpart'):
            part = data['patternpart']
            if dict(part) not in [dict(x) for x in self.option['parts']]:
                return True
        return False

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        if data.get('uri'):
            value = appdata.datamodel.ResolveNameOrUri(data['uri'], None, not self.doc.use_names)
            part = HashableDict({'type': value, 'self': GenPartName(self.option)})
            node = PatternOptionPartNode(self, part)
            self.Expand()
            node.Expand()
            node.children[0].Edit()
            return True
        elif data.get('qname'):
            qname = data['qname']
            if qname.startswith('part2:'):
                qname = qname.replace(':', '.')
                part = HashableDict({'type': qname, 'self': GenPartName(self.option)})
                node = PatternOptionPartNode(self, part)
                self.Expand()
                node.Expand()
                node.children[0].Edit()
                return True
            else:
                return False
        elif data.get('pattern'):
            part = HashableDict({'type': 'patterns.' + data['pattern']})
            node = PatternOptionPartNode(self, part)
            self.Expand()
            node.Expand()
            node.children[0].Edit()
            return True
        elif data.get('patternpart'):
            part = data['patternpart']
            if dict(part) not in [dict(x) for x in self.option['parts']]:
                self.Expand()
                self.doc << actions.DocumentModifyPatternOptionParts(self.option, part) 
                return True
        else:
            return False

class PatternOptionPartNode(TreeNode):
    treenode_editable = True
    vis_icon = 'cube_yellow'

    def __init__(self, parent, part, before = None, after = None):
        TreeNode.__init__(self, parent, before, after)
        self.doc = parent.doc
        self.pattern = parent.pattern
        self.option = parent.option
        self.part = part
        wizard.Subscribe(self.part, self)
        self.Update()
        for role in self.part.iterkeys():
            if role != 'self':
                PatternRoleNode(self, role)

    def CanReload(self):
        return True

    def DoReload(self):
        self.Update()
        for c in self.children:
            m = getattr(c, 'DoReload', None)
            if m:
                m()

    def Highlight(self, enable):
        if enable:
            self.SetColor(QColor("#99FF22"))
        else:
            self.SetColor(Qt.transparent)

    def CreateEditor(self, tree):
        editor = PatternNameEditor(tree, tm.main.name)
        name = self.part.get('self', '')
        editor.SetText(name)
        return editor

    def CommitData(self, editor):
        name_old = self.part.get('self', '')
        name = editor.GetText().strip()

        if name in self.part:
            return False

        if name == name_old:
            return True

        if name_old and name:
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, 'self', name, action = actions.ROLE_BIND)
        elif name:
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, 'self', name, action = actions.ROLE_ADD)
        elif name_old:
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, 'self', action = actions.ROLE_DELETE)
        return True

    def OnSelect(self, select):
        TreeNode.OnSelect(self, select)
        if 'self' in self.part:
            wizard.W_HighlightPatternRole(self.option, self.part['self'], select)

    def CanDrop(self, data = None, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        elif 'uri' in data:
            return True
        elif 'pattern' in data:
            if 'type' in self.part:
                return False
            return True
        elif data.get('patternpart'):
            return True
        return False

    def Drag(self):
        return dict(patternpart = self.part)

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        if 'uri' in data:
            tp = None
            if 'type' in self.part:
                tp = self.part['type']
            value = appdata.datamodel.ResolveNameOrUri(data['uri'], tp, not self.doc.use_names)
            node = PatternRoleNode(self, '')
            self.Expand()
            node.Edit(value)
            return True
        elif 'pattern' in data:
            if 'type' in self.part:
                return False
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, 'type', 'patterns.' + data['pattern'], action = actions.ROLE_ADD)
            return True
        elif data.get('patternpart'):
            part = data['patternpart']
            lst = []
            try:
                parts = [dict(x) for x in self.option['parts']]
                idx = parts.index(dict(part))
                part = self.option['parts'][idx]
            except:
                lst.append(actions.DocumentModifyPatternOptionParts(self.option, part))
                idx = len(self.option['parts'])
            newidx = self.option['parts'].index(self.part)
            if newidx != idx:
                lst.append(actions.DocumentChangePatternOptionPartIndex(self.option, part, newidx))
            if lst:
                self.doc<<MultiAction(lst)
            return True
        else:
            return False

    def W_PatternOptionPartRoleDeleted(self, part, role):
        for i in self.children:
            if i.role == role:
                i.Destroy()
                break
        self.Update()

    def W_PatternOptionPartRoleAdded(self, part, role):
        if not role:
            return

        for i in self.children:
            if i.role == role:
                if role != 'self':
                    i.Update()
                else:
                    i.Destroy()
                return

        if role == 'self':
            self.Update()
            return

        node = PatternRoleNode(self, role)
        self.Update()
        self.Expand()

    def OnDestroy(self):
        wizard.Unsubscribe(self.part, self)
        TreeNode.OnDestroy(self)

    def Update(self):
        if 'type' in self.part and isinstance(self.part['type'], basestring) and self.part['type'].startswith('patterns.'):
            self.treenode_editable = False
        else:
            self.treenode_editable = True


        if self.part in self.option['parts']:
            idx = self.option['parts'].index(self.part) + 1
        else:
            idx = len(self.option['parts']) + 1

        name = self.part.get('self', '')
        icon = 'iso_unknown'

        uri, tp = None, None
        for k, v in self.part.iteritems():
            if k == 'uri':
                uri = v
            elif k == 'type':
                tp = v

        if uri:
            names = []
            for v in value2list(uri):
                n, icon = appdata.datamodel.GetNameAndIcon(v)
                names.append(n)
            name += '=%s'%', '.join(names)
        elif tp:
            if isinstance(tp, basestring) and tp.startswith('patterns.'):
                name += tp
                icon = 'pattern_ico'
            else:
                names = []
                for v in value2list(tp):
                    n, icon = appdata.datamodel.GetNameAndIcon(v)
                    names.append(n)
                name += ':%s'%', '.join(names)
                icon = kb.icons_map.get(icon, 'iso_unknown')

        self.vis_label = name
        self.vis_icon = icon
        self.Refresh()
        self.RefreshProps()

    def GetResolvableUri(self):
        value = self.part.get('uri', self.part.get('type'))
        if isinstance(value, basestring):
            if IsUri(value):
                return value
            else:
                path = value.split('.')
                if len(path) > 1:
                    return appdata.datamodel.GetEntityUri(path[0], path[1])

    def ViewType(self):
        value = self.part.get('uri', self.part.get('type'))
        if isinstance(value, basestring):
            if IsUri(value):
                return appdata.environment_manager.FindViewType(self.doc, value)
            else:
                path = value.split('.')
                if len(path) > 1:
                    if path[0] == 'part2':
                        return type('', (Part2TypesView,), dict(bound_uri='part2:'+path[1]))
                    elif path[0] == 'patterns':
                        if path[1] in self.doc.patterns:
                            return type('', (PatternsView,), dict(document=self.doc, bound_uri = path[1]))
                    else:
                        uri = appdata.datamodel.GetEntityUri(path[0], path[1])
                        if uri:
                           return appdata.environment_manager.FindViewType(self.doc, uri) 

    def DoAdd(self):
        node = PatternRoleNode(self, '')
        self.Expand()
        node.Edit()
        return True

    def DoDelete(self):
        self.doc << actions.DocumentModifyPatternOptionParts(self.option, self.part, True)

    def W_PatternOptionPartRoleChanged(self, part, old_role, role):
        if self.IsSelected() and role == 'self':
            wizard.W_HighlightPatternRole(self.option, old_role, False)
            wizard.W_HighlightPatternRole(self.option, role, True)

        for v in self.children:
            if v.role == old_role:
                v.role = role
                v.Update()
        self.Update()

    def SetupProps(self):
        name = self.part.get('self', '')
        self.SetProp(tm.main.pattern_role_mapping, name)


from framework.util import GenerateModel, ModelCompleter, GenerateSortedModel

class PattternRoleEditor(TreeEditor):

    def __init__(self, parent, roles, values, roles_model, values_model):
        TreeEditor.__init__(self, parent)

        self.role = QComboBox(self)
        self.setFocusProxy(self.role)

        self.value = QComboBox(self)

        self.role.setEditable(True)
        self.value.setEditable(True)

        self.role_completer = ModelCompleter(self)
        self.value_completer = ModelCompleter(self, True, '|')

        self.role_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.value_completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)

        self.role_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.value_completer.setCaseSensitivity(Qt.CaseInsensitive)

        self.role.lineEdit().setCompleter(self.role_completer)
        self.value.lineEdit().setCompleter(self.value_completer)

        layout = QGridLayout()
        layout.setContentsMargins(QMargins())
        layout.setSpacing(0)
        layout.addWidget(self.role, 0, 0)
        layout.addWidget(self.value, 1, 0)
        layout.addWidget(QLabel(tm.main.role), 0, 1)
        layout.addWidget(QLabel(tm.main.value), 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setContentsMargins(0,0,0,0)
        self.layout().insertLayout(0, layout)

        #initialize
        self.role.addItems(roles)
        self.value.addItems(values)
        if roles_model:
            self.role_completer.setModel(roles_model)
        if values_model:
            self.value_completer.setModel(values_model)

    def GetRoleAndValue(self):
        return self.role.currentText().encode('utf-8'), self.value.currentText().encode('utf-8')

def value2list(v):
    if isinstance(v, basestring):
        return [v]
    return v

def list2value(v):
    if isinstance(v, basestring):
        return v
    if len(v) == 1:
        return v[0]
    return v

class PatternRoleNode(TreeNode):
    vis_icon = 'cube_green'
    treenode_editable = True

    def __init__(self, parent, role):
        TreeNode.__init__(self, parent)
        self.doc = parent.doc
        self.pattern = parent.pattern
        self.option = parent.option
        self.part = parent.part
        self.role = role
        self.editor_value = None
        self.Update()

    def CanReload(self):
        return True

    def DoReload(self):
        self.Update()

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if self.IsSelected():
            wizard.W_HighlightPatternRole(self.option, self._role, False)
        self._role = value
        if self.IsSelected():
            if value not in ('uri', 'type'):
                wizard.W_HighlightPatternRole(self.option, self._role, True)

    def Edit(self, value = None):
        self.editor_value = value
        TreeNode.Edit(self)

    def ViewType(self):
        if self.role in ('type', 'uri'):
            return self.parent.ViewType()

    def OnSelect(self, select):
        TreeNode.OnSelect(self, select)
        if not select or self.role not in ('type', 'uri'):
            wizard.W_HighlightPatternRole(self.option, self.role, select)

    def Highlight(self, enable):
        if enable:
            self.SetColor(QColor("#99FF22"))
        else:
            self.SetColor(Qt.transparent)

    def Update(self):
        self.vis_label = self.role

        if not self.role:
            name, icon = '', 'iso_unknown'

        else:
            if isinstance(self.part[self.role], basestring) and self.part[self.role].startswith('patterns.'):
                name = self.part[self.role]
                icon = 'pattern_ico'
            else:
                tp = None
                if self.role not in ('type', 'uri'):
                    tp = self.part.get('type')

                names, icons = [], []
                for v in value2list(self.part[self.role]):
                    vname, vicon = appdata.datamodel.GetNameAndIcon(v, tp)
                    names.append(vname)
                    icons.append(vicon)

                name = '|'.join(names)
                icon = icons[0]

        self.vis_label = '{0}->{1}'.format(self.role, name)
        self.vis_icon = icon
        self.Refresh()
        self.RefreshProps()

    def CreateEditor(self, tree):
        roles = set()
        values = set()

        for v in self.option['parts']:
            roles |= v.viewkeys()
            if 'self' in v:
                roles.add(v['self'])

        roles |= self.pattern['signature'].viewkeys()
        roles |= set(['type', 'uri'])
        roles -= set(self.part.keys())
        roles.discard('self')

        values = []
        tp = None
        if self.role != 'type': 
            tp = self.part.get('type', None)

        props = appdata.datamodel.GetAvailableProps(tp)
        values += props.keys()

        roles = sorted(roles)
        values = sorted(values)

        if self.role:
            if self.role in roles:
                roles.remove(self.role)

            roles.insert(0, self.role)

            value_names = []
            for v in value2list(self.part[self.role]):
                if IsUri(v):
                    n = appdata.datamodel.GetEntityName(v)
                    if n:
                        value_names.append(n)
                    else:
                        value_names.append(v)
                else:
                    value_names.append(v)
            value = '|'.join(value_names)
            if values in values:
                values.remove(value)
            values.insert(0, value)

        if self.editor_value:
            if self.editor_value in values:
                values.remove(self.editor_value)
            values.insert(0, self.editor_value)
            self.editor_value = None

        return PattternRoleEditor(tree, roles, values, GenerateSortedModel(roles), appdata.datamodel.GetModel())

    def RejectData(self, editor):
        if self.part not in self.option['parts']:
            self.parent.Destroy()
        elif not self.role:
            self.Destroy()

    def CommitData(self, editor):
        role, value = editor.GetRoleAndValue()

        tp = None
        if role != 'type' and 'type' in self.part:
            tp = self.part['type']

        if role in ('type', 'uri'):
            values = []
            for v in value.split('|'):
                values.append(appdata.datamodel.ResolveNameOrUri(v, tp, not self.doc.use_names))
            value = list2value(values)
        else:
            value = appdata.datamodel.ResolveNameOrUri(value, tp, not self.doc.use_names)

        if self.part not in self.option['parts']:
            if role:
                if self.role:
                    del self.part[self.role]
                self.role = role
                self.part[self.role] = value
                lst = []
                lst.append(actions.DocumentModifyPatternOptionParts(self.option, self.part))
                #lst.append(actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, role, value = value, action = actions.ROLE_ADD))
                self.doc<<MultiAction(lst)
                return True
            else:
                return False

        if not self.role:
            if role:
                self.role = role
                self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, role, value = value, action = actions.ROLE_ADD)
                return True
            else:
                return False

        if not role:
            return False
        
        self.doc<<actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, self.role, value = (role, value), action = actions.ROLE_MODIFY)
        return True

    def DoDelete(self):
        self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, self.role, action = actions.ROLE_DELETE)

    def CanDrop(self, data = None, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        elif data.get('uri'):
            return True
        elif data.get('qname'):
            qname = data['qname']
            if qname.startswith('part2:'):
                return True
        elif data.get('pattern'):
            if 'type' != self.role:
                return False
            return True
        return False

    def Drop(self, data, before=None, after=None):
        if not self.doc.CanEdit():
            return False
        if data.get('uri'):
            tp = None
            if self.role != 'type' and 'type' in self.part:
                tp = self.part['type']
            value = appdata.datamodel.ResolveNameOrUri(data['uri'], tp, not self.doc.use_names)
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, self.role, value = value, action = actions.ROLE_BIND)
            return True
        elif data.get('qname'):
            qname = data['qname']
            if qname.startswith('part2:'):
                qname = qname.replace(':', '.')
                self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, self.role, value = qname, action = actions.ROLE_BIND)
                return True
            else:
                return False
        elif data.get('pattern'):
            if 'type' != self.role:
                return False
            self.doc << actions.DocumentModifyPatternOptionPartRoles(self.option, self.part, self.role, value = 'patterns.' + data['pattern'], action = actions.ROLE_BIND)
            return True
        else:
            return False

    def SetupProps(self):
        self.SetProp(tm.main.pattern_role, self.role)
        self.SetProp(tm.main.pattern_role_mapping, self.part.get(self.role, ''))

    def GetResolvableUri(self):
        value = self.part.get(self.role)
        if isinstance(value, basestring):
            if IsUri(value):
                return value
            else:
                path = value.split('.')
                if len(path) > 1:
                    return appdata.datamodel.GetEntityUri(path[0], path[1])
