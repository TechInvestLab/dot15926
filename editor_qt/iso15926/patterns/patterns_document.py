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


from framework.document import Document
from iso15926.patterns.patterns_view import PatternsView
import copy
import json
from framework.util import DictDecoder, HashableDict, DataFormatError
import os
import framework.dialogs
import iso15926.common.dialogs
import iso15926.patterns.patterns_actions as actions


@public('dot15926.doctypes')
class PatternsDocument(Document):

    doc_params = Document.doc_params + []
    msg_wildcard = tm.main.patterns_source_wildcard
    vis_icon = 'patterns_doc'
    
    def __init__(self):
        """Constructor."""
        Document.__init__(self)
        self.viewtype = type('', (PatternsView,), dict(document=self))
        self.use_names = True
        self.patterns = {}

    def Cleanup(self):
        self.patterns.clear()
        Document.Cleanup(self)

    def GetName(self):
        if self.doc_name != None:
            if getattr(self, 'importer_type', None) != None:
                return 'Imported file: '+self.doc_name
            return self.doc_name
        if getattr(self, 'importer_type', None) != None:
            if len(self.paths) > 0:
                filenames = []
                for v in self.paths:
                    fname = os.path.basename(v)
                    if fname.lower().endswith('.gz'):
                        fname = fname[:-3]
                    filenames.append(fname)
                return '{0}{1}'.format('Imported file: ', ', '.join(filenames))
            elif len(self.import_source) > 0:
                filenames = []
                for v in self.import_source:
                    fname = os.path.basename(v)
                    if fname.lower().endswith('.gz'):
                        fname = fname[:-3]
                    filenames.append(fname)
                return '{0}{1}'.format('Imported file: ', ', '.join(filenames))
            else:
                return 'Unknown imported file'
        else:
            filenames = []
            for v in self.paths:
                fname = os.path.basename(v)
                if fname.lower().endswith('.gz'):
                    fname = fname[:-3]
                filenames.append(fname)
            return ', '.join(filenames)

    def SetupProps(self):
        if not self.CanView():
            return
            
        self.SetProp(tm.main.name, self.name, 'name')
        self.SetProp(tm.main.location, ', '.join(self.paths))
        self.SetProp(tm.main.patterns_use_names, [tm.main.names, tm.main.uris] if self.use_names else [tm.main.uris, tm.main.names], 'use_names')


    def PropChanged(self, prop, value):
        if prop == 'use_names':
            self<<actions.DocumentPropertyChange(self, prop, value == tm.main.names)
        else:
            self<<actions.DocumentPropertyChange(self, prop, value)

    def OpenFiles(self, paths, readonly=False, **props):
        self.paths = paths
        if len(paths) != 1:
            return
        try:
            with open(self.paths[0], 'r') as f:
                self.patterns = json.load(f, 'utf-8', object_hook = DictDecoder(HashableDict))
            self.ChangeState(self.state_loaded)
        except Exception as e:
            exc = DataFormatError(self.paths[0], str(e))
            print exc
            iso15926.common.dialogs.DataFormatErrorDialog(str(exc), exc.info)
            self.ChangeState(self.state_unavailable)

        self.UpdateRecentSources()

    def CanSave(self):
        return Document.CanSave(self) and len(self.paths)==1

    def Save(self):
        if not self.CanSave():
            return
        with open(self.paths[0], 'w') as f:
            json.dump(self.patterns, f, 'utf-8', ensure_ascii=False)
        self.ChangeState(self.state_loaded)

    def SaveSnapshot(self):
        if not self.CanSaveSnapshot():
            return
        fname = self.name
        if len(self.paths) == 1:
            fname = os.path.basename(self.paths[0])
        path, wildcard = framework.dialogs.SaveSnapshot(tm.main.snapshot_of.format(fname), self.msg_wildcard)
        if not path or not self.VerifySavePath(path):
            return

        with open(path, 'w') as f:
            json.dump(self.patterns, f, 'utf-8', ensure_ascii=False)

        doc = PatternsDocument()
        param = dict()
        doc.OpenFiles([path], **param)
        appdata.project.AddDocument(doc)

    def SaveAs(self):
        if not self.CanSaveAs():
            return
        if len(self.paths) == 1:
            fname = os.path.basename(self.paths[0])
        else:
            fname, ext = os.path.splitext(self.name)
        path, wildcard = framework.dialogs.SaveAs(fname, self.msg_wildcard)

        if not path or (not self.VerifySavePath(path) and path not in self.paths):
            return
  
        self.paths = [path]

        with open(path, 'w') as f:
            json.dump(self.patterns, f, 'utf-8', ensure_ascii=False)
        self.ChangeState(self.state_loaded)

    def UpdateProps(self, props):
        for k, v in props.iteritems():
            setattr(self, k, copy.copy(v))
        self.RefreshProps()

    def NewFile(self, path, readonly=False, **props):
        self.UpdateProps(props)
        self.paths = [path] if path else []
        if readonly:
            self.ChangeState(self.state_readonly)
        else:
            self.ChangeState(self.state_changed)

    def NewImport(self, import_source, importer_type, importer_kwargs = None, reimport = True, **props):
        """Prepares import.

        Args:
            import_source: Path to source file to import, required for reimport.
            importer_type: Type of importer.
            reimport: If set, reimport starts immidietly.
            props: Dict with properties, see UpdateProps method for details.
        """        
        self.UpdateProps(props)

        self.import_source      = import_source
        self.importer_type      = importer_type
        self.importer_kwargs    = importer_kwargs
        if reimport:
            self.Reimport()

    def Reimport(self):
        """Reimports data"""   

        self.patterns = {}
        self.UpdateProps({})
        self.ChangeState(self.state_importing)
        self.importer_type(self, self.import_source, **self.importer_kwargs)
        self.UpdateRecentSources()

