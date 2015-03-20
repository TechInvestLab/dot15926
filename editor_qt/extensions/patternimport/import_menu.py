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
from iso15926 import GraphDocument
from framework.dialogs import Notify, SelectFiles
import cPickle
import itertools
from framework.util import TaskTarget
import json
from collections import defaultdict
import win32com.client
import pythoncom
import locale

def show_excel_error(e = None):
    @public.mth
    def f():
        if e:
            enc = locale.getpreferredencoding()
            Notify(tm.ext.patterns_err_com.format(e.strerror.decode(enc)))
        else:
            Notify(tm.ext.patterns_err_not_avail)

@public('workbench.menu.tools')
class xPtrnImport:
    vis_label = tm.ext.patterns_from_excel

    @staticmethod
    def Do():
        SetupImportDialog()

    @staticmethod
    def Update(action):
        action.setEnabled((appdata.active_document != None) and isinstance(appdata.active_document, GraphDocument))

class SetupImportDialog(QDialog):

    def __init__(self):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.ext.patterns_setup_import)
        self.finished.connect(self.OnClose)
        self.option = None
        self.pattern = None
        self.book = None
        self.sheet = None
        self.sheets_list = []

        self.sheets = QComboBox(self)
        self.sheets.activated[int].connect(self.OnSheetSelect)

        self.patterns = QComboBox(self)
        self.patterns_env = appdata.environment_manager.GetPatternsEnv(appdata.active_document)

        self.patterns.addItem(QIcon(), '')
        self.options_list = []
        for n, v in self.patterns_env.patterns.iteritems():
            for on, o in v.options.iteritems():
                self.options_list.append(('.'.join((n, on)), v, o))

        self.options_list.sort()
        for i, (n, p, o) in enumerate(self.options_list):
            self.patterns.addItem(QIcon(), n)
            self.patterns.setItemData(self.patterns.count()-1, i)

        self.patterns.activated[int].connect(self.OnPatternSelect)

        self.roles = QTableWidget(0, 3, self)
        self.roles.setHorizontalHeaderLabels(['', tm.ext.roles, tm.ext.columns])
        self.roles.horizontalHeader().setStretchLastSection(True)
        self.roles.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.roles.horizontalHeader().setMinimumSectionSize(10)
        self.progress_state = QLabel(self)
        self.progress_bar = QProgressBar(self)

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setColumnStretch(1,1)
        grid.addWidget(QLabel(tm.ext.patterns_select_sheet, self), 0, 0)
        grid.addWidget(self.sheets, 0, 1)
        grid.addWidget(QLabel(tm.ext.patterns_select_pattern, self), 1, 0)
        grid.addWidget(self.patterns, 1, 1)
        layout.addLayout(grid)
        layout.addWidget(self.roles)

        layout.addWidget(self.progress_state)
        layout.addWidget(self.progress_bar)

        self.btn_import = QPushButton(tm.ext.patterns_import, self)
        self.btn_import.clicked.connect(self.DoImport)
        #self.btn_import.setEnabled(False)

        self.btn_close = QPushButton(tm.ext.patterns_close, self)
        self.btn_close.clicked.connect(self.reject)

        self.btn_load = QPushButton(tm.ext.patterns_load_file, self)
        self.btn_load.clicked.connect(self.LoadMappingFromFile)

        self.btn_save = QPushButton(tm.ext.patterns_save_file, self)
        self.btn_save.clicked.connect(self.SaveMappingToFile)

        layout_btn = QHBoxLayout()
        layout_btn.addWidget(self.btn_load)
        layout_btn.addWidget(self.btn_save)
        layout_btn.addStretch(0)
        layout_btn.addWidget(self.btn_import)
        layout_btn.addWidget(self.btn_close)
        layout.addLayout(layout_btn)
        self.task_guard = TaskTarget()
        self.sheet_guard = TaskTarget()
        self.pending_mapping = None


        @public.wth(tm.ext.patterns_init)
        def f():
            try:
                pythoncom.CoInitialize()
                self.xlApp = win32com.client.gencache.EnsureDispatch('Excel.Application')
                @public.mth
                def f2():
                    self.Reload()
                    self.show()
            except:
                log.exception()
                show_excel_error()

    def LoadMappingFromFile(self):
        path, wildcard = SelectFiles(tm.ext.patterns_load_mapping, multi = False, wildcard = '.json file (*.json)')
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f, 'utf-8')
                    pattern = '.'.join((data['pattern'], data['option']))
                    self.SetPatternOption(pattern, data['roles'])
            except:
                log.exception()
                Notify(tm.ext.patterns_err_load)


    def GetRoleMapping(self):
        mapping = {}
        for i in xrange(self.roles.rowCount()):
            role = self.roles.item(i,1).text()
            mapping[role] = {}
            mapping[role]['name'] = self.roles.cellWidget(i, 2).currentText()
            if self.roles.cellWidget(i, 0) and self.roles.cellWidget(i, 0).isChecked():
                mapping[role]['build'] = True

        return mapping

    def SaveMappingToFile(self):
        if self.patterns.currentIndex() != 0:
            pattern, option = self.options_list[self.patterns.itemData(self.patterns.currentIndex())][1:]
            pattern_name = pattern.name
            option_name = option.name

            mapping = self.GetRoleMapping()

            data = {'version': 0, 'pattern': pattern_name, 'option': option_name, 'roles': mapping}

            path, wildcard = SelectFiles(tm.ext.patterns_save_mapping, save = True, wildcard = '.json file (*.json)')
            if path:
                try:
                    with open(path, 'w') as f:
                        json.dump(data, f, 'utf-8', ensure_ascii=True)
                except:
                    Notify(tm.ext.patterns_err_save)


    def SetProgress(self, text, progress = -1):
        @public.mth
        def f():
            self.progress_state.setText(text)
            if progress < 0:
                self.progress_bar.setVisible(False)
            else:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(progress)

    def StopImport(self):
        self.task_guard.ClearTasks()

    def DoImport(self):
        if not self.option or not self.sheet or not appdata.active_document:
            return

        doc = appdata.active_document
        if not isinstance(doc, GraphDocument):
            return

        self.btn_import.setText(tm.ext.patterns_stop)
        self.btn_import.clicked.disconnect(self.DoImport)
        self.btn_import.clicked.connect(self.StopImport)

        self.sheets.setEnabled(False)
        self.patterns.setEnabled(False)
        self.roles.setEnabled(False)
        self.btn_load.setEnabled(False)
        self.btn_save.setEnabled(False)

        mapping = self.GetRoleMapping()

        documents = list(appdata.documents(GraphDocument))

        @public.wth(tm.ext.patterns_wrk_importing, self.task_guard, *documents)
        def f():
            try:
                self.xlApp.Interactive = False
                self.sheet.Activate()
                self.sheet.Cells(1, 1).Select()
                columns        = {}
                rows_count     = 0
                roles_cols     = {}
                validation_cols = {}
                state = tm.ext.patterns_state_indexing
                progress = 0
                self.SetProgress(state, progress)

                count  = self.sheet.UsedRange.Rows(1).Columns.Count
                counter = 0

                for c in self.sheet.UsedRange.Rows(1).Columns:
                    counter += 1
                    current = int(100*counter/count)
                    if current != progress:
                        progress = current
                        self.SetProgress(state, progress)

                    val = unicode(c.Value).encode('utf-8')
                    prefix = '$'+self.option.pattern.name + '.' + self.option.name +'.'
                    if val:
                        if val.startswith(prefix):
                            roles_cols[val[len(prefix):]] = c.Column
                        columns[val] = c.Column

                for k, v in mapping.iteritems():
                    if v['name']:
                        roles_cols[k] = columns[v['name']]

                state = tm.ext.patterns_state_proc
                progress = 0

                row_start = self.sheet.UsedRange.Row + 1
                row_end = self.sheet.Rows.Count

                rows_count = max([int(1 + self.sheet.Cells(row_end, i).End(win32com.client.constants.xlUp).Row-row_start) for i in roles_cols.itervalues()])
                count = rows_count * len(self.option.parts)
                counter = 0
                self.SetProgress(state, progress)

                for part in self.option.parts:
                    part_name = part.name
                    if part_name in roles_cols and part.ownrole:
                        log(tm.ext.patterns_invalid_column, part_name)
                        del roles_cols[part_name]

                done = [set()] * rows_count
                current_build = [set()] * rows_count
                for part in self.option.parts:
                    for row in xrange(row_start, row_start + rows_count):
                        counter += 1
                        current = int(100*counter/count)            
                        if current != progress:
                            progress = current
                            self.SetProgress(state, progress)

                        target = part.get_build_target()
                        if target in mapping and not mapping[target].get('build'):
                            continue

                        found = {}
                        for k, v in roles_cols.iteritems():
                            val = self.sheet.Cells(row, v).Value
                            if val:
                                found[k] = unicode(val).encode('utf-8')

                        if not found:
                            continue

                        params = {}
                        for k, v in found.iteritems():
                            if v:
                                if k in part.roles:
                                    params[k] = v
                                elif k.startswith(part.name):
                                    params[k] = v

                        to_skip = set()
                        for k, v in params.iteritems():
                            if not part.is_literal(k):
                                for d in documents:
                                    uri = d.GetEntityUriByName(v)
                                    if uri:
                                        to_skip.add(k)
                                        params[k] = uri
                            else:
                                to_skip.add(k)

                        result = part.build(doc, params, None, current_build[row-row_start], done[row-row_start])
                        if result:
                            for k in result.keys():
                                if k in to_skip:
                                    continue
                                if k not in roles_cols:
                                    roles_cols[k] = self.sheet.UsedRange.Rows(1).Columns(self.sheet.UsedRange.Rows(1).Columns.Count).Column + 1
                                    self.sheet.Cells(self.sheet.UsedRange.Row, roles_cols[k]).Value = prefix + k
                                v = result[k]
                                self.sheet.Cells(row, roles_cols[k]).NumberFormat = "@"
                                self.sheet.Cells(row, roles_cols[k]).Value = unicode('\'' + v)

                state = tm.ext.patterns_state_update
                progress = 0
                count = len(mapping)
                counter = 0
                vsheet = None
                validation_col = 1
                self.SetProgress(state, progress)
                for s in self.book.Sheets:
                    if s.Name == '!'+self.sheet.Name:
                        vsheet = s
                        vsheet.Cells.Clear()
                        break
                else:
                    vsheet = self.book.Sheets.Add(Type = win32com.client.constants.xlWorksheet, After = self.sheet)
                    vsheet.Name = '!'+ self.sheet.Name
                    vsheet.Visible = False
                
                for k, v in mapping.iteritems():
                    counter += 1
                    current = int(100*counter/count)            
                    if current != progress:
                        progress = current
                        self.SetProgress(state, progress)

                    if not v['name']:
                        continue

                    self.sheet.Range(self.sheet.Cells(row_start, columns[v['name']]), self.sheet.Cells(row_end, columns[v['name']])).Validation.Delete()

                    if v.get('build'):
                        continue

                    data = ['']
                    for d in documents:
                        res = self.option.find_valid(d, k)
                        for s in res:
                            for t in d.grTriplesForSubj(s):
                                if t.p == kb.rdfs_label:
                                    data.append(t.v)
                                    break
                            else:
                                data.append(s)

                    if len(data) > 1:
                        vsheet.Range(vsheet.Cells(1, validation_col), vsheet.Cells(len(data), validation_col)).NumberFormat = "@"
                        vsheet.Range(vsheet.Cells(1, validation_col), vsheet.Cells(len(data), validation_col)).Value = [(dv, ) for di, dv in enumerate(data)]
                        self.sheet.Range(self.sheet.Cells(row_start, columns[v['name']]), self.sheet.Cells(row_end, columns[v['name']])).Validation.Add(
                            win32com.client.constants.xlValidateList,
                            win32com.client.constants.xlValidAlertInformation,
                            win32com.client.constants.xlBetween,
                            '=\'' + vsheet.Name + '\'!' + vsheet.Range(vsheet.Cells(1, validation_col), vsheet.Cells(len(data), validation_col)).Address,
                            ''
                            )
                        self.sheet.Range(self.sheet.Cells(row_start, columns[v['name']]), self.sheet.Cells(row_end, columns[v['name']])).Validation.IgnoreBlank = True
                        validation_col += 1

            except public.BreakTask:
                pass
            except pythoncom.com_error as e:
                show_excel_error(e)
            except:
                log.exception() 
            finally:
                try: self.xlApp.Interactive = True
                except: pass
                self.SetProgress(tm.ext.patterns_ready)
                @public.mth
                def f1():
                    self.btn_import.setText(tm.ext.patterns_import)
                    self.btn_import.clicked.connect(self.DoImport)
                    self.btn_import.clicked.disconnect(self.StopImport)

                    self.sheets.setEnabled(True)
                    self.patterns.setEnabled(True)
                    self.roles.setEnabled(True)

                    self.btn_load.setEnabled(True)
                    self.btn_save.setEnabled(True)

    def OnClose(self, r):
        self.StopImport()
        @public.wth()
        def f():
            if self.xlApp:
                del self.xlApp
            if self.book:
                del self.book
            if self.sheet:
                del self.sheet

    def OnPatternSelect(self, index):
        if index == 0:
            self.roles.setRowCount(0)
            self.option = None
            self.SetProgress('')
            return
        else:
            self.SetPatternOption(self.patterns.itemText(index))

    def OnMappingRoleChange(self, index):
        self.SyncMappingData()

    def FillRoles(self, mapping = None):
        if not self.option:
            return

        for i in xrange(self.roles.rowCount()):
            combo = QComboBox(self.roles)
            combo.wheelEvent = lambda evt: None
            combo.activated[int].connect(self.OnMappingRoleChange)
            self.roles.setCellWidget(i, 2, combo)

        if self.sheet:
            @public.wth('', self.sheet_guard)
            def f():
                try:
                    self.xlApp.Interactive = False
                    items = ['']
                    for c in self.sheet.UsedRange.Rows(1).Columns:
                        val = c.Value
                        if val:
                            items.append(val)

                    @public.mth
                    def f2():
                        for i in xrange(self.roles.rowCount()):
                            combo = self.roles.cellWidget(i, 2)
                            for v in items:
                                combo.addItem(QIcon(), unicode(v).encode('utf-8'))

                        if mapping:
                            self.LoadMapping(mapping)
                            self.SyncMappingData(False)
                        else:
                            self.SyncMappingData(True)
                        self.SetProgress(tm.ext.patterns_ready) 
                except public.BreakTask:
                    pass
                except pythoncom.com_error as e:
                    show_excel_error(e)
                except:
                    log.exception() 
                finally:
                    try: self.xlApp.Interactive = True
                    except: pass
   

    def SyncMappingData(self, load = False):
        if self.sheet:
            if not load:
                mapping = self.GetRoleMapping()
                data = cPickle.dumps(mapping)
                @public.wth('', self.sheet_guard)
                def f():
                    try:
                        self.xlApp.Interactive = False
                        for v in self.sheet.CustomProperties:
                            if v.Name == 'dot15926.mapping':
                                v.Value = data
                                break
                        else:
                            self.sheet.CustomProperties.Add('dot15926.mapping', data)
                    except public.BreakTask:
                        pass
                    except pythoncom.com_error as e:
                        show_excel_error(e)
                    except:
                        log.exception() 
                    finally:
                        try: self.xlApp.Interactive = True
                        except: pass
  
            else:
                @public.wth('', self.sheet_guard)
                def f1():
                    try:
                        self.xlApp.Interactive = False
                        for v in self.sheet.CustomProperties:
                            if v.Name == 'dot15926.mapping':
                                mapping = cPickle.loads(str(v.Value))
                                @public.mth
                                def f2():
                                    self.LoadMapping(mapping)
                                break
                    except public.BreakTask:
                        pass
                    except pythoncom.com_error as e:
                        show_excel_error(e)
                    except:
                        log.exception() 
                    finally:
                        try: self.xlApp.Interactive = True
                        except: pass
  

    def LoadMapping(self, mapping):
        for k, v in mapping.iteritems():
            for i in xrange(self.roles.rowCount()):
                if self.roles.item(i, 1).text() == k:
                    if self.roles.cellWidget(i, 0):
                        self.roles.cellWidget(i, 0).setChecked(v.get('build', False))
                    combo = self.roles.cellWidget(i, 2)
                    for i in xrange(combo.count()):
                        if v['name'] == combo.itemText(i):
                            combo.setCurrentIndex(i)
                            break


    def SetPatternOption(self, name, mapping = None):
        if not name:
            return

        for i in xrange(self.patterns.count()):
            if self.patterns.itemText(i) == name:
                if self.patterns.currentIndex() != i:
                    self.patterns.setCurrentIndex(i)

                self.pattern, self.option = self.options_list[self.patterns.itemData(i)][1:]

                self.roles.setRowCount(0)
                row_count = len(self.pattern.roles)
                self.roles.setRowCount(row_count)
                new = self.option.get_build_targets()
                for i, v in enumerate(sorted(self.pattern.roles.keys())):
                    if v in new:
                        check = QCheckBox()
                        check.clicked[bool].connect(self.OnMappingRoleChange)
                        self.roles.setCellWidget(i, 0, check)

                    item = QTableWidgetItem(v)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.roles.setItem(i, 1, item)

                if self.sheet:
                    option_name = name
                    @public.wth('', self.sheet_guard)
                    def f():
                        try:
                            self.xlApp.Interactive = False
                            for v in self.sheet.CustomProperties:
                                if v.Name == 'dot15926.pattern':
                                    v.Value = option_name
                                    break
                            else:
                                self.sheet.CustomProperties.Add('dot15926.pattern', option_name)
                        except public.BreakTask:
                            pass
                        except pythoncom.com_error as e:
                            show_excel_error(e)
                        except:
                            log.exception() 
                        finally:
                            try: self.xlApp.Interactive = True
                            except: pass

                self.FillRoles(mapping)
                return

        Notify(tm.ext.patterns_err_not_found%name)


    def OnSheetSelect(self, index):
        self.sheet_guard.ClearTasks()
        if index == 0:
            self.Reload()
        else:
            self.book, self.sheet = self.sheets_list[self.sheets.itemData(index)][0]
            @public.wth('', self.sheet_guard)
            def f3():
                try:
                    self.xlApp.Interactive = False
                    pattern = None
                    for v in self.sheet.CustomProperties:
                        if v.Name == 'dot15926.pattern':
                            pattern = v.Value
                    @public.mth
                    def f4():
                        self.SetPatternOption(pattern)
                except public.BreakTask:
                    pass
                except pythoncom.com_error as e:
                    show_excel_error(e)
                except:
                    log.exception() 
                finally:
                    try: self.xlApp.Interactive = True
                    except: pass


    def Reload(self):
        self.sheet_guard.ClearTasks()
        self.sheet = None
        self.sheets.clear()
        self.sheets.addItem(QIcon(), '')
        self.SetProgress('')
        self.FillRoles()
        @public.wth()
        def f():
            try:
                self.sheets_list = []
                self.xlApp.Interactive = False
                for v in self.xlApp.Workbooks:
                    for s in v.Sheets:
                        if s.Visible:
                            self.sheets_list.append(((v, s), '-'.join((v.Name, s.Name))))
                @public.mth
                def f2():
                    for i, (s, n) in enumerate(self.sheets_list):
                        self.sheets.addItem(n)
                        self.sheets.setItemData(self.sheets.count()-1, i)
            except public.BreakTask:
                pass
            except pythoncom.com_error as e:
                show_excel_error(e)
            except:
                log.exception() 
            finally:
                try: self.xlApp.Interactive = True
                except: pass

