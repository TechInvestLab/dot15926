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
import urllib
import requests
from requests.auth import HTTPDigestAuth
import framework.util as util
import zlib
import iso15926.kb as kb

syntax_namespaces = [
    ("xsd", "http://www.w3.org/2001/XMLSchema#"),
    ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
    ("owl", "http://www.w3.org/2002/07/owl#"),
    ("owllist", "http://www.co-ode.org/ontologies/list.owl#")
]

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class SparqlConnection:
    debug = False

    def __init__(self, uri, login=None, password=None):
        self.uri = uri
        self.login = login
        self.password = password
        self.req_prefix = ''.join(['PREFIX {0}: <{1}>\n'.format(*t) for t in syntax_namespaces])
        self.NTLM = False
        self.session = util.Session(self.uri, self.login, self.password)
        self.last_err = 0
        self.connected = self.ReadSubGraph('DESCRIBE rdf:type', None)

    def ReadSubGraph(self, query, graph):
        uri = '{0}?query={1}'.format(self.uri, urllib.quote(self.req_prefix+query))
        try:
            if self.debug:
                log('Path: {0}\n', self.uri)
                log('Query: {0}\n', self.req_prefix+query)
            r = self.session.Open(uri, headers={'Accept': 'application/rdf+xml'})
            self.last_err = r.code
            if r.code==200:
                content = r.content
                if self.debug:
                    log('Response: {0}\n', content)
                if graph is not None:
                    graph.grLoadFromString(content, update_ns=False)
                return True
            else:
                if r.code==401:
                    self.was_401 = True
                    if r.headers['www-authenticate'] == 'Negotiate, NTLM' and not self.NTLM:
                        self.NTLM = True
                        self.session = util.NTLMSession(self.uri, self.login, self.password)
                    return self.ReadSubGraph(query, graph)
                log('Error: {0} {1}\n', r.code, r.error)
                if self.debug:
                    log('Headers: {0}\n', r.headers)
        except public.BreakTask:
            raise
        except Exception as e:
            if hasattr(e, 'reason'):
                log('Exception: {0}\n', e.reason)
            else:
                log('Exception: {0}\n', e)
        return False

    def InitialQuery(self, graph):
        return self.ReadSubGraph('''
            CONSTRUCT { ?s rdf:type ?o } 
            WHERE { {?s rdf:type ?o} 
            FILTER(regex(str(?o), "TemplateDescription$")) } LIMIT 1
            ''', graph)

    def QueryLabeled(self, graph, label):
        return self.ReadSubGraph('DESCRIBE ?ent WHERE {{ {{ ?ent <{1}> ?name }} FILTER (isLiteral(?name) && regex(str(?name), "{0}", "i")) }}'.format(label, kb.rdfs_label), graph)

    def QueryUriSubstring(self, graph, text):
        return self.ReadSubGraph('DESCRIBE ?s WHERE {{ {{ ?s ?p ?o }} FILTER (regex(str(?s), "{0}", "i")) }}'.format(text), graph)

    def QueryUri(self, graph, uri):
        if isinstance(uri, basestring):
            uri = [uri]
        else:
            uri = list(uri)

        for chunk in chunks(uri, 5):
            uri1 = ' '.join(['<{0}>'.format(v) for v in chunk])
            res = self.ReadSubGraph('DESCRIBE {0}'.format(uri1), graph)
            if not res:
                return False
        return True

    def QueryUriWIP(self, graph, uri):
        if isinstance(uri, basestring):
            uri = [uri]
        else:
            uri = list(uri)

        for chunk in chunks(uri, 5):
            uri1 = ' '.join(['<{0}>'.format(v) for v in chunk])
            uri2 = 'UNION'.join(['{{<{0}> <http://posccaesar.org/rdl/rdsWipEquivalent> ?ent}}'.format(v) for v in chunk])
            res = self.ReadSubGraph('DESCRIBE {0} ?ent WHERE {{ GRAPH <http://irm.dnv.com/ontologies/iring.map> {{ {1} }} }}'.format(uri1, uri2), graph)
            if not res:
                return False
        return True

    def QueryProperties(self, graph, ent):
        if ent.startswith('_#z'):
            return self.ReadSubGraph('DESCRIBE <{0}>'.format(ent[3:]), graph)
        return self.ReadSubGraph('DESCRIBE <{0}>'.format(ent), graph)

    def QueryRelationships(self, graph, ent):
        if ent.startswith('_#z'):
            return self.ReadSubGraph('DESCRIBE ?s WHERE {{ ?s ?p <{0}> }}'.format(ent[3:]), graph)
        return self.ReadSubGraph('DESCRIBE ?s WHERE {{ ?s ?p <{0}> }}'.format(ent), graph)

    def QueryTemplates(self, graph, p7tm, text):
        res = self.ReadSubGraph('''
            DESCRIBE ?t ?d ?s
            WHERE 
            {{  ?d <{1}> <{0}TemplateDescription> . 
                ?d <{0}hasTemplate> ?t . 
                OPTIONAL {{ ?t <{2}> ?name }} .
                OPTIONAL {{ ?s <{0}hasSuperTemplate> ?t .
                            ?s <{0}hasSubTemplate>+  ?ts .
                            OPTIONAL {{ ?ts <{2}> ?name2 }} . }} 
               FILTER ((bound(?name) && isLiteral(?name) && regex(str(?name), "{3}", "i"))
                || (bound(?name2) && isLiteral(?name2) && regex(str(?name2), "{3}", "i"))  
                || regex(str(?t), "{3}", "i")
                || regex(str(?ts), "{3}", "i")) }}'''.format(p7tm, kb.rdf_type, kb.rdfs_label, text), graph)
        
        if not res:
            return False

        res = self.ReadSubGraph('''
            DESCRIBE ?rd ?r
            WHERE 
            {{  ?rd <{1}> <{0}TemplateRoleDescription> .
                ?rd <{0}hasTemplate> ?t . 
                ?rd <{0}hasRole> ?r . 
                OPTIONAL {{ ?t <{2}> ?name }} .
                OPTIONAL {{ ?s <{0}hasSuperTemplate> ?t .
                            ?s <{0}hasSubTemplate>+  ?ts .
                            OPTIONAL {{ ?ts <{2}> ?name2 }} . }} 
               FILTER ((bound(?name) && isLiteral(?name) && regex(str(?name), "{3}", "i"))
                || (bound(?name2) && isLiteral(?name2) && regex(str(?name2), "{3}", "i"))  
                || regex(str(?t), "{3}", "i")
                || regex(str(?ts), "{3}", "i")) }}'''.format(p7tm, kb.rdf_type, kb.rdfs_label, text), graph)

        return res

    def QueryAll(self, graph):
        return self.ReadSubGraph('CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }', graph)

    def Query(self, graph, string):
        return self.ReadSubGraph(string, graph)
