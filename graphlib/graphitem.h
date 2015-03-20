/*
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
*/


#ifndef _GRAPHITEM_H_
#define _GRAPHITEM_H_

typedef struct
{
  PyTupleObject t;
} GraphItem;

extern PyTypeObject ObjectTripleType;
extern PyTypeObject LiteralTripleType;
extern PyTypeObject LangQuadType;
extern PyTypeObject DatatypeQuadType;

int init_graphitem_types();
int public_graphitem_types(PyObject *m);


#endif