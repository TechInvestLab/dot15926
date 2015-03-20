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



from PySide.QtCore import *
from PySide.QtGui import *
import sys
import os
import gc
import weakref
from collections import defaultdict
reload(sys)
import traceback
import threading

if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)

QTextCodec.setCodecForCStrings(QTextCodec.codecForName("UTF-8"))
sys.setdefaultencoding('utf-8')

class wizard_cls:
    def __init__(self):
        self.su = defaultdict(set)

    def Subscribe(self, item, subscriber):
        self.su[item].add(subscriber)
        
    def Unsubscribe(self, item, subscriber):
        self.su.get(item, set()).discard(subscriber)

    def UnsubscribeAll(self, subscriber):
        for v in self.su.itervalues():
            v.discard(subscriber)

    def __getitem__(self, item):
        return self.su.get(item, ())

    def __getattr__(self, method):
        def f(*t, **d):
            if len(t) > 1:
                for s in set(self.su.get(t, ())):
                    if s:
                        m = getattr(s, method, None)
                        if m:
                            m(*t, **d)

            for i in t:
                for s in set(self.su.get(i, ())):
                    if s:
                        m = getattr(s, method, None)
                        if m:
                            m(*t, **d)

            for s in set(self.su.get(method, ())):
                if s:
                    m = getattr(s, method, None)
                    if m:
                        m(*t, **d)

        return f

    def __repr__(self):
        return repr(self.su)

class set_t(set):
    def __call__(self, tp):
        for v in self:
            if isinstance(v, tp):
                yield v

class appdata_cls:

    def __init__(self):
        # defaults here...
        self.app_version         = 1.5
        self.app_status          = 'beta'
        self.environment_manager = None
        self.active_document     = None
        self.active_view         = None
        self.extension_manager   = None
        self.topwindow           = None
        self.app                 = None
        self.resources_dir       = None
        self.resources           = None
        self.console_locals      = {}
        self.documents           = set_t()
        self.animated            = set()
        self.views               = set()
        self.path                = None
        self.app_dir             = app_dir
        self.main_thread         = threading.currentThread()

    def get(self, k):
        return getattr(self, k, None)

    def __call__(self, **props):
        return appdata_cm(props)

class appdata_cm:
    def __init__(self, props):
        self.props = props
        self.saved = {}

    def __enter__(self):
        for (k, v) in self.props.iteritems():
            if hasattr(appdata, k):
                self.saved[k] = getattr(appdata, k)
            setattr(appdata, k, v)

    def __exit__(self, type, value, tb):
        for (k, v) in self.saved.iteritems():
            setattr(appdata, k, v)

