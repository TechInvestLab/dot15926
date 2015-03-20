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




import sys
import time
import datetime
import pprint
import traceback
import inspect
import threading
from PySide.QtCore import *
import re

expr1 = re.compile(r'^(.)', re.MULTILINE)
expr2 = re.compile(r'.^(.)', re.MULTILINE)

class Log:

    def __init__(self):
        self.opened = False
        self.filename = None
        self.output = None
        self.pre = []
        self.newline = True

    def exception(self):
        self.write(traceback.format_exc())

    def info(self, fmt = '', offset = 1):
        callerframerecord = inspect.stack()[offset]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        filename = info.filename
        lineno = info.lineno
        self.write('<%s:%s>\n%s'%(filename, lineno, fmt))

    def line(self):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        lineno = info.lineno
        self.write('line: %i\n'%lineno)

    def stack(self):
        data = ''.join(traceback.format_stack()[:-2])
        self.write(data)

    def now(self):
        self.time = -1
        self.write('')

    def open(self, filename=None):
        self.old_stderr = sys.stderr
        self.old_stdout = sys.stdout
        sys.stderr = self
        sys.stdout = self
        self.filename = filename
        self.opened = True
        if self.filename:
            with open(self.filename, 'w') as f:
                pass
        self('Date: ')
        self(datetime.datetime.now().strftime("%Y-%m-%d\n"))

    def setoutput(self, output):
        self.output = output
        self.output(''.join(self.pre))

    def close(self):
        if self.opened:
            sys.stderr = self.old_stderr
            sys.stdout = self.old_stdout
            self.opened = False
            self.filename = None

    def p(self, data):
        self.write(pprint.pformat(data))

    def __call__(self, fmt, *t):
        if t:
            fmt = fmt.format(*t)
        self.write(fmt)
        return self

    def rep(self, fmt, *t):
        if t:
            fmt = fmt.format(*t)
        self.write(fmt)

    def write(self, text):
        time = datetime.datetime.now()
        if threading.currentThread() == appdata.main_thread:
            self._write(text, time)
        else:
            @public.mth
            def f():
                self._write(text, time)

    def _write(self, text, time = None):
        if time:
            timestamp = '[%s]: \\1'%(time.strftime("%H:%M:%S.%f")[:-3])
            if self.newline:
                text = re.sub(expr1, timestamp, text)
            else:
                text = re.sub(expr2, timestamp, text)
        self.newline = text.endswith('\n')

        try:
            if self.old_stdout.encoding:
                std_text = text.encode(self.old_stdout.encoding, 'ignore')
            else:
                std_text = text
            self.old_stdout.write(std_text)
        except:
            pass

        if self.filename:
            with open(self.filename, 'ab') as f:
                f.write(text)
        self.pre.append(text)
        if self.output:
            self.output(text)

if not getattr(sys.modules['__builtin__'], 'log', None):
    sys.modules['__builtin__'].log = Log()
