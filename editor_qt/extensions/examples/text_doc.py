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

"""
This is an example how simple view and edit functionality is implemented 
for a text file as extension to .15926 Editor.
"""
import framework
from extensions.examples.text_view import TextView


"""Any document type should be registered in framework with the following decorator.
It is necessary to guarantee document save and reload in configuration file."""

@public('dot15926.doctypes')
class TextDoc(framework.Document):

    def __init__(self):
        """In constructor super class must be initialized
        and selected desired view type for document"""
        framework.Document.__init__(self)
        self.viewtype = type('', (TextView,), dict(document=self))
        self.my_text = ''   

    @property
    def MyText(self):
        return self.my_text

    @MyText.setter
    def MyText(self, value):
        text_changed = self.my_text != value
        self.my_text = value
        """Next lines switch state to state_changed, so document will be marked with star"""
        if text_changed:
            self.ChangeState(self.state_changed)
            """Rise event telling views that text was chenged""" 
            wizard.W_TextDocChanged(self)       

    def OpenFiles(self, paths, readonly=False, **props):
        """To properly register document in project
        this function must be overloaded."""
        self.ChangeState(self.state_loading)
        """@public.wth() and @public.mth are threads decorators.
        public.wth is the worker thread while public.mth is the main.
        Here a trick how implement async loading for document"""
        @public.wth('Loading {0}...'.format(self.name), self)
        def f1():
            try:
                text = ''
                for v in paths:
                    with open(v, 'r') as f:
                        text = text + f.read()
                @public.mth
                def f2():
                    """Note that here you should change state to actual value."""
                    self.MyText = text
                    self.paths = paths
                    self.ChangeState(self.state_loaded)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)

    def Save(self):
        if not self.CanSave():
            return
        self.ChangeState(self.state_saving)
        @public.wth(tm.example.saving_doc.format(self.name), self)
        def f1():
            try:
                with open(self.paths[0], 'w') as f:
                    f.write(self.MyText)
                @public.mth
                def f2():
                    self.ChangeState(self.state_loaded)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)

    def SaveAs(self):
        if not self.CanSaveAs():
            return
        path, wildcard = framework.dialogs.SaveAs()
        """Next line validates path - we don't want to overwrite opened file"""
        if not path or not self.VerifySavePath(path):
            return
        self.ChangeState(self.state_saving)
        @public.wth(tm.example.saving_doc.format(self.name), self)
        def f1():
            try:
                with open(path, 'w') as f:
                    f.write(self.MyText)
                @public.mth
                def f2():
                    self.paths = [path]
                    self.ChangeState(self.state_loaded)
            except:
                log.exception()
                @public.mth
                def f3():
                    self.ChangeState(self.state_unavailable)