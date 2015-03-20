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




import types
from PySide.QtCore import *
from PySide.QtGui import *
import framework.dialogs
import cPickle
import inspect
from collections import Iterable
import sys
import bisect
import rfc3987
import re
import keyword
import os

def GetPath(p):
    p = p.decode('utf-8')
    if not p.startswith('cfg://'):
        return p
    r = appconfig.get(p)
    if r:
        return r
    d, f = os.path.split(p)
    r = appconfig.get(d)
    if r:
        return os.path.join(r, f)
    return p

def Path2Name(p):
    p = p.decode('utf-8')
    if not p.startswith('cfg://'):
        return p
    if tm.main._haskey(p[6:]+'_name'):
        return tm.main.__getattr__(p[6:]+'_name')
    d, f = os.path.split(p)
    r = appconfig.get(d)
    if r:
        return f
    return p

def IsUri(text):
    try:
        rfc3987.parse(text, rule='URI')
    except:
        return False
    return True

def IsPyVariable(variable):
    return re.match("[_A-Za-z][_a-zA-Z0-9]*$",variable) and not keyword.iskeyword(variable)

def InsertToSortedModel(data, model, parent = None, depth = -1):
    if depth == 0:
        return
    if not parent:
        parent = model.invisibleRootItem()

    lst = [parent.child(i).text().lower() for i in xrange(parent.rowCount())]
    if isinstance(data, basestring):
        row = bisect.bisect_left(lst, data.lower())
        if row >= parent.rowCount() or parent.child(row).text() != data:
            item = QStandardItem(data)
            parent.insertRow(row, [item])
    elif isinstance(data, dict):
        keys = sorted(data.keys(), key = lambda x: x.lower())
        lst = sorted(lst + [v.lower() for v in keys])
        for v in keys:
            row = bisect.bisect_left(lst, v.lower())
            if row >= parent.rowCount() or parent.child(row).text() != v:
                item = QStandardItem(v)
                parent.insertRow(row, [item])
            else:
                item = parent.child(row)
            InsertToSortedModel(data[v], model, item, depth - 1)
    elif isinstance(data, Iterable):
        keys = sorted(data, key = lambda x: x.lower())
        lst = sorted(lst + [v.lower() for v in keys])
        for v in keys:
            row = bisect.bisect_left(lst, data.lower())
            if row >= parent.rowCount() or parent.child(row).text() != v:
                item = QStandardItem(v)
                parent.insertRow(row, [item])

def DeleteFromSortedModel(data, model, parent = None):
    if not parent:
        parent = model.invisibleRootItem()

    if not parent.rowCount():
        return

    lst = [parent.child(i).text().lower() for i in xrange(parent.rowCount())]
    if isinstance(data, basestring):
        row = bisect.bisect_left(lst, data.lower())
        if row < parent.rowCount() and parent.child(row).text() == data:
            parent.removeRow(bisect.bisect_left(lst, data.lower()))
    elif isinstance(data, dict):
        keys = sorted(data.keys(), key = lambda x: x.lower())
        for v in reversed(keys):
            row = bisect.bisect_left(lst, v.lower())
            if row < parent.rowCount() and parent.child(row).text() == v:
                item = parent.child(row)
                DeleteFromSortedModel(data[v], model, item)
                if item.rowCount() == 0:
                    parent.removeRow(row)
    elif isinstance(data, Iterable):
        keys = sorted(data, key = lambda x: x.lower())
        for v in reversed(keys):
            row = bisect.bisect_left(lst, v.lower())
            if row < parent.rowCount() and parent.child(row).text() == v:
                parent.removeRow(row)

def GenerateSortedModel(data, model = None, parent = None, depth = -1):
    if not model:
        model = QStandardItemModel()
    if depth == 0:
        return model
    if not parent:
        parent = model.invisibleRootItem()

    if isinstance(data, basestring):
        item = QStandardItem(data)
        parent.appendRow(item)
    elif isinstance(data, dict):
        for k in sorted(data.iterkeys(), key = lambda x: x.lower()):
            item = QStandardItem(k)
            parent.appendRow(item)
            GenerateSortedModel(data[k], model, item, depth - 1)
    elif isinstance(data, Iterable):
        for v in sorted(data, key = lambda x: x.lower()):
            item = QStandardItem(v)
            parent.appendRow(item)
    return model


def GenerateModel(data, model = None, parent = None, depth = -1):
    if not model:
        model = QStandardItemModel()
    if depth == 0:
        return model
    if not parent:
        parent = model.invisibleRootItem()

    if isinstance(data, basestring):
        item = QStandardItem(data)
        parent.appendRow(item)
    elif isinstance(data, dict):
        for k, v in data.iteritems():
            item = QStandardItem(k)
            parent.appendRow(item)
            GenerateModel(v, model, item, depth - 1)
    elif isinstance(data, Iterable):
        for v in data:
            item = QStandardItem(v)
            parent.appendRow(item)
    return model

