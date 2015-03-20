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
from iso15926.io.rdf_base import ObjectTriple, LiteralTriple
from copy import deepcopy
import uuid

class Builder(object):
    def __init__(self, doc):
        self.doc = doc
        self.lasttemplateid = None

    def collect(self, **props):
        if 'type' in props:
            itemtype = props.pop('type')
            if getattr(itemtype, 'collect', None):
                return itemtype.collect(self.doc, props)
        return set()
        
    def set_uuid_prefix(self, pre):
        self.doc.uuid_prefix = pre

    def UUID(self, pre):
        return pre+str(uuid.uuid4())

    def template(self, **props):
        itemid = props.get('id')
        name   = props.get('name')

        if not itemid:
            itemid = self.doc.infGenerateTemplateUri(name)

        if props.get('delete'):
            for t in self.doc.grCollectEntityTriples(itemid):
                t.deletefrom(t)
            return

        entity = self.doc.grTemplateGetDesc(itemid)
        if not entity:
            entity          = dict(uri=itemid,name='unnamed',comment='')
            entity['uri']   = itemid

        if name:
            entity['name']  = name

        comment = props.get('comment')
        if comment:
            entity['comment']  = comment

        sup = props.get('super')
        if sup:
            entity['supertemplate'] = sup

        self.doc.grUpdateTemplateByDesc(entity)
        self.doc.AsyncChangeState(self.doc.state_changed)

        self.lasttemplateid = itemid
        return itemid

    def template_role(self, **props):
        itemid = props.get('id', self.lasttemplateid)
        if not itemid:
            return

        template  = self.doc.grTemplateGetDesc(itemid, True)
        if not template:
            return

        name = props.get('name')
        if not name:
            return

        role = template['roles'].get(name)        
        superrole = None
        
        sup = template.get('supertemplate')
        if sup:
            supertemplate = self.doc.grTemplateGetDesc(sup, True)
            superrole     = supertemplate['roles'].get(name)

        if props.get('delete') and role:
            self.doc.grDeleteTemplateRole(itemid, role['uri'])
            return

        if not role:
            role = dict(name=name,comment='',type_uri=kb.ns_xsd+'string',is_literal=True,restricted_by_value=False, index = len(template['roles'])+1)

        old_uri = role.get('uri')
        roleid = props.get('roleid')
        if not roleid:
            if not role.get('uri'):
                role['uri'] = self.doc.infGenerateTemplateRoleUri(role.get('name'))
        else:
            role['uri'] = roleid

        tp = props.get('type')
        if tp:
            if not isinstance(tp, basestring):
                tp = tp.uri
            role['type_uri']    = tp
            role['is_literal']  = tp.startswith(kb.ns_xsd)

        comment = props.get('comment')
        if comment:
            role['comment'] = comment

        value = props.get('value')
        if value:
            role['type_uri']            = value
            role['restricted_by_value'] = True
        else:
            role['restricted_by_value'] = False

        if old_uri:
            for t in self.doc.grCollectTemplateRoleTriples(itemid, name, old_uri == role['uri']):
                t.deletefrom(self.doc)

        for t in self.doc.grTemplateRoleTriplesByDesc(itemid, role):
            t.insertto(self.doc)

        self.doc.AsyncChangeState(self.doc.state_changed)

        return role['uri']

    def __call__(self, **props):
        itemid   = props.pop('id', None)
        edit     = props.pop('edit', False)
        itemtype = None

        objprops, dtprops, untranslated = ({}, {}, props)
        if 'type' in props:
            itemtype = props.pop('type')
            if getattr(itemtype, 'build', None):
                return itemtype.build(self.doc, props)
            if getattr(itemtype, 'translate_props', None):
                objprops, dtprops, untranslated = itemtype.translate_props(untranslated, for_build = True)
            else:
                if itemtype:
                    objprops, dtprops, untranslated = self.doc.translate_type_props(set([itemtype]), untranslated)
                objprops[kb.rdf_type] = itemtype
        
        objprops, dtprops, untranslated = self.doc.translate_props(untranslated, objprops, dtprops)

        if itemid is None:
            itemid = self.doc.infGenerateUri()

            for k, v in objprops.iteritems():
                ObjectTriple.insert(self.doc, itemid, k, v)

            for k, v in dtprops.iteritems():
                LiteralTriple.insert(self.doc, itemid, k, v)

        else:
            triples = self.doc.grTriplesForSubj(itemid)

            types = set()
            for t in triples:
                if t.p==kb.rdf_type:
                    types.add(t.o)

            todelete = set()
            if edit and kb.rdf_type in objprops:
                skiproles = set()
                if objprops[kb.rdf_type] != None:
                    for v in self.doc.infGetAvailableRoles([objprops[kb.rdf_type]]).values():
                        skiproles.add(v['uri'])
                for v in self.doc.infGetAvailableRoles(types).values():
                    if v['uri'] not in skiproles:
                        todelete.add(v['uri'])
                types.clear()
                
            if types:
                objprops, dtprops, untranslated = self.doc.translate_type_props(types, untranslated, objprops, dtprops)
            
            if edit:
                for t in triples:
                    if t.p in objprops or t.p in dtprops or t.p in todelete:
                        t.deletefrom(self.doc)

            for k, v in objprops.iteritems():
                if v:
                    ObjectTriple.insert(self.doc, itemid, k, v)
    
            for k, v in dtprops.iteritems():
                if v:
                    LiteralTriple.insert(self.doc, itemid, k, v)

        if getattr(itemtype, 'template', None):
            ObjectTriple.insert(self.doc, itemid, kb.rdf_type, kb.ns_owl+'Thing')

        self.doc.AsyncChangeState(self.doc.state_changed)

        return itemid

    def annotate(self, **props):
        return self.build_main({}, {}, props)

    def edit(self, **props):
        return self(edit = True, **props)

    def delete(self, items):
        if items:
            if isinstance(items, basestring):
                items = set([items])
        else:
            return

        for v in items:
            triples = set(self.doc.grTriplesForSubj(v))           
            for a in triples:
                a.deletefrom(self.doc)
            wizard.W_EntityDestroyed(self.doc, v)

        self.doc.AsyncChangeState(self.doc.state_changed)

    def role(self, **props):
        itemid = props.pop('id', None)

        if not itemid:
            return

        itemprops = self.doc.grTriplesForSubj(itemid)
        types = set()

        for t in itemprops:
            if t.p==kb.rdf_type:
                types.add(t.o)

        roles = self.doc.infGetAvailableRoles(types)

        if not roles:
            log('Instance \'{0}\' does not have any roles\n'.format(itemid))
            return

        objprops           = {}
        dtprops            = {}
        untranslated       = {}
        untranslated['id'] = itemid     

        for k, v in props.iteritems():
            found = False
            for r in roles.itervalues():
                if r['name'] == k:
                    if r:
                        if r['is_literal']:
                            dtprops[r['uri']] = v
                        else:
                            objprops[r['uri']] = v
                        found = True
                        break
            if not found:
                log('Role \'{0}\' not found for instance \'{1}\'\n'.format(k, itemid))
                        
        return self.build_main(objprops, dtprops, untranslated)

    def build_main(self, objprops, dtprops, untranslated):
        itemid = untranslated.pop('id', None)

        objprops, dtprops, untranslated = self.doc.translate_props(untranslated, objprops, dtprops)

        if itemid is None:
            itemid = self.doc.infGenerateUri()

        # undo/redo in the future?

        for k, v in objprops.iteritems():
            ObjectTriple.insert(self.doc, itemid, k, v)

        for k, v in dtprops.iteritems():
            LiteralTriple.insert(self.doc, itemid, k, v)

        self.doc.AsyncChangeState(self.doc.state_changed)

        return itemid