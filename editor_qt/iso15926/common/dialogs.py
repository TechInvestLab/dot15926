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
from framework.dialogs import PopDialog
from framework.dialogs import OkCancelDialog


class DataFormatErrorDialog(QDialog):
    def __init__(self, msg, info):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(tm.main.data_format_error_title)
        self.msg = QLabel(msg, self)
        self.btn_ok = QPushButton(tm.main.ok, self)
        self.btn_info  = QPushButton(tm.main.btn_more_info, self)
        self.info = QPlainTextEdit(self)
        self.info.appendPlainText(info)
        self.info.setReadOnly(True)
        self.info.setVisible(False)

        self.btn_ok.clicked.connect(lambda: self.reject())
        self.btn_info.clicked.connect(lambda: self.toggle_info())

        layout_btn = QHBoxLayout()
        layout_btn.addWidget(self.btn_info)
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_ok)
        layout = QVBoxLayout(self)
        layout.addWidget(self.msg)
        layout.addLayout(layout_btn)
        layout.addWidget(self.info)
        self.exec_()

    def toggle_info(self):
        if not self.info.isVisible():
            self.btn_info.setText(tm.main.btn_less_info)
            self.info.setVisible(True)
        else:
            self.btn_info.setText(tm.main.btn_more_info)
            self.info.setVisible(False)

        self.layout().update()
        self.setMinimumHeight(self.layout().minimumSize().height())
        r = self.geometry()
        r.setHeight(self.layout().minimumSize().height())
        self.setGeometry(r)

class CopyNotify(QDialog):

    RESULT_YES = 0
    RESULT_NO = 1
    RESULT_YES_ALL = 2
    RESULT_NO_ALL = 3

    vis_label = tm.main.copy_entity_title
    vis_info = tm.main.copy_entity_info
    def __init__(self, uri):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)

        self.btn_yes = QPushButton(tm.main.yes, self)
        self.btn_yes_all = QPushButton(tm.main.yes_all, self)

        self.btn_no = QPushButton(tm.main.no, self)
        self.btn_no_all = QPushButton(tm.main.no_all, self)

        self.btn_yes.clicked.connect(lambda: self.done(self.RESULT_YES))
        self.btn_yes_all.clicked.connect(lambda: self.done(self.RESULT_YES_ALL))
        self.btn_no.clicked.connect(lambda: self.done(self.RESULT_NO))
        self.btn_no_all.clicked.connect(lambda: self.done(self.RESULT_NO_ALL))

        label = QLabel(self.vis_info.format(uri), self)
        layout = QVBoxLayout(self)
        layout.addWidget(label)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_yes)
        layout_btn.addWidget(self.btn_yes_all)
        layout_btn.addWidget(self.btn_no)
        layout_btn.addWidget(self.btn_no_all)
        layout.addLayout(layout_btn)


class CopyPropertiesNotify(QDialog):

    RESULT_REPLACE = 0
    RESULT_REPLACE_ALL = 1
    RESULT_ADD = 2
    RESULT_ADD_ALL = 3
    RESULT_SKIP = 4
    RESULT_SKIP_ALL = 5

    vis_label = tm.main.copy_property_title
    vis_info = tm.main.copy_property_info

    def __init__(self, uri, predicate, old_value, new_value):
        QDialog.__init__(self, appdata.topwindow, Qt.WindowSystemMenuHint | Qt.WindowTitleHint)
        self.setWindowTitle(self.vis_label)

        self.btn_replace = QPushButton(tm.main.replace, self)
        self.btn_replace_all = QPushButton(tm.main.replace_all, self)

        self.btn_add = QPushButton(tm.main.add, self)
        self.btn_add_all = QPushButton(tm.main.add_all, self)

        self.btn_skip = QPushButton(tm.main.skip, self)
        self.btn_skip_all = QPushButton(tm.main.skip_all, self)

        self.btn_replace.clicked.connect(lambda: self.done(self.RESULT_REPLACE))
        self.btn_replace_all.clicked.connect(lambda: self.done(self.RESULT_REPLACE_ALL))
        self.btn_add.clicked.connect(lambda: self.done(self.RESULT_ADD))
        self.btn_add_all.clicked.connect(lambda: self.done(self.RESULT_ADD_ALL))
        self.btn_skip.clicked.connect(lambda: self.done(self.RESULT_SKIP))
        self.btn_skip_all.clicked.connect(lambda: self.done(self.RESULT_SKIP_ALL))

        label = QLabel(self.vis_info%(uri, predicate, old_value, new_value), self)
        layout = QVBoxLayout(self)
        layout.addWidget(label)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch(1)
        layout_btn.addWidget(self.btn_replace)
        layout_btn.addWidget(self.btn_replace_all)
        layout_btn.addWidget(self.btn_add)
        layout_btn.addWidget(self.btn_add_all)
        layout_btn.addWidget(self.btn_skip)
        layout_btn.addWidget(self.btn_skip_all)
        layout.addLayout(layout_btn)

