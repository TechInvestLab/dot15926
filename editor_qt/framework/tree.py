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

import framework.menu
import framework.util as util
import cPickle



class TreeEditor(QFrame):
    vis_label = None
    vis_style = 'TreeEditor {border: 2px solid gray;  border-radius: 4px; background-color: darkgrey;}'
    vis_resizable = True
    gripsize = 12
    def __init__(self, parent):
        QFrame.__init__(self, parent)
        self.setObjectName('editor')
        self.tree = None
        self.locked = False
        self.committed = False
        self.item = None
        self.installEventFilter(self)
        self.setStyleSheet(self.vis_style)
        self.setFocusPolicy(Qt.ClickFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(QMargins())
        if self.vis_label:
            layout.addWidget(QLabel(self.vis_label, self))

        if self.vis_resizable:
            self.setWindowFlags(self.windowFlags() | Qt.SubWindow)
            self.sizegrip = QSizeGrip(self)
            self.sizegrip.moveEvent = lambda evt: None
            layout.addWidget(self.sizegrip, 0, Qt.AlignBottom | Qt.AlignRight)

    def RejectData(self):
        self.item.RejectData(self)

    def CommitData(self):
        self.committed = self.item.CommitData(self)
        if not self.committed: 
            self.locked = True

    def resizeEvent(self, evt):
        QFrame.resizeEvent(self, evt)
        self.tree.update()

    def UpdateGeometry(self, optv4, index):
        style = self.tree.style()
        rect = style.subElementRect(QStyle.SE_ItemViewItemText, optv4, self.tree)
        rect.setTop(self.tree.visualRect(index).top())
        self.layout().update()
        pos = rect.topLeft()
        avail = self.tree.width() - pos.x() - self.tree.verticalScrollBar().width()
        size = QFrame.sizeHint(self)
        width = self.tree.header().sectionSize(0)
        size.setWidth(min(size.width(), avail))
        geom = QRect(pos, size)
        self.setMinimumWidth(min(width, avail))
        self.setMaximumWidth(avail)
        self.setMinimumHeight(geom.height())
        self.setMaximumHeight(geom.height())
        self.setGeometry(geom)

    def AddChild(self, obj):
        if obj and obj.isWidgetType():
            obj.installEventFilter(self)

        for v in obj.children():
            self.AddChild(v)

    def RemoveChild(self, obj):
        if obj and obj.isWidgetType():
            obj.removeEventFilter(self)

        for v in obj.children():
            self.RemoveChild(v)

    def eventFilter(self, obj, evt):
        if evt.type() == QEvent.ChildAdded:
            self.AddChild(evt.child())
        elif evt.type() == QEvent.ChildRemoved:
            self.RemoveChild(evt.child())
        elif obj is not self and evt.type() == QEvent.FocusOut:
            appdata.app.sendEvent(self, evt)
        return QFrame.eventFilter(self, obj, evt)


class SimpleTreeNodeEditor(TreeEditor):
    def __init__(self, parent, text = ''):
        TreeEditor.__init__(self, parent)
        self.lineedit = QLineEdit(text)
        self.layout().insertWidget(0, self.lineedit)
        self.setFocusProxy(self.lineedit)

    def SetText(self, txt):
        self.lineedit.setText(txt)

    def GetText(self):
        return self.lineedit.text().encode('utf-8')

class DefaultTreeDelegate(QStyledItemDelegate):
    def __init__(self, tree):
        QStyledItemDelegate.__init__(self)
        self.tree = tree

    def setEditorData(self, editor, index):
        if isinstance(editor, TreeEditor):
            return
        return QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, TreeEditor):
            editor.CommitData()
            return
        return QStyledItemDelegate.setModelData(self, tree, model, index)

    def createEditor(self, parent, option, index):
        item = self.tree.itemFromIndex(index)
        self.tree.setCurrentItem(item)
        editor = item.CreateEditor(parent)
        if editor:
            self.tree.editor = editor
            editor.tree = self.tree
            editor.item = item
            optv4 = QStyleOptionViewItemV4(option)
            self.initStyleOption(optv4, index)
            editor.UpdateGeometry(optv4, index)
            self.tree.doItemsLayout()
            self.tree.scrollToItem(item)
            return editor
        return QStyledItemDelegate.createEditor(self, parent, option, index)

    def updateEditorGeometry(self, editor, option, index):
        if isinstance(editor, TreeEditor):
            optv4 = QStyleOptionViewItemV4(option)
            self.initStyleOption(optv4, index)
            editor.UpdateGeometry(optv4, index)
        else:
            QStyledItemDelegate.updateEditorGeometry(self, editor, option, index)

    def sizeHint(self, option, index):
        if self.tree.editor:
            item = self.tree.itemFromIndex(index)
            if self.tree.editor.item is item:
                optv4 = QStyleOptionViewItemV4(option)
                self.initStyleOption(optv4, index)
                style = self.tree.style()
                size = style.subElementRect(QStyle.SE_ItemViewItemDecoration, optv4, self.tree).size()
                if self.tree.editor.geometry().height() > size.height():
                    size.setHeight(self.tree.editor.geometry().height())
                return size

        return QStyledItemDelegate.sizeHint(self, option, index)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and self.tree.OnTreeItemLeftDown(index):
                return True
            elif event.button() == Qt.MiddleButton and self.tree.OnTreeItemMiddleDown(index):
                return True
            elif event.button() == Qt.RightButton and self.tree.OnTreeItemRightDown(index):
                return True
        elif event.type() == QEvent.MouseButtonDblClick and self.tree.OnTreeItemDblClick(index):
            return True
        return QStyledItemDelegate.editorEvent(self, event, model, option, index)

