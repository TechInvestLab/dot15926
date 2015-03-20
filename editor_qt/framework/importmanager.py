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




try:
    import builtins
except ImportError:
    import __builtin__ as builtins

import imp
import sys
import traceback

class ImportManager:

    _baseimport   = builtins.__import__
    _dependencies = dict()
    _parent       = None

    @staticmethod
    def enable(blacklist=None):
        builtins.__import__ = ImportManager._import

    @staticmethod
    def disable():
        """Disable global module dependency tracking."""
        builtins.__import__ = ImportManager._baseimport
        ImportManager._dependencies.clear()
        ImportManager._parent = None

    @staticmethod
    def GetDependencies(m):
        """Get the dependency list for the given imported module."""
        return ImportManager._dependencies.get(m.__name__, [])

    @staticmethod
    def _import(name, globals=None, locals=None, fromlist=None, level=-1):
        """__import__() replacement function that tracks module dependencies."""
        # Track our current parent module.  This is used to find our current place
        # in the dependency graph.
        parent = ImportManager._parent
        ImportManager._parent = name

        base = None
        try:
            # Perform the actual import using the base import function.
            base = ImportManager._baseimport(name, globals, locals, fromlist, level)
        except:
            raise
        else:
            # If this is a nested import for a reloadable (source-based) module, we
            # append ourself to our parent's dependency list.

            if parent is not None:
                # We get the module directly from sys.modules because the import
                # function only returns the top-level module reference for a nested
                # import statement (e.g. 'package' for `import package.module`).
                parent_module = sys.modules.get(parent, None)
                if parent_module is not None and hasattr(parent_module, '__file__'):
                    l = ImportManager._dependencies.setdefault(name, [])
                    if parent_module not in l:
                        l.append(parent_module)

            # Lastly, we always restore our global _parent pointer.
        finally:
            ImportManager._parent = parent

        return base

