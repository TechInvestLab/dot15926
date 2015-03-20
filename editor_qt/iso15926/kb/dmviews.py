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

@public('dot15926.viewtypes')
class XSDTypesView(FilteredView):
    vis_label = tm.main.xml_schema_types
    vis_icon = 'tpl_ico'
    
    def Search(self, value):
        self.Seed()

    def Filter(self, value):
        self.Seed()

    def Seed(self):
        self.wnd_tree.Clear()

        if self.bound_uri:
            node = XSDNode(self.wnd_tree, self.bound_uri)
            self.vis_label = '{0} ({1})'.format(node.vis_label, self.vis_label)
            self.vis_icon  = node.vis_icon
            return

        m = 0
        n = 0
        pnode = XSDTypesNode(self.wnd_tree)

        fi = self.wnd_filter.value.lower()
        for name in kb.typelist_xsd:
            if fi in name.lower():
                XSDNode(pnode, 'xsd:'+name)
                m += 1
            n += 1

        pnode.Sort()
        pnode.Expand()
        pnode.vis_label = '{0} [{1}/{2}]'.format(XSDTypesNode.vis_label, m, n)
        pnode.Refresh()


@public('dot15926.viewtypes')
class Part2TypesView(XSDTypesView):
    vis_label = tm.main.part2_types_title

    def Seed(self):
        self.wnd_tree.Clear()

        if self.bound_uri:
            node = Part2Node(self.wnd_tree, self.bound_uri)
            self.vis_label = '{0} ({1})'.format(node.vis_label, self.vis_label)
            self.vis_icon  = node.vis_icon
            return

        m = 0
        n = 0
        pnode = Part2TypesNode(self.wnd_tree)

        fi = self.wnd_filter.value.lower()
        for (k, v) in kb.part2_itself.iteritems():
            if fi in v['name'].lower():
                Part2Node(pnode, k)
                m += 1
            n += 1

        pnode.Sort()
        pnode.Expand()
        pnode.vis_label = '{0} [{1}/{2}]'.format(Part2TypesNode.vis_label, m, n)
        pnode.Refresh()

class XSDTypesNode(TreeNode):
    vis_label = tm.main.xmlschema_types_title
    vis_icon = 'tpl_ico'
    vis_bold = True

    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        self.Refresh()


class Part2TypesNode(XSDTypesNode):
    vis_label = tm.main.part2_data_model


class XSDNode(TreeNode):
    vis_icon = 'iso_syntax'

    def __init__(self, parent, qname, prefix='', role = None):
        TreeNode.__init__(self, parent)
        self.qname = qname
        self.uri = kb.ns_xsd+qname.split(':')[1]
        self.vis_label = prefix+qname
        self.role = role
        self.Refresh()

    def SetupProps(self):
        if self.role:
            self.SetProp(kb.ns_dm_part2+self.role['name'], self.uri)
            self.SetProp(kb.ns_dm_rds+self.role['name'], self.uri)
            self.SetProp(kb.ns_dm_part8+self.role['name'], self.uri)
        else:
            self.SetProp(tm.main.uri, self.uri)
        self.SetProp(tm.main.name, self.qname)

    def Drag(self):
        return dict(uri=self.uri)

    def GetResolvableUri(self):
        return kb.ns_xsd+self.qname

    def ViewType(self):
        return type('', (XSDTypesView,), dict(bound_uri=self.qname))


class Part2Node(TreeNode):
    treenode_show_as_nonempty = True
    treenode_track_first_access = True

    def __init__(self, parent, qname, prefix='', role = None):
        TreeNode.__init__(self, parent)
        self.qname = qname
        self.entry = kb.part2_itself[qname]
        self.vis_label = prefix+self.entry['name']
        self.role = role
        if self.role:
            self.vis_icon = kb.icons_map.get(self.entry['icon'], 'iso_unknown')
        else:
            self.vis_icon = self.entry['icon']
        self.Refresh()

    def OnFirstAccess(self):
        classifier_list = self.entry.get('classifier')
        if classifier_list:
            CanBeClassifiedByNode(self, classifier_list)
        classified_list = self.entry.get('classified')
        if classified_list:
            CanClassifyNode(self, classified_list)
        if self.entry['subtypes']:
            SubtypesNode(self, self.entry['subtypes'])
        if self.entry['supertypes']:
            SupertypesNode(self, self.entry['supertypes'])
        if self.entry['roles']:
            RolesNode(self)

        role_in = self.entry.get('role_in')
        if role_in:
            HasRoleInNode(self, role_in)

        disj = self.entry.get('disjoints')
        if disj:
            DisjointsNode(self, disj)
            
    def SetupProps(self):
        if self.role:
            self.SetProp(kb.ns_dm_part2+self.role['name'], kb.ns_dm_part2+self.entry['name'])
            self.SetProp(kb.ns_dm_rds+self.role['name'], kb.ns_dm_rds+self.entry['name'])
            self.SetProp(kb.ns_dm_part8+self.role['name'], kb.ns_dm_part8+self.entry['name'])
        else:
            self.SetProp(tm.main.pcardl_uri, kb.ns_dm_part2+self.entry['name'])
            self.SetProp(tm.main.rdswip_uri, kb.ns_dm_rds+self.entry['name'])
            self.SetProp(tm.main.part8_uri, kb.ns_dm_part8+self.entry['name'])
        self.SetProp(tm.main.name, self.entry['name'])
        self.SetProp(tm.main.comment, self.entry['comment'], None, True)

    def Drag(self):
        return dict(qname=self.qname, label=self.entry['name'])

    def ViewType(self):
        return type('', (Part2TypesView,), dict(bound_uri=self.qname))

class GroupNode(TreeNode):
    treenode_show_count = True
    vis_icon = 'iso_group'

    def __init__(self, parent, group):
        TreeNode.__init__(self, parent)
        for i in group:
            Part2Node(self, i)
        self.Sort()
        self.Refresh()

class SubtypesNode(GroupNode):
    vis_label = tm.main.subtypes

class SupertypesNode(GroupNode):
    vis_label = tm.main.supertypes

class CanClassifyNode(GroupNode):
    vis_label = tm.main.can_classify

class CanBeClassifiedByNode(GroupNode):
    vis_label = tm.main.can_be_classified_by

class DisjointsNode(GroupNode):
    vis_label = tm.main.disjoint_with

class HasRoleInNode(TreeNode):
    vis_label = tm.main.has_role_in
    treenode_show_count = True
    vis_icon = 'iso_group'
    pre = tm.main.role_in_prefix
    def __init__(self, parent, items):
        TreeNode.__init__(self, parent)
        for owner, rname in items:
            Part2Node(self, owner, self.pre%rname)
        self.Sort()
        self.Refresh()

class RolesNode(TreeNode):
    treenode_show_count = True
    vis_label = tm.main.roles
    vis_icon = 'iso_group'

    def __init__(self, parent):
        TreeNode.__init__(self, parent)
        for role in self.parent.entry['roles'].itervalues():
            t = [role['name'], ' : ']
            if role.get('is_optional'):
                t.append('optional ')
            if role.get('is_list'):
                t.append('list of ')
            prefix = ''.join(t)
            type_uri = role['type_uri']
            if type_uri.startswith('xsd:'):
                XSDNode(self, type_uri, prefix, role = role)
            else:
                Part2Node(self, type_uri, prefix, role = role)
        self.Sort()
        self.Refresh()
