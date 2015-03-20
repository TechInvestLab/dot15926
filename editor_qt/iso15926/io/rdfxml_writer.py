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




from xml.sax.saxutils import escape, unescape
import re
from iso15926.io.rdf_base import expand_uri
import iso15926.kb as kb
import gzip

re_qn = re.compile(r'qn(\d+)')

def split_uri(uri):
    p = uri.rfind('#')
    if p==-1:
        p = uri.rfind('/')
    if p==-1:
        return ('', uri)
    return (uri[:p+1], uri[p+1:])

class XmlWriter:

    def x(self, descr, *t):
        if t:
            descr = descr.format(*t)
        return self.r('<').r(descr).r(' />\n')

    def o(self, descr, *t):
        if t:
            descr = descr.format(*t)
        return self.r('<').r(descr).r('>\n')

    def c(self, tag):
        return self.r('</').r(tag).r('>\n')

    def t(self, text):
        return self.r(escape(text))

    def r(self, raw_text):
        self._out(raw_text)
        return self

    def f(self, raw_fmt, *t):
        self.r(raw_fmt.format(*t))
        return self

    def l(self, descr, *t):
        if len(t)>1:
            descr = descr.format(*t[:-1])
        literal = t[-1]
        return self.r('<').r(descr).r('>').r(escape(literal)).r('</').r(descr.split(' ', 1)[0]).r('>\n')

    def e(self, descr, *t):
        if t:
            descr = descr.format(*t)
        return XmlTagContext(self, descr)

class XmlTagContext:
    def __init__(self, writer, descr):
        self.writer = writer
        self.descr = descr

    def __enter__(self):
        self.writer.o(self.descr)

    def __exit__(self, exc_type, exc_value, traceback):
        self.writer.c(self.descr.split(' ', 1)[0])