class AddProperty(OkCancelDialog):
    vis_label = tm.main.add_property_title
    msg_property = tm.main.property_field
    msg_value = tm.main.value_field

    def __init__(self, callback, prop_list):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback
        self.props = list(prop_list)
        self.props.sort()
        self.wnd_prop = QComboBox(self)
        self.wnd_prop.addItems(self.props)
        self.wnd_value = QPlainTextEdit(self)
        self.wnd_value.setTabChangesFocus(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_property, self))
        layout.addWidget(self.wnd_prop)
        layout.addWidget(QLabel(self.msg_value, self))
        layout.addWidget(self.wnd_value)
        self.AddButtons(layout)
        if self.exec_()==QDialog.Accepted:
            self.callback((str(self.wnd_prop.currentText()).strip(), str(self.wnd_value.toPlainText()).strip()))
        else:
            self.callback(None)

class AddAsProperty(OkCancelDialog):
    vis_label = tm.main.add_as_property_title
    msg_property = tm.main.property_field
    msg_object = tm.main.object_field

    def __init__(self, callback, uri, prop_list):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback
        self.props = list(prop_list)
        self.props.sort()
        self.wnd_prop = QComboBox(self)
        self.wnd_prop.addItems(self.props)
        self.wnd_value = QLineEdit(uri, self)
        self.wnd_value.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_property, self))
        layout.addWidget(self.wnd_prop)
        layout.addWidget(QLabel(self.msg_object, self))
        layout.addWidget(self.wnd_value)
        self.AddButtons(layout)
        if self.exec_()==QDialog.Accepted:
            self.callback((str(self.wnd_prop.currentText()).strip(), str(self.wnd_value.text()).strip()))
        else:
            self.callback(None)

class CreateInstance(OkCancelDialog):
    vis_label = tm.main.create_instance_title
    msg_type = tm.main.type_field
    msg_label = tm.main.label_field
    msg_uri = tm.main.uri_auto_field

    def __init__(self, callback, etype):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback
        self.wnd_type = QLineEdit(etype, self)
        self.wnd_type.setReadOnly(True)

        self.wnd_label = QLineEdit(self)
        self.wnd_label.setFocus()
        self.wnd_uri = QLineEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_type, self))
        layout.addWidget(self.wnd_type)
        layout.addWidget(QLabel(self.msg_label, self))
        layout.addWidget(self.wnd_label)
        layout.addWidget(QLabel(self.msg_uri, self))
        layout.addWidget(self.wnd_uri)
        self.AddButtons(layout)
        if self.exec_()==QDialog.Accepted:
            self.callback((str(self.wnd_label.text()).strip(), str(self.wnd_uri.text()).strip()))
        else:
            self.callback(None)

class CreateTemplate(OkCancelDialog):
    vis_label = tm.main.create_template_title
    msg_supertemplate = tm.main.parent_template_field
    msg_label = tm.main.label_field
    msg_comment = tm.main.comment_field
    msg_uri = tm.main.uri_auto_field

    def __init__(self, callback, supertemplate=None):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback
        if supertemplate:
            self.wnd_supertemplate = QLineEdit(supertemplate, self)
            self.wnd_supertemplate.setReadOnly(True)

        self.wnd_label = QLineEdit(self)
        self.wnd_label.setFocus()
        self.wnd_comment = QPlainTextEdit(self)
        self.wnd_comment.setTabChangesFocus(True)
        self.wnd_uri = QLineEdit(self)

        layout = QVBoxLayout(self)
        if supertemplate:
            layout.addWidget(QLabel(self.msg_supertemplate, self))
            layout.addWidget(self.wnd_supertemplate)
        layout.addWidget(QLabel(self.msg_label, self))
        layout.addWidget(self.wnd_label)
        layout.addWidget(QLabel(self.msg_comment, self))
        layout.addWidget(self.wnd_comment)
        layout.addWidget(QLabel(self.msg_uri, self))
        layout.addWidget(self.wnd_uri)
        self.AddButtons(layout)
        if self.exec_()==QDialog.Accepted:
            self.callback((str(self.wnd_label.text()).strip(), str(self.wnd_comment.toPlainText()).strip(), str(self.wnd_uri.text()).strip()))
        else:
            self.callback(None)

