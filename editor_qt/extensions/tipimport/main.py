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

from PySide.QtCore import *
from PySide.QtGui import *
import iso15926.kb as kb
import framework
import framework.dialogs
import pyodbc
import datetime
import iso15926.kb as kb
from iso15926 import GraphDocument
from iso15926 import PatternsDocument, SparqlConnection
from framework.util import DictDecoder, HashableDict
from framework.dialogs import Notify
import copy
import pprint

names_map = {
-1059228930: 'IndirectPropertyOfClassifiedContentOfPartInAssembly',
30257532: 'ClassifiedIdentificationOfClassifiedContentOfPartInAssembly',
688138585: 'ClassifiedIdentificationOfOfWhole???InAssemblyWithConnectedItem',
-799344281: 'ClassificationOfClasifiedContentOfPartInAssembly',
1720291224: 'ClassificationsOf2ObjectsIndirectlyConnectedViaObject',
370755235: 'IndirectPropertyOfClassifiedContentOfWholeInAssembly',
-753581832: 'ClassifiedIdOfWholeInArrangement',
-549610964: 'ClassifiedIdOfClassifiedRepresentation',
1842424147: 'ClassifiedIdOfWholeInAssembly',
-856614935: 'ClassificationOfRolePlayerInActivity',
-1464461254: 'RoleOfContainerInClassifiedContainement',
-683539181: 'ClassifiedIdOfWholeInClassifiedArrangement',
437539504: 'IndirectPropertyOfContentInClassifiedContainement',
-619645690: 'IndirectPropertyOfContainerInClassifiedContainementOfItem',
1009364807: 'ClassifiedIdOfIndirectlyConnectedObject',
442201077: 'ClassifiedDescriptionOfWholeInClassifiedArrangement',
-1279036199: 'ClassifiedIdOfRepresentingDocument',
-593707902: 'IndirectPropertyOfWholeInArrangement',
-1833128188: 'ClassifiedEventTimeForRepresentation',
1516907769: 'ClassificationOfPartInAssembly',
-998056655: 'ClassifiedIdOfRepresentationInDocument',
-857201330: 'IndirectPropertyOfRepresentation',
-888744273: 'ClassificationOfContainerInClassifiedContainment',
1580719718: 'ClassifiedDescriptionOfRepresentation',
-619645690: 'IndirectPropertyOfContainerInClassifiedContainement',
662756941: 'ClassificationOfContentInClassifiedContainement',
-1472668486: 'ClassifiedDescriptionOfWholeInArrangement',
786946174: 'StatusOfRepresentation',
1507301474: 'ClassifiedIdOfContentInClassifiedContainment',
-746354576: 'ClassificationOfWholeInAssembly',
1887855625: 'IndirectPropertyOfIndirectlyConnectedObject',
2096221815: 'ClassifiedIdOfWholeOfWholeInArrangements',
-2067149581: 'ClassifiedIdOfIndirectlyConnectedObject_mmttpl',
6556543: 'ClassifiedIdentificationOfRepresentingDocument',
-2135428962: 'ClassifiedIdOfConnectedObject',
-23131803: 'ClassifiedIdOfWholeInArrangement_mmttpl',
526823634: 'ParticipantInActivityWithInvolvedItem',
2141194498: 'ClassificationOfPartInAssembly_mmttpl',
24939736: 'ClassificationOfWholeInAssemblyWithCompoundType',

}

