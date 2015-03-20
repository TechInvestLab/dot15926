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


#ifndef _GRAPH_H_
#define _GRAPH_H_

enum ge_t {
    GE_TRIPLE_INSERT,
    GE_TRIPLE_DELETE,
    GE_TRIPLE_ADDED,
    GE_TRIPLE_REMOVED,
    GE_LOG,
    GE_PROGRESS,
    GE_MAX
};

typedef struct {
  PyObject_HEAD
  PyObject *ks;
  //PyObject *kp;
  PyObject *ko;
  PyObject *kl;
  PyObject *nslist;
  PyObject *basens;
  PyObject *idi;
  PyObject *ng;
  PyObject *gt;
  struct {
    PyObject **arr;
    size_t len;
  } cb[GE_MAX];
} Graph;

int Graph_insert_item(Graph *graph, PyObject *item);
int Graph_delete_item(Graph *graph, PyObject *item);
int Graph_has_item(Graph *graph, PyObject *item);
PyObject * Graph_cache_pystring(Graph *graph, PyObject *string);
PyObject * Graph_cache_string(Graph *graph, const char *string);

int Graph_insert_object(Graph *graph, const char* s, const char* p, const char* o);
int Graph_insert_literal(Graph *graph, const char* s, const char* p, const char* l);
int Graph_insert_lang(Graph *graph, const char* s, const char* p, const char* l, const char* c);
int Graph_insert_datatype(Graph *graph, const char* s, const char* p, const char* l, const char* c);
int Graph_set_basens(Graph *graph, const char* ns);
int Graph_add_ns(Graph *graph, const char* prefix, const char* uri);

int init_graph_types();
int public_graph_types(PyObject *m);

int Graph_call_cb(Graph *graph, int type, PyObject *data);

#endif