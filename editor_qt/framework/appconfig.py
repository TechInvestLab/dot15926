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




import json
import collections
import traceback
import os

class ConfigVersionConverter:
    version = 4

    @staticmethod
    def Version0(data):
        if data.get('solutiondata', None) != None:
            data['projectdata'] = data['solutiondata']
            del data['solutiondata']

    @staticmethod
    def Version1(data):
        if data.get('projectdata', None) != None:
            for v in data['projectdata']:
                if isinstance(v, dict):
                    if 'is_templates' in v['info']:
                        v['info']['doc_type'] = 'TemplatesDocument'
                        del v['info']['is_templates']
                    if 'is_graph' in v['info']:
                        v['info']['doc_type'] = 'GraphDocument'
                        del v['info']['is_graph']
                    if 'importer_name' in v['info']:
                        v['info']['importer_type'] = v['info']['importer_name']
                        del v['info']['importer_name']

    @staticmethod
    def Version2(data):
        from framework.project import ProjectView
        from framework.dialogs import Notify, SelectFiles, Choice
        projectdata = data.get('projectdata')
        if projectdata:
            Notify(_('Project data found in configuration. Please save it as project file.'))
            del data['projectdata']
            while True:
                path = SelectFiles(tm.main.save_project_as, save = True, wildcard = ProjectView.msg_wildcard)
                if path:
                    try:
                        with open(path, 'w') as f:
                            json.dump(dict(data=projectdata), f, 'utf-8', ensure_ascii=False)
                            data['projectfile'] = path
                            break
                    except:
                        if not Choice(tm.main.config_convert_project_file_failed):
                            break
                else:
                    if Choice(tm.main.config_abort_project_convert):
                        break

    @staticmethod
    def Version3(data):
        data['cfg://part4'] = data.pop('paths.part4', '')
        data['cfg://pca_rdl'] = data.pop('paths.pca_rdl', '')
        data['cfg://p7tpl'] = data.pop('paths.p7tpl', '')

from framework.util import DictDecoder

class AppConfig(dict):
    configfile = os.path.join(appdata.app_dir, 'dot15926.cfg')

    def _key_hook(self, key):
        if key == 'cfg://patterns':
            return 'patterns'

    def get(self, key, default = None):
        result = self._key_hook(key)
        if result != None:
            return result
        return dict.get(self, key, default)

    def __missing__(self, key):
        result = self._key_hook(key)
        if result != None:
            return result
        raise KeyError(key)

    def TryToLoadSettings(self):
        try:
            with open(self.configfile, 'r') as f:
                self.update(json.load(f, 'utf-8', object_hook = DictDecoder()))
        except:
            self.SaveSettings()

    def SaveSettings(self):
        with open(self.configfile, 'w') as f:
            json.dump(self, f, 'utf-8', ensure_ascii=False)

    def CheckVersion(self):
        version = self.get('version', 0)
        if version != ConfigVersionConverter.version:
            for i in range(version, ConfigVersionConverter.version):
                convert_method = getattr(ConfigVersionConverter, 'Version{0}'.format(i), None)
                if convert_method != None:
                    convert_method(self)
            self['version'] = ConfigVersionConverter.version
            self.SaveSettings()