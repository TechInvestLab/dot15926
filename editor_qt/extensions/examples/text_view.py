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
This is an example how simple text view functionality
can be implemented as extension to .15926 Editor.
"""
from PySide.QtCore import *
from PySide.QtGui import *
import framework

"""View class should inherit  from framework.View class
Base class is subclass of QDockWidget with some additional methods.
Feel free to use PySide broadly"""

class TextView(framework.View):
    vis_label = tm.example.txt_view

    def __init__(self, parent):
        framework.View.__init__(self, parent)

        widget = QWidget(self)
        self.textfield = QTextEdit(widget)
        self.textfield.setText(self.document.MyText)
        self.textfield.textChanged.connect(self.OnText)
        layout = QVBoxLayout(widget)
        layout.addWidget(self.textfield)
        """wizard is event service, following 
        line subscribes for event from target document"""
        wizard.Subscribe(self.document, self)
        self.setWidget(widget)
        
    def W_TextDocChanged(self, doc):
        """Here we handle subscribed event"""
        self.textfield.textChanged.disconnect(self.OnText)
        self.UpdateView()
        self.textfield.textChanged.connect(self.OnText)

    def OnText(self):
        wizard.Unsubscribe(self.document, self)
        self.document.MyText = self.textfield.toPlainText()
        wizard.Subscribe(self.document, self)

    def UpdateView(self):
        self.textfield.setText(self.document.MyText)

    def GetLabel(self):
        return self.vis_label  

    def OnDestroy(self):
        wizard.Unsubscribe(self.document, self) 
