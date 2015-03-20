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




import uuid
from collections import defaultdict
import graphlib
import framework.dialogs
from iso15926.io.rdf_graph import RdfGraph, RdfDiff
from framework.document import Document
from iso15926.graph.graph_view import GraphView
import iso15926.kb as kb
import os.path
import heapq
from iso15926.io.rdf_base import *
from iso15926.graph.graph_actions import DocumentPropertyChange
from _ordereddict import ordereddict
from framework.props import PropPatternsEdit, PropDictEdit, PropModulesEdit
import copy
from iso15926.tools.scantools import ScannerPatterns
from framework.util import DataFormatError
import iso15926.common.dialogs
from graphlib import expand_uri

@public('dot15926.doctypes')
class GraphDocument(Document, RdfGraph):
    """Document that contains rdf graph data.

    To change attributes use UpdateProps method.   

    Attributes:
        namespaces: Namespaces used in this rdf graph.
        annotations: Annotations available in this rdf graph.
        chosen_part2: Namespace chosen for Part 2 types.
        module_name: Modle name used by environment.
        basens: Namespace for new entries.
    """

    doc_params = Document.doc_params + ['basens', 'namespaces', 'annotations', 'roles', 'chosen_part2', 'doc_module_name', 'p7tm', 'uri_from_names', 'uuid_prefix']
    msg_wildcard = tm.main.source_wildcard
    wildcard_values = tm.main.source_wildcard.split(';;')
    wildcard_map = {
        wildcard_values[0]: ('rdfxml', False, '.rdf'),
        wildcard_values[1]: ('rdfxml', False, '.owl'),
        wildcard_values[2]: ('turtle', False, '.ttl'),
        wildcard_values[3]: ('rdfxml', True, '.rdf'),
        wildcard_values[4]: ('rdfxml', True, '.owl.gz'),
        wildcard_values[5]: ('turtle', True, '.ttl.gz'),
    }

    _debug = False

    def __init__(self):
        """Constructor."""
        Document.__init__(self)
        RdfGraph.__init__(self)
        self.namespaces = []
        self.annotations = []
        self.roles = []
        self.chosen_part2 = kb.ns_dm_part2
        self.namespaces_by_uri = {}
        self.annotations_by_name = {}
        self.roles_by_name = {}
        self.props_by_uri = {}
        self.basens = "http://example.org/"
        self.viewtype = type('', (GraphView,), dict(document=self))
        self.p7tm = kb.ns_p7tm
        self.uri_from_names = True
        self.uuid_prefix = 'id'
        self.patterns_env_cached = None
        self.uris_by_name = {}
        self.templates = {}
        self.grAddCallback(self.PROGRESS, self.grProgress)
        self.entities = {}
        self.grAddCallback(self.TRIPLE_ADDED, self.TripleAddedCallback)
        self.grAddCallback(self.TRIPLE_REMOVED, self.TripleRemovedCallback)

    def GetEntityUriByName(self, name):
        curi = self.entities.get(name)
        if curi:
            return expand_uri(curi)

    def infGetEntityName(self, uri):
        triples = self.grTriplesForSubj(uri)
        if triples:
            for p in kb.all_labels:
                for t in triples:
                    if t.p == p:
                        return t.v


    def TripleAddedCallback(self, t):
        if t.p in kb.all_labels_dict:
            pri = kb.all_labels_dict[t.p]
            old_names = []

            pri3 = len(kb.all_labels_dict)
            for tt in self.grTriplesForSubj(t.s):
                if tt.p in kb.all_labels_dict:
                    pri2 = kb.all_labels_dict[tt.p]
                    if pri2 < pri:
                        return
                    elif pri2 == pri and t != tt:
                        old_names = []
                        break
                    elif pri2 > pri:
                        if pri2 < pri3:
                            pri3 = pri2
                            old_names = [tt.v]
                        elif pri2 == pri3:
                            old_names.append(tt.v)


            for v in old_names:
                del self.entities[v]
            self.entities[t.v] = t[0]
            appdata.datamodel.EntityNameModified(self.module_name, old_names, [t.v])

    def TripleRemovedCallback(self, t):
        if t.p in kb.all_labels_dict:
            pri = kb.all_labels_dict[t.p]
            new_names = []
            
            pri3 = len(kb.all_labels_dict)
            for tt in self.grTriplesForSubj(t.s):
                if tt.p in kb.all_labels_dict:
                    pri2 = kb.all_labels_dict[tt.p]
                    if pri2 < pri:
                        return
                    elif pri2 == pri:
                        new_names = []
                        break
                    elif pri2 > pri:
                        if pri2 < pri3:
                            pri3 = pri2
                            new_names = [tt.v]
                        elif pri2 == pri3:
                            new_names.append(tt.v)
      
            del self.entities[t.v] 
            for v in new_names:
                self.entities[v] = t[0]
            appdata.datamodel.EntityNameModified(self.module_name, [t.v], new_names)

    def Cleanup(self):
        self.grClear()
        Document.Cleanup(self)

    @property
    def patterns_env(self):
        if self.patterns_env_cached == None:
            self.patterns_env_cached = appdata.environment_manager.GetPatternsEnv(self)
        return self.patterns_env_cached

    def SetupProps(self):
        if not self.CanView():
            return
            
        self.SetProp(tm.main.name, self.name, 'name')
        self.SetProp(tm.main.location, ', '.join(self.paths))
        importer_type = getattr(self, 'importer_type', None)
        if importer_type:
            self.SetProp(tm.main.importer_type, importer_type.__name__)
            self.SetProp(tm.main.import_source, ', '.join(getattr(self, 'import_source', [])))
        self.SetProp(tm.main.module_name, self.module_name)
        self.SetProp(tm.main.part2_ns, self.chosen_part2, 'chosen_part2')
        self.SetProp(tm.main.namespaces, (', '.join([name for name, uri in self.namespaces]),
                                               PropDictEdit, self.namespaces) , 'namespaces')
        self.SetProp(tm.main.annotations, (', '.join([name for name, uri in self.annotations]),
                                               PropDictEdit, self.annotations) , 'annotations')
        self.SetProp(tm.main.roles, (', '.join([name for name, uri in self.roles]),
                                               PropDictEdit, self.roles) , 'roles')
        self.SetProp(tm.main.ns_for_new, self.basens, 'basens')
        self.SetProp(tm.main.p7tm, self.p7tm, 'p7tm')
        self.SetProp(tm.main.uri_for_new, self.uri_from_names, 'uri_from_names')

    def PropChanged(self, prop, value):
        self<<DocumentPropertyChange(self, prop, value)

    def translate_props(self, props, objprops = {}, dtprops = {}, untranslated = {}):
        for k, v in props.iteritems():
            if k in self.roles_by_name:
                objprops[self.roles_by_name[k]] = v
            elif k in self.annotations_by_name:
                dtprops[self.annotations_by_name[k]] = v
            else:
                untranslated[k] = v
        return (objprops, dtprops, untranslated)

    def translate_type_props(self, types, props, objprops = {}, dtprops = {}, untranslated = {}):

        roles = self.infGetAvailableRoles(types)

        for k, v in props.iteritems():
            found = False
            for r in roles.itervalues():
                if r['name'] == k:
                    if r:
                        if r['is_literal']:
                            dtprops[r['uri']] = v
                        else:
                            objprops[r['uri']] = v
                        found = True
                        break
            if not found:
                untranslated[k] = v

        return (objprops, dtprops, untranslated)

    def UpdateProps(self, props):
        """Updates attributes from dict.
            
        Most common attributes are: name, namespaces, annotations, chosen_part2, ,basens, module_name.

        Args:
            props: Dict with properties to update.
        """
        # props:
        #   basens, namespaces, module_name, annotations, chosen_part2
        for k, v in props.iteritems():
            setattr(self, k, copy.copy(v))

        self.nslist = {}
        self.namespaces_by_uri = {}

        valid_namespaces = []
        for ns, uri in self.namespaces:
            if ns in ('p7tm'):
                continue
            self.nslist[ns] = uri
            self.namespaces_by_uri[uri] = ns
            valid_namespaces.append((ns, uri))

        self.namespaces = valid_namespaces

        self.nslist['p7tm'] = self.p7tm
        #self.p7tm_template = self.p7tm + 'template'

        self.props_by_uri = {}
        self.annotations_by_name = {}

        all_annotations = appdata.project.annotations + self.annotations
        for name, uri in all_annotations:
            self.props_by_uri[uri] = {'name': name, 'uri': uri, 'is_literal': True, 'is_optional': True}
            self.annotations_by_name[name] = uri

        self.roles_by_name = {}

        all_roles = appdata.project.roles + self.roles
        for name, uri in all_roles:
            self.props_by_uri[uri] = {'name': name, 'uri': uri, 'is_literal': False, 'is_optional': True}
            self.roles_by_name[name] = uri


        self.patterns_env_cached = None

        self.RefreshProps()

    def NewImport(self, import_source, importer_type, importer_kwargs = {}, reimport = True, **props):
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
        elif getattr(self, 'doc_connection', None) != None:
            return self.doc_connection.uri.replace('https://', '').replace('http://', '')
        else:
            filenames = []
            for v in self.paths:
                fname = os.path.basename(v)
                if fname.lower().endswith('.gz'):
                    fname = fname[:-3]
                filenames.append(fname)
            return ', '.join(filenames)

    def Reimport(self):
        """Reimports data"""   

        self.grClear()
        self.UpdateProps({})
        self.ChangeState(self.state_importing)
        self.importer_type(self, self.import_source, **self.importer_kwargs)
        self.UpdateRecentSources()

    def NewFile(self, path, readonly=False, **props):
        """Creates empty graph with specified props.

        Args:
            path: Path to source file.
            readonly: Useless =).
            props: Dict with properties, see UpdateProps method for details.
        """
        self.grClear()
        self.UpdateProps(props)
        self.paths = [path] if path else []
        if readonly:
            self.ChangeState(self.state_readonly)
        else:
            self.ChangeState(self.state_changed)

    def UpdateNamespacesFromLoad(self):
        maybe_part2 = None
        is_part2_found = False
        is_part2_dm = False
        is_part2_multi = False
        for ns, uri in self.nslist.iteritems():
            if uri in kb.part2_all_ns and not is_part2_dm:
                if is_part2_found:
                    is_part2_multi = True
                else:
                    is_part2_found = True
                    maybe_part2 = uri
                if ns=="dm":
                    is_part2_dm = True
            elif not self.namespaces_by_uri.get(uri):
                self.namespaces.append((ns, uri))

        if is_part2_found and not is_part2_multi:
            self.chosen_part2 = maybe_part2

        if not self.grSubjects(kb.rdf_type, self.p7tm+'TemplateDescription'):
            maybe_p7tm = self.grFindNsByObj('TemplateDescription')
            if maybe_p7tm:
                self.p7tm = maybe_p7tm

        self.UpdateProps({})

    def OpenFiles(self, paths, readonly=False, **props):
        """Opens files with specified props.

        Note that you can open multiple files here.

        Args:
            paths: Paths to source files.
            readonly: Make graph readonly if set to True.
            props: Dict with properties, see UpdateProps method for details.
        """
        self.UpdateProps(props)
        self.paths = paths
        for v in paths:
            if v.startswith('cfg://'):
                readonly = True
                break
                
        self.ChangeState(self.state_loading)
        @public.wth('{0} {1}...'.format(tm.main.loading, self.name), self)
        def f():
            try:
                self.grLoadFromFiles(self.paths)
                is_readonly = readonly
                if len(self.paths)!=1:
                    is_readonly = True
                @public.mth
                def f1():
                    self.UpdateNamespacesFromLoad()
                    if is_readonly:
                        self.ChangeState(self.state_readonly)
                    else:
                        self.ChangeState(self.state_loaded)
                    self.UpdateRecentSources()
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()
                if isinstance(e, DataFormatError):
                    @public.mth
                    def f4():
                        iso15926.common.dialogs.DataFormatErrorDialog(str(e), e.info)
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)
                    self.UpdateRecentSources()

    def OpenSparql(self, connection, **props):
        self.UpdateProps(props)
        self.doc_connection = connection
        self.paths = [connection.uri]
        self.ChangeState(self.state_loading)
        self.grBindSparqlEndpoint(connection)

        @public.wth('{0} {1}...'.format(tm.main.loading, self.name), self)
        def f():
            try:
                self.doc_connection.InitialQuery(self)
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()
            @public.mth
            def f1():
                self.UpdateNamespacesFromLoad()
                self.UpdateRecentSources()
                self.ChangeState(self.state_readonly)

    # common document methods

    def CanSave(self):
        return Document.CanSave(self) and len(self.paths)==1

    def Save(self):
        if not self.CanSave():
            return
        self.ChangeState(self.state_saving)
        @public.wth(tm.main.saving_doc.format(self.name), self)
        def f():
            try:
                self.grSaveToFile(self.paths[0], self.format, self.gzip)
                @public.mth
                def f2():
                    self.ChangeState(self.state_loaded)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)

    def SaveAs(self):
        if not self.CanSaveAs():
            return

        if len(self.paths) == 1:
            fname = os.path.basename(self.paths[0])
        else:
            fname, ext = os.path.splitext(self.name)

        default_wildcard = None
        wildcard_list = []
        for k, v in self.wildcard_map.iteritems():
            if v[0] == self.format and v[1] == self.gzip:
                wildcard_list.append((k, v))

        if wildcard_list:
            for k, v in wildcard_list:
                if v[2] in fname.lower():
                    default_wildcard = k
                    break
            else:
                default_wildcard = wildcard_list[0][0]

        path, wildcard = framework.dialogs.SaveAs(fname, self.msg_wildcard, default_wildcard)

        if not path or (not self.VerifySavePath(path) and path not in self.paths):
            return

        params = {'format': self.wildcard_map[wildcard][0], 'gzip': self.wildcard_map[wildcard][1]}
  
        self.paths = [path]
        self.ChangeState(self.state_saving)
        @public.wth(tm.main.saving_doc.format(self.name), self)
        def f():
            try:
                self.grSaveToFile(path, params['format'], params['gzip'])
                self.format = params['format']
                self.gzip = params['gzip']
                @public.mth
                def f2():
                    self.UpdateRecentSources(True)
                    self.id = None
                    if getattr(self, 'doc_connection', None) != None:
                        self.doc_name = None
                        self.doc_connection = None
                    self.sparql = None
                    self.ChangeState(self.state_loaded)
                    self.UpdateProps({})
                    self.UpdateRecentSources()
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)

    def SaveSnapshot(self):
        if not self.CanSaveSnapshot():
            return
        fname = self.name
        if len(self.paths) == 1:
            fname = os.path.basename(self.paths[0])

        default_wildcard = None
        wildcard_list = []
        for k, v in self.wildcard_map.iteritems():
            if v[0] == self.format and v[1] == self.gzip:
                wildcard_list.append((k, v))

        if wildcard_list:
            for k, v in wildcard_list:
                if v[2] in fname.lower():
                    default_wildcard = k
                    break
            else:
                default_wildcard = wildcard_list[0][0]

        path, wildcard = framework.dialogs.SaveSnapshot(tm.main.snapshot_of.format(fname), self.msg_wildcard, default_wildcard)
        if not path or not self.VerifySavePath(path):
            return

        params = {'format': self.wildcard_map[wildcard][0], 'gzip': self.wildcard_map[wildcard][1]}
  
        state = self.doc_state
        self.ChangeState(self.state_saving)
        @public.wth(tm.main.saving_doc_snapshot.format(self.name), self)
        def f():
            try:
                self.grSaveToFile(path, params['format'], params['gzip'])
                @public.mth
                def f2():
                    self.ChangeState(state)
                    doc = GraphDocument()
                    param = dict(chosen_part2=self.chosen_part2, namespaces=self.namespaces, annotations=self.annotations, roles=self.roles)
                    doc.OpenFiles([path], **param)
                    appdata.project.AddDocument(doc)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(state)

    # infomanagement

    def infGenerateUUID(self):
        return self.uuid_prefix+str(uuid.uuid4())

    def infDefaultRdsId(self, uri = None):
        if not uri:
            return self.uuid_prefix+str(uuid.uuid4())
        return kb.split_uri(uri)[1]

    def infDefaultRdsIdTemplate(self, uri = None):
        if not uri or self.uri_from_names:
            return self.uuid_prefix+str(uuid.uuid4())
        return kb.split_uri(uri)[1]

    def infGenerateUri(self, label=None):
        return self.basens+self.uuid_prefix+str(uuid.uuid4())

    def infGenerateTemplateUri(self, label=None):
        if self.uri_from_names and label:
            return self.basens+label.replace(' ', '_')
        return self.basens+self.uuid_prefix+str(uuid.uuid4())

    def infGenerateTemplateRoleUri(self, label):
        for a in self.grSubjects(kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
            role_uri = self.grOneObj(a, self.p7tm+'hasRole')
            if self.grTemplateRoleName(role_uri) == label:
                return role_uri

        if self.uri_from_names:
            return self.basens+label.replace(' ', '_')
        else:
            return self.basens+self.uuid_prefix+str(uuid.uuid4())

    def infExpandQname(self, qname):
        if qname.startswith('part2:'):
            return qname.replace('part2:', self.chosen_part2)

    def infMakeQname(self, uri, default=None):
        z = kb.split_uri(uri)
        if z:
            uri_head = z[0]
            uri_tail = z[1]
            if uri_head in kb.part2_all_ns:
                return 'part2:'+uri_tail
            prefix = kb.syntax_uri2ns.get(uri_head)
            if not prefix:
                prefix = self.namespaces_by_uri.get(uri_head)
            if prefix:
                return '{0}:{1}'.format(prefix, uri_tail)
        return default

    def infIsPart2Instance(self, types):
        for uri in types:
            z = kb.split_uri(uri)
            if z:
                uri_head = z[0]
                uri_tail = z[1]
                if uri_head not in kb.part2_all_ns:
                    return False
        return True

    def infGetPropertyName(self, uri, default=None):
        prop = self.props_by_uri.get(uri)
        if prop:
            return prop['name']

        for doc in appdata.documents(GraphDocument):
            if doc.grTriplesForSubj(uri):
                return doc.grTemplateRoleName(uri)

        z = kb.split_uri(uri)
        if z:
            uri_head = z[0]
            uri_tail = z[1]
            if uri_head in kb.part2_all_ns:
                return uri_tail
            prefix = kb.syntax_uri2ns.get(uri_head)
            if not prefix:
                prefix = self.namespaces_by_uri.get(uri_head)
            if prefix:
                return '{0}:{1}'.format(prefix, uri_tail)

        return default

    def _findTemplate(self, uri):
        for doc in appdata.documents(GraphDocument):
            tpl = doc.grTemplateGetDesc(uri, True)
            if tpl:
                return tpl

    def infVerifyEntity(self, uri):
        triples = self.grTriplesForSubj(uri)
        for t in triples:
            if t.p == kb.rdf_type:
                ns, fragment = kb.split_uri(t.v)
                if ns in kb.part2_all_ns:
                    info = kb.part2_itself.get('part2:'+fragment)
                    if not info:
                        continue

                    result = defaultdict(lambda: [0, ''])
                    optional = dict([(v['name'], v) for v in info['roles'].itervalues() if 'is_optional' in v and v['is_optional']])
                    required = dict([(v['name'], v) for v in info['roles'].itervalues() if 'is_optional' not in v or not v['is_optional']])
                    found = set()
                    duplicates = defaultdict(list)
                    for t in triples:
                        prop_ns, prop_fragment = kb.split_uri(t.p)
                        if prop_ns in kb.part2_all_ns:
                            duplicates[prop_fragment].append(t)
                            if prop_fragment in required:
                                role = required[prop_fragment]
                                if t.has_literal:
                                    if not role['type_uri'].startswith('xsd:'):
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                elif t.has_object:
                                    if role['type_uri'].startswith('xsd:'):
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                    else:
                                        value = role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                        r = self.infCheckClassification(t.v, value)
                                        if r > 0:
                                            result[t][0] = r
                                            if r == 2:
                                                result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                            else:
                                                result[t][1] += tm.main.prop_probable_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                found.add(prop_fragment)
                            elif prop_fragment in optional:
                                role = optional[prop_fragment]
                                if t.has_literal:
                                    if not role['type_uri'].startswith('xsd:'):
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                elif t.has_object:
                                    if role['type_uri'].startswith('xsd:'):
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                    else:
                                        value = role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                        r = self.infCheckClassification(t.v, value)
                                        if r > 0:
                                            result[t][0] = r
                                            if r == 2:
                                                result[t][1] += tm.main.prop_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                                            else:
                                                result[t][1] += tm.main.prop_probable_wrong_type%role['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                            else:
                                if prop_fragment in kb.part2_object_properties:
                                    result[t][0] = 2
                                    result[t][1] += tm.main.prop_wrong_role
                                else:
                                    result[t][0] = 1
                                    result[t][1] += tm.main.prop_not_standart

                    missing = required.viewkeys() - found
                    if missing:
                        result[None][0] = 2
                        result[None][1] += tm.main.prop_missing_roles%'\n'.join(missing)
                    for v in duplicates.itervalues():
                        if len(v) > 1:
                            for t in v:
                                result[t][0] = 2
                                result[t][1] += tm.main.prop_duplicate
                    return result

                for doc in appdata.documents(GraphDocument):
                    tpl = doc.grTemplateGetDesc(t.v, True)
                    if tpl:
                        result = defaultdict(lambda: [0, ''])
                        required = dict([(v['uri'], v) for v in tpl['roles'].itervalues()])
                        found = set()
                        duplicates = defaultdict(list)
                        for t in triples:
                            if t.p in required:
                                duplicates[t.p].append(t)
                                role = required[t.p]
                                if t.has_literal:
                                    if not role['is_literal']:
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri']
                                elif t.has_object:
                                    if role['is_literal']:
                                        result[t][0] = 2
                                        result[t][1] += tm.main.prop_wrong_type%role['type_uri']
                                    else:
                                        value = role['type_uri']
                                        if role.get('restricted_by_value'):
                                            if t.v != value:
                                                result[t][0] = 2
                                                result[t][1] += tm.main.prop_wrong_value%role['type_uri']
                                        else:
                                            r = self.infCheckClassification(t.v, value)
                                            if r > 0:
                                                result[t][0] = r
                                                if r == 2:
                                                    result[t][1] += tm.main.prop_wrong_type%role['type_uri']
                                                else:
                                                    result[t][1] += tm.main.prop_probable_wrong_type%role['type_uri']
                                found.add(t.p)
                            elif doc.grIsRole(t.p):
                                result[t][0] = 1
                                result[t][1] += tm.main.prop_probable_wrong
                            elif kb.split_uri(t.p)[0] in kb.part2_all_ns:
                                result[t][0] = 2
                                result[t][1] += tm.main.prop_wrong_role

                        missing = required.viewkeys() - found
                        if missing:
                            result[None][0] = 2
                            result[None][1] += tm.main.prop_missing_roles%'\n'.join([required[v]['name'] for v in missing])
                        for v in duplicates.itervalues():
                            if len(v) > 1:
                                for t in v:
                                    result[t][0] = 2
                                    result[t][1] += tm.main.prop_duplicate
                        return result
        return None

    def _grSearchErrors(self):
        res = []
        self.internal_counter = 0
        for s in self.grAllSubj():
            self.internal_counter += 1
            if self.infVerifyEntity(s):
                res.append(s)
        return set(res)

    def grSearchErrors(self, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchErrors()
                @public.mth
                def f2():
                    wizard.W_ResultsAvailable(res_id, result_set=res)
            except public.BreakTask:
                @public.mth
                def f3():
                    wizard.W_ResultsAvailable(res_id, result_set=set(), status = tm.main.status_interrupted)
            except:
                log.exception()
                @public.mth
                def f3():
                    wizard.W_ResultsAvailable(res_id, result_set=set(), status = tm.main.status_error)

    CL_OK      = 0
    CL_WARNING = 1
    CL_ERROR   = 2

    @classmethod
    def infCheckClassifers(cls, classifier, classifiers):
        if classifier in classifiers:
            return cls.CL_OK

        is_p2 = kb.split_uri(classifier)[0] in kb.part2_all_ns

        for c in classifiers:
            if kb.split_uri(c)[0] in kb.part2_all_ns:
                classifiers.remove(c)
                if is_p2:
                    if kb.p2IsDisjoint(classifier, c):
                        return cls.CL_ERROR
                    elif not kb.p2TypeIsSupertypeOf(classifier, c):
                        return cls.CL_WARNING
                    else:
                        return cls.CL_OK
                else:
                    for doc2 in appdata.documents(GraphDocument):
                        classification2 = doc2.patterns_env.patterns.get('Classification')

                        if classification2:
                            classifiers2 = classification2.find(doc2, dict(classified = classifier, classifier = ScannerPatterns.out))
                        
                        if not classifiers2:
                            continue

                        for c2 in classifiers2:    
                            c2_ns, c2_fragment = kb.split_uri(c2)
                            if c2_ns in kb.part2_all_ns:
                                if not kb.p2CanClassify(c2, c):
                                    return cls.CL_WARNING
                                for u in kb.p2GetClassifiers(c):
                                    if kb.p2IsDisjoint(u, c2):
                                        return cls.CL_WARNING
                                return cls.CL_OK
                break

        for c in classifiers:
            if is_p2:
                for doc2 in appdata.documents(GraphDocument):
                    classification2 = doc2.patterns_env.patterns.get('Classification')

                    if classification2:
                        classifiers2 = classification2.find(doc2, dict(classified = c, classifier = ScannerPatterns.out))
                    
                    if not classifiers2:
                        continue

                    for c2 in classifiers2:    
                        c2_ns, c2_fragment = kb.split_uri(c2)
                        if c2_ns in kb.part2_all_ns:
                            if not kb.p2CanClassify(c2, classifier):
                                return cls.CL_WARNING
                            for u in kb.p2GetClassifiers(classifier):
                                if kb.p2IsDisjoint(u, c2):
                                    return cls.CL_WARNING
                            return cls.CL_OK

            elif not is_p2:
                class_matched = c == classifier
                if not class_matched:
                    for doc2 in appdata.documents(GraphDocument):
                        specialization = doc2.patterns_env.patterns.get('Specialization')
                        if specialization:
                            results, current = set([c]), set([c])
                            while current and not class_matched:
                                next = set()
                                for v in current:
                                    found = specialization.find(doc2, dict(subclass = v, superclass = ScannerPatterns.out))
                                    if classifier in found:
                                        class_matched = True
                                        break
                                    next |= found - results
                                    results |= next
                                current = next
                        if class_matched:
                            break

                if class_matched:
                    for doc2 in appdata.documents(GraphDocument):
                        classification2 = doc2.patterns_env.patterns.get('Classification')

                        if classification2:
                            classifiers2 = classification2.find(doc2, dict(classified = classifier, classifier = ScannerPatterns.out))
                        
                        if not classifiers2:
                            continue

                        for c2 in classifiers2:
                            c2_ns, c2_fragment = kb.split_uri(c2)
                            if c2_ns in kb.part2_all_ns:
                                for doc3 in appdata.documents(GraphDocument):
                                    classification3 = doc3.patterns_env.patterns.get('Classification')

                                    if classification3:
                                        classifiers3 = classification3.find(doc3, dict(classified = c, classifier = ScannerPatterns.out))
                                    
                                    if not classifiers3:
                                        continue

                                    for c3 in classifiers3:
                                        c3_ns, c3_fragment = kb.split_uri(c3)
                                        if c3_ns in kb.part2_all_ns:
                                            if kb.p2IsDisjoint(c2, c3):
                                                return cls.CL_WARNING
                                            return cls.CL_OK
                else:
                    return cls.CL_WARNING
                    
        return None


    @classmethod
    def infCheckClassification(cls, uri, classifier):
        for doc in appdata.documents(GraphDocument):
            classification = doc.patterns_env.patterns.get('Classification')

            if classification:
                classifiers = classification.find(doc, dict(classified = uri, classifier = ScannerPatterns.out))
                if not classifiers:
                    continue

                result = cls.infCheckClassifers(classifier, classifiers)
                if result != None:
                    return result
       
        return cls.CL_OK

    def infCheckTypes(self, uri, types, include_superclasses = True):
        for tp in types:
            ns, fragment = kb.split_uri(tp)
            if ns in kb.part2_all_ns:
                for o in self.grObjects(uri, kb.rdf_type):
                    ons, ofragment = kb.split_uri(o)
                    if ons in kb.part2_all_ns and fragment == ofragment:
                        return True

                for doc in appdata.documents(GraphDocument):
                    if doc != self:
                        for o in doc.grObjects(uri, kb.rdf_type):
                            ons, ofragment = kb.split_uri(o)
                            if ons in kb.part2_all_ns and fragment == ofragment:
                                return True

            elif self._findTemplate(tp):
                if tp in set(self.grObjects(uri, kb.rdf_type)):
                    return True

                for doc in appdata.documents(GraphDocument):
                    if doc != self:
                        if tp in set(doc.grObjects(uri, kb.rdf_type)):
                            return True

            else:
                patterns_env = appdata.environment_manager.GetPatternsEnv(self, None)
                if tp in patterns_env.get_classifiers(self, uri):
                    return True
                for doc in appdata.documents(GraphDocument):
                    if doc != self:
                        patterns_env = appdata.environment_manager.GetPatternsEnv(doc, None)
                        if tp in patterns_env.get_classifiers(doc, uri):
                            return True
        
        if include_superclasses:
            next = sup = set(self.infFindSuperClasses(uri))
            while next:
                current, next = next, set()
                for s in current:
                    if self.infCheckTypes(s, types, include_superclasses = False):
                        return True
                else:
                    sup |= next

        return False

    def infFindSuperClasses(self, uri):
        sup = self.grObjects(uri, 'http://www.w3.org/2000/01/rdf-schema#subClassOf')
        if not sup:
            for doc in appdata.documents(GraphDocument):
                if doc != self:
                    sup = doc.grObjects(uri, 'http://www.w3.org/2000/01/rdf-schema#subClassOf')
                    if sup:
                        break
        return sup

    def infFindNameAndTypes(self, uri, defaultname, triples = None):
        if not triples:
            triples = self.grTriplesForSubj(uri)

        if not triples:
            for doc in appdata.documents(GraphDocument):
                if doc != self:
                    triples = doc.grTriplesForSubj(uri)
                    if triples:
                        break
            else:
                return defaultname, []
 
        labels       = []
        literal_repr = []
        types        = []

        for t in triples:
            for idx, value in enumerate(kb.vis_labels):
                if t.p == value:
                    heapq.heappush(literal_repr, (idx, t.l))
            if t.p in kb.labels_rdfs:
                labels.append(t.l)
            elif t.p==kb.rdf_type:
                types.append(t.o)

        if labels:
            return sorted(labels), types
        elif literal_repr:
            return heapq.heappop(literal_repr)[1], types
        else:
            return defaultname, types

    def infGetTypeNameAndIcon(self, uri):
        z = kb.split_uri(uri)
        if z:
            uri_head = z[0]
            uri_tail = z[1]
            if uri_head in kb.part2_all_ns:
                info = kb.part2_itself.get('part2:'+uri_tail)
                if info:
                    return uri_tail, info['icon']

            if kb.syntax_uri2ns.get(uri_head):
                return self.infMakeQname(uri, default=uri), 'iso_syntax'
            elif uri_head == self.p7tm:
                if uri_tail in ('BaseTemplateStatement', 'TemplateSpecialization', 'TemplateDescription', 'TemplateRoleDescription', 'MetaTemplateStatement'):
                    return self.infMakeQname(uri, default=uri), 'iso_template'
                elif uri_tail == 'Template':
                    return self.infMakeQname(uri, default=uri), 'iso_template_c'
                elif uri_tail == 'RDLTemplateStatement':
                    return self.infMakeQname(uri, default=uri), 'iso_spec_template'

        tpl = self._findTemplate(uri)
        if tpl:
            return tpl['name'], 'iso_spec_template' if tpl.get('supertemplate') else 'iso_template'

        return None

    def infGetEntityVisualInternal(self, uri, cache, triples = None, tp_depth = 0, for_subclass = False):
        cached = cache.get(uri)
        if cached:
            return cached

        res = self.infGetTypeNameAndIcon(uri)
        if res:
            result = (res[0], '', res[1])
            cache[uri] = result
            return result

        tp_name = ''
        name, types = self.infFindNameAndTypes(uri, self.infMakeQname(uri, default=uri), triples)

        if tp_depth < 3:
            for tp in types:
                res = self.infGetTypeNameAndIcon(tp)
                if res:
                    found = kb.icons_map.get(res[1])
                    if found:
                        result = (name, res[0], found)
                        cache[uri] = result
                        return result

                tp_name, stp_name, tp_icon = self.infGetEntityVisualInternal(tp, cache, tp_depth = tp_depth + 1)
                if isinstance(tp_name, list):
                    tp_name = ', '.join(tp_name)
                found = kb.icons_map.get(tp_icon)
                if found:
                    result = (name, tp_name, found)
                    cache[uri] = result
                    return result
                found = kb.icons_map.get(tp)
                if found:
                    result = (name, tp_name, found)
                    cache[uri] = result
                    return result

        icon = 'iso_unknown'
        if not for_subclass:
            next = sup = set(self.infFindSuperClasses(uri))
            while next:
                current, next = next, set()
                for s in current:
                    n, t, i = self.infGetEntityVisualInternal(s, cache, tp_depth = tp_depth, for_subclass = True)
                    if i != 'iso_unknown':
                        icon = i
                        if i != 'iso_syntax':
                            result = (name, tp_name, i)
                            cache[uri] = result
                            return result
                    next |= set(self.infFindSuperClasses(s)) - sup
                else:
                    sup |= next

        result = (name, tp_name, icon)
        cache[uri] = result
        return result

    def infGetEntityVisual(self, uri, triples = None):
        cache = {}
        return self.infGetEntityVisualInternal(uri, cache, triples)

    def infGetAvailableProperties(self, uri):
        types = self.grObjects(uri, kb.rdf_type)
        props = dict(self.props_by_uri)
        props.update(self.infGetAvailableRoles(types))
        props[kb.rdf_type] = {'name': 'rdf:type', 'uri': kb.rdf_type, 'is_literal': False}      
        return props

    def infGetAvailableRoles(self, types):
        props = {}
        for uri in types:
            z = kb.split_uri(uri)
            if z:
                uri_head = z[0]
                uri_tail = z[1]
                if uri_head in kb.part2_all_ns:
                    info = kb.part2_itself.get('part2:'+uri_tail)
                    if info:
                        for k, v in info['roles'].iteritems():
                            n = k.replace('part2:', self.chosen_part2)
                            d = dict(v)
                            d['is_literal'] = v['type_uri'].startswith('xsd:')
                            d['uri'] = d['uri'].replace('part2:', self.chosen_part2)
                            d['type_uri'] = d['type_uri'].replace('part2:', self.chosen_part2).replace('xsd:', kb.ns_xsd)
                            props[n] = d
            tpl = self._findTemplate(uri)
            if tpl:
                props.update(tpl['roles'])
        return props

    def grProgress(self, percent):
        self.AsyncChangeState(self.state_loading, percent)

    def grIsTemplate(self, uri):
        for s in self.grSubjects(self.p7tm+'hasTemplate', uri):
            if self.grHas(s, kb.rdf_type, self.p7tm+'TemplateDescription'):
                return True
        return False

    def grTemplateGetDescUri(self, uri):
        for s in self.grSubjects(self.p7tm+'hasTemplate', uri):
            if self.grHas(s, kb.rdf_type, self.p7tm+'TemplateDescription'):
                return s
        return None

    def grTemplateGetDesc(self, uri, include_roles = False):
        for s in self.grSubjects(self.p7tm+'hasTemplate', uri):
            if self.grHas(s, kb.rdf_type, self.p7tm+'TemplateDescription'):
                desc = {}
                name = self.grLiteral(uri, kb.ns_rdfs+'label')
                if name is None:
                    name = kb.split_uri(uri)[1]
                desc['uri'] = uri
                desc['name'] = name
                desc['comment'] = '\n'.join(self.grLiterals(uri, kb.ns_rdfs+'comment'))
                desc['supertemplate'] = self.grTemplateGetSuper(uri)
                if include_roles:
                    desc['roles'] = self.grGetTemplateRoles(uri)
                return desc
        return None

    def grTemplateGetSuper(self, uri):
        templatespec = self.grOneSubj(self.p7tm+'hasSubTemplate', uri)
        if templatespec:
            return self.grOneObj(templatespec, self.p7tm+'hasSuperTemplate')
        return None

    def grTemplateGetSpecializations(self, uri):
        data = []
        next = self.grSubjects(self.p7tm+'hasSuperTemplate', uri)
        while next:
            current = next
            next = []
            for v in current:
                spec = self.grOneObj(v, self.p7tm+'hasSubTemplate')
                if spec:
                    data.append(spec)
                    next += list(self.grSubjects(self.p7tm+'hasSuperTemplate', spec))
        return data

    def grTemplateGetDependencies(self, uri):
        current = uri
        while True:
            templatespec = self.grOneSubj(self.p7tm+'hasSubTemplate', current)
            if not templatespec:
                break
            spec = self.grOneObj(templatespec, self.p7tm+'hasSuperTemplate')
            if not spec:
                break
            current = spec

        data = [current]
        next = self.grSubjects(self.p7tm+'hasSuperTemplate', current)
        while next:
            current = next
            next = []
            for v in current:
                spec = self.grOneObj(v, self.p7tm+'hasSubTemplate')
                if spec:
                    data.append(spec)
                    next += list(self.grSubjects(self.p7tm+'hasSuperTemplate', spec))

        return data

    def grIsRole(self, role_uri):
        for a in self.grSubjects(self.p7tm+'hasRole', role_uri):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                return True
        return False

    def grRoleDescUri(self, template, role_uri):
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription') and self.grHas(a, self.p7tm+'hasRole', role_uri):
                return a

    def grRoleDesc(self, template, role_uri):
        roledesc_uri = self.grRoleDescUri(template, role_uri)
        if not roledesc_uri:
            return

        index = int(self.grLiteral(roledesc_uri, self.p7tm+'valRoleIndex'))
        restricted_type = self.grOneObj(roledesc_uri, self.p7tm+'hasRoleFillerType')
        name = self.grLiteral(role_uri, kb.ns_rdfs+'label')
        if name is None:
            name = kb.split_uri(role_uri)[1]

        ent = {'name': name, 'uri': role_uri, 'type_uri': restricted_type, 'index': index}
        ent['comment'] = '\n'.join(self.grLiterals(roledesc_uri, kb.ns_rdfs+'comment'))
        ent['annotations'] = {}
        ent['roles'] = {}
        for t in self.grTriplesForSubj(role_uri):
            if t.p in self.props_by_uri and t.has_literal:
                ent['annotations'][t.p] = t.l
        for t in self.grTriplesForSubj(role_uri):
            if t.p in self.props_by_uri and t.has_object:
                ent['roles'][t.p] = t.o
        ent['is_literal'] = restricted_type.startswith(kb.ns_xsd)
        ent['restricted_by_value'] = False
        restrictions = [a for a in self.grObjects(template, kb.ns_rdfs+'subClassOf') if self.grHas(a, kb.rdf_type, kb.ns_owl+'Restriction')]
        for a in restrictions:
            if role_uri == self.grOneObj(a, kb.ns_owl+'onProperty'):
                some = self.grOneObj(a, kb.ns_owl+'someValuesFrom')
                if not some:
                    continue
                oneof = self.grOneObj(some, kb.ns_owl+'oneOf')
                if not oneof:
                    continue
                lst = self.grGet_rdflist(oneof)
                if len(lst) == 1:
                    ent['type_uri'] = lst[0]
                    ent['restricted_by_value'] = True
        return ent

    def grGetTemplateRoles(self, uri):
        role_uris = [self.grOneObj(a, self.p7tm+'hasRole') for a in self.grSubjects(self.p7tm+'hasTemplate', uri) if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription')]
        roles = {}
        for r in role_uris:
            role = self.grRoleDesc(uri, r)
            if role:
                roles[role['name']] = role
        return roles

    def infGetRestrictionNameAndIcon(self, uri, restricted_by_value):
        z = kb.split_uri(uri)
        if z:
            uri_head = z[0]
            uri_tail = z[1]
            if uri_head==kb.ns_xsd:
                return ('xsd:'+uri_tail, 'iso_syntax')

        name, tp_label, icon = self.infGetEntityVisual(uri)

        if isinstance(name, list):
            name = ', '.join(name)

        if restricted_by_value:
            return name, icon
        else:
            return name, kb.icons_map.get(icon, 'iso_unknown')

    def grCollectTemplateRoleTriples(self, template, role_name, edit = False):
        triples = []
        found = False
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                role_uri = self.grOneObj(a, self.p7tm+'hasRole')
                if self.grTemplateRoleName(role_uri) == role_name:
                    found = True
                    index = int(self.grLiteral(a, self.p7tm+'valRoleIndex'))
                    triples += self.grTriplesForSubj(a)
                    break

        if not found:
            return []

        for a in self.grObjects(template, kb.ns_rdfs+'subClassOf'):
            if self.grHas(a, kb.rdf_type, kb.ns_owl+'Restriction'):
                if role_uri == self.grOneObj(a, kb.ns_owl+'onProperty'):
                    triples.append(ObjectTriple.of(template, kb.ns_rdfs+'subClassOf', a))
                    triples += self.grTriplesForSubj(a)
                    some = self.grOneObj(a, kb.ns_owl+'someValuesFrom')
                    if some:
                        oneof = self.grOneObj(some, kb.ns_owl+'oneOf')
                        if oneof:
                            triples += self.grTriplesForSubj(some)
                            i = oneof
                            while i and i != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#nil':
                                triples += self.grTriplesForSubj(i)
                                i = self.grOneObj(i, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')
                    break
            elif self.grHas(a, kb.rdf_type, kb.ns_owl+'Class'):
                intersection = self.grOneObj(a, kb.ns_owl+'intersectionOf')
                if intersection:
                    items = self.grGet_rdflist(intersection)
                    found = False
                    for v in items:
                        if role_uri == self.grOneObj(v, kb.ns_owl+'onProperty'):
                            found = True
                    if found:
                        triples.append(ObjectTriple.of(template, kb.ns_rdfs+'subClassOf', a))
                        triples += self.grTriplesForSubj(a)
                        i = intersection
                        while i and i != 'http://www.w3.org/1999/02/22-rdf-syntax-ns#nil':
                            triples += self.grTriplesForSubj(i)
                            triples += self.grTriplesForSubj(self.grOneObj(i, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#first'))
                            i = self.grOneObj(i, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')
                        break

        if edit or len(self.grSubjects(self.p7tm+'hasRole', role_uri)) <= 1:
            triples += self.grTriplesForSubj(role_uri)

        return triples

    def grTemplateRoleTriplesByDesc(self, template, roledesc):
        triples = []
        qname = template
        rindex = str(roledesc['index'])
        rqname = roledesc['uri']
        rtype = roledesc['type_uri']
        rbyvalue = roledesc.get('restricted_by_value')
        rliteral = roledesc['is_literal']
        rname = roledesc.get('name')
        rcomment = roledesc.get('comment')
        rann = roledesc.get('annotations')
        robj = roledesc.get('roles')
        sup = self.grTemplateGetSuper(qname)

        rdesc = '{0}__rdesc{1}'.format(qname, rindex)
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                if rqname == self.grOneObj(a, self.p7tm+'hasRole'):
                    rdesc = a
                    break

        if rbyvalue:
            bnode = new_bnodeid()
            triples.append(ObjectTriple.of(qname, kb.ns_rdfs+'subClassOf', bnode))
            triples.append(ObjectTriple.of(bnode, kb.rdf_type, kb.ns_owl+'Restriction'))
            triples.append(ObjectTriple.of(bnode, kb.ns_owl+'onProperty', rqname))

            bnode2 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode, kb.ns_owl+'someValuesFrom', bnode2))
            triples.append(ObjectTriple.of(bnode2, kb.rdf_type, kb.ns_owl+'Class'))

            bnode3 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode2, kb.ns_owl+'oneOf', bnode3))
            triples.append(ObjectTriple.of(bnode3, kb.rdf_type, kb.ns_rdf + 'List'))
            triples.append(ObjectTriple.of(bnode3, kb.ns_rdf + 'first', rtype))
            triples.append(ObjectTriple.of(bnode3, kb.ns_rdf + 'next', kb.ns_rdfs + 'nil'))

        elif sup:
            bnode = new_bnodeid()
            triples.append(ObjectTriple.of(qname, kb.ns_rdfs+'subClassOf', bnode))
            triples.append(ObjectTriple.of(bnode, kb.rdf_type, kb.ns_owl+'Restriction'))
            triples.append(ObjectTriple.of(bnode, kb.ns_owl+'onProperty', rqname))
            triples.append(ObjectTriple.of(bnode, kb.ns_owl+'someValuesFrom', rtype))

        else:
            bnode = new_bnodeid()
            triples.append(ObjectTriple.of(qname, kb.ns_rdfs+'subClassOf', bnode))
            triples.append(ObjectTriple.of(bnode, kb.rdf_type, kb.ns_owl+'Class'))

            bnode2 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode, kb.ns_owl+'intersectionOf', bnode2))
            triples.append(ObjectTriple.of(bnode2, kb.rdf_type, kb.ns_rdf + 'List'))
            
            bnode3 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode2, kb.ns_rdf + 'first', bnode3))
            triples.append(ObjectTriple.of(bnode3, kb.rdf_type, kb.ns_owl+'Restriction'))
            triples.append(ObjectTriple.of(bnode3, kb.ns_owl+'onProperty', rqname))
            triples.append(ObjectTriple.of(bnode3, kb.ns_owl+'allValuesFrom', rtype))

            bnode4 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode2, kb.ns_rdf + 'rest', bnode4))

            bnode5 = new_bnodeid()
            triples.append(ObjectTriple.of(bnode4, kb.ns_rdf + 'first', bnode5))
            triples.append(ObjectTriple.of(bnode5, kb.rdf_type, kb.ns_owl+'Restriction'))
            triples.append(ObjectTriple.of(bnode5, kb.ns_owl+'onProperty', rqname))
            triples.append(DatatypeQuad.of(bnode5, kb.ns_owl+'qualifiedCardinality', '1', kb.ns_xsd+'nonNegativeInteger'))
            if rliteral:
                triples.append(ObjectTriple.of(bnode5, kb.ns_owl+'onDataRange', rtype))
            else:
                triples.append(ObjectTriple.of(bnode5, kb.ns_owl+'onClass', rtype))
            triples.append(ObjectTriple.of(bnode4, kb.ns_rdf + 'rest', kb.ns_rdf + 'nil'))

        triples.append(ObjectTriple.of(rdesc, kb.rdf_type, self.p7tm+'TemplateRoleDescription'))
        triples.append(ObjectTriple.of(rdesc, kb.rdf_type, kb.ns_owl+'Thing'))
        triples.append(DatatypeQuad.of(rdesc, self.p7tm+'valRoleIndex', rindex, kb.ns_xsd+'integer'))
        triples.append(ObjectTriple.of(rdesc, self.p7tm+'hasRoleFillerType', rtype))
        triples.append(ObjectTriple.of(rdesc, self.p7tm+'hasRole', rqname))
        triples.append(ObjectTriple.of(rdesc, self.p7tm+'hasTemplate', qname))
        if rcomment:
            triples.append(LiteralTriple.of(rdesc, kb.ns_rdfs+'comment', rcomment))

        if rliteral:
            triples.append(ObjectTriple.of(rqname, kb.rdf_type, kb.ns_owl+'DatatypeProperty'))
            triples.append(ObjectTriple.of(rqname, kb.ns_rdfs+'subPropertyOf', self.p7tm+'valDataRoleFiller'))
        else:
            triples.append(ObjectTriple.of(rqname, kb.rdf_type, kb.ns_owl+'ObjectProperty'))
            triples.append(ObjectTriple.of(rqname, kb.ns_rdfs+'subPropertyOf', self.p7tm+'hasObjectRoleFiller'))
        if rname:
            triples.append(LiteralTriple.of(rqname, kb.ns_rdfs+'label', rname))

        if rann:
            for k, v in rann.iteritems():
                triples.append(LiteralTriple.of(rqname, k, v))

        if robj:
            for k, v in robj.iteritems():
                triples.append(ObjectTriple.of(rqname, k, v))

        return triples

    def grTemplateRoleName(self, role_uri):
        name = self.grLiteral(role_uri, kb.ns_rdfs+'label')
        if name is None:
            name = kb.split_uri(role_uri)[1]
        return name

    def grTemplateRoleUri(self, template, role_name):
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                role_uri = self.grOneObj(a, self.p7tm+'hasRole')
                if self.grTemplateRoleName(role_uri) == role_name:
                    return role_uri
        return None

    def grGetTemplateRoleIndex(self, template, role_name):
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                if self.grTemplateRoleName(self.grOneObj(a, self.p7tm+'hasRole')) == role_name:
                    return int(self.grLiteral(a, self.p7tm+'valRoleIndex'))

    def grSetTemplateRoleIndex(self, template, role_name, index):
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                if self.grTemplateRoleName(self.grOneObj(a, self.p7tm+'hasRole')) == role_name:
                    for t in self.grTriplesForSubj(a):
                        if t.has_literal and t.p == self.p7tm+'valRoleIndex':
                            index_old = int(t.l)
                            if index_old != index:
                                t.with_l(str(index)).insertto(self)
                                t.deletefrom(self)
                            return index_old


    def grUpdateTemplateByDesc(self, desc):
        qname   = desc['uri']
        sup     = desc.get('supertemplate')
        name    = desc.get('name')
        comment = desc.get('comment')

        templatedesc = self.grTemplateGetDescUri(qname)
        if not templatedesc:
            templatedesc = qname+'__desc'
        else:
            for t in self.grTriplesForSubj(templatedesc):
                if self.p7tm+'valNumberOfRoles':
                    t.deletefrom(self)

        templatespec = self.grOneSubj(self.p7tm+'hasSubTemplate', qname)
        if not templatespec:
            templatespec = qname+'__spec'
        else:
            sup_old = self.grOneObj(templatespec, self.p7tm+'hasSuperTemplate')
            if sup_old != sup:
                for v in self.grGetTemplateRoles(uri).itervalues():
                    for t in self.grCollectTemplateRoleTriples(uri, v['uri']):
                        t.deletefrom(self)
                for t in self.grTriplesForSubj(templatespec):
                    t.deletefrom(self)

        for t in self.grTriplesForSubj(qname):
            if t.p in (kb.ns_rdfs+'label', kb.ns_rdfs+'comment', kb.ns_rdfs+'subClassOf'):
                t.deletefrom(self)

        if name:
            LiteralTriple.insert(self, qname, kb.ns_rdfs+'label', name)
        if comment:
            LiteralTriple.insert(self, qname, kb.ns_rdfs+'comment', comment)

        ObjectTriple.insert(self, qname, kb.rdf_type, kb.ns_owl+'Class')
        ObjectTriple.insert(self, qname, kb.rdf_type, self.p7tm+'Template')

        if sup:
            ObjectTriple.insert(self, qname, kb.ns_rdfs+'subClassOf', self.p7tm+'RDLTemplateStatement')
            ObjectTriple.insert(self, qname, kb.ns_rdfs+'subClassOf', sup)
            ObjectTriple.insert(self, templatespec, kb.rdf_type, self.p7tm+'TemplateSpecialization')
            ObjectTriple.insert(self, templatespec, kb.rdf_type, kb.ns_owl+'Thing')
            ObjectTriple.insert(self, templatespec, self.p7tm+'hasSubTemplate', qname)
            ObjectTriple.insert(self, templatespec, self.p7tm+'hasSuperTemplate', sup)
            suproles = self.grGetTemplateRoles(sup)
            for v in suproles.itervalues():
                for t in self.grTemplateRoleTriplesByDesc(qname, v):
                    t.insertto(self)
        else:
            ObjectTriple.insert(self, qname, kb.ns_rdfs+'subClassOf', self.p7tm+'BaseTemplateStatement')

        roles_count = 0
        for a in self.grSubjects(self.p7tm+'hasTemplate', qname):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                roles_count += 1

        ObjectTriple.insert(self, templatedesc, kb.rdf_type, self.p7tm+'TemplateDescription')
        ObjectTriple.insert(self, templatedesc, kb.rdf_type, kb.ns_owl+'Thing')
        DatatypeQuad.insert(self, templatedesc, self.p7tm+'valNumberOfRoles', str(roles_count), kb.ns_xsd+'integer')
        ObjectTriple.insert(self, templatedesc, self.p7tm+'hasTemplate', qname)

    def grCollectEntityTriples(self, uri, edit = False):
        triples = self.grTriplesForSubj(uri)
        if self.grIsTemplate(uri):
            for v in self.grGetTemplateRoles(uri).itervalues():
                triples += self.grCollectTemplateRoleTriples(uri, v['name'], edit)
            templatespec = self.grOneSubj(self.p7tm+'hasSubTemplate', uri)
            if templatespec:
                triples += self.grTriplesForSubj(templatespec)
            for s in self.grSubjects(self.p7tm+'hasTemplate', uri):
                if self.grHas(s, kb.rdf_type, self.p7tm+'TemplateDescription'):
                    triples += self.grTriplesForSubj(s)
                    break
        return triples

    def grGetTemplates(self):
        templates = {}
        for s in self.grSubjects(kb.rdf_type, self.p7tm+'TemplateDescription'):
            tpl = self.grOneObj(s, self.p7tm+'hasTemplate')
            if tpl:
                name = self.grLiteral(tpl, kb.ns_rdfs+'label')
                if name is None:
                    name = kb.split_uri(tpl)[1]
                templates[name] = tpl
        return templates

    def grDeleteTemplateRole(self, template, role_name):
        index = self.grGetTemplateRoleIndex(template, role_name)
        for a in self.grSubjects(self.p7tm+'hasTemplate', template):
            if self.grHas(a, kb.rdf_type, self.p7tm+'TemplateRoleDescription'):
                for t in self.grTriplesForSubj(a):
                    if t.has_literal and t.p == self.p7tm+'valRoleIndex':
                        other_index = int(t.l)
                        if self.index < other_index:
                            t.with_l(str(other_index-1)).insertto(self.g)
                            t.deletefrom(self.g)
                            break

        for t in self.grCollectTemplateRoleTriples(template, role_name):
            t.deletefrom(self)       

    def grFindTemplates(self, label, res_id):
        @public.wth(tm.main.loading_rels_in.format(self.name), self)
        def f1():
            try:
                if self.sparql:
                    self.sparql.QueryTemplates(self, self.p7tm, label)

                all_labels = [compact_uri(v) for v in kb.all_labels]
                res = set()
                dlabel = label.decode('utf-8').lower()
                for a in self.grSubjects(kb.rdf_type, self.p7tm+'TemplateDescription'):
                    self.qs.add(a)
                    tpl = self.grOneObj(a, self.p7tm+'hasTemplate')
                    if tpl:
                        self.qs.add(tpl)
                        if label in tpl:
                            res.add(tpl)
                        else:
                            for value in all_labels:
                                for t in self.grTriplesForSubj(tpl):
                                    if t.has_literal and t[1] == value and dlabel in t[2].decode('utf-8').lower():
                                        res.add(tpl)
                        
                @public.mth
                def f2():
                    wizard.W_ResultsAvailable(res_id, result_set=res)
            except public.BreakTask:
                @public.mth
                def f3():
                    wizard.W_ResultsAvailable(res_id, result_set=set(), status = tm.main.status_interrupted)
            except:
                log.exception()
                @public.mth
                def f3():
                    wizard.W_ResultsAvailable(res_id, result_set=set(), status = tm.main.status_error)