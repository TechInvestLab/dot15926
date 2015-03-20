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




import iso15926.common.dialogs as dialogs
from framework.dialogs import Notify, Choice
from _ordereddict import ordereddict


def GenPartName(option, default = None):
    if default:
        i = 0
        name_gen = default
    else:
        i = 1
        name_gen = 'entity%i'%i

    while True:
        for p in option['parts']:
            if 'self' in p and p['self']==name_gen:
                break
        else:
            return name_gen
        i += 1
        name_gen = 'entity%i'%i

class DocumentPropertyChange():
    props_change = True
    
    def __init__(self, doc, prop, value):
        self.doc = doc
        self.prop = prop
        self.value = value

    def Redo(self):
        self.old_value = getattr(self.doc, self.prop, None)
        if self.old_value == self.value:
            return False
        self.doc.UpdateProps({self.prop: self.value})
        return True

    def Undo(self):
        self.doc.UpdateProps({self.prop: self.old_value})
        self.doc.RefreshProps()

class DocumentModifyPatterns():

    def __init__(self, doc, pattern, delete = False, new = True):
        self.doc = doc
        self.pattern = pattern
        self.delete = delete
        self.new = new

    def Redo(self):
        if self.delete:
            if self.pattern['name'] not in self.doc.patterns or self.doc.patterns[self.pattern['name']] != self.pattern:
                return False
            del self.doc.patterns[self.pattern['name']]
            wizard.W_PatternDeleted(self.pattern)
        else:
            if not self.new:
                counter = 1
                name = self.pattern['name']
                while name:
                    for p in self.doc.patterns.iterkeys():
                        if name == p:
                            name = '%s%i'%(self.pattern['name'], counter)
                            counter += 1
                            break
                    else:
                        self.pattern['name'] = name
                        break
            if self.pattern['name'] in self.doc.patterns:
                Notify(tm.main.pattern_already_exist)
                return False
            self.doc.patterns[self.pattern['name']] = self.pattern
            wizard.W_PatternAdded(self.doc, self.pattern, new = self.new)
            self.new = False
        return True

    def Undo(self):
        if self.delete:
            self.doc.patterns[self.pattern['name']] = self.pattern
            wizard.W_PatternAdded(self.doc, self.pattern)
        else:
            del self.doc.patterns[self.pattern['name']]
            wizard.W_PatternDeleted(self.pattern)

class DocumentChangePatternName():

    def __init__(self, doc, pattern, new_name):
        self.doc = doc
        self.pattern = pattern
        self.new_name = new_name

    def Redo(self):
        self.old_name = self.pattern['name']
        if not self.new_name:
            Notify(tm.main.empty_pattern_name)
            return False
        if self.old_name == self.new_name:
            return False
        if self.new_name in self.doc.patterns:
            Notify(tm.main.pattern_option_already_exist)
            return False
        self.pattern['name'] = self.new_name
        del self.doc.patterns[self.old_name]
        self.doc.patterns[self.new_name] = self.pattern
        wizard.W_PatternNameChanged(self.pattern)
        return True

    def Undo(self):
        self.pattern['name'] = self.old_name
        del self.doc.patterns[self.new_name]
        self.doc.patterns[self.old_name] = self.pattern
        wizard.W_PatternNameChanged(self.pattern)

class DocumentChangePatternProperty():
    def __init__(self, doc, pattern, prop, value):
        self.doc = doc
        self.pattern = pattern
        self.prop = prop
        self.value = value

    def Redo(self):
        self.old_value = self.pattern.get(self.prop, type(self.value)())
        if self.value == self.old_value:
            return False
        self.pattern[self.prop] = self.value
        wizard.W_PatternPropsChanged(self.pattern)
        return True

    def Undo(self):
        self.pattern[self.prop] = self.old_value
        wizard.W_PatternPropsChanged(self.pattern)

class DocumentChangePatternOptionName():

    def __init__(self, pattern, option, new_name):
        self.pattern = pattern
        self.option = option
        self.new_name = new_name

    def Redo(self):
        self.old_name = self.option.get('name')
        if self.old_name == self.new_name:
            return False
        if self.new_name:
            if self.new_name in (o.get('name') for o in self.pattern['options']):
                Notify(tm.main.pattern_option_already_exist)
                return False
            self.option['name'] = self.new_name
        elif self.old_name:
            del self.option['name']

        wizard.W_PatternOptionChanged(self.option)
        return True

    def Undo(self):
        if self.old_name:
            self.option['name'] = self.old_name
        elif self.new_name:
            del self.option['name']
        wizard.W_PatternOptionChanged(self.option)

