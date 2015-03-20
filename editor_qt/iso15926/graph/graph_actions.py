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
from iso15926.io.rdf_base import *
import iso15926.common.dialogs as dialogs
from framework.dialogs import Notify, Choice

class DocumentPropertyChange():
    props_change = True
    
    def __init__(self, doc, prop, value):
        self.doc = doc
        self.prop = prop
        self.value = value

    def Redo(self):
        self.old_value = getattr(self.doc, self.prop, None)
        if self.old_value == self.value:
            return False
        self.doc.UpdateProps({self.prop: self.value})
        return True

    def Undo(self):
        self.doc.UpdateProps({self.prop: self.old_value})
        self.doc.RefreshProps()

class UpdateTemplateRole():
    def __init__(self, g, template, roledesc):
        self.g = g
        self.template = template
        self.roledesc = roledesc

    def Redo(self):
        role_name         = self.g.grTemplateRoleName(self.roledesc['uri'])
        deletions         = self.g.grCollectTemplateRoleTriples(self.template, role_name, True)
        insertions        = self.g.grTemplateRoleTriplesByDesc(self.template, self.roledesc)

        subj = set()
        objs = set()

        self.old_role = deletions

        for t in deletions:
            t.deletefrom(self.g)
            subj.add(t.s)
            if t.has_object:
                objs.add(t.o)

        for t in insertions:
            t.insertto(self.g)
            subj.add(t.s)
            if t.has_object:
                objs.add(t.o)

        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

        for s in subj:
            if not self.g.grTriplesForSubj(s):
                wizard.W_EntityDestroyed(self.g, s)
            else:
                wizard.W_EntityPropertiesChanged(self.g, s)

        wizard.W_TemplateRolesChanged(self.g, self.template)
        return True

    def Undo(self):
        if not self.old_role:
            return

        role_name  = self.g.grTemplateRoleName(self.roledesc['uri'])
        deletions  = self.g.grCollectTemplateRoleTriples(self.template, role_name, True)

        subj = set()
        objs = set()

        for t in deletions:
            t.deletefrom(self.g)
            subj.add(t.s)
            if t.has_object:
                objs.add(t.o)

        for t in self.old_role:
            t.insertto(self.g)
            subj.add(t.s)
            if t.has_object:
                objs.add(t.o)

        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

        for s in subj:
            if not self.g.grTriplesForSubj(s):
                wizard.W_EntityDestroyed(self.g, s)
            else:
                wizard.W_EntityPropertiesChanged(self.g, s)

        wizard.W_TemplateRolesChanged(self.g, self.template)

'''
class ChangeTemplateRoleComment():
    def __init__(self, g, template, role_uri, comment):
        self.g = g
        self.template = template
        self.comment = comment
        self.role_uri = role_uri

    def Redo(self):
        roledesc_uri = self.g.grRoleDescUri(self.template, self.role_uri)
        if not self.g.grTriplesForSubj(roledesc_uri):
            return False

        self.comment_old = self.grLiteral(roledesc_uri, kb.ns_rdfs+'comment')
        if self.comment_old:
            if self.comment_old == self.comment:
                return False
            LiteralTriple.of(roledesc_uri, kb.ns_rdfs+'comment', self.comment_old).deletefrom(self.g)
        LiteralTriple.of(roledesc_uri, kb.ns_rdfs+'comment', self.comment).insertto(self.g)

    def Undo(self):
        roledesc_uri = self.g.grRoleDescUri(self.template, self.role_uri)
        if not self.g.grTriplesForSubj(roledesc_uri):
            return False

        LiteralTriple.of(roledesc_uri, kb.ns_rdfs+'comment', self.comment).deletefrom(self.g)
        if self.comment_old:
            LiteralTriple.of(roledesc_uri, kb.ns_rdfs+'comment', self.comment_old).insertto(self.g)
'''