@public('dot15926.importers')
class TIPImporter:

    def __init__(self, target_doc, import_source, import_patterns = True, generate_generic = True):
        self.source_path                    = import_source[0]
        self.target_doc                     = target_doc
        self.import_patterns = import_patterns
        self.generate_generic = generate_generic
        self.iiptpl_ver1 = None
        self.iiptpl_ver2 = None
        self.mmttpl_ver = None
        self.DoImport()

    def InitEnvironment(self):
        if not self.iiptpl_ver1:
            self.iiptpl_ver1 = GraphDocument()
            self.iiptpl_ver1.OpenSparql(SparqlConnection('http://posccaesar.org/sandbox/iip/sparql'))
        if not self.iiptpl_ver2:
            self.iiptpl_ver2 = GraphDocument()
            self.iiptpl_ver2.OpenSparql(SparqlConnection('http://www.iringsandbox.org/repositories/SandboxPt8/query'))
        if not self.mmttpl_ver:
            self.mmttpl_ver = GraphDocument()
            self.mmttpl_ver.OpenSparql(SparqlConnection('http://www.iringsandbox.org/repositories/JORDTemplatesProposed/query'))
        return True

    def read_class(self, id):
        res = {}
        cls = self.cur.execute('SELECT * FROM Class WHERE Id=?;', id).fetchone()
        res['uri'] = 'http://rdl.rdlfacade.org/data#' + cls.RDL_Class_Id
        res['template'] = cls.Temp_Id
        return res

    def part_exists(self, id, parts):
        for p in parts:
            if 'self' in p and p['self'] == id:
                return True
        return False

    def read_synonym(self, id):
        if id:
            param = self.cur.execute('SELECT * FROM Parameter_Synonym WHERE Parameter_Id=?;', id).fetchone()
            if param:
                return param.Name
        return ''

    def read_param(self, id):
        if id:
            param = self.cur.execute('SELECT * FROM Parameter WHERE Id=?;', id).fetchone()
            return param
        return None

    def gen_scolem(self):
        self.scolem_counter += 1
        return 'IND' + str(self.scolem_counter)

    def gen_name(self, parts):
        i = 1
        while True:
            name_gen = 'entity%i'%i
            for p in parts:
                if 'self' in p and p['self'] == name_gen:
                    break
            else:
                return name_gen
            i += 1



    def read_template(self, id, parts, possessor, signature):
        tpl = self.cur.execute('SELECT * FROM Template WHERE Id=?;', id).fetchone()
        tpl_id = tpl.RDL_Template_Id.strip()
        tpl_name = tpl.Name.strip()

        part = {'self': self.gen_name(parts)}
        parts.append(part)

        tpl_uri = ('http://tpl.rdlfacade.org/data#' + tpl_id).encode('utf-8')
        pre = self.templ_query_cache.get(tpl_uri)
        if not pre:
            if self.iiptpl_ver1._grSearchUri(tpl_uri) and self.iiptpl_ver1.grLiteral(tpl_uri, 'http://www.w3.org/2000/01/rdf-schema#label') == tpl_name:
                print 'found in primary iip', tpl_id, tpl_name
                pre = 'iiptpl.'
            if self.iiptpl_ver2._grSearchUri(tpl_uri) and self.iiptpl_ver2.grLiteral(tpl_uri, 'http://www.w3.org/2000/01/rdf-schema#label') == tpl_name:
                print 'found in secondary iip', tpl_id, tpl_name
                pre = 'iiptpl.'
            elif self.mmttpl_ver._grSearchUri(tpl_uri) and self.mmttpl_ver.grLiteral(tpl_uri, 'http://www.w3.org/2000/01/rdf-schema#label') == tpl_name:
                print 'found in mmt', tpl_id, tpl_name
                pre = 'mmttpl.'

        if not pre:
            print 'template %s(%s) not found in iiptpl or mmttpl, iiptpl used as default\n'%(tpl_name, tpl_id)
            pre = 'iiptpl.'

        part['type'] = pre + tpl_name
        self.templ_query_cache[tpl_uri] = pre

        for r in self.cur.execute('SELECT * FROM Role WHERE Template_Id=?;', id).fetchall():
            role_value = r.Value
            role_name = r.Role_Name
            role_type = r.Type
            role_parameter = self.read_param(r.Parameter_Id)
            
            if role_type == 'Reference':
                cls = self.read_class(role_value)
                role_value = role_value.replace('CLASS', 'IND')
                if not cls['template']:
                    role_value = role_parameter.Name.replace('.','') if role_parameter else role_value
                if not self.part_exists(role_value, parts):
                    ref_part = {}
                    ref_part['self'] = role_value
                    ref_part['uri'] = cls['uri']
                    parts.append(ref_part)
                if cls['template']:
                    self.read_template(cls['template'], parts, role_value, signature)
                part[role_value] = role_name
            elif role_type == 'Possessor':
                part[possessor] = role_name
            elif role_type == 'FixedValue':
                cls = self.read_class(role_value)
                role_value = role_value.replace('CLASS', 'IND')
                if not cls['template']:
                    role_value = role_parameter.Name.replace('.','') if role_parameter else role_value
                if not self.part_exists(role_value, parts):
                    ref_part = {}
                    ref_part['self'] = role_value
                    ref_part['type'] = cls['uri']
                    parts.append(ref_part)
                if cls['template']:
                    self.read_template(cls['template'], parts, role_value, signature)
                part[role_value] = role_name
            elif role_parameter:
                syn = self.read_synonym(role_parameter.Id)
                comment = 'Name: %s\nTypical value: %s\nSynonym: %s'%(role_parameter.Name, role_parameter.Typical_value,syn)
                signature[role_parameter.Name.replace('.','')] = {'inverse_title': '', 'comment': comment}
                part[role_parameter.Name.replace('.','')] = role_name
            else:
                part[role_value] = role_name
                print 'unmapped role %s in template %s\n'%(r.Id, id)

    def normalize_pattern(self, signature, parts):
        restr_roles = set()
        signature_result = {'Possessor': {'inverse_title': '', 'comment': ''}}
        parts_result = []
        role_map = {}


        for p in parts:
            if 'type' in p and isinstance(p['type'], basestring) and (p['type'].startswith('iiptpl') or p['type'].startswith('mmttpl')):
                parts_result.append(dict(p))
            else:
                if 'self' in p and not p['self'].startswith('entity'):
                    restr_roles.add(p['self'])

        for p in parts_result:
            for r in p.keys():
                if r == 'self':
                    if not p[r].startswith('entity'):
                        for p1 in parts_result:
                            if p != p1 and p[r] in p1.keys():
                                break
                        else:
                            del p[r]

                elif r not in ('Possessor', 'type', 'uri'):
                    for p1 in parts_result:
                        if p != p1 and r in p1.keys():
                            break
                    else:
                        value = p[r]
                        name = value[3:]
                        del p[r]
                        n = 0
                        while name in signature_result:
                            n += 1
                            name = value[3:] + str(n)
                        p[name] = value
                        signature_result[name] = {'inverse_title': '', 'comment': ''}

        return signature_result, parts_result

    def get_hash(self, parts):
        parts_sign = [frozenset([(k, v) if k in ('type', 'uri') else v for k, v in p.iteritems() if k != 'self']) for p in parts]

        for i, p in enumerate(parts):
            for k, v in p.iteritems():
                if k not in ('type', 'uri', 'self'):
                    for i1, p1 in enumerate(parts):
                        if i != i1 and k in p1:
                            parts_sign.append((parts_sign[i], v, parts_sign[i1]))

        return hash(frozenset(parts_sign))

    def Clear(self):
        self.iiptpl_ver1.Cleanup()
        self.iiptpl_ver1 = None        
        self.iiptpl_ver2.Cleanup()
        self.iiptpl_ver2 = None
        self.mmttpl_ver.Cleanup()
        self.mmttpl_ver = None

    def DoImport(self):
        if not self.InitEnvironment():
            self.target_doc.ChangeState(self.target_doc.state_importfailed)
            return

        @public.wth(tm.ext.importing_doc.format(self.target_doc.name), self.target_doc)
        def f():

            @public.mth
            def f2():
                if not self.iiptpl_ver1.CanView() or not self.iiptpl_ver2.CanView() or not self.mmttpl_ver.CanView():
                    self.Clear()
                    self.target_doc.ChangeState(self.target_doc.state_importfailed)
                    return

                @public.wth(tm.ext.importing_doc.format(self.target_doc.name), self.target_doc)
                def f3():                
                    try:
                        DRV = '{Microsoft Access Driver (*.mdb)}'
                        PWD = 'pw'
                        self.con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,self.source_path,PWD))
                        self.cur = self.con.cursor()
                        self.ProcessModel()
                        @public.mth
                        def f4():
                            self.Clear()
                            self.target_doc.ChangeState(self.target_doc.state_changed)
                    except:
                        log.exception()
                        @public.mth
                        def f5():
                            self.Clear()
                            self.target_doc.ChangeState(self.target_doc.state_importfailed)

    def ProcessModel(self):
        self.scolem_counter = 0
        templates = {}
        decoder = DictDecoder(HashableDict)
        self.templ_query_cache = {}
        for row in self.cur.execute('SELECT * FROM Tip;').fetchall():
            if row.Status == '3' and row.Mapping_Status == '3':
                name = row.Name.replace(' ', '')
                signature = {'Possessor': {'inverse_title': '', 'comment': ''}}
                parts = []
                possessor = 'Possessor'
                tpl = self.cur.execute('SELECT * FROM Template WHERE Tip_Id=?;', row.Id).fetchone()
                if tpl:
                    scolem_counter = 0
                    comms = self.cur.execute('SELECT * FROM Commodity_Tip WHERE Tip_Id=?;', row.Id).fetchall()
                    if comms:
                        ref_part = {}
                        ref_part['self'] = possessor
                        ref_part['type'] = []
                        for r in comms:
                            com = self.cur.execute('SELECT * FROM Commodity WHERE Id=?;', r.Commodity_Id).fetchone()
                            ref_part['type'].append('http://rdl.rdlfacade.org/data#' + com.RDL_Class_ID)
                        parts.append(ref_part)

                    self.read_template(tpl.Id, parts, possessor, signature)
                    comment = 'Name: %s\nID: %s\nDescription: %s\nRemarks: %s'%(row.Name, row.Id, row.Description, row.Remarks)
                    templates[name.encode('utf-8')] = (decoder._decode_dict(signature), decoder._decode_list(parts))
                    if self.import_patterns:
                        self.target_doc.patterns[name.encode('utf-8')] = decoder._decode_dict(
                            {
                                'name': name,
                                'comment': comment,
                                'signature': signature,
                                'options': [{'name': 'lifted', 'parts': parts}]
                            }
                        )
                else:
                    print 'Template not found for %s'%name

        self.templ_query_cache = None
        self.cur.close()
        self.con.close()

        if not self.generate_generic:
            return

        groups = []
        completed = set()

        for k1 in templates.viewkeys():
            if k1 in completed:
                continue
            completed.add(k1)
            group = set([k1])
            parts = self.normalize_pattern(*templates[k1])[1]
            values = self.get_hash(parts)
            if values:
                for k2 in templates.viewkeys() - completed:
                    parts = self.normalize_pattern(*templates[k2])[1]
                    other = self.get_hash(parts)
                    if other == values:
                        group.add(k2)
                        completed.add(k2)
                groups.append((group, values, self.normalize_pattern(*templates[k1])))


        groups = sorted(groups, key=lambda value: len(value[2][1]), reverse = True)

        counter = 1
        for group, h, (signature, parts) in groups:
            #data += '\'\'\'\nHash: %s\n%s\n\'\'\'\n'%(str(h), '\n'.join(group))

            name = names_map.get(h)
            if not name:
                if len(parts) == 1:
                    tp = parts[0].get('type')
                    if tp:
                        print 'one template pattern %s'%tp
                        #pprint.pprint(parts[0])
                        name = tp.split('.')[1]
                        if name.encode('utf-8') in self.target_doc.patterns:
                            name += '_' + tp.split('.')[0][:-3]
                            if name.encode('utf-8') in self.target_doc.patterns:
                                print 'pattern naming error'
                                name = None
                if not name:
                    name = 'Group%i'%counter
                    counter += 1

            self.target_doc.patterns[name.encode('utf-8')] = decoder._decode_dict({
                'comment': 'Generic pattern\nHash: %s\n%s'%(str(h), '\n'.join(group)),
                'name': name,
                'signature': signature,
                'options': [{'parts': parts}]
            })
            if self.import_patterns:
                for p in group:
                    options = self.target_doc.patterns[p]['options']
                    removed_parts = []
                    new_parts = []
                    for part in options[0]['parts']:
                        if 'self' in part and not part['self'].startswith('entity'):
                            new_parts.append(copy.copy(part))
                        else:
                            removed_parts.append(part)

                    sign_scan = {}
                    sign_scan2 = {}
                    for rp in removed_parts:
                        rt = rp.get('type', rp.get('uri'))
                        for rr, rv in rp.iteritems():
                            if rr not in ('uri', 'type', 'self'):
                                sign_scan.setdefault(rr, set()).add(rt)
                                sign_scan.setdefault(rr, set()).add(rv)

                    for rp in parts:
                        rt = rp.get('type', rp.get('uri'))
                        for rr, rv in rp.iteritems():
                            sign_scan2.setdefault(rr, set()).add(rt)
                            sign_scan2.setdefault(rr, set()).add(rv)

                    new_option = {}
                    new_option['name'] = 'spec'
                    new_option['parts'] = new_parts
                    ppart = { 'type': 'patterns.' + name }

                    for rr, rv in sign_scan.iteritems():
                        for rr1, rv1 in sign_scan2.iteritems():
                            if rv==rv1:
                                ppart[rr] = rr1
                                break
                        else:
                            print 'wrong mapping!!'

                    new_parts.append(ppart)
                    options.append(decoder._decode_dict(new_option))


class SetupImportDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.ext.import_geom_title)

        self.import_patterns = QCheckBox(self)
        self.import_patterns.setText(tm.ext.tip_import_patterns)
        self.import_patterns.setChecked(bool(appconfig.get('tip.import_patterns', True)))
        self.generate_generic = QCheckBox(self)
        self.generate_generic.setText(tm.ext.tip_generate_generic)
        self.generate_generic.setChecked(bool(appconfig.get('tip.generate_generic', True)))

        grid = QGridLayout(self)
        grid.addWidget(self.import_patterns, 0, 0, 1, 2)
        grid.addWidget(self.generate_generic, 1, 0, 1, 2)

        self.btn_ok = QPushButton(tm.ext.ok, self)
        self.btn_ok.setDefault(True)
        self.btn_cancel = QPushButton(tm.ext.cancel, self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)

        grid.addLayout(layout_btn, 2, 0, 1, 2)

        if self.exec_()==QDialog.Accepted:
            import_patterns = self.import_patterns.isChecked()
            generate_generic = self.generate_generic.isChecked()
            appconfig['tip.import_patterns'] = import_patterns
            appconfig['tip.generate_generic'] = generate_generic
            appconfig.SaveSettings()

            path, wildcard = framework.dialogs.SelectFiles(tm.ext.menu_import_tip, multi=False)
            if not path:
                return

            doc = PatternsDocument()
            doc.NewImport([path], TIPImporter,{'import_patterns': import_patterns, 'generate_generic': generate_generic}, **(dict()))
            appdata.project.AddDocument(doc)



@public('workbench.menu.tools')
class xTipImport:
    vis_label = tm.ext.menu_import_tip

    @classmethod
    def Do(cls):
        SetupImportDialog()
        # path, wildcard = framework.dialogs.SelectFiles(cls.vis_label, multi=False)
        # if not path:
        #     return

        # doc = PatternsDocument()
        # doc.NewImport([path], TIPImporter, **(dict()))
        # appdata.project.AddDocument(doc)
