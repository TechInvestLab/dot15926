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


from iso15926.tools.scantools import *
from iso15926 import kb
import os
from collections import defaultdict
import itertools
from iso15926.io.rdf_base import ObjectTriple, LiteralTriple
from framework.util import fileline, IsUri
import rfc3987
import inspect
from iso15926.patterns.patterns_document import PatternsDocument
#from framework.util import timeit_context

class PatternPartException(Exception):
    debug = False
    def __init__(self, pattern, option, part_idx, error):
        self.pattern = pattern
        self.option = option
        self.part_idx = part_idx
        self.error = error
        if self.debug:
            print str(self)

    def __str__(self):
        return 'Pattern {0}, option {1}, part {2}. Error: {3}'.format(self.pattern.name, self.option.name, self.part_idx, self.error)

class PatternRequirementException(Exception):
    def __init__(self, pattern):
        Exception.__init__(self, 'Pattern %s not found\n'%pattern)
        self.pattern = pattern

class PatternDict(dict):
    def __init__(self, pattern, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.pattern = pattern
        self.reasons = []

    def __ior__(self, other):
        if other:
            sourcecount = len(other.itervalues().next()) 
            destcount   = self.ResultsCount()
            for k, v in self.iteritems():
                if k in other:
                    self[k] += other[k]
                else:
                    self[k] += [None] * sourcecount

            for k in (other.viewkeys() - self.viewkeys()):
                self[k] = [None] * destcount + other[k]

            self.reasons += other.reasons 

        return self

    def __eq__(self, other):
        if isinstance(other, PatternDict):
            return self.MakeSet() == other.MakeSet()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        if isinstance(other, PatternDict):
            return self.MakeSet() != other.MakeSet()
        return dict.__eq__(self, other)

    def RemoveSkolems(self):
        for k in self.viewkeys() - self.pattern.roles.viewkeys():
            del self[k]

    def AppendResult(self, roles, reasons):
        for k, v in roles.iteritems():
            self.setdefault(k, []).append(v)
        self.reasons.append(reasons)

    def AppendFromOther(self, other, idx):
        for k, v in other.iteritems():
            self.setdefault(k, []).append(v[idx])
        self.reasons.append(other.reasons[idx])

    def MakeSet(self):
        return set([(values, self.GetReasons(idx)) for idx, values in self.IterResults()])

    def FromSet(self, data):
        self.clear()
        self.reasons = []
        for item in data:
            for v in item[0]:
                self.setdefault(v[0], []).append(v[1])
            self.reasons.append(item[1])

    def RemoveDuplicates(self):
        new_items   = {}
        new_reasons = []
        cache       = set()
        for idx in xrange(self.ResultsCount()):
            values = frozenset([(k, v[idx]) for k, v in self.iteritems()])
            reasons = self.GetReasons(idx)
            data = (values, reasons)
            if data in cache:
                continue
            cache.add(data)
            for v in values:
                new_items.setdefault(v[0], []).append(v[1])
            new_reasons.append(reasons)

        self.update(new_items)
        self.reasons = new_reasons

    def GetPattern(self):
        return self.pattern

    def GetPatternName(self):
        return self.pattern.name

    def GetPatternSignature(self):
        return self.pattern.roles

    def ResultsCount(self):
        return len(self.itervalues().next()) if self else 0

    def ContainsReasons(self):
        return self.reasons

    def GetReasons(self, idx):
        if idx < len(self.reasons):
            return self.reasons[idx]
        return frozenset()

    def GetResult(self, idx):
        if idx < self.ResultsCount():
            return frozenset([(k, v[idx]) for k, v in self.iteritems() if v[idx] != None])
        return frozenset()

    def IterResults(self):
        for idx in xrange(self.ResultsCount()):
            res = frozenset([(k, v[idx]) for k, v in self.iteritems() if v[idx] != None])
            yield (idx, res)

    def IterResults2(self):
        for idx in xrange(self.ResultsCount()):
            yield dict(((k, v[idx]) for k, v in self.iteritems() if v[idx] != None))

class PatternsEnv(object):
    def __init__(self, work_env, graph, patterns_filter = None):
        self.patterns             = {}
        self.info                 = {}
        self.graph                = graph
        self.work_env             = work_env
        self.work_env['patterns'] = self
        self.patterns_filter      = patterns_filter
        self.load_patterns()

    # def __call__(self, txt):
    #     if txt:
    #         lst = txt.split('.')
    #         pattern = self.get_pattern(lst[0])
    #         if len(lst) > 1:
    #             return pattern.options.get(lst[1])
    #         return pattern

    def load_patterns(self):
        for doc in appdata.documents(PatternsDocument):
            for name, pattern in doc.patterns.iteritems():
                if self.patterns_filter == None or (doc.name in self.patterns_filter and (not self.patterns_filter[doc.name] or name in self.patterns_filter[doc.name])):
                    self.info.setdefault(name, []).append(pattern)
    
        while self.info:
            pattern = self.info.iterkeys().next()
            self.get_pattern(pattern)

    def get_pattern(self, pattern):
        proxy = self.patterns.get(pattern)
        if self.info:
            data = self.info.pop(pattern, None)
            if data:
                if proxy == None:
                    proxy = PatternProxy(pattern, self)
                    for i in data:
                        proxy.Update(i)
                    if proxy:
                        self.patterns[pattern] = proxy
                    else:
                        proxy = None
                else:
                    for i in data:
                        proxy.Update(i)
        return proxy

    def __repr__(self):
        return 'Available patterns:\n{0}'.format('\n'.join([k for k in self.patterns.keys()]))

    def __getattr__(self, k):
        return self.get_pattern(k)

    def get(self, uri, graph = None):
        uri_list = set_lift(uri)

        if not graph:
            graph = self.graph

        patterns = {}
        for k, v in self.patterns.iteritems():
            r = v.check_uri(graph, uri_list)
            if r:
                patterns[k] = r
        return patterns

    def get_signature(self, pattern):
        return self.patterns[pattern].GetRoles()

    def check_classification(self, graph, uri, classifiers):
        results = set()
        classification = self.patterns.get('Classification')
        if classification:
            results = classification.find(graph, dict(classified = uri, classifier = ScannerPatterns.out))
            if classifiers & results:
                return True

            specialization = self.patterns.get('Specialization')
            if specialization:
                current = set(results)
                while current:
                    found = specialization.find(graph, dict(subclass = current, superclass = ScannerPatterns.out))
                    if classifiers & found:
                        return True
                    current = found - results
                    results |= current
        return False

    def get_subclasses(self, graph, uri):
        results = set()
        specialization = self.patterns.get('Specialization')
        if specialization:
            current = set(uri)
            while current:
                found = specialization.find(graph, dict(superclass = current, subclass = ScannerPatterns.out))
                current = found - results
                results |= current
        return results

    def get_classified(self, graph, uri):
        results = set()
        classification = self.patterns.get('Classification')
        if classification:
            specialization = self.patterns.get('Specialization')
            items = set((uri,))
            if specialization:
                current = set(items)
                while current:
                    found = specialization.find(graph, dict(superclass = current, subclass = ScannerPatterns.out))
                    current = found - items
                    items |= current
            results |= classification.find(graph, dict(classifier = items, classified = ScannerPatterns.out))
        return results

class PatternProxy(object):
    def __init__(self, name, env):
        self.unnamedcount   = 0
        self.name           = name
        self.roles          = {}
        self.options        = {}
        self.env            = env

    def __nonzero__(self):
        return True if self.options else False

    def get_option(self, name):
        return self.options.get(name)

    def Update(self, patterninfo):
        self.roles.update(patterninfo.get('signature', {}))
        for v in patterninfo.get('options', []):
            try:
                option = PatternOption(self, v)
            except PatternPartException as e:
                continue
            self.options[option.name] = option

    def GetRoles(self):
        return self.roles

    def check_uri(self, graph, uri_list):
        res = PatternDict(self)
        for v in self.options.itervalues():
            res |= v.check_uri(graph, uri_list)
        res.RemoveDuplicates()
        return res
         
    def find(self, graph, props):
        to_out = out_marker.get(props)

        if to_out:
            res = set()
        else:
            res = PatternDict(self)

        for v in self.options.itervalues():
            res |= v.find(graph, props.copy())

        return res

    def __repr__(self):
        return 'Pattern {0}\nRoles:\n{1}\nOptions:\n{2}'.format(self.name, '\n'.join([k for k in self.roles.iterkeys()]), '\n'.join([k for k in self.options.iterkeys()]))

    def __getattr__(self, k):
        return self.options[k]

def parts_compare(x, y):
    if x.use_classification != y.use_classification:
        if x.use_classification:
            return 1
        else:
            return -1

    if x.types and not y.types:
        return -1
    elif not x.types and y.types:
        return 1

    return len(y.roles) - len(x.roles)

def roles_permutation(roles):
    result = []
    for v in itertools.product(*[ [ (k, item) for item in v] for k, v in roles.iteritems() ] ):
        result.append(dict(v))
    return result

class PatternPart(object):
    def __init__(self, part, index, option, pattern):
        if not part:
            raise PatternPartException(pattern, option, index, 'empty part')

        part          = copy.copy(part)
        tp            = part.pop('type', None)
        self.uri      = part.pop('uri', None)
        self.roles    = part
        self.props    = {}
        self.ownrole  = part.pop('self', None)
        self.option   = option
        self.pattern  = pattern
        self.index    = index
        self.base     = None
        self.typename = None
        self.types    = set()
        self.name     = 'part_%i'%self.index
        self.value    = part.pop('value', None)
        self.function = part.pop('lambda', None)
        self.use_classification = False

        if self.uri:
            self.uri = set_lift(self.uri)

        if tp:
            if isinstance(tp, basestring):
                if IsUri(tp):
                    self.use_classification = True
                    self.types = set_lift(tp)
                else:
                    try:
                        tp = eval(tp, {}, self.pattern.env.work_env)
                    except:
                        raise PatternPartException(pattern, option, index, 'type %s not evaluated'%tp)
                    if isinstance(tp, PatternProxy) or isinstance(tp, PatternOption):
                        self.base = tp
                    else:
                        if getattr(tp, 'uri', None) != None:
                            self.types = set_lift(tp.uri)
                        if getattr(tp, 'template', None) != None:
                            self.typename = tp.template['name']
            else:
                self.use_classification = True
                self.types = set_lift(tp)

        for k, v in self.roles.iteritems():
            if self.base:
                if v not in self.base.GetRoles():
                    raise PatternPartException(pattern, option, index, 'role %s not found in base pattern'%v)
                self.props[v] = k
            elif isinstance(v, basestring):
                prop = None

                if tp and hasattr(tp, 'get_prop'):
                    prop = tp.get_prop(v)

                if not prop and self.pattern.env.graph:
                    doc = self.pattern.env.graph
                    prop_uri = doc.roles_by_name.get(v)
                    if not prop_uri:
                        prop_uri = doc.annotations_by_name.get(v)
                    if not prop_uri:
                        prop_uri = v
                    prop = doc.props_by_uri.get(prop_uri)

                if prop:
                    self.props[prop['uri']] = k
                    self.roles[k] = prop
                elif IsUri(v):
                    self.props[v] = k
                    self.roles[k] = {'uri': v, 'is_literal': False, 'is_optional': True}
                else:
                    raise PatternPartException(pattern, option, index, 'property %s not found in environment'%v)
            else:
                raise PatternPartException(pattern, option, index, 'property %s not evaluated'%v)

        if self.ownrole:
            self.roles[self.ownrole] = 'self'

    def is_literal(self, role):
        r = self.roles.get(role)
        if r:
            if self.base:
                if hasattr(self.base, 'is_literal'):
                    return self.base.is_literal(r)
            elif r != 'self':
                return r['is_literal']
            else:
                return False
        return None

    def get_build_target(self):
        return self.ownrole

    def build(self, doc, roles, items = None, current = None, done = None):
        if self.base:
            if hasattr(self.base, 'build'):
                roles = self.base.build(doc, self.prepare_base_props(roles), items, current, done)
                return self.translate_base(roles, True)
            else:
                return

        if self.value:
            return {self.ownrole if self.ownrole else name: self.value}

        if self.function:
            value = eval(self.function, dict(roles))
            return {self.ownrole if self.ownrole else name: value}

        itemid = None

        if self.name in roles and not self.ownrole:
            itemid = roles[self.name]
        else:
            if self.uri:
                if len(self.uri) == 1:
                    itemid = iter(self.uri).next()
                else:
                    return
            elif self.ownrole:
                if self.ownrole in roles:
                    itemid = roles[self.ownrole]
                    if not itemid:
                        return
                        
            if not itemid:
                found = self.scan_by_roles(doc, roles)
                if len(found) == 1:
                    itemid = iter(found).next()
                    # if items != None:
                    #     items.add(itemid)
                    # return {self.ownrole if self.ownrole else name: itemid}
            elif itemid != 'new':
                if not IsUri(itemid):
                    itemid = doc.basens + itemid
            else:
                itemid = doc.infGenerateUri()

        for k, v in self.roles.iteritems():
            if v == 'self':
                continue
            value = roles.get(k)
            if not value and (not itemid or not v.get('is_optional')):
                return

        if not itemid:
            itemid = doc.infGenerateUri()

        result = {}
        result[self.ownrole if self.ownrole else self.name]  = itemid

        triples = doc.grTriplesForSubj(itemid)

        if self.types and len(self.types) == 1:
            if (itemid, kb.rdf_type) not in done:
                if (itemid, kb.rdf_type) not in current:
                    for t in triples:
                        if t.p == kb.rdf_type:
                            t.deletefrom(doc)
                current.add((itemid, kb.rdf_type))
                for v in self.types:
                    ObjectTriple.insert(doc, itemid, kb.rdf_type, v)

        for k, v in self.roles.iteritems():
            if v == 'self':
                continue
            value = roles.get(k)
            if not value:
                continue

            if (itemid, v['uri']) in done:
                continue

            if value == 'new':
                if not v['is_literal']:
                    value = doc.infGenerateUri()
                result[k] = value

            if (itemid, v['uri']) not in current:
                for t in triples:
                    if t.p == v['uri']:
                        t.deletefrom(doc)

            current.add((itemid, v['uri']))

            if v['is_literal']:
                LiteralTriple.insert(doc, itemid, v['uri'], value)
            else:
                ObjectTriple.insert(doc, itemid, v['uri'], value)

        doc.AsyncChangeState(doc.state_changed)
        if items != None:
            items.add(itemid)
        return result

    def prepare_props(self, props):
        result = {}
        for k, v in props.iteritems():
            if k in self.roles:
                prop = self.roles[k]
                if prop == 'self':
                    result[k] = v
                else:
                    result[prop['uri']] = v
        return result

    def prepare_base_props(self, props):
        result = {}
        prefix = self.name + '.'
        for k, v in props.iteritems():
            if k.startswith(prefix):
                base_role = k[len(prefix):]
                result[base_role] = out_marker.remove(v)
            else:
                base_role = self.roles.get(k)
                if base_role:
                    result[base_role] = out_marker.remove(v)
        return result

    def scan_by_roles(self, graph, roles):
        if self.base or (len(self.roles) == (1 if self.ownrole else 0)):
            return set()

        items = set()
        literal_roles = {}

        for k, v in self.roles.iteritems():

            if v == 'self':
                continue

            value = roles.get(k)
            if not value:
                return set()

            if v['is_literal']:
                found_items = set(graph.grSubjectsL(v['uri'], value))
            else:
                found_items = set(graph.grSubjects(v['uri'], value))

            items = found_items if not items else items & found_items

            if not items:
                return set()

        if self.types:
            if items:
                found_items = set()
                for uri in items:
                    for tp in self.types:
                        if graph.grHas(uri, kb.rdf_type, tp):
                           found_items.add(uri)
                           break
                    else:
                        if self.use_classification and self.pattern.env.check_classification(graph, uri, self.types):
                            found_items.add(uri)
                items = found_items
            else:
                for uri in self.types:
                    items |= set(graph.grSubjects(kb.rdf_type, uri))
                    if self.use_classification:
                        items |= self.pattern.env.get_classified(graph, uri)

        return items

    def translate_base(self, res, full = True):
        prefix = self.name + '.'
        for k, v in self.roles.iteritems():
            if k != v and v in res:
                res[k] = res[v]
                del res[v]
        for k in res.viewkeys() - self.roles.viewkeys():
            if full:
                new_name = prefix + k
                res[new_name] = res[k]
            del res[k]
        return res

    def scan_by_props(self, graph, props):
        if self.base:
            return self.translate_base(self.base.find(graph, self.prepare_base_props(props)))

        items = self.uri

        props = self.prepare_props(props)

        for (k, v) in props.copy().iteritems():
            if self.ownrole == k:
                continue
                
            if isinstance(v, basestring):
                if self.roles[self.props[k]]['is_literal']:
                    found_items = set(graph.grSubjectsL(k, v))
                else:
                    found_items = set(graph.grSubjects(k, v))
            elif isinstance(v, set):
                found_items = set()
                if self.roles[self.props[k]]['is_literal']:
                    for i in v:
                        found_items |= set(graph.grSubjectsL(k, i))
                else:
                    for i in v:
                        found_items |= set(graph.grSubjects(k, i))
            else:
                continue

            if not found_items:
                return set()

            items = found_items if not items else items & found_items
            del props[k]

        if self.ownrole in props:
            items = filter_items(graph, props[self.ownrole], items)
            del props[self.ownrole]

        if self.types:
            if items:
                found_items = set()
                for uri in items:
                    for tp in self.types:
                        if graph.grHas(uri, kb.rdf_type, tp):
                           found_items.add(uri)
                           break
                    else:
                        if self.use_classification and self.pattern.env.check_classification(graph, uri, self.types):
                            found_items.add(uri)
                items = found_items
            elif props:
                items = set()
                for uri in self.types:
                    items |= set(graph.grSubjects(kb.rdf_type, uri))
                    if self.use_classification:
                        items |= self.pattern.env.get_classified(graph, uri)

        if len(props)==1:
            filterfunc = prop_match(*props.items()[0])
            items = scan_filter(graph, filterfunc, items)
        else:
            filterfunc = props_match(props)
            items = scan_filter(graph, filterfunc, items)

        return self.scan_by_self(graph, items)

    def scan_graph_by_restrictions(self, graph):
        items = self.uri
        if self.types:
            res = set()
            for uri in self.types:
                res |= set(graph.grSubjects(kb.rdf_type, uri))
                if self.use_classification:
                    res |= self.pattern.env.get_classified(graph, uri)
            items = items & res if items else res
        return items

    def scan_graph(self, graph):
        if self.base:
            return self.translate_base(self.base.find(graph, {}))
        items = self.scan_graph_by_restrictions(graph)
        if items:
            return self.scan_by_self(graph, items)
        else:
            return self.scan_by_self(graph, set([expand_uri(curi) for curi in graph.ks.iterkeys()]))

    def scan_by_self(self, graph, items):
        found = PatternDict(self.pattern)
        if self.uri:
            items = items & self.uri

        for uri in items:
            foundroles = {}
            type_matched = not self.types

            if self.ownrole:
                reason = frozenset()
                foundroles[self.ownrole] = [uri]
            else:
                reason = frozenset([uri])

            for t in graph.grTriplesForSubj(uri):
                if not type_matched and (t.p == kb.rdf_type) and (t.v in self.types):
                    type_matched = True
                if t.p in self.props:
                    foundroles.setdefault(self.props[t.p], []).append(LiteralValue(t.l) if t.has_literal else t.o)

            if len(foundroles) == len(self.roles):
                if type_matched or (self.use_classification and self.pattern.env.check_classification(graph, uri, self.types)):
                    for res in roles_permutation(foundroles):
                        found.AppendResult(res, reason)

        return found

    def check_uri(self, graph, items):
        if self.base:
            return self.translate_base(self.base.check_uri(graph, items))

        found = PatternDict(self.pattern)

        if self.ownrole:
            found |= self.scan_by_self(graph, items)

        for uri in items:
            for tt in graph.grTriplesForObj(uri):
                if tt.p in self.props:
                    rolename = self.props[tt.p]
                    if not self.uri or tt.s in self.uri:
                        type_matched = not self.types

                        if self.ownrole:
                            foundroles = {self.ownrole: [tt.s], rolename: [uri]}
                            reason = frozenset()
                        else:
                            foundroles = {rolename: [uri]}
                            reason = frozenset([tt.s])

                        for t in graph.grTriplesForSubj(tt.s):
                            if not type_matched and (t.p == kb.rdf_type) and ((not self.types) or (t.v in self.types)):
                                type_matched = True
                            if t.p in self.props and self.props[t.p] != rolename:
                                foundroles.setdefault(self.props[t.p], []).append(LiteralValue(t.l) if t.has_literal else t.o)

                        if len(foundroles) == len(self.roles):
                            if type_matched or (self.use_classification and self.pattern.env.check_classification(graph, uri, self.types)):
                                for res in roles_permutation(foundroles):
                                    found.AppendResult(res, reason)  
        return found

    def scan_by_found(self, graph, found):
        for rolename, roleval in self.roles.iteritems():
            foundlist = found.get(rolename, None)
            if foundlist:
                break

        result = PatternDict(self.pattern)

        if self.base:
            for idx, uri in enumerate(foundlist):
                found_other = self.translate_base(self.base.find(graph, {roleval: uri}))
                for i, res in found_other.IterResults():
                    reason = found_other.GetReasons(i)
                    res = dict(res)
                    for k, v in found.iteritems():
                        res[k] = v[idx]
                    result.AppendResult(res, found.reasons[idx] | reason) 
            return result

        for idx, uri in enumerate(foundlist):
            if roleval == 'self':
                if self.uri and uri not in self.uri:
                    continue
                type_matched = not self.types
                foundroles = {}
                reason = frozenset()
                for t in graph.grTriplesForSubj(uri):
                    if not type_matched and (t.p == kb.rdf_type) and (t.v in self.types):
                        type_matched = True
                    if t.p in self.props:
                        foundroles.setdefault(self.props[t.p], []).append(LiteralValue(t.l) if t.has_literal else t.o)

                if len(foundroles) == len(self.roles)-1:
                    if type_matched or (self.use_classification and self.pattern.env.check_classification(graph, uri, self.types)):
                        for k, v in found.iteritems():
                            foundroles.setdefault(k, []).append(v[idx])
                        for res in roles_permutation(foundroles):
                            result.AppendResult(res, found.reasons[idx] | reason)  
            else:
                triples = graph.grTriplesForLit(uri) if roleval['is_literal'] else graph.grTriplesForObj(uri)
                for tt in triples:
                    if tt.p in self.props and self.props[tt.p] == rolename:
                        if not self.uri or tt.s in self.uri:
                            type_matched = not self.types
                            if self.ownrole:
                                foundroles = {self.ownrole: [tt.s]}
                                reason = frozenset()
                            else:
                                foundroles = {}
                                reason = frozenset([tt.s])

                            for t in graph.grTriplesForSubj(tt.s):
                                if not type_matched and (t.p == kb.rdf_type) and ((not self.types) or (t.v in self.types)):
                                    type_matched = True
                                if t.p in self.props and self.props[t.p] != rolename:
                                    foundroles.setdefault(self.props[t.p], []).append(LiteralValue(t.l) if t.has_literal else t.o)

                            if len(foundroles) == len(self.roles)-1:
                                if type_matched or (self.use_classification and self.pattern.env.check_classification(graph, uri, self.types)):
                                    for k, v in found.iteritems():
                                        foundroles.setdefault(k, []).append(v[idx])
                                    for res in roles_permutation(foundroles):
                                        result.AppendResult(res, found.reasons[idx] | reason)  

        return result

class PatternOption(object):
    def __init__(self, pattern, option):
        self.pattern        = pattern
        option              = copy.copy(option)
        self.name           = option.pop('name', None)
        if not self.name:
            self.name             = 'Unnamed_%i'%pattern.unnamedcount
            pattern.unnamedcount += 1
        self.expansionname  = option.pop('expansion', None)
        parts               = option.pop('parts', None)
        self.parts          = []

        if not parts:
            parts = [option]

        for i, v in enumerate(parts):
            part = PatternPart(v, i, self, pattern)
            if part.uri and len(part.roles) == (1 if part.ownrole else 0):
                 self.parts.insert(0, part)
            else:
                self.parts.append(part)

    def collect(self, doc, roles):
        collectors = set(public.all('collectors')) | set(public.all('collectors.'+self.pattern.name))
        items = set()
        if collectors:
            for collector in collectors:
                argspec = inspect.getargspec(collector)
                arguments = (roles, self.pattern.name, self.name)[:len(argspec.args)]
                for r in collector(*arguments):
                    self.build(doc, r, items)
        return items

    def GetRoles(self):
        return self.pattern.GetRoles()

    def build(self, doc, roles, items = None, current = None, done = None):

        done = set(done) if done else set()
        if current:
            done |= current
        current = set()

        for v in self.parts:
            res = v.build(doc, roles, items, current, done)
            if res:
                roles.update(res)
        return roles

    def get_build_targets(self):
        res = set()
        for v in self.parts:
            t = v.get_build_target()
            if t:
                res.add(t)
        return res

    def is_literal(self, role):
        for v in self.parts:
            res = v.is_literal(role)
            if res != None:
                return res
        return None

    def find_valid(self, doc, role):
        for v in self.parts:
            if v.ownrole and role == v.ownrole:
                res = v.scan_graph_by_restrictions(doc)
                if res:
                    return res
        return set()

    @property
    def expansion(self):
        return getattr(self.pattern, self.expansionname, None)

    def __repr__(self):
        if self.expansionname:
            return 'Pattern {0} option {1} expansion {2}'.format(self.pattern.name, self.name, self.expansionname)
        return 'Pattern {0} option {1}'.format(self.pattern.name, self.name)

    def check_uri(self, graph, uri_list):
        result = PatternDict(self.pattern)
        for v in self.parts:
            #with timeit_context('start ' + v.get_name()):
            found = v.check_uri(graph, uri_list)

            if found:
                parts = self.parts[:]
                parts.remove(v)

                while (parts and found):
                    last = None
                    for p in parts:
                        if found.viewkeys() & p.roles.viewkeys():
                            last = p
                            #with timeit_context('next ' + p.get_name()):
                            found = p.scan_by_found(graph, found)
                            parts.remove(p)
                            break
                    if not last:
                        raise Exception('Pattern definition error! Pattern name = {0}, option name = {1}.'.format(self.pattern.name, self.name))

                if found:
                    result |= found

        return result


    def find_internal(self, graph, props):
        to_out = out_marker.get(props)
        if to_out and isinstance(props[to_out], marker):
            del props[to_out]

        parts  = self.parts[:]
        found  = PatternDict(self.pattern)

        if props and props.viewkeys() & self.pattern.roles.viewkeys():
            for v in parts:
                if v.roles.viewkeys() & props.viewkeys():
                    found = v.scan_by_props(graph, props)
                    if found:
                       parts.remove(v)
                       break
        else:
            parts.sort(cmp = parts_compare)
            found = parts.pop(0).scan_graph(graph)

        while (parts and found):
            last = None
            for p in parts:
                if found.viewkeys() & p.roles.viewkeys():
                    last = p
                    found = p.scan_by_found(graph, found)
                    parts.remove(p)
                    break
            if not last:
                raise Exception('Pattern definition error! Pattern name = {0}, option name = {1}.'.format(self.pattern.name, self.name))

        if not found:
            if to_out:
                return set()
            return PatternDict(self.pattern)

        for role in self.pattern.roles:
            role_cond = condition_lift(props.pop(role, None))
            if role_cond:
                res = set()
                result = PatternDict(self.pattern)
                for idx in xrange(found.ResultsCount()):
                    if role_cond.match(found[role][idx]):
                        result.AppendFromOther(found, idx)
                found = result

        if 'object' in props or 'literal' in props or to_out == 'object' or to_out == 'literal':
            obj_cond = condition_lift(props.pop('object', None))
            lit_cond = condition_lift(props.pop('literal', None))
            out = set()
            to_out_obj = to_out == 'object'
            to_out_lit = to_out == 'literal'
            result = PatternDict(self.pattern)
            for idx in xrange(len(found.itervalues().next())):
                obj_found = not obj_cond
                lit_found = not lit_cond
                for k, v in found.iteritems():
                    val = v[idx]
                    if getattr(val, 'has_literal', None):
                        if lit_cond and lit_cond.match(val):
                            lit_found = True
                            if to_out_lit:
                                out.add(val)
                        elif to_out_lit and not lit_cond:
                            out.add(val)
                    else:
                        if obj_cond and obj_cond.match(val):
                            obj_found = True
                            if to_out_obj:
                                out.add(val)
                        elif to_out_obj and not obj_cond:
                            out.add(val)

                if to_out_obj or to_out_lit:
                    continue

                if obj_found and lit_found:
                    result.AppendFromOther(found, idx)

            if to_out_obj or to_out_lit:
                return out

            found = result

        if to_out:
            return set(found.get(to_out, set()))
        
        return found


    def find(self, graph, props):
        to_out = out_marker.get(props)
        res_types = set(('literal', 'object')) & props.viewkeys()
        roles = self.pattern.roles.viewkeys() & props.viewkeys()
        wrong_props = props.viewkeys() - res_types - roles

        if wrong_props:
            if to_out:
                return set()
            return PatternDict(self.pattern)

        if to_out and isinstance(props[to_out], out_marker):
            roles.discard(to_out)
            res_types.discard(to_out)

        if res_types and not roles:
            if to_out:
                found = set()
            else:
                found  = PatternDict(self.pattern)

            for rtype in ('object', 'literal'):
                if rtype in res_types:
                    for r in self.pattern.roles:
                        if self.is_literal(r) == (rtype == 'literal'):
                            new_props = {k: v for k, v in props.iteritems() if k != rtype}

                            if rtype == to_out:
                                new_props[rtype] = ScannerPatterns.out

                            if r == to_out:
                                new_props[r] = out_marker.apply(props[rtype])
                            else:
                                new_props[r] = props[rtype]

                            found |= self.find_internal(graph, new_props)
                    break

            return found

        return self.find_internal(graph, props)

class Dummy(object):
    def __getattr__(self, k):
        return Dummy()

class DummyVerify(Dummy):
    def __init__(self, k, v, o = 4):
        self.k = k
        self.i = '<%s, %i>\nNot found: %s'%(fileline(o)+(k,))
        self.v = v
        self.v.add(self.i)

    def __getattr__(self, k):
        self.v.discard(self.i)
        return DummyVerify('.'.join((self.k, k)), self.v, 3)

class EnvDict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory(key)
        return value
