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




import re
from iso15926.io.rdf_base import expand_uri, compact_uri
import iso15926.kb as kb
import gzip
from graphlib import bnode_prefix

re_qn = re.compile(r'qn(\d+)')

def escape(str):
    if "\n" in str:
        encoded = str.replace('\\', '\\\\')
        if '"""' in str:
            encoded = encoded.replace('"""', '\\"\\"\\"')
        if encoded[-1] == '"' and encoded[-2] != '\\':
            encoded = encoded[:-1] + '\\' + '"'

        return '"""%s"""' % encoded.replace('\r', '\\r')
    else:
        return '"%s"' % str.replace(
            '\n', '\\n').replace(
                '\\', '\\\\').replace(
                    '"', '\\"').replace(
                        '\r', '\\r')

def split_uri(uri):
    p = uri.rfind('#')
    if p==-1:
        p = uri.rfind('/')
    if p==-1:
        return ('', uri)
    return (uri[:p+1], uri[p+1:])

class TrigWriter(object):

    def SaveGraphToFile(self, graph, fname, ttl=False, use_gzip = False):
        self.ttl = ttl
        if use_gzip:
            with gzip.open(fname, 'wb') as f:
                self.write = f.write
                self.write_graph(graph)
        else:
            with open(fname, 'wb') as f:
                self.write = f.write
                self.write_graph(graph)

        self.write = None
        public.collect_garbage()

    def write_graph(self, graph):

        graphs = {}

        graphs[''] = graph
        graphs.update(graph.ng)

        bases = set()
        self.nslist = {}
        self.nsset = set()

        for k, v in graphs.iteritems():
            bases.add(v.basens)
            self.nslist.update(v.nslist)
            self.nsset |= v.grGetUsedNamespaces()

        self.basens = None
        bases = list(bases)
        if len(bases) == 1 and bases[0]:
            self.basens = bases.pop()
            self.nslist['basens'] = self.basens

        names = set()
        uris = set()

        uris.add(self.basens)
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
                        break
                if not found:
                    self.nslist['qn{0}'.format(unk)] = uri
                    unk += 1

        self.ns_compact_name = {}
        for name, uri in self.nslist.iteritems():
            self.ns_compact_name[uri] = name
            self.write('@prefix {0}: <{1}>.\n'.format(name, uri))

        self.write('\n')

        for k, v in graphs.iteritems():
            if k:
                if not self.ttl:
                    self.write('<{0}> {{\n'.format(k))
                self.process_graph(v)
                if not self.ttl:
                    self.write('}\n')
            elif len(v.ks):
                if not self.ttl:
                    self.write('{\n')
                self.process_graph(v)
                if not self.ttl:
                    self.write('}\n')

    def to_ref(self, uri):
        ns, name = split_uri(uri)

        if uri.startswith(bnode_prefix):
            return '_:'+name

        ns = self.ns_compact_name.get(ns, None)
        if ns is None:
            return '<{0}>'.format(name)

        return '{0}:{1}'.format(ns, name)

    def resource(self, property, value):
        self.write('{0} {1}'.format(self.to_ref(property), self.to_ref(value)))

    def nontyped(self, property, value):
        self.write('{0} {1}'.format(self.to_ref(property), escape(value)))

    def langtyped(self, property, value, lang):
        self.write('{0} {1}@{2}'.format(self.to_ref(property), escape(value), escape(lang)))

    def datatyped(self, property, value, datatype):
        self.write('{0} {1}^^{2}'.format(self.to_ref(property), escape(value), self.to_ref(datatype)))

    def rdflist(self, property, lst):
        self.write('{0} ({1})'.format(self.to_ref(property), '\n'.join([self.to_ref(v) for v in lst])))

    def write_entity(self, g, ent, triples):
        if not triples:
            return

        self.write(self.to_ref(ent))
        self.write('\n')

        blank_nodes = set()

        l = list(triples)
        l.sort()
        first = True
        for t in l:
            if not first:
                self.write(';\n')
            first = False
            p = t.p
            if t.has_literal:
                if t.has_lang:
                    self.langtyped(p, t.l, t.lang)
                elif t.has_datatype:
                    self.datatyped(p, t.l, t.datatype)
                else:
                    self.nontyped(p, t.l)
            else:
                o = t.o
                if g.grIs_rdflist(o):
                        self.rdflist(p, g.grGet_rdflist(o))
                else:
                    self.resource(p, o)
                    if o.startswith('_#'):
                        blank_nodes.add(o)
        self.write('.\n')

        for v in blank_nodes:
            self.write_entity(g, v, g.ks.get(compact_uri(v), ()))

    def process_graph(self, g):
        total = len(g.ks)
        count = 0
        kl = g.ks.keys()
        kl.sort()
        for ent in kl:
            eent = expand_uri(ent)
            if eent.startswith('_#') and g.ko.get(ent) is not None:
                continue
            self.write_entity(g, eent, g.ks[ent])
            count += 1
            if count % 1000 == 0:
                st = getattr(g, 'AsyncChangeState', None)
                if st:
                    # graph is Document
                    g.AsyncChangeState(g.state_saving, 100*count/total)
            

