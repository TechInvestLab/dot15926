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




import iso15926.kb as kb
from iso15926.tools.builder import Builder
from iso15926.tools.scanner import Scanner, ScannerPatterns
from iso15926.tools.scantools import set_lift
from iso15926.graph.graph_view import Command_show, Command_sparql, Command_templates
from iso15926.kb.dmviews import XSDTypesView, Part2TypesView
from iso15926.graph.graph_view import GraphView
from framework.document import Document
from iso15926.graph.graph_document import GraphDocument
from iso15926.patterns.patterns_document import PatternsDocument
from iso15926.tools.patterns import PatternsEnv
import sys
from framework.util import GenerateModel, ModelCompleter, GenerateSortedModel
from framework.util import InsertToSortedModel, DeleteFromSortedModel, IsUri, TaskTarget
from PySide.QtCore import *
from PySide.QtGui import *
from graphlib import *

def verify_patterns():
    import csv
    def inf(uri):
        tp, label, rdl = '', '', ''
        for doc in appdata.documents(GraphDocument):
            if getattr(doc, 'idi', None) != None:
                for t in doc.grTriplesForSubj(uri):
                    if t.p == kb.rdf_type:
                        tp = t.v
                    elif t.p == kb.rdfs_label:
                        label = t.v
                    elif t.p == 'http://posccaesar.org/rdl/rdsWipEquivalent':
                        rdl = t.v
        return tp, label, rdl

    with open('verify.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        
        writer.writerow(('Pattern', ' Template', 'Role', 'Expected', 'Found', 'Found RDL', 'Found type', 'Found label', 'Error type'))
        doc = appdata.active_document
        fi = {doc.name: doc.patterns.keys()}
        patterns_env = appdata.environment_manager.GetPatternsEnv(None, fi)

        for k, v in patterns_env.patterns.iteritems():
            for on, o in v.options.iteritems():
                for p in o.parts:
                    if p.ownrole:
                        value = None
                        fixed = False

                        for p1 in o.parts:
                            role = p1.roles.get(p.ownrole)
                            if role and 'type_uri' in role:
                                value = role['type_uri']
                                fixed = role.get('restricted_by_value', False)
                                template_name = p1.typename
                                role_name = role['name']
                                break

                        if value:
                            if fixed:
                                if set([value]) != p.uri:
                                    for u in p.uri:
                                        tp, label, rdl = inf(u)
                                        writer.writerow((k, template_name, role_name, value, u, rdl, tp, label, 'Value'))
                            else:
                                if isinstance(value, basestring):
                                    types = [value]
                                else:
                                    types = value

                                if p.uri:
                                    uris = set()
                                    for uri in p.uri:
                                        for d in appdata.documents(GraphDocument):
                                            for t in d.grTriplesForSubj(uri):
                                                if t.p != 'http://posccaesar.org/rdl/rdsWipEquivalent':
                                                    uris.add(uri)
                                                    break

                                    for u in p.uri - uris:
                                        tp, label, rdl = inf(u)
                                        writer.writerow((k, template_name, role_name, value, u, rdl, tp, label, 'Not found'))

                                    unmatched = set()
                                    for uri in uris:
                                        for tp in types:
                                            res = GraphDocument.infCheckClassification(uri, tp)
                                            if res == GraphDocument.CL_OK:
                                                break
                                        else:
                                            unmatched.add(uri)

                                    for u in unmatched:
                                        tp, label, rdl = inf(u)
                                        writer.writerow((k, template_name, role_name, value, u, rdl, tp, label, 'URI'))

                                if p.types:
                                    uris = set()
                                    for uri in p.types:
                                        for d in appdata.documents(GraphDocument):
                                            for t in d.grTriplesForSubj(uri):
                                                if t.p != 'http://posccaesar.org/rdl/rdsWipEquivalent':
                                                    uris.add(uri)
                                                    break

                                    for u in p.types - uris:
                                        tp, label, rdl = inf(u)
                                        writer.writerow((k, template_name, role_name, value, u, rdl, tp, label, 'Not found'))

                                    unmatched = set()
                                    for uri in uris:
                                        for tp in types:
                                            res = GraphDocument.infCheckClassifers(tp, set([uri]))
                                            if res == GraphDocument.CL_OK:
                                                break
                                        else:
                                            unmatched.add(uri)

                                    for u in unmatched:
                                        tp, label, rdl = inf(u)
                                        writer.writerow((k, template_name, role_name, value, u, rdl, tp, label, 'Type'))



class EnvironmentContextException(Exception):
    pass

class EnvironmentContext:
    """Allows to execute python code like if it was executed in console."""
    def __init__(self, target = None, locals = None, env_cache = False):
        """Constructor.
        
        Args:
            target: Module name or document, dafult environment will based on it
            local: dict with local varibles
        """
        self.environment        = None
        self.locals             = locals if locals != None else appdata.console_locals
        if env_cache:
            self.env_cache          = {}
            self.locals['context']  = self.SwitchEnvironmentEx
        else:
            self.locals['context']  = self.SwitchEnvironment
        self.Update(target)

    def ExecutePythonString(self, text):
        try:
            try:
                return eval(text, globals(), self.GetLocals())
            except SyntaxError:
                tb = sys.exc_traceback
                if tb.tb_next is None:
                    exec text in self.GetLocals()
                else:
                    raise
        except NameError as e:
            tb = sys.exc_traceback
            if tb.tb_next and tb.tb_next.tb_next is None:
                log("Error: {0}\n", e.args[0])
            else:
                raise

    def ExecutePythonString2(self, text):
        try:
            return eval(text, globals(), self.GetLocals())
        except SyntaxError:
            tb = sys.exc_traceback
            if tb.tb_next is None:
                exec text in self.GetLocals()
            else:
                raise

    def ExecutePythonFile(self, filename):
        execfile(filename, self.GetLocals())

    def Update(self, target = None):
        env = None

        if appdata.environment_manager:
            if target != None:
                if isinstance(target, Document):
                    env = appdata.environment_manager.GetWorkEnvironment(target, include_scanner=True, include_builder=True, include_patterns=True)
                else:
                    env = FindEnvironment(module_name)
            else:
                document = appdata.active_document
                view     = appdata.active_view
                if view:
                    document = view.document
                if document:
                    env = appdata.environment_manager.GetWorkEnvironment(document, include_scanner=True, include_builder=True, include_patterns=True)
        
        self.Setup(env)

    def Setup(self, environment = None):
        previous_env = self.environment

        if previous_env != None:
            for k, v in previous_env.iteritems():
                del self.locals[k]

        self.environment = environment
        
        if self.environment != None:
            self.locals.update(self.environment)

        return previous_env

    def GetLocals(self):
        return self.locals

    def GetEnvironment(self):
        return self.environment

    def FindEnvironment(self, name):
        for doc in appdata.documents(GraphDocument):
            if doc.module_name == name and appdata.environment_manager:
                return appdata.environment_manager.GetWorkEnvironment(doc, include_scanner=True, include_builder=True, include_patterns=True)
        return None

    def SwitchEnvironmentEx(self, name):
        if name in self.env_cache:
            env = self.env_cache[name]
        else:
            env = self.FindEnvironment(name)
            
        if not env:
            raise EnvironmentContextException('Can not switch environment. Wrong module name.\n')
        
        if self.env_cache != None:
            self.env_cache[name] = env

        return EnvironmentContextGuard(self, env)

    def SwitchEnvironment(self, name):
        env = self.FindEnvironment(name)
        if not env:
            raise EnvironmentContextException('Can not switch environment. Wrong module name.\n')
        
        return EnvironmentContextGuard(self, env)

class EnvironmentContextGuard:
    def __init__(self, cc, env):
        self.cc  = cc
        self.env = env

    def __enter__(self):
        self.env = self.cc.Setup(self.env)

    def __exit__(self, type, value, tb):
        self.cc.Setup(self.env)


class DataModel(object):
    def __init__(self):
        self.modules = {}
        self.callbacks = {}
        self.entities = {}
        self.deferred_events = {}
        self.properties = set()

        self.model_ready = True
        self.model = QStandardItemModel()
        self.tasks = {}
        self.modules_prepearing = set()

        wizard.Subscribe('W_ProjectModulesChanged', self)
        wizard.Subscribe('W_DocumentStateChanged', self)
        wizard.Subscribe('W_DocumentPropertiesChanged', self)
        wizard.Subscribe('W_TemplateRolesChanged', self)
        wizard.Subscribe('W_EntityCreated', self)
        wizard.Subscribe('W_EntityDestroyed', self)

        self.entities['part2'] = {}
        for v in kb.part2_itself.itervalues():
            name = v['name']
            self.entities['part2'][name] = compact_uri(name)
        #initialize model with p2
        InsertToSortedModel(self.entities, self.model, depth = 2)

    def GetTypeRoles(self, tp):
        if IsUri(tp):
            return self.GetTypeRolesByUri(tp)
        else:
            path = tp.split('.')
            if len(path) > 1:
                return self.GetTypeRolesByName(path[0], path[1])
        return None

    def GetNameAndIcon(self, value, tp = None):
        is_uri = IsUri(value)

        if is_uri:
            v = kb.uri2name(value)
            if v:
                is_uri = False
                value = v

        if tp:
            if tp.startswith('patterns.'):
                return value, 'iso_literal'

            v = kb.uri2name(tp)
            if v:
                tp = v
 
            roles = self.GetTypeRoles(tp)
            role = None
            if roles:
                if is_uri:
                    for v in roles.itervalues():
                        if value == v.get('uri'):
                            role = v
                            break
                else:
                    role = roles.get(value)

            if role:
                if tp.startswith('part2.'):
                    type_uri = role['type_uri']
                    if type_uri.startswith('xsd:'):
                        return role['name'], 'iso_syntax'
                    else:
                        return role['name'], kb.icons_map.get(kb.part2_itself[type_uri]['icon'], 'iso_unknown')
                else:
                    doc = self.GetEntityDoc(tp)
                    type_uri = roles[value]['type_uri']
                    restricted_by_value = roles[value].get('restricted_by_value', False)
                    type_label, type_icon = doc.infGetRestrictionNameAndIcon(type_uri, restricted_by_value)
                    return role['name'], type_icon
        else:
            uri = None
            if is_uri:
                uri = value
            else:
                path = value.split('.')
                if path[0] == 'part2':
                    if 'part2:'+path[1] in kb.part2_itself:
                        return path[1], kb.part2_itself['part2:'+path[1]]['icon']
                if len(path) > 1:
                    uri = self.GetEntityUri(path[0], path[1])
            if uri:
                doc = self.GetEntityDoc(uri)
                if doc:
                    name, tp_label, icon  = doc.infGetEntityVisual(uri)
                    if isinstance(name, list):
                        name = ', '.join(name)
                    return name, icon

        for k, v in appdata.project.annotations:
            if (is_uri and v == value) or (not is_uri and k == value):
                return k, 'iso_annotation'

        for k, v in appdata.project.roles:
            if (is_uri and v == value) or (not is_uri and k == value):
                return k, 'iso_role'

        return value, 'iso_unknown'


    def GetAvailableProps(self, tp = None):
        props = {}
        props.update({k: {'uri': v} for k, v in appdata.project.annotations})
        props.update({k: {'uri': v} for k, v in appdata.project.roles})

        if tp != None:
            found_roles = self.GetTypeRoles(tp)
            if found_roles:
                props.update(found_roles)

        return props

    def ResolveNameOrUri(self, value, tp = None, force_uri = False):
        is_uri = IsUri(value)

        if is_uri and force_uri:
            return value

        props = self.GetAvailableProps(tp)
        for propname, prop in props.iteritems():
            if is_uri and 'uri' in prop and prop['uri'] == value:
                return propname
            elif not is_uri and value == propname:
                return propname

        if is_uri:
            path = self.GetEntityModuleAndName(value)
        else:
            path = value.split('.')

        if path and len(path) > 1:
            if path[0] == 'part2':
                return value
            doc = self.modules.get(path[0])
            if doc:
                templates = doc.grGetTemplates()
                if path[1] in templates:
                    if force_uri:
                        return templates[path[1]]
                    else:
                        return '.'.join((path[0], path[1]))
                else:
                    m = self.entities.get(path[0])
                    if m:
                        curi = m.get(path[1])
                        if curi:
                            return expand_uri(curi)

        return value

    def GetTypeRolesByUri(self, uri):
        for doc in appdata.documents(GraphDocument):
            v = doc.grTemplateGetDesc(uri, True)
            if v:
                return v['roles']


    def GetTypeRolesByName(self, module, tp):
        if module == 'part2':
            v = kb.part2_itself.get('part2:' + tp)
            if v:
                return {r['name']: r for r in v['roles'].itervalues()}
        elif module == 'patterns':
            roles = set()
            for doc in appdata.documents(PatternsDocument):
                if tp in doc.patterns:
                    roles.update(set(doc.patterns[tp]['signature'].keys()))
                    for o in doc.patterns[tp]['options']:
                        for p in o['parts']:
                            roles |= set(p.keys())
            if roles:
                return {r: {} for r in roles}
        else:
            doc = self.modules.get(module)
            if doc:
                templates = doc.grGetTemplates()
                if tp in templates:
                    return self.GetTypeRolesByUri(templates[tp])
        return None

    def GetEntityUri(self, module, name):
        m = self.entities.get(module)
        if m:
            value = m.get(name)
            if value:
                return expand_uri(value)

    def GetEntityDoc(self, text):
        uri = None
        if IsUri(text):
            uri = text
        else:
            path = text.split('.')
            if len(path) > 1:
                uri = self.GetEntityUri(path[0], path[1])

        if uri:
            for doc in appdata.documents(GraphDocument):
                for t in doc.grTriplesForSubj(uri):
                    if t.p in (kb.rdf_type, kb.rdfs_subclassof):
                        return doc

    def GetEntityName(self, uri):
        v = kb.uri2name(uri)
        if v:
            return v
        for m, doc in self.modules.iteritems():
            for p in kb.all_labels:
                name = doc.grLiteral(uri, p)
                if name:
                    return '.'.join((m, name))
        return None


    def GetEntityModuleAndName(self, uri):
        for m, doc in self.modules.iteritems():
            for p in kb.all_labels:
                name = doc.grLiteral(uri, p)
                if name:
                    return m, name
        return None

    def GetModel(self):
        return self.model

    def EntityNameModified(self, module, old_names, new_names):
        if module in self.modules:
            for v in old_names:
                DeleteFromSortedModel({module: v}, self.model)
            for v in new_names:
                InsertToSortedModel({module: v}, self.model, depth = 2)

    def ClearModule(self, module):
        if module in self.modules:
            self.tasks[module].ClearTasks()
            del self.tasks[module]
            DeleteFromSortedModel(module, self.model)
            del self.entities[module]
            del self.modules[module]

    def UpdateProperties(self):
        self.properties = set()
        for doc in appdata.documents(GraphDocument):
            if doc.CanView():
                self.properties |= set(doc.annotations_by_name.keys())
                self.properties |= set(doc.roles_by_name.keys())

    def UpdateDocuments(self):
        for doc in appdata.documents(GraphDocument):
            if doc.module_name not in self.modules and doc.CanView() and doc.module_name:
                self.modules[doc.module_name] = doc
                self.tasks[doc.module_name] = TaskTarget()
                self.entities[doc.module_name] = doc.entities
                InsertToSortedModel({doc.module_name: doc.entities}, self.model, depth=2)

    def Cleanup(self):
        modules_found = set()
        for doc in appdata.documents(GraphDocument):
            if doc.module_name:
                modules_found.add(doc.module_name)
        for v in self.modules.viewkeys() - modules_found:
            self.ClearModule(v)

    def Update(self):
        self.UpdateDocuments()
        self.Cleanup()  

    def W_ProjectModulesChanged(self):
        self.Update()

    def W_DocumentPropertiesChanged(self, doc):
        self.UpdateProperties()

    def W_DocumentStateChanged(self, doc):
        self.Update()
        self.Cleanup()

appdata.datamodel = DataModel()

class EnvironmentManager:
    def __init__(self):
        self.graph_documents = set()
        self.need_rebuild = True
        self.environment = {}
        self.patterns_env = None
        self.latest_console_input = None
        self.patterns_cache = {}
        self.datamodel = {
                        'modules' : {},
                        'annotations' : {},
                        'roles': {}
                        }
        wizard.Subscribe('W_DocumentStateChanged', self)
        wizard.Subscribe('W_DocumentPropertiesChanged', self)

    def UpdateDocuments(self):
        self.graph_documents = set()
        for doc in appdata.documents(GraphDocument):
            if doc.CanView():
                self.graph_documents.add(doc)
        self.patterns_env = None
        self.need_rebuild = True

    def W_DocumentPropertiesChanged(self, dummy):
        self.UpdateDocuments()

    def W_DocumentStateChanged(self, dummy):
        self.UpdateDocuments()

    def FindViewType(self, document, uri):
        z = kb.split_uri(uri)
        if z:
            uri_head = z[0]
            uri_tail = z[1]
            if uri_head in kb.part2_all_ns:
                return type('', (Part2TypesView,), dict(bound_uri='part2:'+uri_tail))
            if uri_head==kb.ns_xsd:
                return type('', (XSDTypesView,), dict(bound_uri='xsd:'+uri_tail))

        if getattr(document, 'idi', None) != None:
            for t in document.grTriplesForSubj(uri):
                if t.p in (kb.rdf_type, kb.rdfs_subclassof):
                    return type('', (GraphView,), dict(document=document, bound_uri=uri))

        for doc in self.graph_documents:
            for t in doc.grTriplesForSubj(uri):
                if t.p in (kb.rdf_type, kb.rdfs_subclassof):
                    return type('', (GraphView,), dict(document=doc, bound_uri=uri))

        if getattr(document, 'idi', None) != None:
            return type('', (GraphView,), dict(document=document, bound_uri=uri))

    def RebuildEnvironment(self, builder = None):
        self.need_rebuild = False
        self.environment = {}
        self.patterns_env = None
        for doc in self.graph_documents:
            if doc.module_name:
                self.environment[doc.module_name] = GraphEnv(doc, builder)

    def GetPatternsEnv(self, document, patterns_filter = None, force = False):
        if not force and self.patterns_env and self.patterns_env.graph == document and self.patterns_env.patterns_filter == patterns_filter:
            return self.patterns_env
        env = self.GetWorkEnvironment(document)
        self.patterns_env = PatternsEnv(env, document, patterns_filter)
        return self.patterns_env

    def GetWorkEnvironment(self, document, include_builder=False, include_scanner=False, include_patterns=False):
        if not document:
            return dict(self.environment)

        builder = None
        if include_builder and document.doc_state != document.state_readonly:
            if getattr(document, 'idi', None) != None:
                builder = Builder(document)
            appdata.builder = builder

        if self.need_rebuild or builder != None:
            self.RebuildEnvironment(builder)

        env = dict(self.environment)

        if builder != None:
            env['builder'] = builder


        part2ns = getattr(document, 'chosen_part2', None)

        env['xsd'] = XSDEnv()

        if part2ns:
            env['part2'] = Part2Env(part2ns, builder)

        if getattr(document, 'idi', None) == None:
            return env

        if include_scanner:
            scanner = Scanner(document)
            env['scanner'] = scanner
            appdata.scanner = scanner
            env['find'] = scanner.find
            env['show'] = Command_show
            env['templates'] = Command_templates
            env['sparql'] = Command_sparql
            for k, v in ScannerPatterns.__dict__.iteritems():
                env[k] = v
            env['check'].find = scanner._find
            env['wrong'].verify = document.infVerifyEntity
            env['error'].verify = document.infVerifyEntity
            env['warning'].verify = document.infVerifyEntity

        if include_scanner and include_patterns:
            PatternsEnv(env, document)

        return env

class TemplateProxy:
    def __init__(self, template, env, builder, specializations = None):
        self.template = template
        self.env = env
        if specializations:
            self.uri = set(specializations + [self.template['uri']])
        else:
            self.uri = self.template['uri']
        self.builder = builder

    @property
    def any(self):
        return TemplateProxy(self.template, self.env, self.env.builder, self.env.doc.grTemplateGetSpecializations(self.template['name']))

    def __repr__(self):
        return 'TemplateProxy(template="{0}")'.format(self.template['name'])

    def __call__(self, *t, **d):
        if t:
            for v in self.template['roles'].itervalues():
                d[v['name']] = t[v['index']-1]

        return self.builder(type = self, **d)

    def extract(self, graph, uri):
        d = {}
        roles = self.template['roles']
        for t in graph.grTriplesForSubj(uri):
            p = t.p
            for k, v in roles.itervalues():
                if v['uri']==p:
                    d[k] = t.v
        return d

    def translate_name(self, propname):
        if propname:
            r = self.template['roles'].get(propname)
            if r:
                return r['uri']

    def get_prop(self, propname):
        if propname:
            return self.template['roles'].get(propname)
        return None

    def translate_props(self, props, for_build = False):
        objprops = {}
        dtprops = {}
        untranslated = {}
        for k, r in self.template['roles'].iteritems():
            v = props.pop(k, None)
            if for_build and r.get('restricted_by_value'):
                objprops[r['uri']] = r['type_uri']
            elif v:
                if r['is_literal']:
                    dtprops[r['uri']] = v
                else:
                    objprops[r['uri']] = v
        objprops[kb.ns_rdf+'type'] = self.uri
        return (objprops, dtprops, props)

class GraphSubEnv(object):
    def __init__(self, env):
        self.env = env

    @property
    def uri(self):
        return set(self.env.templates.values())

class GraphEnv(object):
    silent = False
    def __init__(self, doc, builder):
        self.doc = doc
        self.templates = doc.grGetTemplates()
        self.builder = builder
        self.any = GraphSubEnv(self)

    def __getitem__(self, k):
        return self.doc.grFindExactLabel(k)

    def update_templates(self):
        self.templates = self.doc.grGetTemplates()

    def get_annotations(self):
        return self.doc.annotations_by_name

    def get_roles(self):
        return self.doc.roles_by_name

    def get_prop(self, propname):
        if propname:
            if propname in self.doc.annotations_by_name:
                return self.doc.props_by_uri[self.doc.annotations_by_name[propname]]
            elif propname in self.doc.roles_by_name:
                return self.doc.props_by_uri[self.doc.roles_by_name[propname]]
        return None

    def all_subjects(self):
        return self.doc.grAllSubj()

    def subjects_count(self):
        return self.doc.grSubjCount()

    def find_uri(self, uri):
        return self.doc._grSearchUri(uri)

    def find_uri_wip_eq(self, uri):
        return self.doc._grSearchUriWIP(uri)

    def sparql_query(self, text):
        return self.doc._grSparqlQuery(text)

    def get_doc_instance(self):
        return self.doc

    def tplrole(self, uri, restricted_by_value = False):
        if getattr(uri, 'uri', None):
            uris = set_lift(uri.uri)
        else:
            uris = set_lift(uri)

        result = set()
        for v in self.templates.itervalues():
            tpl = self.doc.grTemplateGetDesc(v, True)
            for r in tpl['roles'].itervalues():
                if r['type_uri'] in uris and r['restricted_by_value'] == restricted_by_value:
                    result.add(v)

        return result

    def __repr__(self):
        return 'GraphEnv(doc={0})'.format(self.doc)

    def __getattr__(self, k):
        tpl = self.templates.get(k)
        if tpl:
            return TemplateProxy(self.doc.grTemplateGetDesc(tpl, True), self, self.builder)
        if not self.silent:
            raise AttributeError('{0} not found'.format(k))
        return None

    def dump_templates(self):
        l = []
        for v in self.templates.itervalues():
            tpl = self.doc.grTemplateGetDesc(v, True)
            name = self.doc.module_name+'.'+tpl['name']
            l.append('types.add(type='+name)
            for r in tpl['roles'].itervalues():
                i = r['index']
                rname = r['name']
                if r['is_literal']:
                    l.append(', {0}=d{1}'.format(rname, i))
                else:
                    l.append(', {0}=x{1}'.format(rname, i))
            l.append(')\n')
        log(''.join(l))

class XSDEnv(object):
    def __getattr__(self, k):
        name = kb.typelist_xsd.get(k)
        if not k:
            raise Exception('{0} not found in XML Schema'.format(k))
        return '{0}{1}'.format(kb.ns_xsd, name)

class Part2Env(object):
    def __init__(self, part2ns, builder):
        self.part2ns = part2ns
        self.builder = builder

    @property
    def any(self):
        types = set([self.part2ns + ti['name'] for ti in kb.part2_itself.itervalues()])
        return Part2Proxy(self.part2ns, types, self.builder)

    def __repr__(self):
        return 'Part2Env(part2ns={0})'.format(self.part2ns)

    def __getattr__(self, k):
        if kb.part2_itself.get('part2:'+k) == None:
            raise Exception('{0} not found in part 2'.format(k))
        return Part2Proxy(self.part2ns, self.part2ns+k, self.builder)

    def dump(self):
        l = []
        for k, v in kb.part2_itself.iteritems():
            name = 'part2.'+v['name']
            l.append('types.add(type='+name)
            i = 1
            for r in v['roles'].itervalues():
                rname = r['name']
                if r['is_literal']:
                    l.append(', {0}=d{1}'.format(rname, i))
                else:
                    l.append(', {0}=x{1}'.format(rname, i))
                i += 1
            l.append(')\n')
        log(''.join(l))


class Part2Proxy:
    def __init__(self, part2ns, uri, builder):
        self.part2ns = part2ns
        self.uri = uri
        self.builder = builder

    @property
    def any(self):
        if isinstance(self.uri, basestring):
            types = set()
            def f(ti):
                types.add(self.part2ns+ti['name'])
                for i in ti['subtypes']:
                    f(kb.part2_itself[i])
            f(kb.part2_itself['part2:'+kb.split_uri(self.uri)[1]])
            return Part2Proxy(self.part2ns, types, self.builder)
        return None

    def __repr__(self):
        return 'Part2Proxy(part2ns={0}, uri={1})'.format(self.part2ns, self.uri)

    def __call__(self, **d):
        return self.builder(type = self, **d)

    def extract(self, graph, uri):
        d = {}
        for t in graph.grTriplesForSubj(uri):
            p = t.p
            if p.startswith(self.part2ns):
                d[p.split('#')[1]] = t.v
        return d

    def translate_name(self, propname):
        if propname in kb.part2_object_properties or propname in kb.part2_datatype_properties:
            return self.part2ns+propname

    def get_prop(self, propname):
        if propname:
            if propname in kb.part2_datatype_properties:
                return {'uri': self.part2ns+propname, 'is_literal': True}
            elif propname in kb.part2_object_properties:
                return {'uri': self.part2ns+propname, 'is_literal': False}
        return None

    def translate_props(self, props, for_build = False):
        objprops = {}
        dtprops = {}
        untranslated = {}
        for k, v in props.iteritems():
            if k in kb.part2_object_properties:
                objprops[self.part2ns+k] = v
            elif k in kb.part2_datatype_properties:
                dtprops[self.part2ns+k] = v
            else:
                untranslated[k] = v
        objprops[kb.ns_rdf+'type'] = self.uri
        return (objprops, dtprops, untranslated)


appdata.environment_manager = EnvironmentManager()
