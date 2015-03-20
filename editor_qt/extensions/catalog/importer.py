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


"""
Catalog importer adapter.
Import mechanism uses Builder API.
Importer does it job on file creation, so importer constructor has fixed arguments.

"""

import datetime
from iso15926.graph.graph_document import GraphDocument
import iso15926.kb as kb
import json

"""Any importer must register self by @public('dot15926.importers') decorator"""
@public('dot15926.importers')
class CatalogImporter:

    def __init__(self, target_doc, import_source):
        """Constructor for importer has fixed arguments"""

        self.attr_inheritance               = appconfig.get('catalog.attr_inheritance')
        self.source_path                    = import_source[0]
        self.target_doc                     = target_doc
        self.enviponment_prepeared          = self.PrepareEnvironment()
        self.DoImport()

    def DoImport(self):
        if not self.enviponment_prepeared:
            return

        if not self.InitEnvironment():
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            return

        @public.wth('Importing {0}...'.format(self.target_doc.name), self.target_doc, self.p7tpl_doc, self.pcardl_doc)
        def f():
            try:
                with open(self.source_path, 'r') as f:
                    self.data = json.load(f, 'windows-1251')
                self.ProcessModel()
                @public.mth
                def f2():
                    self.target_doc.ChangeState(self.target_doc.state_changed)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.target_doc.ChangeState(self.target_doc.state_importfailed)

    def InitEnvironment(self):
        """Initilizes environment.

        Environment is generally the same as console local variables,
        so acces to them by module names and keywords like 'builder'.
        '"""

        environment = appdata.environment_manager.GetWorkEnvironment(self.target_doc, include_builder=True)

        self.builder        = environment.get('builder', None)
        self.part2          = environment.get('part2', None)
        self.p7tpl          = environment.get(self.p7tpl_doc.module_name, None)

        return self.builder and self.part2 and self.p7tpl

    def PrepareEnvironment(self):
        """Prepeares environment for import.
        
        Here opened all files needed by import.
        To check file is already opened here used FindDocumentByPaths document method.
        """

        if not bool(appconfig.get('paths.p7tpl_catalog') and appconfig.get('paths.rdl_catalog') and appconfig.get('catalog.proj_ns')):
            log('Import error: Catalog dependencies not set!\n')            
            return False

        self.target_doc.UpdateProps({'basens': appconfig.get('catalog.proj_ns')})

        self.p7tpl_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.p7tpl_catalog')])
        if not self.p7tpl_doc:
            self.p7tpl_doc = GraphDocument()
            param = dict(name="Template set (Catalog)", chosen_part2=kb.ns_dm_part8, module_name="p7tpl")
            self.p7tpl_doc.OpenFiles([appconfig.get('paths.p7tpl_catalog')], **param)
            appdata.project.AddDocument(self.p7tpl_doc)

        self.pcardl_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.rdl_catalog')])
        if not self.pcardl_doc:
            self.pcardl_doc = GraphDocument()
            param = dict(name='RDL (Catalog)', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf)
            self.pcardl_doc.OpenFiles([appconfig.get('paths.rdl_catalog')], **param)
            appdata.project.AddDocument(self.pcardl_doc)

        ready = True

        """If file needed to be loaded, subscribe on it's events."""

        if not self.p7tpl_doc.CanView():
            wizard.Subscribe(self.p7tpl_doc, self)
            ready = False

        if not self.pcardl_doc.CanView():
            wizard.Subscribe(self.pcardl_doc, self)
            ready = False

        return ready

    def W_DocumentStateChanged(self, doc):
        """This handler detects that necessary files were loaded succesfully."""

        if doc.CanView(): 
            wizard.Unsubscribe(doc, self)
        elif doc.IsUnavailable():
            log('Import error: {0} unavailable!\n', doc.name)
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            wizard.Unsubscribe(doc, self)
        if self.p7tpl_doc.CanView() and self.pcardl_doc.CanView():
            self.enviponment_prepeared = True
            appdata.app.After(self.DoImport)

    def GetUnitByDesc(self, attribute):

        unit_type = attribute['unit']

        if unit_type == '':
            return None

        if unit_type in self.unit_generated:
            return self.unit_generated[unit_type]

        else:
            unit_item = self.part2.Scale()
            self.builder.annotate(id = unit_item, label=unit_type)
            self.unit_generated[unit_type] = unit_item
            return unit_item

    def GetAttributeById(self, attr_id):
        if attr_id in self.attr_generated:
            return self.attr_generated[attr_id]
        return None

    def GetAttributeByDesc(self, attribute):

        attr_id   = attribute['id']

        if attr_id == '':
            return None

        if attr_id in self.attr_generated:
            return self.attr_generated[attr_id]

        else:
            item    = None
            type    = attribute['type']

            if type == 'string':
                item = self.part2.ClassOfClassOfIndividual()
                self.builder.annotate(id = item, label=attr_id)

            elif type == 'real':
                item = self.part2.ClassOfIndirectProperty()
                self.builder.annotate(id = item, label=attr_id)

            elif type == 'integer':
                item = self.part2.EnumeratedPropertySet()
                self.builder.annotate(id = item, label=attr_id)

            elif type == 'date/time':
                item_a = self.part2.RoleAndDomain()
                self.builder.annotate(id = item_a, label="POSSESOR_OF_"+attr_id)
                self.attr_generated["POSSESOR_OF_"+attr_id] = item_a
                item_b = self.part2.RoleAndDomain()
                self.builder.annotate(id = item_b, label="RANGE_OF_"+attr_id)
                self.attr_generated["RANGE_OF_"+attr_id] = item_b
                self.p7tpl.Specialization(item_b, "http://posccaesar.org/rdl/RDS16432820")

                item = self.part2.ClassOfRelationshipWithSignature(hasClassOfEnd1 = item_a, hasClassOfEnd2 = item_b)

                self.builder.annotate(id = item, label=attr_id)

            elif type == 'reference':
                item = self.part2.ClassOfClassOfIndividual()
                self.builder.annotate(id = item, label=attr_id)

            else:
                return None

            self.part2.Classification(hasClassified=item, hasClassifier=self.attr_type)
            self.RusIdent(item, attribute['name'])

            self.attr_generated[attr_id] = item

            return item

    def ProcessAttribute(self, attribute, class_item):

        attr_item = self.GetAttributeByDesc(attribute)
        unit_item = self.GetUnitByDesc(attribute)

        if attr_item:
            type    = attribute['type']
            if type == 'string':
                self.p7tpl.ClassOfClassification(class_item, attr_item)
            elif type == 'real' and unit_item:
                self.p7tpl.PropertyRangeTypeRestrictionOfClass(class_item, attr_item, unit_item)
            elif type == 'integer':
                self.p7tpl.ClassOfClassification(class_item, attr_item)
            elif type == 'date/time':
                attr_id = "POSSESOR_OF_"+attribute['id']
                self.part2.Specialization(hasSubclass=class_item, hasSuperclass=self.GetAttributeById(attr_id))
            elif type == 'reference':
                self.p7tpl.ClassOfClassification(class_item, attr_item)
            else:
                pass
 
    def ReadClass(self, classnode, parent_attributes = [], parent_class = None):

        if classnode['id'] == '':
            return

        if self.attr_inheritance:
            attributes = parent_attributes[:]
        else:
            attributes = []

        class_item = self.part2.ClassOfIndividual()
        self.builder.annotate(id = class_item, label=classnode['id'])

        if parent_class:
            self.part2.Specialization(hasSubclass=class_item, hasSuperclass=parent_class)

        self.part2.Classification(hasClassified=class_item, hasClassifier=self.eq_class)
        self.RusIdent(class_item, classnode['name'])

        if 'attributes' in classnode:
            class_attributes = classnode['attributes']
            if type(class_attributes)==type(list()):
                attributes[len(attributes):] = class_attributes
            elif type(class_attributes)==type(dict()):
                attributes[len(attributes):] = [class_attributes]
            else:
                log("err!!")

        for subitem in attributes:
            self.ProcessAttribute(subitem, class_item)

        if 'subClasses' in classnode:
            class_subclasses = classnode['subClasses']
            if type(class_subclasses)==type(list()):
                for subitem in class_subclasses:
                    self.ReadClass(subitem, attributes, class_item)
            elif type(class_subclasses)==type(dict()):
                self.ReadClass(class_subclasses, attributes, class_item)
            else:
                log("err!!")

    def ProcessModel(self):

        self.ru_ident = self.part2.ClassOfClassOfIdentification()
        self.builder.annotate(id = self.ru_ident, label='CATALOG RUSSIAN IDENTIFICATION')

        self.attr_type = self.part2.ClassOfClass()
        self.builder.annotate(id = self.attr_type, label='CATALOG ATTRIBUTE TYPE')

        self.eq_class = self.part2.ClassOfClassOfIndividual()
        self.builder.annotate(id = self.eq_class, label='CATALOG EQUIPMENT CLASS')

        data = self.data
        self.attr_generated = {}
        self.unit_generated = {}
        self.ReadClass(data)

    def RusIdent(self, item, name):
        exs = self.part2.ExpressString()
        self.builder.annotate(id = exs, label=name)
        coi = self.part2.ClassOfIdentification(hasRepresented=item, hasPattern=exs)
        self.p7tpl.Classification(coi, self.ru_ident)