class ModelCompleter(QCompleter):
    def __init__(self, parent, multi = False, sep = ' '):
        QCompleter.__init__(self, parent)
        self.multi = multi
        self.sep = sep

    def pathFromIndex(self, index):
        model = self.model()
        role = self.completionRole()
        i = index;
        data = []
        while i.isValid():
            data.append(model.data(i, role))
            i = i.parent()

        if self.multi:
            txt = None
            if isinstance(self.widget(), QComboBox):
                txt = self.widget().currentText()
            if txt:
                res = re.match(r'(.+{0}\s*)(?!{0})\s*\S*$'.format(re.escape(self.sep)), txt)
                if res:
                    return res.group(1)+'.'.join(reversed(data))
        return '.'.join(reversed(data))

    def splitPath(self, path):
        if self.multi:
            res = re.match(r'.+{0}\s*(?!{0})\s*(\S*)$'.format(re.escape(self.sep)), path)
            if res:
                path = res.group(1)
        if path.endswith('.'):
            path = path[-1]
        return path.split('.')

def fileline(offset):
    callerframerecord = inspect.stack()[offset]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    filename = info.filename
    lineno = info.lineno
    return (filename, lineno)

class Flags():
    def __init__(self, string):
        for f in string.split():
            setattr(self, f, frozenset([f]))

def IsChild(parent, child):
    while child:
        if child == parent:
            return True
        pw = child.parentWidget()
        if sys.getrefcount(pw) == 2:
            pw.__pw = pw
        child = pw
    return False

def CanAcceptFocus(widget, policy):
    focus = widget
    while focus.focusProxy():
        focus = focus.focusProxy()

    if (widget.focusPolicy() & policy) != policy:
        return False

    if widget != focus and (focus.focusPolicy() & policy) != policy:
        return False

    return True

def FindFocusTarget(widget, policy):
    while widget:
        if widget.isEnabled() and (CanAcceptFocus(widget, policy) or isinstance(widget, QAction)):
            return widget
        if widget.isWindow():
            break;
        pw = widget.parentWidget()
        if sys.getrefcount(pw) == 2:
            pw.__pw = pw
        widget = pw

class FileBrowseButton(QWidget):
    def __init__(self, parent, text = '', wildcard = ''):
        QWidget.__init__(self, parent)
        self.edit = QLineEdit(self)
        self.edit.setText(text)
        self.button = QPushButton(tm.main.browse, self)
        self.button.clicked.connect(self.OnBrowseClick)
        self.wildcard = wildcard

        layout = QHBoxLayout(self)
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        layout.setContentsMargins(0,0,0,0)

    def OnBrowseClick(self):
        path, wildcard = framework.dialogs.SelectFiles(tm.main.choose_file, wildcard = self.wildcard)
        if path:
            self.edit.setText(path)

    def GetPath(self):
        return self.edit.text()

def findcommonmethod(items, method):
    found = None
    for v in items:
        m = getattr(v, method, None)
        if not m:
            return None
        if not found:
            found = m
        elif found is not m:
            return None

    if isinstance(found, types.FunctionType):
        def f(*t, **d):
            return found(items, *t, **d)
        return f
    elif len(items)==1:
        return found


def SetClipboard(text = None, mimedata = None):
    clipboardMimeData    = QMimeData()

    if text:
        clipboardMimeData.setText(text)

    if mimedata:
        for mime, data in mimedata.iteritems():
            itemData    = QByteArray()
            dataStream  = QDataStream(itemData, QIODevice.WriteOnly)
            dataStream.writeString(cPickle.dumps(data))
            clipboardMimeData.setData(mime, itemData)

    QApplication.clipboard().setMimeData(clipboardMimeData)    

def CheckClipboard(mime = None):
    if mime:
        mimeData    = QApplication.clipboard().mimeData()
        if mimeData and mimeData.hasFormat(mime):
            return True
    return False


def GetClipboard(mime = None):
    mimeData = QApplication.clipboard().mimeData()
    if mimeData:
        if mime:
            encodedData = mimeData.data(mime)
            if encodedData:
                dataStream = QDataStream(encodedData, QIODevice.ReadOnly)
                return cPickle.loads(str(dataStream.readString()))
        else:
            return str(mimeData.text())
    return None

import urllib
import requests
from requests.auth import HTTPDigestAuth

import urllib2
from urllib2 import OpenerDirector
from ntlm import HTTPNtlmAuthHandler