class ChangeTemplateRoleName():
    def __init__(self, g, template, role_name, new_name):
        self.g = g
        self.template = template
        self.role_name = role_name
        self.new_name = new_name

    def Redo(self):
        if self.role_name == self.new_name:
            return False
        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            if not self.g.grIsTemplate(v):
                Notify(tm.main.crossfile_template_specializations_detected)
                return False

        found = set()
        for v in items:
            role_uri = self.g.grTemplateRoleUri(v, self.role_name)
            if role_uri and role_uri not in found and self.g.grTriplesForSubj(role_uri):
                LiteralTriple.of(role_uri, kb.ns_rdfs+'label', self.role_name).deletefrom(self.g)
                LiteralTriple.of(role_uri, kb.ns_rdfs+'label', self.new_name).insertto(self.g)
                found.add(role_uri)
                wizard.W_EntityPropertiesChanged(self.g, role_uri)
            wizard.W_TemplateRolesChanged(self.g, v)
        if not found:
            return False
        return True

    def Undo(self):
        items = self.g.grTemplateGetDependencies(self.template)
        found = set()
        for v in items:
            role_uri = self.g.grTemplateRoleUri(v, self.new_name)
            if role_uri and role_uri not in found and self.g.grTriplesForSubj(role_uri):
                LiteralTriple.of(role_uri, kb.ns_rdfs+'label', self.new_name).deletefrom(self.g)
                LiteralTriple.of(role_uri, kb.ns_rdfs+'label', self.role_name).insertto(self.g)
                found.add(role_uri)
                wizard.W_EntityPropertiesChanged(self.g, role_uri)
            wizard.W_TemplateRolesChanged(self.g, v)

class ChangeTemplateRoleIndex():
    def __init__(self, g, template, role_name, index):
        self.g = g
        self.template = template
        self.role_name = role_name
        self.index = index

    def Redo(self):
        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            if not self.g.grIsTemplate(v):
                Notify(tm.main.crossfile_template_specializations_detected)
                return False

        self.index_old = None
        for v in items:
            index_old = self.g.grGetTemplateRoleIndex(v, self.role_name)
            if self.index_old == None:
                self.index_old = index_old
            elif self.index_old != index_old:
                Notify(tm.main.invalid_template_specializations_detected)
                return False

        if self.index_old and self.index_old != self.index:
            for v in items:
                self.g.grSetTemplateRoleIndex(v, self.role_name, self.index)
                wizard.W_TemplateRolesChanged(self.g, v)
            return True
        return False

    def Undo(self):
        if self.index_old:
            items = self.g.grTemplateGetDependencies(self.template)
            for v in items:
                self.g.grSetTemplateRoleIndex(v, self.role_name, self.index_old)
                wizard.W_TemplateRolesChanged(self.g, v)

