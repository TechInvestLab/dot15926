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
from iso15926.io.rdf_base import expand_uri
import copy

class ScannerException(Exception):
    pass

class LiteralValue(str):
    has_literal = True

class marker(object):
    is_marker = True
    def __init__(self):
        self.marker_class = type(self)

    def __eq__(self, other):
        return self.apply(other)

    @classmethod
    def apply(cls, other):
        if hasattr(other, '__dict__'):
            other = copy.copy(other)
            other.marker_class = cls
            return other
        else:
            return type('', (type(other),), dict(marker_class=cls))(other)

    @classmethod
    def remove(cls, other):
        if getattr(other, 'marker_class', None) == cls:
            other = copy.copy(other)
            other.marker_class = None
        return other

    @classmethod
    def get(cls, props):
        for k, v in props.iteritems():
            if getattr(v, 'marker_class', None) == cls:
                return k
        return None

class out_marker(marker):
    pass

class groupby_marker(marker):
    pass

class condition(object):
    is_stopper = False
    def __neg__(self):
        return condition_not(self)
    def __and__(self, other):
        return condition_and(self, other)
    def __or__(self, other):
        return condition_or(self, other)

class condition_not(condition):
    def __init__(self, cond):
        self.cond = cond
    def match(self, value):
        return not self.cond.match(value)

class condition_and(condition):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def match(self, value):
        return self.lhs.match(value) and self.rhs.match(value)

class condition_or(condition):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def match(self, value):
        return self.lhs.match(value) or self.rhs.match(value)

class any_marker(condition):
    def __init__(self):
        pass
    def match(self, value):
        return True

class void_marker(condition):
    is_stopper = True
    def __init__(self):
        pass
    def match(self, value):
        return False

class wrong_marker(condition):
    verify = None
    def __init__(self):
        pass
    def match(self, value):
        return bool(self.verify(value))

class error_marker(condition):
    verify = None
    def __init__(self):
        pass
    def match(self, value):
        res = self.verify(value)
        if res:
            for level, desc in res.itervalues():
                if level == 2:
                    return True
        return False

class warning_marker(condition):
    verify = None
    def __init__(self):
        pass
    def match(self, value):
        res = self.verify(value)
        if res:
            for level, desc in res.itervalues():
                if level == 1:
                    return True
        return False

class ScannerPatterns:
    any = any_marker()
    exists = any_marker()
    void = void_marker()
    out = out_marker()
    groupby = groupby_marker()
    wrong = wrong_marker()
    error = error_marker()
    warning =  warning_marker()

    class check(condition):
        find = None
        def __init__(self, **d):
            
            for i, v in d.iteritems():
                if getattr(v, 'marker_class', None):
                    raise ScannerException('Modifiers are not allowed in ''check'' function.')

            self.constraints = d

        def match(self, value):
            return self.find(set([value]), **self.constraints)

    class exact(condition):
        def __init__(self, value):
            self.value = value
        def match(self, value):
            return self.value==self.value.__class__(value)

    class oneof(condition):
        def __init__(self, values):
            self.values = values
        def match(self, value):
            return value in self.values

    class contains(condition):
        def __init__(self, substr):
            self.substr = substr
        def match(self, value):
            return self.substr in value

    class icontains(condition):
        def __init__(self, substr):
            self.substr = substr.decode('utf-8').lower()
        def match(self, value):
            return self.substr in value.decode('utf-8').lower()

    class beginswith(condition):
        def __init__(self, substr):
            self.substr = substr
        def match(self, value):
            return value.startswith(self.substr)

    class ibeginswith(condition):
        def __init__(self, substr):
            self.substr = substr.decode('utf-8').lower()
        def match(self, value):
            return value.decode('utf-8').lower().startswith(self.substr)

    class endswith(condition):
        def __init__(self, substr):
            self.substr = substr
        def match(self, value):
            return value.endswith(self.substr)

    class iendswith(condition):
        def __init__(self, substr):
            self.substr = substr.decode('utf-8').lower()
        def match(self, value):
            return value.decode('utf-8').lower().endswith(self.substr)

    class lt(condition):
        def __init__(self, ordvalue):
            self.ordvalue = ordvalue
        def match(self, value):
            return self.ordvalue.__class__(value) < self.ordvalue

    class le(condition):
        def __init__(self, ordvalue):
            self.ordvalue = ordvalue
        def match(self, value):
            return self.ordvalue.__class__(value) <= self.ordvalue

    class gt(condition):
        def __init__(self, ordvalue):
            self.ordvalue = ordvalue
        def match(self, value):
            return self.ordvalue.__class__(value) > self.ordvalue

    class ge(condition):
        def __init__(self, ordvalue):
            self.ordvalue = ordvalue
        def match(self, value):
            return self.ordvalue.__class__(value) >= self.ordvalue

    class between(condition):
        def __init__(self, lower, upper):
            self.lower = lower
            self.upper = upper
        def match(self, value):
            v = self.lower.__class__(value)
            return self.lower <= v and self.upper >= i