class DocumentChangePatternSignature():

    def __init__(self, pattern, role, data, old_role = None):
        self.pattern = pattern
        self.role = role
        self.data = data
        self.old_role = old_role

    def Redo(self):
        if self.old_role:
            self.old_data = self.pattern['signature'][self.old_role]
            del self.pattern['signature'][self.old_role]
        if self.role:
            self.pattern['signature'][self.role] = self.data
        wizard.W_PatternSignatureChanged(self.pattern, self.role, self.old_role)
        return True

    def Undo(self):
        if self.role:
            del self.pattern['signature'][self.role]
        if self.old_role:
            self.pattern['signature'][self.old_role] = self.old_data
        wizard.W_PatternSignatureChanged(self.pattern, self.old_role, self.role)

class DocumentModifyPatternOptions():

    def __init__(self, pattern, option, delete = False, new = True):
        self.pattern = pattern
        self.option = option
        self.delete = delete
        self.new = new

    def Redo(self):
        if self.delete:
            if self.option not in self.pattern['options']:
                return False

            self.idx = self.pattern['options'].index(self.option)
            del self.pattern['options'][self.idx]
            wizard.W_PatternOptionDeleted(self.option)
        else:
            if self.option in self.pattern['options']:
                return False

            if not self.new:
                counter = 1
                name = self.option.get('name')
                while name:
                    for o in self.pattern['options']:
                        if name == o.get('name'):
                            name = '%s%i'%(self.option['name'], counter)
                            counter += 1
                            break
                    else:
                        self.option['name'] = name
                        break

            self.pattern['options'].append(self.option)
            wizard.W_PatternOptionAdded(self.pattern, self.option, new = self.new)
            self.new = False
        return True

    def Undo(self):
        if self.delete:
            self.pattern['options'].insert(self.idx, self.option)
            wizard.W_PatternOptionAdded(self.pattern, self.option)
        else:
            self.pattern['options'].remove(self.option)
            wizard.W_PatternOptionDeleted(self.option)

class DocumentModifyPatternOptionParts():

    def __init__(self, option, part, delete = False):
        self.option = option
        self.part = part
        self.delete = delete

    def Redo(self):
        if self.delete:
            if self.part not in self.option['parts']:
                return False

            self.idx = self.option['parts'].index(self.part)
            del self.option['parts'][self.idx]
            wizard.W_PatternOptionPartDeleted(self.option, self.part)
        else:
            if self.part in self.option['parts']:
                return False

            if 'type' not in self.part or not self.part['type'].startswith('patterns.'):
                name = self.part.get('self', None)
                self.part['self'] = GenPartName(self.option, name) 

            self.option['parts'].append(self.part)
            wizard.W_PatternOptionPartAdded(self.option, self.part)
        return True

    def Undo(self):
        if self.delete:
            self.option['parts'].insert(self.idx, self.part)
            wizard.W_PatternOptionPartAdded(self.option, self.part)
        else:
            self.option['parts'].remove(self.part)
            wizard.W_PatternOptionPartDeleted(self.option, self.part)

class DocumentChangePatternOptionPartIndex():

    def __init__(self, option, part, new_idx):
        self.option = option
        self.part = part
        self.new_idx = new_idx

    def Redo(self):
        if self.new_idx >= len(self.option['parts']):
            return False
        self.old_idx = self.option['parts'].index(self.part)
        if self.old_idx == self.new_idx:
            return False

        del self.option['parts'][self.old_idx]
        self.option['parts'].insert(self.new_idx, self.part)
        wizard.W_PatternOptionPartIndexChanged(self.option, self.part)
        return True


    def Undo(self):
        del self.option['parts'][self.new_idx]
        self.option['parts'].insert(self.old_idx, self.part)
        wizard.W_PatternOptionPartIndexChanged(self.option, self.part)

class DocumentModifyPatternOptionPartName():
    def __init__(self, part, name):
        self.part = part
        self.name = name

    def Redo(self):
        self.old_name = self.part.get('self')
        if self.old_name == self.name:
            return False
        if self.name:
            self.part['self'] = self.name
        else:
            del self.part['self']
        wizard.W_PatternOptionPartNameChanged(self.part)

    def Undo(self):
        if self.old_name:
            self.part['self'] = self.old_name
        else:
            del self.part['self']
        wizard.W_PatternOptionPartNameChanged(self.part)

