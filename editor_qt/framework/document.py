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




from framework.dialogs import Notify
import os.path
from framework.util import TaskTarget, GetPath
from framework.docinfo import CollectDocInfo, CompareDocSources
from framework.props import PropsClient

class MultiAction:
    def __init__(self, actions):
        self.actions = actions

    def Redo(self):
        actions_list = list(self.actions)
        self.actions = []
        for v in actions_list:
            if v.Redo():
                self.actions.append(v)
        return bool(self.actions)

    def Undo(self):
        for v in reversed(self.actions):
            v.Undo()

@public('dot15926.doctypes')
class Document(TaskTarget, PropsClient):
    """Base class for documents.

    In most cases you should add document to project before use,
    call appdata.project.AddDocument() to do it. Also you need to
    set appropriate view type for document, see SetViewType()
    method.

    You need to set document state manually, see SetDocumentState()
    method.
    """

    state_unloaded = 0
    state_loaded = 1
    state_changed = 2
    state_loading = 3
    state_updating = 4
    state_saving = 5
    state_readonly = 6
    state_unavailable = 7
    state_internal = 8
    state_importing = 9
    state_importfailed = 10
    state_merging = 11

    msg_form1 = [getattr(tm.main, 'document_form1_%i'%i) for i in xrange(12)]
    msg_form2 = [getattr(tm.main, 'document_form2_%i'%i) for i in xrange(12)]
    msg_cantedit = tm.main.document_cantedit
    msg_cantsave = tm.main.document_cantsave

    doc_params = ['doc_name']

    def __init__(self):
        self.doc_info = None
        self.InitDoc()

    def InitDoc(self):
        self.doc_module_name = ''
        self.doc_name = None
        self.doc_state = 0
        self.doc_progress = None
        self.doc_editable = False
        self.doc_clients = set()
        self.doc_paths = []
        self.doc_owner = None
        self.his_entries = []
        self.his_index = 0
        self.his_pos = 0
        self.his_savedpos = None
        self.view_type = None
        self.props_pos = 0
        self.props_savedpos = 0
        self.props_changed = False
        self.pending_state = None

    @property
    def paths(self):
        return [GetPath(v) for v in self.doc_paths]

    @paths.setter
    def paths(self, value):
        self.doc_paths = value

    @property
    def label(self):
        return self.GetLabel()

    @property
    def name(self):
        return self.GetName()

    @name.setter
    def name(self, value):
        self.SetName(value)

    @property
    def module_name(self):
        return self.doc_module_name

    @module_name.setter
    def module_name(self, value):
        if not value:
            self.doc_module_name = ''
            return
        test = value
        i = 0
        while True:
            for doc in appdata.documents:
                if doc != self and doc.module_name == test:
                    break
            else:
                break
            i += 1
            test = value + str(i)
        self.doc_module_name = test

    def SetName(self, name):
        """Sets name for the document."""
        newName =  self.doc_name != name
        self.doc_name = name
        if newName:
            wizard.W_DocumentLabelChanged(self)
            wizard.W_DocumentPropertiesChanged(self)

    def GetName(self):
        """Returns name for the document."""
        if self.doc_name == None:
            filenames = []
            for v in self.paths:
                filenames.append(os.path.basename(v))
            return ', '.join(filenames)
        else:
            return self.doc_name
            
    def GetLabel(self):
        """Returns string corresponds to current document state."""
        if self.doc_progress:
            return self.msg_form2[self.doc_state].format(self.name, self.doc_progress)
        else:
            return self.msg_form1[self.doc_state].format(self.name)

    def AddClient(self, client):
        self.doc_clients.add(client)
        appdata.documents.add(self)

    def RemoveClient(self, client):
        self.doc_clients.discard(client)
        if not self.doc_clients:
            self.UpdateRecentSources(True)
            appdata.documents.discard(self)
            wizard.W_DocumentStateChanged(self)
            self.is_dead = True
            self.Cleanup()

    def UpdateRecentSources(self, add = False):
        info = CollectDocInfo(self)
        if not info:
            return
        recent = appconfig.setdefault('recent_sources', [])
        recent = [v for v in recent if not CompareDocSources(info, v)]
        if add:
            recent.append(info)
        recent = recent[-20:]
        appconfig['recent_sources'] = recent
        appconfig.SaveSettings()
        if appdata.topwindow and getattr(appdata.topwindow, 'startpage', None):
            appdata.topwindow.startpage.Refresh()

    def CanReimport(self):
        """Can document be reimported?"""
        importer   = getattr(self, 'importer_type', None)
        return importer !=  None

    def Reimport(self):
        """Reimports document."""
        pass

    def NewImport(self, import_source, importer_type, importer_kwargs = {}, reimport = True, **params):
        """Prepares import."""
        pass

    def CanUndo(self):
        return self.his_index>0

    def CanRedo(self):
        return self.his_index<len(self.his_entries)

    def GetIcon(self):
        if getattr(self, 'idi', None) != None:
            return 'rdf_ico'
        elif getattr(self, 'patterns', None) != None:
            return 'patterns_doc'
        else:
            return 'blank_ico'

    def Undo(self):
        if self.CanUndo():
            self.his_index -= 1
            action = self.his_entries[self.his_index]
            action.Undo()
            if getattr(action, 'props_change', None):
                self.props_pos -= 1
                self.UpdatePropsState()
            else:
                self.his_pos -= 1
                self.UpdateStar()

    def Redo(self):
        if self.CanRedo():
            action = self.his_entries[self.his_index]
            action.Redo()
            self.his_index += 1
            if getattr(action, 'props_change', None):
                self.props_pos += 1
                self.UpdatePropsState()
            else:
                self.his_pos += 1
                self.UpdateStar()

    def UpdateStar(self):
        if self.his_savedpos != None and self.his_pos==self.his_savedpos:
            self.ChangeState(self.state_loaded)
        else:
            self.ChangeState(self.state_changed)

    def UpdatePropsState(self, saved = False):
        if saved:
            self.props_changed = False
            self.props_savedpos = self.props_pos
            wizard.W_DocumentStateChanged(self)
        else:
            if self.props_savedpos != None and self.props_pos==self.props_savedpos:
                self.props_changed = False
            else:
                self.props_changed = True
            self.RefreshProps()
            wizard.W_DocumentPropertiesChanged(self)

    def CanView(self):
        return self.doc_state in (self.state_loaded, self.state_changed, self.state_saving, self.state_readonly)

    def CanEdit(self):
        return self.doc_editable

    def Edit(self, action):
        if not self.doc_editable and not getattr(action, 'props_change', None):
            return

        if not action.Redo():
            return

        if isinstance(action, MultiAction):
            if len(action.actions) == 1:
                action = action.actions[0]

        if self.his_index<len(self.his_entries):
            self.his_entries = self.his_entries[:self.his_index]
        self.his_entries.append(action)
        self.his_index += 1

        if getattr(action, 'props_change', None):
            if self.props_savedpos and self.props_savedpos>self.props_pos:
                self.his_savedpos = None
            self.props_pos += 1
            self.UpdatePropsState()
        else:
            if self.his_savedpos and self.his_savedpos>self.his_pos:
                self.his_savedpos = None
            self.his_pos += 1
            self.UpdateStar()

    def __lshift__(self, action):
        self.Edit(action)

    def ChangeState(self, state, progress=None):
        """Changes document state and triggers events.

        Note:
            This part of code under refactoring, so suggested to use your own events.

        Triggers events:
            W_DocumentStateChanged(self): Always
            W_DocumentLabelChanged: If label changed
            W_NewDocumentState: If state changed

        Example:
            self.ChangeState(self.state_loaded)

        Args:
            state: Desired state of document.
            progress: Percentage of state progress, for example, while loading.

        Document states list:
            state_unloaded: Unloaded document, nothing can be done.
            state_loaded: Document loaded
            state_changed: Document changed
            state_loading: Document is loading
            state_updating: Unused
            state_saving: Document is saving
            state_readonly: Document is read only
            state_unavailable: Document is unavailable
            state_internal: Unused
            state_importing: Document is importing
            state_importfailed: Document import failed
        """
        if self.doc_state==state and self.doc_progress==progress:
            return

        old_state = self.doc_state
        self.doc_state = state

        old_progress = self.doc_progress
        self.doc_progress = progress

        if state == self.state_loaded:
            self.his_savedpos = self.his_pos

        self.doc_editable = state in (self.state_loaded, self.state_changed)

        if old_progress != progress or old_state != state:
            wizard.W_DocumentLabelChanged(self)

        if old_state != self.doc_state:
            wizard.W_DocumentStateChanged(self)

    def VerifySavePath(self, path):
        """Is that path used by other opened documents?"""
        for doc in appdata.documents:
            for p in doc.paths:
                if doc != self and p == path:
                    Notify(self.msg_cantsave.format(p))
                    return False
        return True

    def AsyncChangeState(self, state, progress=None):
        if self.doc_state==state and self.doc_progress==progress:
            return
        @public.mth
        def f():
            self.ChangeState(state, progress)

    @classmethod
    def VerifyEditablePaths(cls, paths):
        """Returns true if source already opened for editing."""
        for doc in appdata.documents:
            for p in doc.paths:
                if p in paths:
                    Notify(cls.msg_cantedit.format(p))
                    return False
        return True

    @classmethod
    def FindDocumentByPaths(cls, paths):
        """Returns document by paths if found."""
        for doc in appdata.documents:
            if doc.__class__==cls and doc.paths==paths:
                return doc

    @classmethod
    def SaveAll(cls):
        for doc in appdata.documents:
            if doc.doc_state == doc.state_changed:
                if doc.CanSave():
                    doc.Save()
                elif doc.CanSaveAs():
                    doc.SaveAs()

    @classmethod
    def CanSaveAll(cls):
        for doc in appdata.documents:
            if doc.doc_state == doc.state_changed:
                return True
        return False

    # override

    def OpenFiles(self, paths, readonly=False, **props):
        """Opens files with specified props.

        Note that you can open multiple files here.

        Args:
            paths: Paths to source files.
            readonly: Make graph readonly if set to True.
            props: Dict with properties
        """
        pass

    def Cleanup(self):
        self.ClearTasks()

    def CanLoad(self):
        return (self.doc_state==self.state_unloaded and self.name is not None)

    def Load(self):
        pass

    def IsUnavailable(self):
        self.doc_state == self.state_unavailable

    def CanUnload(self):
        return True

    def Unload(self):
        pass 

    def CanSave(self):
        """Can document be saved?"""
        return (self.doc_state == self.state_changed)

    def Save(self):
        """Saves document."""
        pass

    def SaveSnapshot(self):
        """Saves snapshot of document."""
        pass

    def CanSaveAs(self):
        """Can document be saved as file?"""
        return (self.doc_state in (self.state_loaded, self.state_changed, self.state_readonly))

    def CanSaveSnapshot(self):
        """Can document's snaphot be saved as file?"""
        return (self.doc_state in (self.state_loaded, self.state_changed, self.state_readonly))

    def SaveAs(self):
        """Saves document as file."""
        pass

    def SetViewType(self, viewtype):
        """Sets view type for document."""
        self.view_type = viewtype

    def ViewType(self):
        """Opens view."""
        return self.view_type


