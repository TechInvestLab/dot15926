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



import os
import framework.dialogs as dialogs
from framework.util import GetPath, Path2Name

class DocInfoVersionConverter:
    version = 2
    @staticmethod
    def Check(docinfo):
        version = docinfo.get('version', 0)
        if version != DocInfoVersionConverter.version:
            for i in xrange(version, DocInfoVersionConverter.version):
                convert_method = getattr(DocInfoVersionConverter, 'Version{0}'.format(i), None)
                if convert_method != None:
                    convert_method(docinfo)

    @staticmethod
    def Version0(docinfo):
        if docinfo['info']['doc_type'] == 'TemplatesDocument':
            docinfo['info']['doc_type'] = 'GraphDocument'

    @staticmethod
    def Version1(docinfo):
        for k, v in docinfo['params'].iteritems():
            if k in ('annotations', 'roles', 'namespaces'):
                docinfo['params'][k] = [tuple(line.split(' ', 1)) for line in v.splitlines()]


def CollectDocInfo(document, base_path = None):

    is_valid = False
    docinfo = dict()
    docinfo['version'] = DocInfoVersionConverter.version
    docinfo['params'] = dict()
    docinfo['info']   = dict()

    docinfo['info']['doc_type'] = document.__class__.__name__
    docinfo['name'] = document.name

    for k in document.doc_params:
        v = getattr(document, k, None)
        if v != None:
            if k in ('annotations', 'roles', 'namespaces'):
                docinfo['params'][k] = [list(value) for value in v]
            else:
                docinfo['params'][k] = v

    connection = getattr(document, 'doc_connection', None)
    importer   = getattr(document, 'importer_type', None)

    if connection:
        docinfo['info']['connection'] = {'uri': connection.uri, 'login': connection.login, 'password': connection.password}
        is_valid = True
    elif len(document.doc_paths) > 0:
        if base_path:
            try:
                base_dir = os.path.dirname(base_path)
                docinfo['info']['paths'] = [p if p.startswith('cfg://') else os.path.relpath(p, base_dir) for p in document.doc_paths]
            except:
                docinfo['info']['paths'] = document.doc_paths
        else:
            docinfo['info']['paths'] = document.doc_paths
        is_valid = True

    if importer:
        docinfo['info']['importer_name'] = importer.__name__
        docinfo['info']['import_source'] = document.import_source
        docinfo['info']['importer_kwargs'] = document.importer_kwargs
        is_valid = True

    if is_valid:
        return docinfo
    else:
        return None

def OpenDoc(docinfo, base_path = None):

    DocInfoVersionConverter.Check(docinfo)

    info = docinfo['info']
    params = docinfo['params']

    doctype = None
    doc_typename = info['doc_type']
    for v in public.all("dot15926.doctypes"):
        if v.__name__ == doc_typename:
            doctype = v

    if doctype == None:
        return

    doc = doctype()
    from_file = False
    if 'paths' in info:
        if base_path:
            base_dir = os.path.dirname(base_path)
            paths = [p if p.startswith('cfg://') or os.path.isabs(p) else os.path.normpath(os.path.join(base_dir, p)) for p in info['paths']]
        else:
            paths = info['paths']

        not_found = []
        for i, p in enumerate([GetPath(v) for v in paths]):
            if not os.path.exists(p):
                not_found.append((i, p))

        if not_found:
            if dialogs.Choice(tm.main.paths_not_found%'\n'.join([Path2Name(p) for v in not_found])):
                new_paths, wildcard = dialogs.SelectFiles(tm.main.paths_not_found_select, multi=True)
                if new_paths:
                    for i, p in reversed(not_found):
                       paths.pop(i)
                    paths += new_paths
            else:
                return

        if not doctype.VerifyEditablePaths([v.decode('utf-8') for v in [appconfig.get(v, '').decode('utf-8') if v.startswith('cfg://') else v for v in paths]]):
            return

        doc.OpenFiles([v.decode('utf-8') for v in paths], **params)
        from_file = True
    elif 'connection' in info:
        from iso15926.io.sparql import SparqlConnection
        connection = SparqlConnection(**info['connection'])
        doc.OpenSparql(connection, **params)
    if 'importer_name' in info:
        importer_name = info['importer_name']
        for v in public.all("dot15926.importers"):
            if v.__name__ == importer_name:
                doc.NewImport([path.decode('utf-8') for path in info['import_source']], v, info['importer_kwargs'], reimport = (from_file == False), **params)


    return doc

def NameWithPrefix(docinfo):
    return docinfo['name']

def CompareDocSources(first, second):
    if first == second:
        return True

    if first['info']['doc_type'] != second['info']['doc_type']:
        return False

    if 'paths' in first['info'] or 'paths' in second['info']:
        return first['info'].get('paths') == second['info'].get('paths')
    elif 'importer_name' in first['info'] or 'importer_name' in second['info']:
        return first['info'].get('import_source') == second['info'].get('import_source')
    elif 'connection' in first['info'] and 'connection' in second['info']:
        return first['info']['connection']['uri'] == second['info']['connection']['uri']
    return False

def GetDocSource(doc):
    if 'paths' in doc['info']:
        return ', '.join(doc['info']['paths'])
    if 'importer_name' in doc['info']:
        return ', '.join(doc['info']['import_source'])
    elif 'connection' in doc['info']:
        return doc['info']['connection']['uri']
    return ''