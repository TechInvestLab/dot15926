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
class GeomImporter:

    def __init__(self, target_doc, import_source):
        self.source_path                    = import_source[0]
        self.target_doc                     = target_doc
        self.DoImport()

    def InitEnvironment(self):
        environment     = appdata.environment_manager.GetWorkEnvironment(self.target_doc, include_builder=True)
        self.builder    = environment.get('builder', None)
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

        name_defs = {}
        
        base_templ = {}

        ann_targets = set()
        builder.set_uuid_prefix('R-')

        @rd.SafeRows('Class')
        def f(r):
            id = r.text('ID')
            label = r.text('Label')
            if label and id:
                name_defs[label] = id

        @rd.SafeRows('Base Template')
        def f(r):

            templateid = r.text('TemplateID')
            templatename = r.text('TemplateName')
            templatedescr = r.text('TemplateDescription')
            base_templ[templatename] = templateid
            ann_targets.add(builder.template(id = templateid, name = templatename, comment = templatedescr))

            for i in xrange(1,8):
                idx = 'Role{0}'.format(i)
                roleid = r.text('{0}ID'.format(idx))
                rolename = r.text('{0}Name'.format(idx))
                if not rolename:
                    continue
                roledesc = r.text('{0}Description'.format(idx))
                rolevalue = r.text('{0}Value'.format(idx))
                roletype = r.text('{0}Type'.format(idx))
                if roletype.startswith('xsd:'):
                    roletype = kb.ns_xsd+roletype[4:]
                else:
                    roletype = name_defs.get(roletype)
                ann_targets.add(builder.template_role(roleid = roleid, name = rolename, comment = roledesc, type = roletype, value = name_defs.get(rolevalue)))
        
        for uri in ann_targets:
            if self.target_doc.uri_from_names:
                builder.annotate(id = uri, defaultRdsId = builder.UUID('R-'))
            else:
                builder.annotate(id = uri, defaultRdsId = kb.split_uri(uri)[1])