class AddTemplate():
    def __init__(self, g, templatedesc):
        self.g = g
        self.templatedesc = templatedesc

    def Redo(self):
        if self.g.grTriplesForSubj(self.templatedesc['uri']):
            return False

        triples = []
        qname = self.templatedesc['uri']
        sup = self.templatedesc.get('supertemplate')
        name = self.templatedesc.get('name')
        comment = self.templatedesc.get('comment')
        anns = self.templatedesc.get('annotations')

        triples.append(ObjectTriple.insert(self.g, qname, kb.rdf_type, kb.ns_owl+'Class'))
        triples.append(ObjectTriple.insert(self.g, qname, kb.rdf_type, self.g.p7tm+'Template'))
        
        if name:
            triples.append(LiteralTriple.insert(self.g, qname, kb.ns_rdfs+'label', name))
        if comment:
            triples.append(LiteralTriple.insert(self.g, qname, kb.ns_rdfs+'comment', comment))

        if sup:
            triples.append(ObjectTriple.insert(self.g, qname, kb.ns_rdfs+'subClassOf', self.g.p7tm+'RDLTemplateStatement'))
            triples.append(ObjectTriple.insert(self.g, qname, kb.ns_rdfs+'subClassOf', sup))
            triples.append(ObjectTriple.insert(self.g, qname+'__spec', kb.rdf_type, self.g.p7tm+'TemplateSpecialization'))
            triples.append(ObjectTriple.insert(self.g, qname+'__spec', kb.rdf_type, kb.ns_owl+'Thing'))
            triples.append(ObjectTriple.insert(self.g, qname+'__spec', self.g.p7tm+'hasSubTemplate', qname))
            triples.append(ObjectTriple.insert(self.g, qname+'__spec', self.g.p7tm+'hasSuperTemplate', sup))
            suproles = self.g.grGetTemplateRoles(sup)
            for v in suproles.itervalues():
                for t in self.g.grTemplateRoleTriplesByDesc(qname, v):
                    triples.append(t.insertto(self.g))
        else:
            triples.append(ObjectTriple.insert(self.g, qname, kb.ns_rdfs+'subClassOf', self.g.p7tm+'BaseTemplateStatement'))

        triples.append(ObjectTriple.insert(self.g, qname+'__desc', kb.rdf_type, self.g.p7tm+'TemplateDescription'))
        triples.append(ObjectTriple.insert(self.g, qname+'__desc', kb.rdf_type, kb.ns_owl+'Thing'))
        triples.append(DatatypeQuad.insert(self.g, qname+'__desc', self.g.p7tm+'valNumberOfRoles', '0', kb.ns_xsd+'integer'))
        triples.append(ObjectTriple.insert(self.g, qname+'__desc', self.g.p7tm+'hasTemplate', qname))

        if anns:
            for k, v in anns.iteritems():
                triples.append(LiteralTriple.insert(self.g, qname, k, v))

        self.triples = [t for t in triples if t]

        wizard.W_EntityCreated(self.g, self.templatedesc['uri'])
        return True

    def Undo(self):
        if not self.triples:
            return

        for t in self.triples:
            t.deletefrom(self.g)

        if not self.g.grTriplesForSubj(self.templatedesc['uri']):
            wizard.W_EntityDestroyed(self.g, self.templatedesc['uri'])
        else:
            wizard.W_EntityPropertiesChanged(self.g, self.templatedesc['uri'])

        self.triples = None


class AddTemplateRole():
    def __init__(self, g, template, role):
        self.g = g
        self.template = template
        self.role = role

    def Redo(self):
        self.triples = []
        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            if not self.g.grIsTemplate(v):
                Notify(tm.main.crossfile_template_specializations_detected)
                return False

        for v in items:
            index = 0
            for a in self.g.grSubjects(self.g.p7tm+'hasTemplate', v):
                if self.g.grHas(a, kb.rdf_type, self.g.p7tm+'TemplateRoleDescription'):
                    prop = self.g.grOneObj(a, self.g.p7tm+'hasRole')
                    if 'name' in self.role and self.role['name'] == self.g.grLiteral(prop, kb.ns_rdfs+'label'):
                        return False
                    for t in self.g.grTriplesForSubj(a):
                        if t.has_literal and t.p == self.g.p7tm+'valRoleIndex':
                            index = max(int(t.l), index)

            self.role['index'] = index + 1
            self.triples += [t for t in self.g.grTemplateRoleTriplesByDesc(v, self.role) if t.insertto(self.g)]

            for t in self.g.grTriplesForSubj(self.g.grTemplateGetDescUri(v)):
                if t.has_literal and t.p == self.g.p7tm+'valNumberOfRoles':
                    t.with_l(str(int(t.l) + 1)).insertto(self.g)
                    t.deletefrom(self.g)
                    break

            wizard.W_TemplateRolesChanged(self.g, v)
            wizard.W_EntityPropertiesChanged(self.g, v)

        return True

    def Undo(self):
        if not self.triples:
            return

        for t in self.triples:
            t.deletefrom(self.g)

        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            for t in self.g.grTriplesForSubj(self.g.grTemplateGetDescUri(v)):
                if t.has_literal and t.p == self.g.p7tm+'valNumberOfRoles':
                    t.with_l(str(int(t.l) - 1)).insertto(self.g)
                    t.deletefrom(self.g)
                    break
            wizard.W_TemplateRolesChanged(self.g, v)
            wizard.W_EntityPropertiesChanged(self.g, v)
        self.triples = None