class Tree(QTreeWidget):
    UseMultiselect = True
    UseDragAndDrop = True
    popup_menu = 'workbench.menu.element'

    def __init__(self, parent = None):
        QTreeWidget.__init__(self, parent)
        # self.installEventFilter(self)
        self.editor = None
        self.header().setStretchLastSection(False)
        self.header().setResizeMode(QHeaderView.ResizeToContents)
        self.header().close()
        #self.header().setMinimumSectionSize(0)
        self.setItemDelegate(DefaultTreeDelegate(self))
        selectionmodel = QItemSelectionModel(self.model())
        self.setSelectionModel(selectionmodel)
        if self.UseMultiselect:
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.expanded.connect(self.OnItemExpanded)
        self.collapsed.connect(self.OnItemCollapsed)
        self.selectionModel().selectionChanged.connect(self.OnTreeSelChanged)

        if self.UseDragAndDrop:
            self.setDragDropMode(QAbstractItemView.DragDrop)
            self.setDragDropOverwriteMode(True)

        self.item_to_select = None

    # def eventFilter(self, obj, evt):
    #     return QTreeWidget.eventFilter(self, obj, evt)

    def closeEditor(self, editor, hint):
        if isinstance(editor, TreeEditor):
            if editor.locked:
                editor.locked = False
                return
            if not editor.committed:
                editor.RejectData()
            self.editor = None
        QTreeWidget.closeEditor(self, editor, hint)
        self.doItemsLayout()

    def ItemAboutToBeRemoved(self, item):
        if (item is self.item_to_select) or ((self.item_to_select is None) and (item is self.currentItem())):
            if self.item_to_select is None:
                @public.mth
                def f():
                    self.setCurrentItem(self.item_to_select)
                    self.item_to_select = None
            self.item_to_select = self.itemFromIndex(self.moveCursor(QAbstractItemView.MoveDown, Qt.NoModifier))
            if (item is self.item_to_select):
                self.item_to_select = self.itemFromIndex(self.moveCursor(QAbstractItemView.MoveUp, Qt.NoModifier))

    def clear(self):
        self.setCurrentIndex(QModelIndex())
        while self.topLevelItemCount():
            self.topLevelItem(0).Destroy(True)
        QTreeWidget.clear(self)

    def Sorted(self, items):
        data = {}
        for v in items:
            rows = []
            p = v
            while p:
                rows.append(self.indexFromItem(p).row())
                p = p.parent
            data[v] = rows[::-1]

        def _compare(x, y):
            rows_x = data[x]
            rows_y = data[y]
            for i in xrange(min(len(rows_x), len(rows_y))):
                value = rows_x[i] - rows_y[i]
                if value:
                    return value
            return len(rows_x) - len(rows_y)

        return sorted(items, cmp=_compare)

    @property
    def selected(self):
        return self.GetSelectedNodes()

    @property
    def selected_sorted(self):
        return self.Sorted(self.selected)

    @property
    def children(self):
        l = []
        for i in xrange(self.topLevelItemCount()):
            l.append(self.topLevelItem(i))
        return l

    @property
    def children_sorted(self):
        return self.Sorted(self.children)

    def keyPressEvent(self, evt):
        if evt == QKeySequence.Copy:
            evt.ignore()
            return
        QTreeWidget.keyPressEvent(self, evt)

    def focusInEvent(self, evt):
        if self.state() == QAbstractItemView.EditingState:
            if self.editor:
                self.editor.setFocus()
                return

        QTreeWidget.focusInEvent(self, evt)
        if len(self.selected) == 1:
            for v in self.selected:
                v.OnSelect(1)

    def AddChild(self, item):
        self.addTopLevelItem(item)

    def IndexOf(self, item):
        return self.indexOfTopLevelItem(item)

    def InsertChild(self, index, item):
        self.insertTopLevelItem(index, item)

    def RemoveChild(self, item):
        index = self.indexOfTopLevelItem(item)
        return self.takeTopLevelItem(index)

    def GetChild(self, index):
        return self.topLevelItem(index)

    def Clear(self):
        self.clear()

    def SelectNode(self, item):
        self.selectionModel().select(self.indexFromItem(item), QItemSelectionModel.ClearAndSelect)

    def SelectNodes(self, items):
        selection = QItemSelection()
        for v in items:
            selection.append(self.indexFromItem(v))
        self.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)

    def UnselectAll(self):
        self.selectionModel().clearSelection()

    def UnselectNode(self, item):
        self.selectionModel().select(self.indexFromItem(item), QItemSelectionModel.Deselect)
       
    def UnselectNodes(self, items):
        selection = QItemSelection()
        for v in items:
            selection.append(self.indexFromItem(v))
        self.selectionModel().select(selection, QItemSelectionModel.Deselect)

    def GetSelectedNode(self):
        sel = self.selectedItems()
        if sel:
            return sel[0]
        return None

    def GetSelectedNodes(self):
        return self.selectedItems()

    def GetPointedNode(self, point):
        return self.itemAt(point)

    def OnItemExpanded(self, index):
        item = self.itemFromIndex(index)
        if item.treenode_track_appearance:
            item.treenode_track_appearance = False
            for c in item.children():
                c.OnAppear()
        if item.treenode_track_first_access:
            item.treenode_track_first_access = False
            item.OnFirstAccess()
        item.OnExpand(True)
        if item.children:
            self.scrollToItem(item.children[-1])
        self.scrollToItem(item)

    def OnItemCollapsed(self, index):
        item = self.itemFromIndex(index)
        item.OnExpand(False)

    def OnTreeSelChanged(self, selected, deselected):
        if not self.hasFocus():
            return

        for v in deselected.indexes():
            item = self.itemFromIndex(v)
            item.OnSelect(0)

        if len(self.selected) == 1:
            for v in self.selected:
                v.OnSelect(1)

    def OnTreeItemLeftDown(self, index):
        item = self.itemFromIndex(index)
        action = getattr(item, 'OnLeftDown', None)
        if action:
            return action()
        return False

    def OnTreeItemRightDown(self, index):
        item = self.itemFromIndex(index)
        action = getattr(item, 'OnRightDown', None)
        if action:
            return action()
        return False

    def OnTreeItemMiddleDown(self, index):
        item = self.itemFromIndex(index)
        action = getattr(item, 'OnMiddleDown', None)
        if action:
            return action()
        return False

    def OnTreeItemDblClick(self, index):
        item = self.itemFromIndex(index)
        if item.treenode_editable:
            return False
        action = getattr(item, 'OnDblClick', None)
        if action:
            return action()
        return False

    def decodeMime(self, data):
        if data.hasFormat('application/treeitem-dnd'):
            encodedData = data.data('application/treeitem-dnd')
            dataStream = QDataStream(encodedData, QIODevice.ReadOnly)
            return cPickle.loads(str(dataStream.readString()))
        return None

    def dragMoveEvent(self, evt):
        QTreeWidget.dragMoveEvent(self, evt)
        item = self.itemAt(evt.pos())
        data = evt.mimeData()
        content = self.decodeMime(data)

        if content == None:
            evt.ignore()
            return

        dip = self.dropIndicatorPosition()
        if item:
            if dip == QAbstractItemView.OnItem:
                if not item.CanDrop(data = content):
                    evt.ignore()
                    return
            elif dip == QAbstractItemView.AboveItem:
                if not item.parent or not item.parent.CanDrop(data = content, before=item):
                    evt.ignore()
                    return
            elif dip == QAbstractItemView.BelowItem:
                if not item.parent or not item.parent.CanDrop(data = content, after=item):
                    evt.ignore()
                    return
            elif dip == QAbstractItemView.OnViewport:
                evt.ignore()
                return
        else:
            evt.ignore()


    def supportedDropActions(self):
        return Qt.CopyAction

    def mimeTypes(self):
        return ['application/treeitem-dnd']

    def mimeData(self, items):
        action = util.findcommonmethod(items, 'Drag')
        if action:
            itemData = QByteArray()
            dataStream = QDataStream(itemData, QIODevice.WriteOnly)
            dataStream.writeString(cPickle.dumps(action()))
            self.currentMimeData = QMimeData()
            self.currentMimeData.setData('application/treeitem-dnd', itemData)
            return self.currentMimeData
        return None

    def dropMimeData(self, parent, index, data, action):
        if action == Qt.IgnoreAction:
            return True

        if not parent:
            return False

        content = self.decodeMime(data)

        if content == None:
            return False

        return parent.Drop(content, before=parent.child(index), after = parent.child(index-1))

    def contextMenuEvent(self, evt):
        menu = framework.menu.Menu(self)
        framework.menu.MakeMenu(menu, self.popup_menu)
        menu.popup(evt.globalPos())
