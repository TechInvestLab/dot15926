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
from iso15926.tools.scantools import *
from iso15926.tools.patterns import PatternDict
import threading, Queue
from PySide.QtCore import *
from PySide.QtGui import *

class Scanner:
    def __init__(self, doc):
        self.doc = doc
        self.graph = doc

    def scan_main(self, objprops, dtprops, untranslated, items=None):
        passed = set()

        if items and len(items)==1:
            return self.scan_props(objprops, dtprops, untranslated, passed, items)

        for (k, v) in dtprops.iteritems():
            if isinstance(v, basestring):
                found_items = set(self.graph.grSubjectsL(k, v))
            elif isinstance(v, set):
                found_items = set()
                for i in v:
                    found_items |= set(self.graph.grSubjectsL(k, i))
            else:
                continue

            if not found_items:
                return set()

            items = found_items if not items else items & found_items

            passed.add(k)

        for (k, v) in objprops.iteritems():
            if isinstance(v, basestring):
                found_items = set(self.graph.grSubjects(k, v))
            elif isinstance(v, set):
                found_items = set()
                for i in v:
                    found_items |= set(self.graph.grSubjects(k, i))
            else:
                continue

            if not found_items:
                return set()

            items = found_items if not items else items & found_items

            passed.add(k)

        return self.scan_props(objprops, dtprops, untranslated, passed, items)

    def scan_props(self, objprops, dtprops, untranslated, passed, items=None):
        to_out = None
        to_groupby = None
        props = objprops
        props.update(dtprops)
        props.update(untranslated)

        for k, v in props.iteritems():
            if getattr(v, 'marker_class', None) == out_marker:
                to_out = prop_match(k, v)
                break

        for k, v in props.iteritems():
            if getattr(v, 'marker_class', None) == groupby_marker:
                to_groupby = prop_match(k, v)
                if isinstance(v, marker):
                    del props[k]
                break

        for k in passed:
            del props[k]

        if len(props)==0:
            res = items if items else set()
        elif len(props)==1:
            filterfunc = prop_match(*props.items()[0])
            res = scan_filter(self.graph, filterfunc, items)
        else:
            filterfunc = props_match(props)
            res = scan_filter(self.graph, filterfunc, items)

        if to_out or to_groupby:
            res_out = set()
            for r in res:
                gb = []
                r_out = []
                for t in self.graph.grTriplesForSubj(r):
                    if to_out and to_out((t,)):
                        if t.has_literal:
                            r_out.append(LiteralValue(t.v))
                        else:
                            r_out.append(t.v)
                    if to_groupby and to_groupby((t,)):
                        if t.has_literal:
                            gb.append(LiteralValue(t.v))
                        else:
                            gb.append(t.v)

                if to_out is None:
                    r_out.append(r)
                elif r_out is None:
                    continue
                if len(gb) > 0:
                    r_out_copy = r_out[:]
                    r_out = []
                    for v1 in r_out_copy:
                        for v2 in gb:
                            r_out.append(v1+'|'+v2)
                res_out.update(set(r_out))
            res = res_out

        return res

    def find(self, *args, **kwargs):
        if threading.currentThread() != appdata.main_thread:
            return self._find(*args, **kwargs)
        queue = Queue.Queue()
        @public.wth('Searching...')
        def f():
            try:
                queue.put(self._find(*args, **kwargs))
            except Exception as e:
                if not isinstance(e, public.BreakTask):
                    log.exception()
                queue.put(set())

        if QThread.currentThread() == QCoreApplication.instance().thread():
            while True:
                try:
                    return queue.get_nowait()
                except Queue.Empty:
                    QCoreApplication.processEvents()
        else:
            return queue.get()

    def _find(self, collection = None, **props):
        part2ns = self.doc.chosen_part2
        items = props.pop('id', None)

        if not items and collection:
            items = collection
            collection = None

        if items:
            items = filter_items(self.graph, items, collection)
            if len(props)==0:
                return items

        itemtype = props.pop('type', None)
        if itemtype and not isinstance(itemtype, basestring) and getattr(itemtype, 'find', None):
            result = itemtype.find(self.graph, props)
            if isinstance(result, PatternDict):
                result.RemoveDuplicates()
            return result

        if not itemtype or not getattr(itemtype, 'translate_props', None):
            objprops = {}
            dtprops = {}
            untranslated = {}
            for k, v in props.iteritems():
                if k in kb.part2_object_properties:
                    objprops[part2ns+k] = v
                elif k in kb.part2_datatype_properties:
                    dtprops[part2ns+k] = v
                else:
                    untranslated[k] = v
            if itemtype:
                objprops[kb.rdf_type] = itemtype
        else:
            objprops, dtprops, untranslated = itemtype.translate_props(props)

        if itemtype and getattr(itemtype, 'marker_class', None):
            objprops[kb.rdf_type] = itemtype.marker_class.apply(objprops[kb.rdf_type])

        objprops, dtprops, untranslated = self.doc.translate_props(untranslated, objprops, dtprops, {})
    
        return self.scan_main(objprops, dtprops, untranslated, items)