def filter_items(graph, cond, items = None):
    if isinstance(cond, basestring):
        if graph.grTriplesForSubj(cond):
            found = set([cond])
            return found & items if items else found
        else:
            return set()
    if isinstance(cond, set):
        found = set([i for i in cond if graph.grTriplesForSubj(i)])
        return found & items if items else found

    cond = condition_lift(cond)
    if not cond:
        return items

    found = set()
    if items:        
        for uri in items:
            if cond.match(uri) and graph.grTriplesForSubj(uri):
                found.add(uri)
    else:
        for curi, s in graph.ks.iteritems():
            if s:
                uri = expand_uri(curi)
                if cond.match(uri):
                    found.add(uri)

    return found

def set_lift(s):
    if isinstance(s, basestring):
        return set([s])
    elif isinstance(s, list):
        return set(s)
    return s

def condition_lift(s):
    if s is None:
        return None
    elif isinstance(s, marker):
        return ScannerPatterns.exists
    elif getattr(s, 'uri', None):
        if isinstance(s.uri, basestring):
            return ScannerPatterns.exact(s.uri)
        elif isinstance(s.uri, set):
            return ScannerPatterns.oneof(s.uri)
        else:
            return None
    elif isinstance(s, condition):
        return s
    elif isinstance(s, basestring):
        return ScannerPatterns.exact(s)
    elif isinstance(s, set):
        return ScannerPatterns.oneof(s)
    return None

def scan_filter(graph, filterfunc, items=None):
    results = set()
    if items is None:
        for (s, ks) in graph.ks.iteritems():
            if filterfunc(ks):
                results.add(graph.grExpand(s))
    else:
        for i in items:
            if filterfunc(graph.grTriplesForSubj(i)):
                results.add(i)
    return results

def prop_match(prop, cond):
    cond = condition_lift(cond)
    if prop == 'object':
        def f(triples):
            for t in triples:
                if t.has_object and cond.match(t.o):
                    return True
            return False
        return f
    if prop == 'literal':
        def f(triples):
            for t in triples:
                if t.has_literal and cond.match(t.l):
                    return True
            return False
        return f
    if prop == 'name':
        def f(triples):
            for value in kb.all_labels:
                for t in triples:
                    if t.has_literal and t.p == value:
                        if cond.match(t.l):
                            return True
                        return False
            return False
        return f
    if cond and cond.is_stopper:
        def f_void(triples):
            for t in triples:
                if t.p==prop:
                    return False
            return True
        return f_void
    def f(triples):
        for t in triples:
            if t.p==prop and cond.match(t.v):
                return True
        return False
    return f

def props_match(propcond_dict):

    key_object = condition_lift(propcond_dict.pop('object', None))
    key_literal = condition_lift(propcond_dict.pop('literal', None))
    key_name = condition_lift(propcond_dict.pop('name', None))

    propcond_dict = dict([(k, condition_lift(v)) for (k, v) in propcond_dict.iteritems() if condition_lift(v)])
    ok_len = len([q for q in propcond_dict if not propcond_dict[q].is_stopper])

    #print propcond_dict
    def f(triples):
        ok = set()
        object_matched  = not key_object
        literal_matched = not key_literal
        
        def name_scan(triples):
            if not key_name:
                return True
            for value in kb.all_labels:
                for t in triples:
                    if t.has_literal and t.p == value:
                        if key_name.match(t.l):
                            return True
                        return False

        name_matched = name_scan(triples)

        for t in triples:
            #check universal keys
            if key_object and t.has_object and key_object.match(t.o):
                object_matched = True
            if key_literal and t.has_literal and key_literal.match(t.l):
                literal_matched = True

            p = t.p
            m = propcond_dict.get(p)
            if m:
                if m.is_stopper:
                    return False
                elif m.match(t.v):
                    ok.add(p)
                # if not match - continue, maybe there is still something for our pattern
        if len(ok)==ok_len and object_matched and literal_matched:
            return True
        return False
    return f