class public_cls:

    def __init__(self):
        self.entities = {}
        self.last_idx = 0
        self.places = {}
        self.mtimes = {}


    def __call__(self, *t):
        return public_reg(t)

    def print_public_keys(self):
        log('public keys:\n')
        for k in self.places.iterkeys():
            log('  {0}\n', k)

    def discard(self, ent):
        for p in ent._regs_:
            del self.places[p][ent._key_]

    def one(self, path):
        place = self.places.get(path)
        if not place:
            return None
        return place.values()[0]

    def all(self, path):
        place = self.places.get(path)
        if not place:
            return ()
        v = place.values()
        v.sort(key=lambda x:x._sort_key_)
        return v

    @staticmethod
    def find_dependencies(x, dep, visited):
        dependencies = ImportManager.GetDependencies(x)
        if x not in visited:
            visited.add(x)
            for v in dependencies:
                log("   {0}\n", v.__name__)
                dep.add(v)
                public_cls.find_dependencies(v, dep, visited)

    @staticmethod
    def check_dependency(x, y, visited):
        dependencies = ImportManager.GetDependencies(x)
        if x not in visited:
            visited.add(x)
            for v in dependencies:
                if v == y:
                    return True
                if public_cls.check_dependency(v, y, visited):
                     return True

        return False

    @staticmethod
    def module_compare(x, y):
        if public_cls.check_dependency(x, y, set()):
            return -1
        return 0

    def reimport(self):
        modules_to_reload   = set()
        dependent_modules   = set()

        for k, v in sys.modules.items():
            try:
                fname = v.__file__
                
                found = False
                for pre in ('framework', 'extensions', 'iso15926'):
                    if pre in fname:
                        found = True
                        break

                if not found:
                    continue

                if fname.endswith('.pyc') or fname.endswith('.pyo'):
                        fname = fname[:-1]
                stat = os.stat(fname)
            except:
                continue
            mtime = stat.st_mtime
            mtime -= stat.st_ctime # msw32
            old = self.mtimes.get(fname)
            if old is not None and old!=mtime:
                modules_to_reload.add(v)

            self.mtimes[fname] = mtime

        if len(modules_to_reload) == 0:
            return

        log('\n<<< REIMPORT >>>\n')

        for v in modules_to_reload:
            log("dependencies for {0}\n", v.__name__)
            public_cls.find_dependencies(v, dependent_modules, set())

        modules_to_reload = list(modules_to_reload | dependent_modules)

        modules_to_reload = sorted(modules_to_reload, cmp=public_cls.module_compare)

        for v in modules_to_reload:
            log("reloading {0}\n", v.__name__)
            reload(v)
   
        import framework.menu   
        framework.menu.AssignMenuBar(appdata.topwindow, 'workbench.menubar')


    def report_err(self):
        exc = traceback.format_exc()
        if QThread.currentThread() == QCoreApplication.instance().thread():
            log.now()
            log(exc)
        else:
            @public.mth
            def f():
                log.now()
                log(exc)

    def location(self):
        f = sys._getframe().f_back.f_back
        return 'file: "{0}" line: {1}'.format(f.f_code.co_filename, f.f_lineno)

    def collect_garbage(self):
        gc.collect()

class public_reg:

    def __init__(self, regs):
        self.regs = regs

    def __call__(self, ent):
        idx = public.last_idx
        public.last_idx += 1
        name = getattr(ent, '__name__', None)
        if name is None:
            name = '.'.join((ent.__class__.__name__, idx))
            ent.__name__  = name
        key = '.'.join((ent.__module__, name))
        sort_key = '{0}.({1:08}).{2}'.format(ent.__module__, idx, name)
        public.entities[key] = ent
        for p in self.regs:
            newplace = public.places.get(p)
            if newplace is None:
                newplace = {}
                public.places[p] = newplace
            newplace[key] = ent
        ent._key_ = key
        ent._sort_key_ = sort_key
        ent._regs_ = self.regs
        return ent

import pydoc
import pkgutil

class _Helper(pydoc.Helper):
    def listmodules(self, key=''):
        if key != '':
            pydoc.Helper.listmodules(self, key)
        else:
            self.output.write('''
Please wait a moment while I gather a list of all available modules...

''')
            modules = []
            for module_loader, name, ispkg in pkgutil.iter_modules():
                if '__main__' in name or '__init__' in name:
                    continue
                modules.append(name)
            self.list(modules)
            self.output.write('''
Enter any module name to get more help.  Or, type "modules spam" to search
for modules whose descriptions contain the word "spam".
''')

class BreakOperation(Exception):
    pass

class BreakTask(Exception):
    pass

root                    = sys.modules['__builtin__']
root._                  = lambda x: x
root.help               = _Helper()
root.public             = public_cls()
root.wizard             = wizard_cls()
public.wth              = lambda x: None
public.mth              = lambda x: None
public.BreakOperation   = BreakOperation
public.BreakTask        = BreakTask
root.appdata            = appdata_cls()

from framework.importmanager import ImportManager
ImportManager.enable()

import framework.log
log.open("dot15926.log")

from framework.appconfig import AppConfig
root.appconfig = AppConfig()
appconfig.TryToLoadSettings()

import _winreg
import site
try:
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Python\\PythonCore\\2.7\\PythonPath', 0, _winreg.KEY_READ)
    if key:
        PythonPath, tp = _winreg.QueryValueEx(key, '')
        for v in PythonPath.split(os.pathsep):
            site.addsitedir(v.encode(sys.getfilesystemencoding()))