class DeleteTemplateRole():
    def __init__(self, g, template, role_name):
        self.g = g
        self.template = template
        self.role_name = role_name
        self.index = -1

    def Redo(self):
        objs =set()
        subj = set()
        self.triples = []
        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            if not self.g.grIsTemplate(v):
                Notify(tm.main.crossfile_template_specializations_detected)
                return False

        for v in items:
            triples    = self.g.grCollectTemplateRoleTriples(v, self.role_name)
            self.index = self.g.grGetTemplateRoleIndex(v, self.role_name)

            for a in self.g.grSubjects(self.g.p7tm+'hasTemplate', v):
                if self.g.grHas(a, kb.rdf_type, self.g.p7tm+'TemplateRoleDescription'):
                    for t in self.g.grTriplesForSubj(a):
                        if t.has_literal and t.p == self.g.p7tm+'valRoleIndex':
                            other_index = int(t.l)
                            if self.index < other_index:
                                t.with_l(str(other_index-1)).insertto(self.g)
                                t.deletefrom(self.g)
                                break

            for t in self.g.grTriplesForSubj(self.g.grTemplateGetDescUri(v)):
                if t.has_literal and t.p == self.g.p7tm+'valNumberOfRoles':
                    t.with_l(str(int(t.l) - 1)).insertto(self.g)
                    t.deletefrom(self.g)
                    break

            for a in triples:
                a.deletefrom(self.g)
                subj.add(a.s)
                if a.has_object:
                    objs.add(a.o)

            self.triples += triples
            wizard.W_TemplateRolesChanged(self.g, v)
            wizard.W_EntityPropertiesChanged(self.g, v)

        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

        for s in subj:
            if not self.g.grTriplesForSubj(s):
                wizard.W_EntityDestroyed(self.g, s)

        return True

    def Undo(self):
        if not self.triples:
            return

        items = self.g.grTemplateGetDependencies(self.template)
        for v in items:
            for a in self.g.grSubjects(self.g.p7tm+'hasTemplate', v):
                if self.g.grHas(a, kb.rdf_type, self.g.p7tm+'TemplateRoleDescription'):
                    for t in self.g.grTriplesForSubj(a):
                        if t.has_literal and t.p == self.g.p7tm+'valRoleIndex':
                            other_index = int(t.l)
                            if self.index <= other_index:
                                t.with_l(str(other_index+1)).insertto(self.g)
                                t.deletefrom(self.g)
                                break

            for t in self.g.grTriplesForSubj(self.g.grTemplateGetDescUri(v)):
                if t.has_literal and t.p == self.g.p7tm+'valNumberOfRoles':
                    t.with_l(str(int(t.l) + 1)).insertto(self.g)
                    t.deletefrom(self.g)
                    break

            wizard.W_TemplateRolesChanged(self.g, v)
            wizard.W_EntityPropertiesChanged(self.g, v)

        objs = set()
        for a in self.triples:
            a.insertto(self.g)
            if a.has_object:
                objs.add(a.o)

        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

        self.triples = None


