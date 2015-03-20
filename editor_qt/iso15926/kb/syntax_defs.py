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



from _ordereddict import ordereddict

ns_xsd = "http://www.w3.org/2001/XMLSchema#"
ns_rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
ns_rdfs = "http://www.w3.org/2000/01/rdf-schema#"
ns_owl = "http://www.w3.org/2002/07/owl#"
ns_owllist = "http://www.co-ode.org/ontologies/list.owl#"
ns_meta = 'http://standards.iso.org/iso/ts/15926/-8/ed-1/tech/reference-data/metadata#'
ns_dc = 'http://purl.org/dc/elements/1.1/'
ns_p7tm = 'http://standards.iso.org/iso/ts/15926/-8/ed-1/tech/reference-data/p7tm#'
ns_skos = 'http://www.w3.org/2004/02/skos/core#'

syntax_namespaces = [
    ("xsd", ns_xsd),
    ("rdf", ns_rdf),
    ("rdfs", ns_rdfs),
    ("owl", ns_owl),
    ("owllist", ns_owllist)
]

syntax_meta_namespaces = syntax_namespaces + [
    ("meta", ns_meta)
]

syntax_ns2uri = {}
syntax_uri2ns = {}

annlist_rdfs = ['label', 'comment']
rdf_type = ns_rdf+'type'
rdfs_label = ns_rdfs+'label'
skos_label = ns_skos+'prefLabel'
rdfs_comment = ns_rdfs+'comment'
rdfs_subclassof = ns_rdfs+'subClassOf'
labels_rdfs = [rdfs_label]

typelist_xsd = [
    'string', 'normalizedString', 'token', 'base64Binary', 'hexBinary', 'integer',
    'positiveInteger', 'negativeInteger', 'nonNegativeInteger', 'nonPositiveInteger',
    'long', 'unsignedLong', 'int', 'unsignedInt', 'short', 'unsignedShort', 'byte',
    'unsignedByte', 'decimal', 'float', 'double', 'boolean', 'duration', 'dateTime',
    'date', 'time', 'gYear', 'gYearMonth', 'gMonth', 'gMonthDay', 'gDay', 'Name', 'QName',
    'NCName', 'anyURI', 'language'
]

meta_unique = ns_meta + 'annUniqueName'
labels_meta = [meta_unique]

def _init():
    for t in syntax_namespaces:
        syntax_ns2uri[t[0]] = t[1]
        syntax_uri2ns[t[1]] = t[0]
_init()