except:
    pass
try:
    key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Python\\PythonCore\\2.7\PythonPath', 0, _winreg.KEY_READ)
    if key:
        PythonPath, tp = _winreg.QueryValueEx(key, '')
        for v in PythonPath.split(os.pathsep):
            site.addsitedir(v.encode(sys.getfilesystemencoding()))
except:
    pass 

appdata.path = sys.path[:]
for v in appconfig.get('sys.path', []):
    site.addsitedir(v.encode(sys.getfilesystemencoding()))

site.addsitedir(os.path.join(app_dir, 'lib'))

from framework.resources import ResourcesStorage, TextManager
appdata.resources_dir = 'resources'
root.tm = TextManager()

from framework.util import DaemonThread, Queue2

import framework
framework.Initialize()

import iso15926.tools.environment
import framework.workbench
import iso15926.common.testing

from framework.extensions import ExtensionManager
appdata.extension_manager = ExtensionManager()
appdata.extension_manager.LoadExtensions()

import re
font_expr = re.compile(r'font-size\s*:\s*\d*\s*px\s*;', re.MULTILINE | re.IGNORECASE)

class MainApp(QApplication):

    vis_label = '.15926 Editor v{0}{1}'.format(appdata.app_version, appdata.app_status)
    EVENT_AFTER_TYPE = QEvent.Type(QEvent.registerEventType())
    event_filters = set()

    def Init(self):
        self.installTranslator(tm._translator)
        appdata.app = self
        appdata.resources = ResourcesStorage()

        appconfig.CheckVersion()

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.UpdateAnims)
        self.anim_timer.start(500)
        self.anim_phase = 0

        self.worker_thread = self.Daemon()
        self.worker_thread2 = self.Daemon()
        public.mth = self.After
        public.wth = self.worker_thread.After
        public.wth2 = self.worker_thread2.After
        
        self.defaultfontsize = QApplication.font().pointSizeF()

        self.top = framework.workbench.Workbench()
        self.top.setWindowIcon(appdata.resources.GetIcon('elephant'))
        self.top.show()
        self.aboutToQuit.connect(self.OnQuit)

    def AddEventFilter(self, func):
        self.event_filters.add(func)

    def RemoveEventFilter(self, func):
        self.event_filters.discard(func)

    def OnQuit(self):
        pass

    def notify(self, receiver, evt):
        if evt.type() == QEvent.Wheel and evt.modifiers() & Qt.ControlModifier:
            appdata.app.SetFontSize(appconfig.get('fontsize', 1.0) + evt.delta()/1000.0)
            return True

        for f in list(self.event_filters):
            if f in self.event_filters and f(receiver, evt):
                return True
        
        return QApplication.notify(self, receiver, evt)

    def Daemon(self, func=None):
        th = DaemonThread()
        th.daemon = True
        th.start()
        if func is not None:
            th.After(func)
        return th

    def After(self, func):
        evt = QEvent(self.EVENT_AFTER_TYPE)
        evt.func = func
        QApplication.postEvent(self, evt)

    def customEvent(self, evt):
        if evt.type() == self.EVENT_AFTER_TYPE:
            evt.func()

    def SetStatus(self, msg=""):
        appdata.topwindow.SetStatus(msg)

    def UpdateAnims(self):
        anims = tuple(appdata.animated)
        for w in anims:
            w.Animate(self.anim_phase)
        self.anim_phase = self.anim_phase+1

    def SetFontSize(self, size):
        if size < 0.1 or size > 8:
            return
        newsize = self.defaultfontsize * size
        appconfig['fontsize'] = size
        appconfig.SaveSettings()
        f = QFont(QApplication.font())
        f.setPointSizeF(newsize)
        QApplication.setFont(f)
        appdata.topwindow.setStyleSheet('font-size: {0}pt;'.format(newsize))

public.reimport()
app = MainApp(sys.argv)
app.Init()
sys.exit(app.exec_())