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
import framework.log

class ExtensionManager:
    extensions_path = 'extensions'

    def __init__(self):
        self.extensions = {}
        pass
        
    def LoadExtensions(self):
        extensions_settings = appconfig.setdefault('extensions', {})
        found_extensions = []

        lst = os.listdir(self.extensions_path)
        for v in lst:
            if v == '__init__.py':
                continue

            path = self.extensions_path + os.sep + v
            if os.path.isdir(path):
                name = v
                module_name = self.extensions_path + '.' + v
            elif v.endswith('.py'):
                name = v[:-3]
                module_name = self.extensions_path + '.' + v[:-3]
            else:
                continue

            found_extensions.append(name)

            if name in extensions_settings:
                if not extensions_settings[name]:
                    log( 'Skipping extension {0}\n'.format(name) )
                    continue
            else:
                if name in ('examples'):
                    extensions_settings[name] = False
                    continue

                extensions_settings[name] = True

            log( 'Loading extension {0}\n'.format(name) )

            try:
                __import__(module_name)
            except:
                log.exception()

        for k in extensions_settings.copy().iterkeys():
            if k not in found_extensions:
                del extensions_settings[k]
        
        appconfig.SaveSettings()