ROLE_ADD    = 0
ROLE_DELETE = 1
ROLE_BIND   = 2
ROLE_RENAME = 3
ROLE_MODIFY = 4

class DocumentModifyPatternOptionPartRoles():

    def __init__(self, option, part, role, value = None, action = None):
        self.option = option
        self.part = part
        self.role = role
        self.value = value
        self.action = action
        self.other = None

    def Redo(self):
        if self.action == ROLE_DELETE:
            if self.role not in self.part:
                return False

            self.value = self.part[self.role]
            del self.part[self.role]
            wizard.W_PatternOptionPartRoleDeleted(self.part, self.role)

        elif self.action == ROLE_ADD:
            if self.role in self.part:
                Notify(tm.main.pattern_option_part_role_already_exist)
                return False
            self.part[self.role] = self.value
            wizard.W_PatternOptionPartRoleAdded(self.part, self.role)

        elif self.action == ROLE_BIND:
            if self.value == self.part[self.role]:
                return False
            self.old_value = self.part[self.role]
            self.part[self.role] = self.value
            wizard.W_PatternOptionPartRoleChanged(self.part, self.role, self.role)

        elif self.action == ROLE_RENAME:
            if self.value == self.role:
                return False
            if self.value in self.part:
                Notify(tm.main.pattern_option_part_role_already_exist)
                return False
            self.part[self.value] = self.part[self.role]
            del self.part[self.role]
            wizard.W_PatternOptionPartRoleChanged(self.part, self.role, self.value)

        elif self.action == ROLE_MODIFY:
            if self.role not in self.part:
                return False
            self.old_value = self.part[self.role]
            if self.value[0] == self.role and self.value[1] == self.old_value:
                return False
            if self.value[0] != self.role:
                if self.value[0] in self.part:
                    Notify(tm.main.pattern_option_part_role_already_exist)
                    return False
                del self.part[self.role]
            self.part[self.value[0]] = self.value[1]
            wizard.W_PatternOptionPartRoleChanged(self.part, self.role, self.value[0])

        if 'self' in self.part and 'type' in self.part and isinstance(self.part['type'], basestring) and self.part['type'].startswith('patterns.'):
            self.other = DocumentModifyPatternOptionPartRoles(self.option, self.part, 'self', action = ROLE_DELETE)
        elif 'self' not in self.part and ('type' not in self.part or not isinstance(self.part['type'], basestring) or not self.part['type'].startswith('patterns.')):
            self.other = DocumentModifyPatternOptionPartRoles(self.option, self.part, 'self', value = GenPartName(self.option), action = ROLE_ADD)

        if self.other and not self.other.Redo():
            self.other = None

        return True


    def Undo(self):
        if self.other:
            self.other.Undo()

        if self.action == ROLE_DELETE:
            self.part[self.role] = self.value
            wizard.W_PatternOptionPartRoleAdded(self.part, self.role)

        elif self.action == ROLE_ADD:
            del self.part[self.role]
            wizard.W_PatternOptionPartRoleDeleted(self.part, self.role)

        elif self.action == ROLE_BIND:
            self.part[self.role] = self.old_value
            wizard.W_PatternOptionPartRoleChanged(self.part, self.role, self.role)

        elif self.action == ROLE_RENAME:
            self.part[self.role] = self.part[self.value]
            del self.part[self.value]
            wizard.W_PatternOptionPartRoleChanged(self.part, self.value, self.role)

        elif self.action == ROLE_MODIFY:
            del self.part[self.value[0]]
            self.part[self.role] = self.old_value
            wizard.W_PatternOptionPartRoleChanged(self.part, self.value[0], self.role)

class DocumentChangePatternOptionPartRole():

    def __init__(self, option, part, old_role, role, value):
        self.option = option
        self.part = part
        self.old_role = old_role
        self.role = role
        self.value = value
        self.name = None

    def Redo(self):
        self.old_value = self.part[self.old_role]
        if self.old_value == self.value and self.old_role == self.role:
            return False
        del self.part[self.old_role]

        self.part[self.role] = self.value

        if self.role == 'type' and self.value.startswith('patterns.') and 'self' in self.part:
            self.name = self.part['self']
            del self.part['self']

        wizard.W_PatternOptionPartRoleChanged(self.part, self.old_role, self.role)
        return True

    def Undo(self):
        del self.part[self.role]

        if self.name:
            self.part['self'] = GenPartName(self.option, self.name)

        self.part[self.old_role] = self.old_value
        wizard.W_PatternOptionPartRoleChanged(self.part, self.role, self.old_role)
