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
from iso15926.graph.graph_document import GraphDocument
from iso15926.io.rdf_base import *

class cardinalities_cnt:
    # pseudo-dictionary for converting cardinalities
    def get(self, key, default):
        try:
            vmin, vmax = key.strip('()').split(':')
            return (vmin, vmax)
        except:
            return default

@public('dot15926.importers')
class TabLanImporter:

    def __init__(self, target_doc, import_source):

        self.source_path                    = import_source[0]
        self.target_doc                     = target_doc
        self.enviponment_prepeared          = self.PrepareEnvironment()


        self.part2names = {}
        for (k, v) in kb.part2_itself.iteritems():
            self.part2names[v['name']] = v['name']

        self.cardinalities = cardinalities_cnt()
        self.relations = {}
        for k in dir(self):
            if k.startswith('R_'):
                self.relations[k[2:].replace('_', ' ')] = getattr(self, k)

        self.DoImport()

    def DoImport(self):

        if not self.enviponment_prepeared:
            return

        if not self.InitEnvironment():
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            return

        @public.wth(tm.ext.importing_doc.format(self.target_doc.name), self.target_doc, self.p7tpl_doc, self.pcardl_doc)
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


    def InitEnvironment(self):
        environment         = appdata.environment_manager.GetWorkEnvironment(self.target_doc, include_builder=True)
        self.builder        = environment.get('builder', None)
        self.part2          = environment.get('part2', None)
        self.p7tpl          = environment.get(self.p7tpl_doc.module_name, None)
        return self.builder and self.part2 and self.p7tpl

    def PrepareEnvironment(self):

        if not bool(appconfig.get('paths.p7tpl_tablan') and appconfig.get('paths.rdl_tablan') and appconfig.get('tablan.proj_ns')):
            log('Import error: TabLan dependencies not set!\n')
            return False

        self.target_doc.UpdateProps({'basens': appconfig.get('tablan.proj_ns')})

        self.p7tpl_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.p7tpl_tablan')])
        if not self.p7tpl_doc:
            self.p7tpl_doc = GraphDocument()
            param = dict(name="Template set (TabLan)", chosen_part2=kb.ns_dm_part8, module_name="p7tpl")
            self.p7tpl_doc.OpenFiles([appconfig.get('paths.p7tpl_tablan')], **param)
            appdata.project.AddDocument(self.p7tpl_doc)

        self.pcardl_doc = GraphDocument.FindDocumentByPaths([appconfig.get('paths.rdl_tablan')])
        if not self.pcardl_doc:
            self.pcardl_doc = GraphDocument()
            param = dict(name='RDL (TabLan)', chosen_part2=kb.ns_dm_part2, namespaces=kb.namespaces_std, annotations=kb.annotations_pcardl_rdf)
            self.pcardl_doc.OpenFiles([appconfig.get('paths.rdl_tablan')], **param)
            appdata.project.AddDocument(self.pcardl_doc)

        ready = True

        if not self.p7tpl_doc.CanView():
            wizard.Subscribe(self.p7tpl_doc, self)
            ready = False

        if not self.pcardl_doc.CanView():
            wizard.Subscribe(self.pcardl_doc, self)
            ready = False

        return ready

    def W_DocumentStateChanged(self, doc):
        if doc.CanView(): 
            wizard.Unsubscribe(doc, self)
        elif doc.IsUnavailable():
            log('Import error: {0} unavailable!\n', doc.name)
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            wizard.Unsubscribe(doc, self)
        if self.p7tpl_doc.CanView() and self.pcardl_doc.CanView():
            self.enviponment_prepeared = True
            appdata.app.After(self.DoImport)

    def ProcessModel(self):

        rd = self.rd

        ids = {}
        ru_names = {}
        en_names = {}
        doc_names = {}

        def is_section(r):
            return r.text('Section')!=''

        # classes creation

        @rd.SafeRows('Class Definitions')
        def f(r):
            if is_section(r): return

            class_id = r.text('URI')
            ru_name = r.text('Russian Unique Class Name')
            en_name = r.text('English Unique Class Name')

            if not en_name and not ru_name:
                r.row_error('Russian or english name is required for every class')

            if class_id.startswith('rdl:'):
                class_id = 'http://posccaesar.org/rdl/'+class_id[4:]
            elif class_id.startswith('til:'):
                class_id = 'http://techinvestlab.ru/data#'+class_id[4:]
            else:
                p2type = r.known('Part 2 Type', self.part2names)
                class_id = getattr(self.part2, p2type)()
                if en_name:
                    self.builder.annotate(id = class_id, label=en_name, label_en=en_name)
                if ru_name:
                    if not en_name:
                        self.builder.annotate(id = class_id, label=ru_name, label_ru=ru_name)
                    else:
                        self.builder.annotate(id = class_id, label_ru=ru_name)
                source = r.nonempty('Source')
                self.builder.annotate(id = class_id, annSource=source)
            #else:
            #    r.row_error('Wrong URI field')

            if en_name:
                en_names[class_id] = en_name
                ids[en_name] = class_id
            if ru_name:
                ru_names[class_id] = ru_name
                ids[ru_name] = class_id

        # for later use
        self.EmptyClass = ids['EmptyClass']
        
        # structure model creation

        @rd.SafeRows('Structure Model')
        def f(r):
            if is_section(r): return

            item_name = r.text('Item ID')
            if not item_name:
                return

            item = self.part2.ClassOfInformationObject()
            doc_names[item] = item_name
            ids[item_name] = item
            self.builder.annotate(id = item, label=item_name)
            
        self.was_item = None

        # structure model specification

        @rd.SafeRows('Structure Model')
        def f(r):
            if is_section(r): return

            item = r.known_or_empty('Item ID', ids)

            if not item:
                item = self.was_item

                classifier = r.known_or_empty('Classifier Class', ids)
                if classifier:
                    self.part2.Classification(hasClassified=item, hasClassifier=classifier)

                subject = r.known_or_empty('Item Subject', ids)
                if subject:
                    self.p7tpl.DescriptionByInformationObject(subject, item)
                return
            else:
                self.was_item = item

            item_class = r.known('Item Class', ids)
            text = r.nonempty('Item Text')
            whole = r.known_or_empty('Item of Whole', ids)
            classifier = r.known_or_empty('Classifier Class', ids)
            subject = r.known_or_empty('Item Subject', ids)

            if text:
                self.builder.annotate(id = item, annTextDefinition=text)

            self.part2.Specialization(hasSubclass=item, hasSuperclass=item_class)
            if classifier:
                self.part2.Classification(hasClassified=item, hasClassifier=classifier)
            if whole:
                self.p7tpl.ClassOfArrangementOfIndividual(item, whole)
            if subject:
                self.p7tpl.DescriptionByInformationObject (subject,item)

        # classes specification

        @rd.SafeRows('Class Definitions')
        def f(r):
            if is_section(r): return

            ru_name = r.text('Russian Unique Class Name')
            en_name = r.text('English Unique Class Name')
            if ru_name:
                class_id = ids[ru_name]
            else:
                class_id = ids[en_name]

            superclass = r.known_or_empty('Superclass', ids)
            classifier = r.known_or_empty('Classifier Class', ids)

            if superclass:
                self.part2.Specialization(hasSubclass=class_id, hasSuperclass=superclass)
            if classifier:
                self.part2.Classification(hasClassified=class_id, hasClassifier=classifier)

        # properties

        @rd.SafeRows('Class Properties')
        def f(r):
            if is_section(r): return

            # now
            class_id = r.known('Class Name', ids)
            prop = r.known('Property Name', ids)
            ind_prop = r.known_or_empty('Indirect Property Name', ids)
            vmin = r.nonempty('Property Min')
            vmax = r.nonempty('Property Max')
            source = r.nonempty('Source')

            pr_min = ids.get(vmin)
            if pr_min is None:
                pr_min = self.part2.Property(label=vmin)
                ids[vmin] = pr_min

            pr_max = ids.get(vmax)
            if pr_max is None:
                pr_max = self.part2.Property(label=vmax)
                ids[vmax] = pr_max

            rng = self.part2.PropertyRange(annSource=source)
            self.part2.Specialization(hasSubclass=rng, hasSuperclass=prop, annSource=source)
            self.p7tpl.LowerUpperOfPropertyRange(rng, pr_min, pr_max, annSource=source)
            
            if ind_prop:
                self.p7tpl.PropertyRangeRestrictionOfClass(class_id, ind_prop, rng, annSource=source)
            else:
                self.part2.ClassOfClassification(hasClassOfClassified=class_id, hasClassOfClassifier=rng, annSource=source)

        # classifiers

        @rd.SafeRows('Classifier Definition')
        def f(r):
            if is_section(r): return

            class_id = r.known('Class Name', ids)
            superclass = r.known_or_empty('Superclass Name', ids)
            rel_class = r.known_or_empty('Classifier Relationship Class', ids)
            class_class = r.known_or_empty('Class of Classifier Classes', ids)
            source = r.nonempty('Source')

            if superclass:
                rel_id = self.part2.Specialization(hasSubclass=class_id, hasSuperclass=superclass, annSource=source)
                if rel_class:
                    self.part2.Classification(hasClassified=rel_id, hasClassifier=rel_class, annSource=source)
            if class_class:
                self.part2.Classification(hasClassified=class_id, hasClassifier=class_class, annSource=source)

        # breakdown

        @rd.SafeRows('Breakdown Definition')
        def f(r):
            if is_section(r): return

            class_id = r.known('Class Name', ids)
            whole_class = r.known_or_empty('Whole Class Name', ids)
            rel_class = r.known_or_empty('Breakdown Relationship Class', ids)
            class_class = r.known_or_empty('Class of Breakdown Classes', ids)
            source = r.nonempty('Source')

            if whole_class:
                rel_id = self.part2.ClassOfCompositionOfIndividual(hasClassOfPart=class_id, hasClassOfWhole=whole_class, annSource=source)
                if rel_class:
                    self.part2.Classification(hasClassified=rel_id, hasClassifier=rel_class, annSource=source)
            if class_class:
                self.part2.Classification(hasClassified=class_id, hasClassifier=class_class, annSource=source)

        # relationships

        @rd.SafeRows('Other Relationships')
        def f(r):
            if is_section(r): return

            role1 = r.known('Role 1', ids)
            role1c = r.known_or_empty('Role 1 Cardinality', self.cardinalities)
            rel_code = r.known('Relates to', self.relations)
            role2 = r.known('Role 2', ids)
            role2c = r.known_or_empty('Role 2 Cardinality', self.cardinalities)
            source = r.nonempty('Source')

            rel_id = rel_code(role1, role2, role1c, role2c, source)

        # requirements

        @rd.SafeRows('Requirements')
        def f(r):
            if is_section(r): return

            status = r.known('Statement Classification', ids)
            role1 = r.known('Role 1', ids)
            role1c = r.known_or_empty('Role 1 Cardinality', self.cardinalities)
            rel_code = r.known('Relates to', self.relations)
            role2 = r.known('Role 2', ids)
            role2c = r.known_or_empty('Role 2 Cardinality', self.cardinalities)
            source = r.nonempty('Source')

            rel_id = rel_code(role1, role2, role1c, role2c, source)

            if rel_id:
                if type(rel_id)==tuple:
                    rel_id = rel_id[0]
                    self.part2.Specialization(hasSubclass=rel_id, hasSuperclass=status, annSource=source)
                else:
                    self.part2.Classification(hasClassified=rel_id, hasClassifier=status, annSource=source)

    def R_is_described_by(self, role1, role2, role1c, role2c, source):
        pi = self.part2.PossibleIndividual(annSource=source)
        self.part2.Classification(hasClassified=pi, hasClassifier=role2, annSource=source)
        rel_id = self.part2.Description(hasRepresented=role1, hasSign=pi, annSource=source)
        return rel_id

    def R_participates_in(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.ClassOfCompositionOfIndividual(hasClassOfPart=role1, hasClassOfWhole=role2, annSource=source)
        if role1c is not None:
            if role1c[1] == "*":
                 self.p7tpl.CardinalityEnd1Min(rel_id, role1c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd1MinMax(rel_id, role1c[0], role1c[1], annSource=source)
        if role2c is not None:
            if role2c[1] == "*":
                 self.p7tpl.CardinalityEnd2Min(rel_id, role2c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd2MinMax(rel_id, role2c[0], role2c[1], annSource=source)
        return rel_id, 1

    def R_is_a_predecessor_in_time_of(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.ClassOfTemporalSequence(hasClassOfPredecessor=role1, hasClassOfSuccessor=role2, annSource=source)
        if role1c is not None:
            if role1c[1] == "*":
                 self.p7tpl.CardinalityEnd1Min(rel_id, role1c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd1MinMax(rel_id, role1c[0], role1c[1], annSource=source)
        if role2c is not None:
            if role2c[1] == "*":
                 self.p7tpl.CardinalityEnd2Min(rel_id, role2c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd2MinMax(rel_id, role2c[0], role2c[1], annSource=source)
        return rel_id, 1

    def R_has_as_part(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.ClassOfCompositionOfIndividual(hasClassOfPart=role2, hasClassOfWhole=role1, annSource=source)
        if role1c is not None:
            if role1c[1] == "*":
                 self.p7tpl.CardinalityEnd1Min(rel_id, role1c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd1MinMax(rel_id, role1c[0], role1c[1], annSource=source)
        if role2c is not None:
            if role2c[1] == "*":
                 self.p7tpl.CardinalityEnd2Min(rel_id, role2c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd2MinMax(rel_id, role2c[0], role2c[1], annSource=source)
        return rel_id, 1

    def R_is_disjoint(self, role1, role2, role1c, role2c, source):
        # self.p7tpl.IntersectionOf2Classes not present in Part 8 files
        eset = self.part2.EnumeratedSetOfClass(annSource=source)
        self.part2.Classification(hasClassified=role1, hasClassifier=eset, annSource=source)
        self.part2.Classification(hasClassified=role2, hasClassifier=eset, annSource=source)
        self.p7tpl.IntersectionOfSetOfClass(eset, self.EmptyClass, annSource=source)

    def R_is_performed_by(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.ClassOfCompositionOfIndividual(hasClassOfPart=role2, hasClassOfWhole=role1, annSource=source)
        if role1c is not None:
            if role1c[1] == "*":
                 self.p7tpl.CardinalityEnd1Min(rel_id, role1c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd1MinMax(rel_id, role1c[0], role1c[1], annSource=source)
        if role2c is not None:
            if role2c[1] == "*":
                 self.p7tpl.CardinalityEnd2Min(rel_id, role2c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd2MinMax(rel_id, role2c[0], role2c[1], annSource=source)
        return rel_id, 1

    def R_is_related_to(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.OtherRelationship(hasEnd1=role1, hasEnd2=role2, annSource=source)
        if role1c is not None:
            if role1c[1] == "*":
                 self.p7tpl.CardinalityEnd1Min(rel_id, role1c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd1MinMax(rel_id, role1c[0], role1c[1], annSource=source)
        if role2c is not None:
            if role2c[1] == "*":
                 self.p7tpl.CardinalityEnd2Min(rel_id, role2c[0], annSource=source)
            else:
                 self.p7tpl.CardinalityEnd2MinMax(rel_id, role2c[0], role2c[1], annSource=source)
        return rel_id

    def R_is_classified_as(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.Classification(hasClassified=role1, hasClassifier=role2, annSource=source)
        return rel_id

    def R_is_subclass_of(self, role1, role2, role1c, role2c, source):
        rel_id = self.part2.Specialization(hasSubclass=role1, hasSuperclass=role2, annSource=source)
        return rel_id

    def R_complies_to_description_in(self, role1, role2, role1c, role2c, source):
        pi = self.part2.PossibleIndividual(annSource=source)
        self.part2.Classification(hasClassified=pi, hasClassifier=role2, annSource=source)
        rel_id = self.part2.Description(hasRepresented=role1, hasSign=pi, annSource=source)
        return rel_id
