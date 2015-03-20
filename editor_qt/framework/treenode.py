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




import framework.dialogs
from framework.util import TaskTarget
from framework.tree import Tree
from PySide.QtCore import *
from PySide.QtGui import *
from framework.props import PropsClient

class TreeNode(QTreeWidgetItem, PropsClient):

    vis_label = 'No label'
    vis_icon = None
    vis_icon2 = None
    vis_tooltip = None
    vis_bold = False
    vis_italic = False

    treenode_editable = False
    treenode_show_count = False
    treenode_track_appearance = False
    treenode_track_first_access = False
    treenode_show_as_nonempty = False
    treenode_attached_grid = None
    treenode_loading = False
    treenode_anim_phase = None

    def __init__(self, parent, before = None, after = None):
        QTreeWidgetItem.__init__(self)
        self.items_count = None
        self.Init(parent, before, after)
        flags = self.flags()
        if getattr(self, 'Drag', None):
            flags |= Qt.ItemIsDragEnabled
        if getattr(self, 'Drop', None):
            flags |= Qt.ItemIsDropEnabled
        self.setFlags(flags)

    @property
    def tree(self):
        return self.treeWidget()

    @property
    def parent(self):
        return QTreeWidgetItem.parent(self)

    @property
    def children(self):
        l = []
        for i in xrange(self.childCount()):
            l.append(self.child(i))
        return l

    @property
    def children_sorted(self):
        return self.tree.Sorted(self.children) if self.tree else []

    @property
    def childrencount(self):
        return self.childCount()

    def TakeChildren(self):
        return self.takeChildren()

    def Init(self, parent, before = None, after = None):
        if before:
            parent.InsertChild(parent.IndexOf(before), self)
        elif after:
            parent.InsertChild(parent.IndexOf(after)+1, self)
        else:
            parent.AddChild(self)

    def Edit(self):
        if self.tree:
            self.tree.editItem(self)

    def SetExpandable(self, value):
        if value:
            self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        else:
            self.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicatorWhenChildless)

    def IsDestroyAllowed(self):
        for i in xrange(self.childCount()):
            if not self.child(i).IsDestroyAllowed():
                return False
        return True

    def Destroy(self, force = False):
        if force or self.IsDestroyAllowed():
            self.DestroyChildren()
            self.OnDestroy()
            if self.tree:
                self.tree.ItemAboutToBeRemoved(self)
            if self.parent:
                self.parent.RemoveChild(self)
            elif self.tree:
                self.tree.RemoveChild(self)
            return True
        return False

    def DestroyChildren(self, force = False):
        for v in self.children:
            v.Destroy(force)

    def Clear(self):
        self.DestroyChildren(True)

    def SetCurrent(self):
        self.tree.setCurrentItem(self)

    def Select(self):
        self.tree.SelectNode(self)

    def Unselect(self):
        self.tree.UnselectNode(self)

    def IsSelected(self):
        if not self.tree:
            return False
        return self in set(self.tree.GetSelectedNodes())

    def RemoveChild(self, item):
        self.removeChild(item)

    def AddChild(self, item):
        self.addChild(item)

    # def TakeChild(self, item):
    #     i = self.indexOfChild(item)
    #     return self.takeChild(i)

    def IndexOf(self, item):
        return self.indexOfChild(item)

    def InsertChild(self, index, item):
        self.insertChild(index, item)

    def IsValid(self):
        return self.parent is not None or self.tree is not None

    def GetChild(self, index):
        return self.child(index)

    def GetNextSibling(self):
        owner = self.parent if self.parent else self.tree
        return owner.GetChild(owner.IndexOf(self) + 1)

    def GetPrevSibling(self):
        owner = self.parent if self.parent else self.tree
        return owner.GetChild(owner.IndexOf(self) - 1)

    def GetItemsCount(self):
        if self.items_count:
            return self.items_count
        return self.childCount()

    def Refresh(self):
        label = self.vis_label.replace('\n', ' ')

        self.SetExpandable(self.treenode_show_as_nonempty)

        if self.treenode_show_count:
            if self.treenode_loading:
                self.setText(0, '{0} (?)'.format(label))
            else:
                self.setText(0, '{0} ({1})'.format(label, self.GetItemsCount()))
        else:
            self.setText(0, label)
        if self.treenode_loading and self.treenode_anim_phase is None:
            appdata.animated.add(self)

        if self.vis_icon:
            icons = [self.vis_icon]
        else:
            icons = []

        if self.vis_icon2:
            icons.append(self.vis_icon2)

        if self.treenode_loading and self.treenode_anim_phase is not None:
            icons.append('loading{0}'.format(self.treenode_anim_phase))

        icon = ';'.join(icons)

        if icon:
            self.setIcon(0, appdata.resources.GetIcon(icon))
        else:
            self.setIcon(0, QIcon())

        font = QFont(self.font(0))
        font.setBold(self.vis_bold)
        font.setItalic(self.vis_italic)
        self.setFont(0, font)

        if self.vis_tooltip:
            self.setToolTip(0, self.vis_tooltip)
        else:
            self.setToolTip(0, '')

        self.SetEditable(self.treenode_editable)

    def Sort(self):
        self.sortChildren(0, Qt.AscendingOrder)

    def Expand(self):
        self.setExpanded(True)

    def Collapse(self):
        self.setExpanded(False)

    def Animate(self, phase):
        if not self.IsValid():
            appdata.animated.discard(self)
            return

        if self.vis_icon:
            icons = [self.vis_icon]
        else:
            icons = []

        if self.vis_icon2:
            icons.append(self.vis_icon2)

        if self.treenode_loading:
            self.treenode_anim_phase = phase%3
            icons.append('loading{0}'.format(self.treenode_anim_phase))
        else:
            self.treenode_anim_phase = None
            appdata.animated.discard(self)

        icon = ';'.join(icons)
        if icon:
            self.setIcon(0, appdata.resources.GetIcon(icon))
        else:
            self.setIcon(0, QIcon())
            
    def SetColor(self, color):
        if color != None:
            self.setBackground(0, QBrush(color))

    def SetTextColor(self, color):
        if color != None:
            self.setForeground(0, QBrush(color))

    def SetEditable(self, enable):
        if enable:
            self.setFlags(self.flags() | Qt.ItemIsEditable)
        else:
            self.setFlags(self.flags() & ~Qt.ItemIsEditable)

    def OnDblClick(self):
        action = getattr(self, 'ViewType', None)
        if action:
            appdata.project.NewView(action())
            return True
        return False

    def OnMiddleDown(self):
        action = getattr(self, 'ViewType', None)
        if action:
            appdata.project.NewView(action(), tabify = False)
            return True
        return False

    def OnRightDown(self):
        return False

    # override

    def CreateEditor(self, tree):
        return None

    def RejectData(self, editor):
        pass

    def CommitData(self, editor):
        return True

    def OnDestroy(self):
        self.ClearProps()

    def OnExpand(self, expanding):
        pass

    def OnSelect(self, select):
        if select:
            self.ShowProps()

    def OnAppear(self):
        pass

    def CanDrop(self, data = None, before=None, after=None):
        return False

    def Drop(self, data, before=None, after=None):
        return False

    # def CanCut(self):
    #     return False

    # def Cut(self):
    #     return None

    # def CanCopy(self):
    #     return False

    # def Copy(self):
    #     return None

    # def CanPaste(self):
    #     return False

    # def Paste(self):
    #     return None
