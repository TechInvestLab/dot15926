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


from syntax_defs import *
from part2_defs import *
from other_defs import *

from _ordereddict import ordereddict

namespaces_std = syntax_namespaces
namespaces_std_meta = syntax_meta_namespaces

annotations_rdfs = [(name, ns_rdfs + name) for name in annlist_rdfs]
annotations_rdfs_ex = annotations_rdfs + [('defaultRdsId', ns_pcardl_rdf + 'defaultRdsId')]
annotations_meta = [(name, ns_meta + name) for name in annlist_meta]
annotations_pcardl_rdf = annotations_rdfs + [(name, ns_pcardl_rdf + name) for name in annlist_pcardl]
annotations_pcardl_sparql = annotations_rdfs + [(name, ns_pcardl_sparql + name) for name in annlist_pcardl]

roles_std = [
    ('subClassOf', rdfs_subclassof),
    ('type', rdf_type)
    ]

roles_pcardl_sparql = roles_std + [
    ('rdsWipEquivalent', 'http://posccaesar.org/rdl/rdsWipEquivalent')
    ]


annotations_old_part4 = annotations_rdfs + [(name, ns_old_part4 + name) for name in annlist_old_part4] + [(name, ns_old_part6) for name in annlist_old_part6]
annotations_til = annotations_rdfs + annotations_meta + [(name, ns_til + name) for name in annlist_til]
annotations_pcardl_rdf_til = annotations_pcardl_rdf + annotations_meta + [(name, ns_til + name) for name in annlist_til]
all_known_namespaces = syntax_namespaces + syntax_meta_namespaces + [
    ("pcardl", ns_pcardl_sparql),
    ("rdswip", ns_rdswip), 
    ("dm",     ns_dm_part2)
    ]

all_labels = [
rdfs_label,
pca_rdf_designation,
pca_sparql_designation,
] + labels_part2 + [meta_unique] + [skos_label]

all_labels_dict = {v: i for i, v in enumerate(all_labels)}

vis_labels = [
rdfs_label,
pca_rdf_designation,
pca_sparql_designation,
pca_rdf_definition,
pca_sparql_definition,
] + labels_part2 + [meta_unique] + [skos_label]




rdsid  = 'http://posccaesar.org/rdl/defaultRdsId' 

def split_uri(uri):
    p = uri.rfind('#')
    if p==-1:
        p = uri.rfind('/')
    if p==-1:
        return ('', uri)
    return (uri[:p+1], uri[p+1:])


def p2GetSupertypesNamesByNames(names):
    return [part2_itself[i]['name'] for i in part2_itself['part2:'+name]['supertypes'] for name in names]

def p2GetSupertypes(uri):
    ns, name = split_uri(uri)[1]
    return [ns+part2_itself[i]['name'] for i in part2_itself['part2:'+name]['supertypes']]

# classifier->classified

def p2CanClassify(classifier, classified):
    classifier_ns, classifier_name = split_uri(classifier)
    classified_ns, classified_name = split_uri(classified)

    if classifier_ns not in part2_all_ns:
        return False

    if classified_ns not in part2_all_ns:
        return False

    info = part2_itself.get('part2:'+classifier_name)

    if info == None:
        return False

    classified_list = info.get('classified')

    if not classified_list or 'part2:'+classified_name not in classified_list:
        return False

    return True

def p2IsDisjoint(uri_1, uri_2):
    ns1, name1 = split_uri(uri_1)
    ns2, name2 = split_uri(uri_2)

    if ns1 not in part2_all_ns:
        return False

    if ns2 not in part2_all_ns:
        return False

    info = part2_itself.get('part2:'+name1)

    if info == None:
        return False

    disj = info.get('disjoints')

    if not disj or 'part2:'+name2 not in disj:
        return False

    return True

def p2GetClassifiers(uri):
    ns, name = split_uri(uri)

    if ns not in part2_all_ns:
        return set()

    qname = 'part2:'+name

    info = part2_itself.get(qname)

    if info == None:
        return set()

    return info.get('classifier', set())

def p2TypeIsSupertypeOf(sup, sub):
    ns_sup, name_sup = split_uri(sup)
    ns_sub, name_sub = split_uri(sub)

    if ns_sup not in part2_all_ns:
        return False

    if ns_sub not in part2_all_ns:
        return False

    if name_sup == name_sub:
        return True

    qname_sup = 'part2:' + name_sup
    qname_sub = 'part2:' + name_sub

    info = part2_itself.get(qname_sub)

    if info == None:
        return set()

    next = set([qname_sub])
    while next:
        lst, next = next, set()
        for i in lst:
            s = part2_itself[i]['supertypes']
            if qname_sup in s:
                return True
            else:
                next |= set(s)

    return False

def p2GetSubtypes(uri):
    ns, name = split_uri(uri)

    if ns not in part2_all_ns:
        return set()

    qname = 'part2:'+name

    info = part2_itself.get(qname)

    if info == None:
        return set()

    types = set()
    def f(ti):
        for i in ti['subtypes']:
            types.add(ns+part2_itself[i]['name'])
            f(part2_itself[i])

    f(info)

    return types

def p2GetClassifiersTypeList(uri):
    result = set()
    ns, name = split_uri(uri)
    if ns in part2_all_ns:
        qname = 'part2:'+name
        if qname in part2_itself:
            classifier_list = part2_itself[qname].get('classifier')
            if classifier_list:
                def f(ti):
                    result.add(ns + ti['name'])
                    for i in ti['subtypes']:
                        f(part2_itself[i])
                for v in classifier_list:
                    f(part2_itself[v])
    return result


def uri2name(uri, delim = '.'):
    ns, name = split_uri(uri)
    if ns in part2_all_ns:
        return delim.join(('part2', name))

icons_map = { 'iso_class': 'iso_class_i',
              'iso_individual': 'iso_individual_i',
              'iso_classofclass': 'iso_classofclass_i',
              'iso_co_rel': 'iso_co_rel_i',
              'iso_rel': 'iso_rel_i',
              'iso_co_classofrel': 'iso_co_classofrel_i',
              'iso_class_i': 'iso_individual_i',
              'iso_classofclass_i': 'iso_class_i',
              'iso_co_rel_i': 'iso_rel_i',
              'iso_co_classofrel_i': 'iso_co_rel_i',
              'iso_spec_template': 'iso_template_inst',
              'iso_template': 'iso_template_inst',
              'iso_template_c': 'iso_template',
              ns_owl+'ObjectProperty': 'iso_role',
              ns_owl+'DatatypeProperty': 'iso_annotation' }