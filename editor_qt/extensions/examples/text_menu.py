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

import extensions.examples.example_menu
from extensions.examples.text_doc import TextDoc
import framework.dialogs

"""
To add a sub-item to an item declare new class with public('<menu_content>')  decorator, where <menu_content> is path to menu sub-item defined in menu item class.
Class attributes:
	vis_label: Text label of new menu sub-item.
Class methods:
	Update(cls, action): Update callback of QAction, passed as 'action' argument.
	Do(cls): Action required on menu click.

"""
@public('dot15926.menu.example_menu')
class xTextMenuItem:
    vis_label = tm.example.menu_open_txt

    @classmethod
    def Do(cls):
        path, wildcard = framework.dialogs.SelectFiles(tm.example.open_txt_title)
        if not path:
            return

        doc = TextDoc()
        doc.OpenFiles([path])
        appdata.project.AddDocument(doc)
