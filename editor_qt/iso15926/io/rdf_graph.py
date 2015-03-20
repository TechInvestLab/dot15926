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




from collections import defaultdict
from iso15926.io.rdfxml_writer import RdfXmlWriter
from iso15926.io.trig_writer import TrigWriter
from iso15926.io.sparql import SparqlConnection
from iso15926.io.rdf_base import *
import iso15926.kb as kb
from framework.util import TaskTarget, DataFormatError
from graphlib import *
import sys


class RdfGraph(Graph):

    def __init__(self):
        Graph.__init__(self)
        self.format = 'rdfxml'
        self.gzip = False
        self.tg = RdfGraph
        self.grClear()

    def grClear(self):
        Graph.grClear(self)
        self.sparql = None # sparql connection or None
        self.qs = set() # sparql, information for subj was delivered earlier
        self.qo = set() # sparql, information for obj was delivered earlier

    # low level

    def grGetUsedNamespaces(self):
        nsset = set()
        for s in self.ks.itervalues():
            for t in s:
                t.collect_ns_to(nsset)

        return set([expand_uri(c) for c in nsset])

    def grCompact(self, uri):
        return compact_uri(uri)

    def grExpand(self, curi):
        return expand_uri(curi)

    def grSubjCount(self):
        return len(self.ks)

    def grAllSubj(self):
        for s in self.ks.iterkeys():
            yield expand_uri(s)

    def grAllTriples(self):
        for s in self.ks.itervalues():
            for t in s:
                yield t

    def grFindNsByObj(self, s):
        for curi in self.ko:
            if curi_tail(curi) == s:
                return expand_uri(curi_head(curi))
        return None

    def grFindNsBySubj(self, s):
        for curi in self.ks:
            if curi_tail(curi) == s:
                return expand_uri(curi_head(curi))
        return None

    def grTriplesForSubj(self, s):
        return list(self.ks.get(compact_uri(s), ()))

    def grTriplesForObj(self, o):
        o = compact_uri(o)
        return self.ko.get(o, ())

    def grTriplesForLit(self, l):
        return self.kl.get(l, ())

    def grHas(self, s, p, o):
        return ObjectTriple.test(self, s, p, o)

    def grLiteral(self, s, p):
        s = compact_uri(s)
        p = compact_uri(p)
        ks = self.ks.get(s, ())
        for t in ks:
            if t[1]==p:
                if t.has_literal:
                    return t[2]

    def grLiterals(self, s, p):
        l = []
        s = compact_uri(s)
        p = compact_uri(p)
        ks = self.ks.get(s, ())
        for t in ks:
            if t[1]==p:
                if t.has_literal:
                    l.append(t[2])
        return l

    def grOneObj(self, s, p):
        s = compact_uri(s)
        p = compact_uri(p)
        ks = self.ks.get(s, ())
        for t in ks:
            if t[1]==p:
                return t.v

    def grObjects(self, s, p):
        l = []
        s = compact_uri(s)
        p = compact_uri(p)
        ks = self.ks.get(s, ())
        for t in ks:
            if t[1]==p:
                l.append(t.o)
        return l

    def grOneSubj(self, p, o):
        p = compact_uri(p)
        o = compact_uri(o)
        ko = self.ko.get(o, ())
        for t in ko:
            if t[1]==p:
                return t.s

    def grSubjects(self, p, o):
        r = []
        p = compact_uri(p)
        o = compact_uri(o)
        ko = self.ko.get(o, ())
        for t in ko:
            if t[1]==p:
                r.append(t.s)
        return r

    def grSubjectsL(self, p, l):
        r = []
        p = compact_uri(p)
        kl = self.kl.get(l, ())
        for t in kl:
            if t[1]==p:
                r.append(t.s)
        return r

    # high level

    def grGet_rdflist(self, s):
        l = []
        h = self.grOneObj(s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#first')
        if h is not None:
            l.append(h)
            s = self.grOneObj(s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')
            while s and s!='http://www.w3.org/1999/02/22-rdf-syntax-ns#nil':
                h = self.grOneObj(s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#first')
                l.append(h)
                s = self.grOneObj(s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest')
        return l

    def grGet_owllist(self, s):
        l = []
        h = self.grOneObj(s, 'http://www.co-ode.org/ontologies/list.owl#hasContents')
        while h is not None:
            l.append(h)
            s = self.grOneObj(s, 'http://www.co-ode.org/ontologies/list.owl#hasNext')
            h = self.grOneObj(s, 'http://www.co-ode.org/ontologies/list.owl#hasContents')
        return l

    def grIs_rdflist(self, s):
        return ObjectTriple.test(self, s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#List')

    def grIs_owllist(self, s):
        return ObjectTriple.test(self, s, 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', 'http://www.co-ode.org/ontologies/list.owl#OWLList')

    def grNeedProperties(self, s, reload=False):
        if self.sparql:
            if reload or (s not in self.qs):
                self.qs.add(s)
                @public.wth(tm.main.loading_props_in.format(self.name), self)
                def f1():
                    self.sparql.QueryProperties(self, s)
                    @public.mth
                    def f2():
                        wizard.W_EntityPropertiesChanged(self, s)
                return True

    def grNeedRelationships(self, o, reload=False):
        if self.sparql:
            if reload or (o not in self.qo):
                self.qo.add(o)
                @public.wth(tm.main.loading_rels_in.format(self.name), self)
                def f1():
                    self.sparql.QueryRelationships(self, o)
                    @public.mth
                    def f2():
                        wizard.W_EntityRelationshipsChanged(self, o)
                return True

    def _grSearchUri(self, uri):
        if isinstance(uri, basestring):
            uri = set([uri])

        if self.sparql:
            for v in uri:
                if self.ks.get(compact_uri(v), None) != None:
                    del self.ks[compact_uri(v)]
            self.sparql.QueryUri(self, uri)
            
        res = set()

        for v in uri:
            t = self.ks.get(compact_uri(v), None)
            if t:
                res.add(v)
                self.qs.add(v)

        return res

    def grSearchUri(self, uri, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchUri(uri)
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

    def _grSparqlQuery(self, string):
        if self.sparql:
            res = set()
            def f(t):
                res.add(t.s)
            self.grAddCallback(self.TRIPLE_INSERT, f)
            self.sparql.Query(self, string)
            self.grRemoveCallback(self.TRIPLE_INSERT, f)
            return res
        return set()

    def grSparqlQuery(self, string, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSparqlQuery(string)
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

    def _grSearchUriWIP(self, uri):
        if isinstance(uri, basestring):
            uri = set([uri])

        if self.sparql:
            for v in uri:
                if self.ks.get(compact_uri(v), None) != None:
                    del self.ks[compact_uri(v)]
            self.sparql.QueryUriWIP(self, uri)
            
        res = {}

        for v in uri:
            for t in self.grTriplesForSubj(v):
                if t.p == 'http://posccaesar.org/rdl/rdsWipEquivalent':
                    res[v] = t.v
                    self.qs.add(t.v)

        return res

    def grSearchUriWIP(self, uri, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = set(self._grSearchUriWIP(uri).values())
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

    def _grSearchAll(self):
        if self.sparql:
            self.sparql.QueryAll(self)
            all_uri = set([expand_uri(v) for v in self.ks.iterkeys()]) | set([expand_uri(v) for v in self.ko.iterkeys()])
            self.qs |= all_uri
            self.qo |= all_uri
        return set([expand_uri(curi) for curi in self.ks.iterkeys()])

    def grSearchAll(self, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchAll()
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


    def _grSearchText(self, text):
        dtext = text.decode('utf-8').lower()

        all_labels = [compact_uri(v) for v in kb.all_labels]

        if self.sparql:
            to_delete = set()
            for s, v in self.ks.iteritems():
                s = expand_uri(s)
                if dtext in s.decode('utf-8').lower():
                    to_delete.add(s)
                else:
                    for value in all_labels:
                        for t in v:
                            if t.has_literal and t[1] == value and dtext in t[2].decode('utf-8').lower():
                                    to_delete.add(s)

            for v in to_delete:
                del self.ks[compact_uri(v)]

            self.sparql.QueryUriSubstring(self, text)
            self.sparql.QueryLabeled(self, text)

        res = set()

        for s, v in self.ks.iteritems():
            s = expand_uri(s)
            if dtext in s.decode('utf-8').lower():
                res.add(s)
            else:
                for value in all_labels:
                    for t in v:
                        if t.has_literal and t[1] == value and dtext in t[2].decode('utf-8').lower():
                            self.qs.add(s)
                            res.add(s)
        return res

    def grSearchText(self, text, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchText(text)
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


    def _grSearchUriSubstring(self, text):
        dtext = text.decode('utf-8').lower()

        all_labels = [compact_uri(v) for v in kb.all_labels]

        if self.sparql:
            to_delete = set()
            for s, v in self.ks.iteritems():
                s = expand_uri(s)
                if dtext in s.decode('utf-8').lower():
                    to_delete.add(s)

            for v in to_delete:
                del self.ks[compact_uri(v)]

            self.sparql.QueryUriSubstring(self, text)

        res = set()

        for s, v in self.ks.iteritems():
            s = expand_uri(s)
            if dtext in s.decode('utf-8').lower():
                res.add(s)
                
        return res

    def grSearchUriSubstring(self, text, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchUriSubstring(text)
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


    def _grSearchLabel(self, label):
        dlabel = label.decode('utf-8').lower()

        all_labels = [compact_uri(v) for v in kb.all_labels]

        if self.sparql:
            to_delete = set()
            for v in self.ks.itervalues():
                for value in all_labels:
                    for t in v:
                        if t.has_literal and t[1] == value and dlabel in t[2].decode('utf-8').lower():
                                to_delete.add(t.s)

            for v in to_delete:
                del self.ks[compact_uri(v)]

            self.sparql.QueryLabeled(self, label)

        res = set()

        for v in self.ks.itervalues():
                for value in all_labels:
                    for t in v:
                        if t.has_literal and t[1] == value and dlabel in t[2].decode('utf-8').lower():
                            self.qs.add(t.s)
                            res.add(t.s)

        return res

    def grSearchLabel(self, label, res_id):
        @public.wth(tm.main.searching_in.format(self.name), self)
        def f1():
            try:
                res = self._grSearchLabel(label)
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

    def grFindExactLabel(self, label):
        rl = compact_uri('http://www.w3.org/2000/01/rdf-schema#label')
        kl = self.kl.get(label, ())
        for v in kl:
            for t in v:
                if t[1]==rl:
                    return t.s

    def grLoadFromFiles(self, fnames, update_ns=True):
        self.format = None
        for f in fnames:
            info = []
            for format in ('rdfxml', 'turtle'):
                info += ['Trying %s:'%format]
                log_msg = []
                def fl(text):
                    log_msg.append(text)
                self.grAddCallback(self.LOG, fl)
                try:
                    read_rdf_file(f, self, format)
                    with open(f, 'rb') as ff:
                        if (ff.read(2) == b'\x1f\x8b'):
                            self.gzip = True
                    self.format = format

                    @public.mth
                    def f2():
                        log('\n'.join(log_msg))
                    break
                except Exception as e:
                    if isinstance(e, public.BreakTask):
                        break
                    else:
                        info += log_msg + [str(e)+'\n']
                finally:
                    self.grRemoveCallback(self.LOG, fl)
            else:
                raise DataFormatError(f, '\n'.join(info))

    def grLoadFromString(self, data, update_ns=True):
        #print data
        read_rdf_string(str(data), len(str(data)), self)

    def grSaveToFile(self, fname, mode, use_gzip = False):
        #write_rdf_file(fname, self, 'turtle');
        if mode == 'turtle':
            wr = TrigWriter()
            wr.SaveGraphToFile(self, fname, ttl=True, use_gzip = use_gzip)
        else:
            wr = RdfXmlWriter()
            wr.SaveGraphToFile(self, fname, use_gzip = use_gzip)

    def grBindSparqlEndpoint(self, connection):
        self.sparql = connection

    def grPrintErr(self, err):
        @public.mth
        def f():
            log(err)


RESULT_KEY = 1
PARENT_KEY = 2

class RdfDiff(RdfGraph):

    def __init__(self):
        self.deletions = self.ng['deletions'] = RdfGraph()
        self.insertions = self.ng['insertions'] = RdfGraph()
        self.blanks = {}
        self.other_blanks = {}
        self.docs = None
        self.ready = False

    def LoadFromFile(self, filename):
        @public.wth(tm.main.loading_diff)
        def f():
            try:
                self.LoadFromFileProc(filename)
                @public.mth
                def f2():
                    self.ready = True
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()

    def LoadFromFileProc(self, filename):
        read_rdf_file(filename, self, 'trig')

    def SaveToFile(self, filename):
        @public.wth(tm.main.saving_diff)
        def f():
            try:
                self.SaveToFileProc(filename)
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()

    def SaveToFileProc(self, filename):
        writer = TrigWriter()
        writer.SaveGraphToFile(self, filename)

    def Compare(self, first, second):
        @public.wth(tm.main.diff_comparing)
        def f():
            try:
                self.CompareProc(first, second)
                @public.mth
                def f2():
                    self.ready = True
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()

    def UpdateEntity(self, subject):
        if not self.docs:
            return

        for t in self.deletions.grTriplesForSubj(subject):
            t.deletefrom(self.deletions)

        for t in self.insertions.grTriplesForSubj(subject):
            t.deletefrom(self.insertions)

        all_first = set(self.docs[0].grTriplesForSubj(subject))

        analyze_blanks = False
        all_second     = None
        if subject.startswith(bnode_prefix):
            if subject in self.blanks:
                all_second = [t.with_s(subject) for t in self.docs[1].grTriplesForSubj(self.blanks[subject])]
                all_second = set([t.with_o(self.other_blanks.get(t.v, t.v)) if t.has_object else t for t in all_second])
            elif subject in self.other_blanks:
                all_second = [t.with_s(self.other_blanks[subject]) for t in self.docs[1].grTriplesForSubj(subject)]
                all_second = set([t.with_o(self.other_blanks.get(t.v, t.v)) if t.has_object else t for t in all_second])
            else:
                analyze_blanks = True

        if not all_second:
            all_second = set([t.with_o(self.other_blanks.get(t.v, t.v)) if t.has_object else t for t in self.docs[1].grTriplesForSubj(subject)])

        for t in all_first - all_second:
            t.insertto(self.deletions)

        for t in all_second - all_first:
            t.insertto(self.insertions)

        if analyze_blanks:
            self.AnalyzeBlanks(subject)

    def CompareProc(self, first, second):
        self.docs = (first, second)

        all_first = []
        all_second = []

        for v in first.ks.itervalues():
            all_first += v

        for v in second.ks.itervalues():
            all_second += v
        
        all_first = set(all_first)
        all_second = set(all_second)

        for t in all_first - all_second:
            t.insertto(self.deletions)

        for t in all_second - all_first:
            t.insertto(self.insertions)

        self.AnalyzeBlanks()

    def FindBlank(self, uri, items):
        triples = self.deletions.grTriplesForSubj(uri)
        rels = self.deletions.grTriplesForObj(uri)
        best_count = 0
        best_values = []

        if not items:
            for v in self.insertions.grAllSubj():
                if self.NotIdentified(v):
                    count = 0
                    for t in triples:
                        for tt in self.insertions.grTriplesForSubj(v):
                            if t.p == tt.p and t.d == tt.d:
                                if t.v == tt.v or self.NotIdentified(t.v) and self.NotIdentified(tt.v):
                                    count += 1

                    for t in rels:
                        for tt in self.insertions.grTriplesForObj(v):
                            if t.p == tt.p:
                                if t.s == tt.s or self.NotIdentified(t.s) and self.NotIdentified(tt.s):
                                    count += 1

                    if count > best_count:
                        best_values = [v]
                        best_count = count
                    elif count == best_count:
                        best_values.append(v)
        else:
            for uri in items:
                count = 0
                for t in triples:
                    for tt in self.insertions.grTriplesForSubj(uri):
                        if t.p == tt.p and t.d == tt.d:
                            if t.v == tt.v or self.NotIdentified(t.v) and self.NotIdentified(tt.v):
                                count += 1

                for t in rels:
                    for tt in self.insertions.grTriplesForObj(uri):
                        if t.p == tt.p:
                            if t.s == tt.s or self.NotIdentified(t.s) and self.NotIdentified(tt.s):
                                count += 1

                if count > best_count:
                    best_values = [uri]
                    best_count = count
                elif count == best_count:
                    best_values.append(uri)

        return best_values


    def NotIdentified(self, uri):
        return uri.startswith(bnode_prefix) and uri not in self.blanks


    def CheckSubject(self, uri):
        if self.NotIdentified(uri) and not self.insertions.grTriplesForSubj(uri):

            processed = set()
            blanks  = [uri]
            roots = [uri]

            while blanks:
                for v in blanks[:]:
                    processed.add(v)
                    triples = self.deletions.grTriplesForObj(v)
                    blanks = [t.s for t in triples if self.NotIdentified(t.s) and t.s not in processed]
                    if triples:
                        roots = [t.s for t in triples]

            roots           = set(roots)
            depths          = {}
            parents         = {}
            results         = {}
            check_list      = {}

            if roots:
                for uri in roots:
                    if self.NotIdentified(uri):
                        check_list.setdefault(uri, [])
                        parents[uri] = None
                        depths[uri] = 0
                    else:
                        for t in self.deletions.grTriplesForSubj(uri):
                            for tt in self.insertions.grTriplesForSubj(uri):
                                if t.p == tt.p and t.d == tt.d and self.NotIdentified(t.v) and self.NotIdentified(tt.v):
                                    check_list.setdefault(t.v, []).append(tt.v)
                                    parents.setdefault(t.v, set()).add(uri)
                                    parents.setdefault(t.v, set()).add(uri)
                                    depths[t.v] = 1

            while check_list:
                uri = check_list.iterkeys().next()
                items = check_list[uri]
                del check_list[uri]
                result = self.FindBlank(uri, items)
                if result:
                    results.setdefault(uri, []).extend(result)
                    for t in self.deletions.grTriplesForSubj(uri):
                        for r in result:
                            for tt in self.insertions.grTriplesForSubj(r):
                                if t.p == tt.p and t.d == tt.d:
                                    if self.NotIdentified(t.v) and self.NotIdentified(tt.v):
                                        check_list.setdefault(t.v, []).append(tt.v)
                                        parents.setdefault(t.v, set()).add(uri)
                                        parents.setdefault(tt.v, set()).add(r)
                                        depths[t.v] = max(depths[uri] + 1, depths.get(t.v, -1))

            priority = sorted(depths, key = depths.get)
            while priority:
                uri = priority.pop()
                variants = []
                res = results.get(uri)
                p_list = parents.get(uri)
                if res:
                    found_res = None
                    if p_list:
                        for rr in res:
                            if found_res:
                                break
                            p_other = parents.get(rr, set())
                            for p in p_list:
                                p_res = results.get(p)
                                if p_res:
                                    possible_res = list(set(p_res) & set(p_other))
                                    if possible_res:
                                        results[p] = possible_res
                                        found_res = rr
                                        break

                    if found_res:
                        self.UpdateBlank(uri, found_res)
                    else:
                        self.UpdateBlank(uri, res[0])


    def UpdateBlank(self, first, second):
        self.blanks[first] = second
        self.other_blanks[second] = first
        for t in list(self.insertions.grTriplesForSubj(second)):
            t.deletefrom(self.insertions)
            item = t.with_s(first)
            found = False
            for tt in self.deletions.grTriplesForSubj(first):
                if tt == item:
                    found = True
                    break
            if found:
                item.deletefrom(self.deletions)
            else:
                item.insertto(self.insertions)

        lst = self.insertions.grTriplesForObj(second)[:]
        for t in lst:
            t.deletefrom(self.insertions)
            item = t.with_o(first)
            found = False
            for tt in self.deletions.grTriplesForObj(first):
                if tt == item:
                    found = True
                    break
            if found:
                item.deletefrom(self.deletions)
            else:
                item.insertto(self.insertions)

    def SortBlanks(self, items):
        res = []
        for curi in items:
            uri = expand_uri(curi)
            if self.NotIdentified(uri):
                k = len(self.deletions.grTriplesForSubj(uri)) + len(self.deletions.grTriplesForObj(uri))
                res.append((k, curi))
        return sorted(res, reverse=True)

    def AnalyzeBlanks(self, subject = None):
        found_blanks = {}

        if not subject:
            for k, uri in self.SortBlanks(self.deletions.ks.keys()):
                self.CheckSubject(expand_uri(uri))
        else:
            if self.deletions.grTriplesForSubj(subject):
                self.CheckSubject(subject)

    def MakeLocalDiff(self, dest, source):
        all_subj = self.deletions.ks.viewkeys() | self.insertions.ks.viewkeys()
        for v in all_subj:
            uri = expand_uri(v)
            triples = set(source.grTriplesForSubj(uri)) - set(self.deletions.grTriplesForSubj(uri))
            for t in triples:
                t.insertto(dest)

        for t in self.insertions.grAllTriples():
            t.insertto(dest)

        return dest