class AddRole(OkCancelDialog):
    vis_label = tm.main.add_role_title
    msg_label = tm.main.label_field
    msg_uri = tm.main.uri_field
    msg_comment = tm.main.comment_field

    def __init__(self, callback):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback
        self.wnd_label = QLineEdit(self)
        self.wnd_label.setFocus()
        self.wnd_comment = QPlainTextEdit(self)
        self.wnd_comment.setTabChangesFocus(True)
        self.wnd_uri = QLineEdit(self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_label, self))
        layout.addWidget(self.wnd_label)
        layout.addWidget(QLabel(self.msg_comment, self))
        layout.addWidget(self.wnd_comment)
        layout.addWidget(QLabel(self.msg_uri, self))
        layout.addWidget(self.wnd_uri)
        self.AddButtons(layout)
        if self.exec_()==QDialog.Accepted:
            self.callback((str(self.wnd_label.text()).strip(), str(self.wnd_comment.toPlainText()).strip(), str(self.wnd_uri.text()).strip()))
        else:
            self.callback(None)

from iso15926.io.sparql import SparqlConnection
import urlparse

class OpenEndpoint(OkCancelDialog):

    vis_label = tm.main.open_endpoint_title
    msg_uri = tm.main.endpoint_uri_field
    msg_login = tm.main.endpoint_login_field
    msg_pasword = tm.main.endpoint_password_field
    msg_connecting = tm.main.endpoint_connecting
    msg_401 = tm.main.endpoint_401
    msg_notfound = tm.main.endpoint_notfound
    msg_error = tm.main.endpoint_error

    def __init__(self, label=None):
        OkCancelDialog.__init__(self, label=label or self.vis_label)
        self.wnd_uri = QLineEdit(self)
        self.wnd_login = QLineEdit(self)
        self.wnd_password = QLineEdit(self)
        self.wnd_password.setEchoMode(QLineEdit.Password)
        self.wnd_report = QPlainTextEdit(self)
        self.wnd_report.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_uri, self))
        layout.addWidget(self.wnd_uri)
        layout.addWidget(QLabel(self.msg_login, self))
        layout.addWidget(self.wnd_login)
        layout.addWidget(QLabel(self.msg_pasword, self))
        layout.addWidget(self.wnd_password)

        box = QGroupBox(tm.main.connection_log, self)
        layout.addWidget(box)
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(self.wnd_report)
        self.AddButtons(layout)

        self.connection = None
        self.exec_()

    def accept(self):
        self.uri = str(self.wnd_uri.text()).strip()
        parsed = urlparse.urlparse(self.uri)
        if parsed.username and parsed.password:
            self.login = parsed.username
            self.password = parsed.password
            s1 = self.uri.split('//', 1)[0]
            s2 = self.uri.split('@', 1)[-1]
            self.uri = s1+'//'+s2
        else:
            self.login = str(self.wnd_login.text())
            self.password = str(self.wnd_password.text())
        self.wnd_report.setPlainText(self.msg_connecting.format(self.uri))
        self.connection = SparqlConnection(self.uri, self.login, self.password)
        if self.connection.connected:
            OkCancelDialog.accept(self)
            return
        if self.connection.last_err==401:
            self.wnd_report.appendPlainText(self.msg_401)
        elif self.connection.last_err==0:
            self.wnd_report.appendPlainText(self.msg_notfound)
        else:
            self.wnd_report.appendPlainText(self.msg_error.format(self.connection.last_err))
        self.connection = None

class AddPetternRole(OkCancelDialog):
    vis_label = tm.main.add_role_title
    msg_role = tm.main.role_field
    msg_value = tm.main.value_field

    def __init__(self, callback, roles, values):
        OkCancelDialog.__init__(self, label=self.vis_label)
        self.callback = callback

        self.wnd_role = QComboBox(self)
        self.wnd_role.setEditable(True)
        self.wnd_role.addItems(sorted(list(roles)))

        self.wnd_value = QComboBox(self)
        self.wnd_value.setEditable(True)
        self.wnd_value.addItems(sorted(list(roles)))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.msg_role, self))
        layout.addWidget(self.wnd_role)
        layout.addWidget(QLabel(self.msg_value, self))
        layout.addWidget(self.wnd_value)
        self.AddButtons(layout)
 
        if self.exec_()==QDialog.Accepted:
            self.callback( str(self.wnd_role.text()).strip(), str(self.wnd_value.text()).strip() )
        else:
            self.callback(None)

