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




import framework.console
from iso15926.tools.environment import EnvironmentContext
from collections import deque
import sys
import pprint
import framework.console
from PySide.QtCore import *
from PySide.QtGui import *

class PseudoFileIn:

    def __init__(self, readline, readlines=None):
        if callable(readline):
            self.readline = readline
        else:
            raise ValueError, 'readline must be callable'
        if callable(readlines):
            self.readlines = readlines

    def readline(self):
        pass

    def write(self, s):
        pass

    def writelines(self, l):
        map(self.write, l)

    def flush(self):
        pass

    def isatty(self):
        return 1

class PythonConsole(framework.console.Console):
    vis_label = tm.main.python_console

    TYPE_STRING    = 0
    TYPE_FILE      = 1

    def __init__(self, parent):
        framework.console.Console.__init__(self, parent, self.ExecutePythonString, self.ExecutePythonFile)
        log.setoutput(self.AddText)
        self.context = EnvironmentContext()
        self.reader = PseudoFileIn(self.readline, self.readlines)
        self.reader.input = ''
        self.reader.isreading = False
        sys.stdin = self.reader
        self.queue = deque()
        self.running = False

    def readline(self):
        input = ''
        reader = self.reader
        reader.isreading = True
        try:
            while not reader.input:
                QCoreApplication.processEvents()
            input = reader.input
        finally:
            reader.input = ''
            reader.isreading = False
        input = str(input)  # In case of Unicode.
        return input

    def readlines(self):
        """Replacement for stdin.readlines()."""
        lines = []
        while lines[-1:] != ['\n']:
            lines.append(self.readline())
        return lines

    def Run(self, type, param):

        self.queue.append((type, param))

        if self.running:
            return

        self.running = True
        try:
            while self.queue:
                type, param = self.queue.pop()

                self.context.Update()

                if type == self.TYPE_FILE:
                    self.context.ExecutePythonFile(param)

                elif type == self.TYPE_STRING:
                    if self.context.GetEnvironment():
                        appdata.environment_manager.latest_console_input = param

                    res = self.context.ExecutePythonString(param)
                    if res is not None:
                        pprint.pprint(res)
        finally:
            self.running = False

    def ExecutePythonFile(self, filename):
        self.Run(self.TYPE_FILE, filename)

    def ExecutePythonString(self, text):
        if self.reader.isreading:
            self.reader.input = text
        else:
            self.Run(self.TYPE_STRING, text)


