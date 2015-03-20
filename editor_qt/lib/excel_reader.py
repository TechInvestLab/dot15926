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

from xml.dom import minidom
from contextlib import closing
import zipfile

class SheetContentException(Exception):
    def __init__(self, message, sheet_name=None, row_id=None, col_name=None):
        self.message = message
        self.sheet_name = sheet_name
        self.row_id = row_id
        self.col_name = col_name
    def __str__(self):
        l = ['Error']
        if self.sheet_name is not None:
            l.append(' Sheet = "{0}"'.format(self.sheet_name))
        if self.row_id is not None:
            l.append(' Row id = {0}'.format(self.row_id))
        if self.col_name is not None:
            l.append(' Column name = "{0}"'.format(self.col_name))
        l.append(': {0}'.format(self.message))
        return ''.join(l)

class RowIterator:
    def __init__(self, sheet_name, sheet):
        self.sheet_name = sheet_name
        self.names = {}
        # column headers from row 1
        for k, v in sheet['1'].iteritems():
            self.names[v] = k
        self.iter = sheet['seq'].__iter__()
        # skip headers (row 1)
        self.iter.next()

    def __iter__(self):
        return self

    def next(self):
        self.row_id, self.cur = self.iter.next()
        return self

    def __getattr__(self, col_id):
        return self.cur.get(col_id, '')

    def text(self, col_name):
        return self.cur.get(self.names[col_name], '')

    def nonempty(self, col_name):
        text = self.cur.get(self.names[col_name], '')
        if text==u'':
            raise SheetContentException('Value expected', self.sheet_name, self.row_id, col_name)
        return text

    def known(self, col_name, ids):
        text = self.cur.get(self.names[col_name], '')
        if text=='':
            raise SheetContentException('Value expected', self.sheet_name, self.row_id, col_name)
        item = ids.get(text, None)
        if item is None:
            raise SheetContentException('Unknown item "{0}"'.format(text), self.sheet_name, self.row_id, col_name)
        return item

    def known_or_empty(self, col_name, ids):
        text = self.cur.get(self.names[col_name], '')
        if text=='':
            return None
        item = ids.get(text, None)
        if item is None:
            raise SheetContentException(u'Unknown item "{0}"'.format(text), self.sheet_name, self.row_id, col_name)
        return item

    def sheet_error(self, message):
        raise SheetContentException(message, self.sheet_name)

    def row_error(self, message):
        raise SheetContentException(message, self.sheet_name, self.row_id)

    def cell_error(self, message):
        raise SheetContentException(message, self.sheet_name, self.row_id, col_name)

class ExcelReader:
    def __init__(self, filename):
        self.Read(filename)

    def Dom(self, path):
        return minidom.parseString(self.zip.read(path))

    def Read(self, filename):
        with closing(zipfile.ZipFile(filename, 'r')) as zip:
            self.zip = zip
            self.ReadContent()
        return self.sheets

    def ReadContent(self):
        l = []
        try:
            dom = self.Dom('xl/sharedStrings.xml')
            nodes = dom.firstChild.childNodes
            for n in nodes:
                t = n.firstChild.firstChild
                v = ''
                if t:
                    if t.nodeValue:
                        v = t.nodeValue
                    elif t.hasChildNodes():
                        nodes2 = t.parentNode.parentNode.childNodes
                        v = ''.join([str(n2.getElementsByTagName('t')[0].firstChild.nodeValue) for n2 in nodes2])
                l.append(v)
        except KeyError:
            l = None
        self.strings = l

        self.sheets = {}
        i = 1
        dom = self.Dom('xl/workbook.xml')
        for n in dom.firstChild.getElementsByTagName('sheets')[0].childNodes:
            self.ReadSheet(i, str(n._attrs['name'].value))
            i += 1

    def ReadSheet(self, index, name):

        sheet = {}
        self.sheets[name] = sheet
        seq = []
        sheet['seq'] = seq

        dom = self.Dom('xl/worksheets/sheet%i.xml'%index)
        data = dom.firstChild.getElementsByTagName('sheetData')[0]
        for row in data.childNodes:
            row_id = str(row.getAttribute('r'))
            row_data = {}

            for cell in row.childNodes:
                cell_id = str(cell.getAttribute('r'))
                col_id = cell_id[:-len(row_id)]
                cell_type = cell.getAttribute('t')
                cell_style = cell.getAttribute('s')

                formula = None
                content = None

                try:
                    formula = cell.getElementsByTagName('f')[0].firstChild.nodeValue
                except:
                    pass

                try:
                    content = str(cell.getElementsByTagName('v')[0].firstChild.nodeValue)
                    if cell_type=='s':
                        content = self.strings[int(content)]
                except:
                    pass

                if content is not None:
                    data = content.strip() # remove leading and trailing spaces
                    if data:
                        row_data[col_id] = data

            if row_data:
                sheet[row_id] = row_data
                seq.append((row_id, row_data))

    def Sheets(self):
        return self.sheets.keys()

    def Rows(self, sheet_name):
        sheet = self.sheets[sheet_name]
        return RowIterator(sheet_name, sheet)

    def SafeRows(self, sheet_name):
        sheet = self.sheets[sheet_name]
        iter = RowIterator(sheet_name, sheet)
        def f(func):
            while 1:
                try:
                    iter.next()
                except:
                    return
                try:
                    func(iter)
                except SheetContentException as exc:
                    log('{0}\n', str(exc))
                    if exc.row_id==None:
                        return
        return f
