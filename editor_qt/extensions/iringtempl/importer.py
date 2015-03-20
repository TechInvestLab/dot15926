"""Copyright 2012 TechInvestLab.ru dot15926@gmail.com

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

import datetime
import excel_reader
import iso15926.kb as kb
from iso15926 import SparqlConnection
from iso15926 import GraphDocument

@public('dot15926.importers')
class IRingImporter:

    def __init__(self, target_doc, import_source):
        self.source_path                    = import_source[0]
        self.target_doc                     = target_doc

        #self.jord_sparql = GraphDocument.FindDocumentByPaths(['http://posccaesar.org/endpoint/sparql'])
        #if not self.jord_sparql:
        #    self.jord_sparql = GraphDocument()
        #    self.jord_sparql.OpenSparql(SparqlConnection('http://posccaesar.org/endpoint/sparql'), **(dict(chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_sparql, module_name = 'jord_sparql', roles = kb.roles_pcardl_sparql)))
        #    appdata.project.AddDocument(self.jord_sparql)
        #else:
        #    self.jord_sparql.UpdateProps(dict(module_name = 'jord_sparql'))

        self.DoImport()

    def InitEnvironment(self):
        environment     = appdata.environment_manager.GetWorkEnvironment(self.target_doc, include_builder=True)
        self.builder    = environment.get('builder', None)
        #self.jord       = environment.get('jord_sparql', None)
        return self.builder

    def DoImport(self):
        if not self.InitEnvironment():
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            return

        @public.wth(tm.ext.importing_doc.format(self.target_doc.name), self.target_doc)
        def f():
            try:
                self.rd = excel_reader.ExcelReader(self.source_path)
                self.ProcessModel()
                @public.mth
                def f2():
                    self.target_doc.ChangeState(self.target_doc.state_changed)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.target_doc.ChangeState(self.target_doc.state_importfailed)

    def ProcessModel(self):
        rd = self.rd
        builder = self.builder
        #jord = self.jord

        name_defs = {}
        
        base_templ = {}

        @rd.SafeRows('Class')
        def f(r):
            id = r.text('ID')
            label = r.text('Label')
            if label and id:
                name_defs[label] = id

        #ids = set(name_defs.values())
        #eq = jord.find_uri_wip_eq(ids)

        #for k, v in name_defs.iteritems():
        #    if v in eq:
        #        name_defs[k] = eq[v]

        ann_targets = set()
        info = {'ignored': 0}

        @rd.SafeRows('Base Template')
        def f(r):
            templateid = r.text('TemplateID')
            if not templateid:
                info['ignored'] += 1
                return
            for i in xrange(1,8):
                idx = 'Role{0}'.format(i)
                rolename = r.text('{0} Name'.format(idx))
                if not rolename:
                    continue
                roleid = r.text('{0} ID'.format(idx))
                if not roleid:
                    info['ignored'] += 1
                    return

            templatename = r.text('Template Name')
            templatedescr = r.text('Template Description')
            base_templ[templatename] = templateid
            ann_targets.add(templateid)
            builder.template(id = templateid, name = templatename, comment = templatedescr)

            for i in xrange(1,8):
                idx = 'Role{0}'.format(i)
                roleid = r.text('{0} ID'.format(idx))
                rolename = r.text('{0} Name'.format(idx))
                if not rolename:
                    continue
                roledesc = r.text('{0} Description'.format(idx))
                rolevalue = r.text('{0} Value'.format(idx))
                roletype = r.text('{0} Type'.format(idx))
                ann_targets.add(roleid)
                builder.template_role(roleid = roleid, name = rolename, comment = roledesc, type = name_defs.get(roletype), value = name_defs.get(rolevalue))

        @rd.SafeRows('Specialized Individual Template')
        def f(r):
            templateid = r.text('TemplateID')
            if not templateid:
                info['ignored'] += 1
                return
            for i in xrange(1,8):
                idx = 'Role{0}'.format(i)
                rolename = r.text('{0} Name'.format(idx))
                if not rolename:
                    continue
                roleid = r.text('{0} ID'.format(idx))
                if not roleid:
                    info['ignored'] += 1
                    return

            templatename = r.text('Template Name')
            templatedescr = r.text('Template Description')
            supertempl = r.text('Parent Template')
            ann_targets.add(templateid)
            builder.template(id = templateid, super = base_templ[supertempl], name = templatename, comment = templatedescr)

            for i in xrange(1,8):
                idx = 'Role{0}'.format(i)
                roleid = r.text('{0} ID'.format(idx))
                rolename = r.text('{0} Name'.format(idx))
                if not rolename:
                    continue
                roledesc = r.text('{0} Description'.format(idx))
                rolevalue = r.text('{0} Value'.format(idx))
                roletype = r.text('{0} Type'.format(idx))
                ann_targets.add(roleid)
                builder.template_role(roleid = roleid, name = rolename, comment = roledesc, type = name_defs.get(roletype), value = name_defs.get(rolevalue))
        
        for uri in ann_targets:
            builder.annotate(id = uri, defaultRdsId = kb.split_uri(uri)[1])

        log('Templates ignored: {0}\n', info['ignored'])