class PasteProperties:
    def __init__(self, g, data):
        self.g = g
        self.data = data

    def Redo(self):
        self.deletions   = set()
        self.skipped     = []
        replace_all      = False
        add_all          = False
        skip_all         = False

        for t in self.data['triples']:
            skip = skip_all
            add  = add_all
            if not skip_all:
                for tt in self.g.grTriplesForSubj(t.s):
                    if t.p == tt.p:
                        if t == tt:
                            skip = True
                        elif tt in self.deletions:
                            continue
                        elif not add:
                            skip    = False
                            replace = replace_all
                            if not replace:
                                res = dialogs.CopyPropertiesNotify(t.s, t.p, tt.v, t.v).exec_()
                                if res == dialogs.CopyPropertiesNotify.RESULT_SKIP:
                                    skip = True
                                elif res == dialogs.CopyPropertiesNotify.RESULT_SKIP_ALL:
                                    skip_all = skip = True
                                elif res == dialogs.CopyPropertiesNotify.RESULT_REPLACE:
                                    replace = True
                                elif res == dialogs.CopyPropertiesNotify.RESULT_REPLACE_ALL:
                                    replace_all = replace = True
                                elif res == dialogs.CopyPropertiesNotify.RESULT_ADD:
                                    add = True
                                elif res == dialogs.CopyPropertiesNotify.RESULT_ADD_ALL:
                                    add_all = add = True

                            if add or skip_all:
                                break
                            elif replace:
                                self.deletions.add(tt)
                                break
            if skip:
                self.skipped.append(t)

        insertions = set(self.data['triples']) - set(self.skipped)
        if not insertions:
            return False

        entities = set()
        for t in self.deletions:
            entities.add(t.s)
            t.deletefrom(self.g)
            if t.has_object:
               wizard.W_EntityRelationshipsChanged(self.g, t.o)

        for t in insertions:
            entities.add(t.s)
            t.insertto(self.g)
            if t.has_object:
               wizard.W_EntityRelationshipsChanged(self.g, t.o)

        for uri in entities:
            wizard.W_EntityCreated(self.g, uri)

        return True

    def Undo(self):
        for t in set(self.data['triples']) - set(self.skipped):
            t.deletefrom(self.g)
            _notify(self.g, t)

        for t in self.deletions:
            t.insertto(self.g)
            _notify(self.g, t)

        del self.deletions
        del self.skipped

class PasteEntities:
    def __init__(self, g, data):
        self.g = g
        self.data = data

    def Redo(self):
        triples = self.data['triples']
        folders = self.data['folders']

        self.accepted  = set()
        self.deletions = []

        rejected       = set()
        insertions     = []

        accept_all = False
        reject_all = False

        for t in triples:
            if t.s in rejected:
                continue

            if t.s not in self.accepted:
                if self.g.grTriplesForSubj(t.s):

                    if reject_all:
                        rejected.add(t.s)
                        continue

                    if not accept_all:
                        res = dialogs.CopyNotify(t.s).exec_()

                        if res == dialogs.CopyNotify.RESULT_NO:
                            rejected.add(t.s)
                            continue
                        if res == dialogs.CopyNotify.RESULT_NO_ALL:
                            reject_all = True
                            rejected.add(t.s)
                            continue
                        if res == dialogs.CopyNotify.RESULT_YES_ALL:
                            accept_all = True

                    self.deletions.append(RemoveEntity(self.g, t.s))

                self.accepted.add(t.s)

            insertions.append(t)

        for v in self.deletions:
            v.Redo()

        for t in insertions:
            t.insertto(self.g)
            if t.has_object:
               wizard.W_EntityRelationshipsChanged(self.g, t.o)

        if not self.accepted:
            return False

        in_folders = set()
        for k, v in folders.iteritems():
            items = v & self.accepted
            wizard.W_FolderCreated(self.g, tm.main.copy_of%k, items = list(items))
            in_folders |= items

        for uri in self.accepted - in_folders:
            wizard.W_EntityCreated(self.g, uri)

        return True

    def Undo(self):
        triples = self.data['triples']
        folders = self.data['folders']

        for k in folders.iterkeys():
            wizard.W_FolderDestroyed(self.g, tm.main.copy_of%k)

        for uri in self.accepted:
            wizard.W_EntityDestroyed(self.g, uri)

        for t in triples:
            if t.s in self.accepted:
                t.deletefrom(self.g)
                if t.has_object:
                    wizard.W_EntityRelationshipsChanged(self.g, t.o)

        for v in self.deletions:
            v.Undo()

        del self.accepted
        del self.deletions