class RdfXmlWriter(XmlWriter):

    def SaveGraphToFile(self, graph, fname, use_gzip = False):
        if use_gzip:
            with gzip.open(fname, 'wb') as f:
                self._out = f.write
                self.write_begin(graph.basens, graph.nslist, graph.grGetUsedNamespaces())
                self.write_graph(graph)
                self.write_end()
        else:
            with open(fname, 'wb') as f:
                self._out = f.write
                self.write_begin(graph.basens, graph.nslist, graph.grGetUsedNamespaces())
                self.write_graph(graph)
                self.write_end()
        self._out = None
        public.collect_garbage()

    def write_begin(self, basens=None, nslist={}, nsset=set()):
        self.basens = basens

        self.nslist = dict(nslist)
        self.nsset = set(nsset)

        names = set()
        uris = set()

        if self.basens:
            self.nslist['basens'] = self.basens

        for name, uri in self.nslist.iteritems():
            names.add(name)
            uris.add(uri)

        unkns = []
        for name in names:
            if re_qn.match(name):
                unkns.append(int(name[2:]))
        if unkns:
            unk = max(unkns)+1
        else:
            unk = 1

        for uri in self.nsset:
            if uri not in uris and uri != '' and uri != '_#':
                found = False
                for k, v in kb.all_known_namespaces:
                    if v == uri and k not in names:
                        self.nslist[k] = uri
                        found = True
                if not found:
                    self.nslist['qn{0}'.format(unk)] = uri
                    unk += 1

        self.ns_compact_name = {}
        for name, uri in self.nslist.iteritems():
            self.ns_compact_name[uri] = name

        self.r('<?xml version="1.0"?>\n\n')
        self.r('<!DOCTYPE rdf:RDF [\n')
        for n, uri in self.nslist.iteritems():
            self.f('  <!ENTITY {0} "{1}" >\n', n, uri)
        self.r(']>\n\n')
        self.r('<rdf:RDF \n')
        if self.basens:
            self.f('  xmlns="{0}"\n', self.basens)
            if self.basens[-1] == '#':
                self.f('  xml:base="{0}"\n', self.basens[:-1])
        for n, uri in self.nslist.iteritems():
            self.f('  xmlns:{0}="{1}"\n', n, uri)
        self.r('>\n')

    def write_end(self):
        self.r('</rdf:RDF>\n')

    def to_tag(self, uri):
        ns, name = split_uri(uri)
        if self.basens==ns:
            return name
        return ':'.join((self.ns_compact_name[ns], name))

    def to_ref(self, uri):
        ns, name = split_uri(uri)
        if self.basens[-1] == '#' and self.basens==ns:
            return '#'+name
        ns = self.ns_compact_name.get(ns, None)
        if ns is None:
            return uri
        return '&{0};{1}'.format(ns, name)

    def entity(self, ent, type):
        return self.x('{0} rdf:about="{1}"', type, self.to_ref(ent))

    def in_entity(self, ent=None, type=None):
        if type is None:
            type = 'rdf:Description'
        else:
            type = self.to_tag(type)
        if ent is None:
            return self.e(type)
        else:
            return self.e('{0} rdf:about="{1}"', type, self.to_ref(ent))

    def in_prop(self, property):
        return self.e(self.to_tag(property))

    def resource(self, property, value):
        return self.x('{0} rdf:resource="{1}"', self.to_tag(property), self.to_ref(value))

    def nontyped(self, property, value):
        return self.l('{0}', self.to_tag(property), value)

    def langtyped(self, property, value, lang):
        return self.l('{0} xml:lang="{1}"', self.to_tag(property), lang, value)

    def datatyped(self, property, value, datatype):
        return self.l('{0} rdf:datatype="{1}"', self.to_tag(property), self.to_ref(datatype), value)

    def write_entity(self, g, ent, triples):
        if not triples:
            return
        typ = g.grObjects(ent, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type')
        if len(typ)==1:
            if ent.startswith('_#'):
                e = self.in_entity(None, typ[0])
            else:
                e = self.in_entity(ent, typ[0])
            typ = True
        else:
            if ent.startswith('_#'):
                e = self.in_entity(None)
            else:
                e = self.in_entity(ent)
            typ = False
        with e:
            for t in triples:
                p = t.p
                if t.has_literal:
                    if t.has_lang:
                        self.langtyped(p, t.l, t.lang)
                    elif t.has_datatype:
                        self.datatyped(p, t.l, t.datatype)
                    else:
                        self.nontyped(p, t.l)
                else:
                    if typ and p=='http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                        continue
                    o = t.o
                    if g.grIs_rdflist(o):
                        with self.e('{0} rdf:parseType="Collection"', self.to_tag(p)):
                            for a in g.grGet_rdflist(o):
                                if a.startswith('_#'):
                                    self.write_entity(g, a, g.grTriplesForSubj(a))
                                else:
                                    self.x('rdf:Description rdf:about="{0}"', self.to_ref(a))
                    elif g.grIs_owllist(o):
                        with self.e(self.to_tag(p)):
                            lst = g.grGet_owllist(o)
                            for a in lst:
                                if a.startswith('_#'):
                                    self.r('<owllist:OWLList><owllist:hasContents>')
                                    self.write_entity(g, a, g.grTriplesForSubj(a))
                                    self.r('</owllist:hasContents><owllist:hasNext>')
                                else:
                                    self.f('<owllist:OWLList><owllist:hasContents rdf:resource="{0}" /><owllist:hasNext>', self.to_ref(a))
                            self.r('<owllist:OWLList />')
                            for a in lst:
                                self.r('</owllist:hasNext></owllist:OWLList>')
                            self.r('\n')
                    elif o.startswith('_#'):
                        with self.e(self.to_tag(p)):
                            self.write_entity(g, o, g.grTriplesForSubj(o))
                    else:
                        self.resource(p, o)

    def write_graph(self, g):
        total = len(g.ks)
        count = 0
        for curi, triples in g.ks.iteritems():
            uri = expand_uri(curi)
            if uri.startswith('_#') and g.ko.get(curi) is not None:
                continue
            self.write_entity(g, uri, triples)
            count += 1
            if count % 1000 == 0:
                st = getattr(g, 'AsyncChangeState', None)
                if st:
                    # graph is Document
                    g.AsyncChangeState(g.state_saving, 100*count/total)
            

