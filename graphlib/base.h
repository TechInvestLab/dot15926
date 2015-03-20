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


#ifndef _BASE_H_
#define _BASE_H_
#define MAX_URI_LENGTH 2048

extern const char * const bnode_prefix;
extern const size_t bnode_prefix_len;

char * compact_uri(const char* uri, char* out);
char * expand_uri(const char* curi, char* out);
char * curi_head(const char* curi, char* out);
char * curi_tail(const char* curi, char* out);

const char* compact_uri_str(const char *uri);
const char* expand_uri_str(const char *curi);
const char* new_bnodeid();
const char* bnodeid(const char *id);

PyObject * py_new_bnodeid();
PyObject * py_bnodeid(PyObject *id);
PyObject * py_compact_uri(PyObject *uri);
PyObject * py_expand_uri(PyObject *uri);
PyObject * py_curi_head(PyObject *curi);
PyObject * py_curi_tail(PyObject *curi);

#endif