class AddEntity:
    def __init__(self, g, uri, types_uri, label = None, properties = None):
        self.g = g
        self.uri = uri
        self.types_uri = types_uri
        self.label = label
        self.props = properties

    def Redo(self):
        self.type_triples = []
        for v in self.types_uri:
            self.type_triples.append(ObjectTriple.insert(self.g, self.uri, kb.rdf_type, v))
            wizard.W_EntityRelationshipsChanged(self.g, v)

        if self.label:
            self.label_triple = LiteralTriple.insert(self.g, self.uri, kb.rdfs_label, self.label)

        if self.props:
            for t in self.props:
                t.insertto(self.g)
                if t.has_object:
                    wizard.W_EntityRelationshipsChanged(self.g, t.v)

        wizard.W_EntityCreated(self.g, self.uri)

        return True

    def Undo(self):
        if self.type_triples:
            for v in self.type_triples:
                if v:
                    v.deletefrom(self.g)

            for v in self.types_uri:
                wizard.W_EntityRelationshipsChanged(self.g, v)

            if self.label and self.label_triple:
                self.label_triple.deletefrom(self.g)
            
            if self.props:
                for t in self.props:
                    t.deletefrom(self.g)
                    if t.has_object:
                        wizard.W_EntityRelationshipsChanged(self.g, t.v)

            wizard.W_EntityDestroyed(self.g, self.uri)

class RemoveEntity:
    def __init__(self, g, uri):
        self.g = g
        self.uri = uri

    def Redo(self):
        self.uri_list = [self.uri]
        if self.g.grIsTemplate(self.uri):
            specs = self.g.grTemplateGetSpecializations(self.uri)
            if specs:
                if not Choice(tm.main.template_with_spec_delete_query):
                    return False
                self.uri_list += specs

        objs = set()
        subj = set()
        self.triples = []
        for uri in self.uri_list:
            triples = self.g.grCollectEntityTriples(uri)
            self.triples += triples
            for a in triples:
                a.deletefrom(self.g)
                subj.add(a.s)
                if a.has_object:
                    objs.add(a.o)

        if not self.triples:
            return False

        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

        for s in subj:
            if not self.g.grTriplesForSubj(s):
                wizard.W_EntityDestroyed(self.g, s)

        return True

    def Undo(self):
        if not self.triples:
            return

        objs = set()
        for a in self.triples:
            a.insertto(self.g)
            if a.has_object:
                objs.add(a.o)

        for uri in self.uri_list:
            wizard.W_EntityCreated(self.g, uri)
            
        for o in objs:
            wizard.W_EntityRelationshipsChanged(self.g, o)

def _notify(g, t, old_t=None):
    if not g.grTriplesForSubj(t.s):
        wizard.W_EntityDestroyed(g, t.s)
    else:
        wizard.W_EntityPropertiesChanged(g, t.s, prop_new = t, prop_old = old_t)

    if t.has_object:
       wizard.W_EntityRelationshipsChanged(g, t.o)
    if old_t and old_t.has_object:
        wizard.W_EntityRelationshipsChanged(g, old_t.o)

class AddProperty:
    def __init__(self, g, t):
        self.g = g
        self.t = t

    def Redo(self):
        self.done = self.t.insertto(self.g)
        if self.done:
            _notify(self.g, self.t)
            return True
        return False

    def Undo(self):
        if self.done:
            self.t.deletefrom(self.g)
            _notify(self.g, self.t)

class RemoveProperty:
    def __init__(self, g, t):
        self.g = g
        self.t = t

    def Redo(self):
        self.done = self.t.deletefrom(self.g)
        if self.done:
            _notify(self.g, self.t)
            return True
        return False

    def Undo(self):
        if self.done:
            self.t.insertto(self.g)
            _notify(self.g, self.t)

class ChangeProperty:
    def __init__(self, g, t, old_t):
        self.g = g
        self.t = t
        self.old_t = old_t

    def Redo(self):
        self.deleted = self.old_t and self.old_t.deletefrom(self.g)
        self.inserted = self.t.insertto(self.g)
        _notify(self.g, self.t, self.old_t)
        return True

    def Undo(self):
        if self.inserted:
            self.t.deletefrom(self.g)
        if self.deleted:
            self.old_t.insertto(self.g)
        _notify(self.g, self.old_t, self.t)