class Result:
    def __init__(self, code, content, headers, error):
        self.code = code
        self.content = content
        self.headers = headers
        self.error   = error

class Session:
    def __init__(self, uri, login=None, password=None):
        if login and password:
            self.session = requests.session(auth=HTTPDigestAuth(login, password))
        else:
            self.session = requests.session()

    def Open(self, uri, headers = {}):
        r = requests.get(uri, session=self.session, headers=headers, allow_redirects=True, timeout=60)
        return Result(r.status_code, r.content, r.headers, r.error)

class NTLMSession:
    def __init__(self, uri, login=None, password=None):
        if login and password:
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, uri, login, password)
            auth_NTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)
            self.opener = urllib2.build_opener(auth_NTLM)
        else:
            self.opener = urllib2.build_opener()

    def Open(self, uri, headers = {}):
        request = urllib2.Request(uri, headers=headers, timeout=60)
        r = self.opener.open(request)
        return Result(r.code, r.read(), r.headers, '')

class DictDecoder:

    def __init__(self, dict_tp = None, list_tp = None):
        self.dict_tp = dict_tp if dict_tp else dict
        self.list_tp = list_tp if list_tp else list

    def __call__(self, data):
        return self._decode_dict(data)

    def _decode_list(self, data):
        rv = self.list_tp()
        for item in data:
            if isinstance(item, unicode):
                item = item.encode('utf-8')
            elif isinstance(item, list):
                item = self._decode_list(item)
            elif isinstance(item, dict):
                item = self._decode_dict(item)
            rv.append(item)
        return rv

    def _decode_dict(self, data):
        rv = self.dict_tp()
        for key, value in data.iteritems():
            if isinstance(key, unicode):
               key = key.encode('utf-8')
            if isinstance(value, unicode):
               value = value.encode('utf-8')
            elif isinstance(value, list):
               value = self._decode_list(value)
            elif isinstance(value, dict):
               value = self._decode_dict(value)
            rv[key] = value
        return rv


import threading, Queue, ctypes

class TaskTarget:

    def AddTask(self, task):
        if getattr(self, '_tasks', None) == None:
            self._tasks = set()
        self._tasks.add(task)

    def RemoveTask(self, task):
        self._tasks.discard(task)       

    def HasTasks(self):
        if getattr(self, '_tasks', None):
            return bool(self._tasks)
        return False

    def ClearTasks(self):
        if getattr(self, '_tasks', None):
            for v in list(self._tasks):
                v.Stop()

class Task():
    def __init__(self, name, targets, func, thread):
        self.name = name
        self.targets = targets
        self.func = func
        self.thread = thread
        for v in self.targets:
            v.AddTask(self)

    def __call__(self):
        @public.mth
        def f(): 
            appdata.app.SetStatus(self.name)
        self.func()
    
    def Stop(self):
        self.thread.Stop(self)

    def Clear(self):
        @public.mth
        def f():
            appdata.app.SetStatus('')
            for v in self.targets:
                v.RemoveTask(self)

class Queue2(Queue.Queue):
    def remove(self, item):
        with self.mutex:
            if item in self.queue:
                self.queue.remove(item)
                return True
            return False

import time

class DaemonThread(threading.Thread):

    wait_time = 0.025

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.mutex      = threading.Lock()
        self.event      = threading.Event()
        self.queue      = Queue2()
        self.task       = None

    def run(self):
        while True:
            try:
                self.event.clear()
                with self.mutex:
                    self.task = self.queue.get_nowait()

                if self.task is None:
                    break

                self.task()

            except public.BreakTask:
                pass

            except Queue.Empty:
                time.sleep(self.wait_time)

            finally:
                if self.task:
                    self.task.Clear()
                    self.event.set()
                    with self.mutex:
                        self.task = None
                        
    def GetCurrentTask(self):
        with self.mutex:
            return self.task

    def Stop(self, task):
        if not self.queue.remove(task):
            with self.mutex:
                if task == self.task:
                    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, ctypes.py_object(public.BreakTask))
                    if res > 1:
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
                    self.event.wait()

    def Close(self):
        if self.is_alive():
            self.queue.put(None)
            self.join()

    def After(self, name = '', *targets):
        def f(func):    
            task = Task(name, targets, func, self)
            self.queue.put(task)
        return f

class HashableDict(dict):
    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return id(self) == id(other)

from contextlib import contextmanager

@contextmanager
def timeit_context(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print('[{0}] finished in {1} ms'.format(name, int(elapsedTime * 1000)))


class DataFormatError(Exception):
    def __init__(self, path, info = ''):
        self.path = path
        self.info = info

    def __str__(self):
        return tm.main.data_format_error.format(self.path)
