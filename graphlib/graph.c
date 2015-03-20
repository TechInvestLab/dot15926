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


#include "Python.h"
#include "structmember.h"
#include "graph.h"
#include "base.h"
#include "_ordereddict/inc/ordereddict.h"
#include "graphitem.h"

static PyTypeObject GraphType;

int bisect_left(PyObject *list, PyObject *item)
{
    int lo = 0;
    int hi = PyList_Size(list);
    while (lo < hi) {
        int mid = (lo+hi)/2;
        PyObject *i = PyList_GET_ITEM(list, mid);
        if ( PyObject_RichCompareBool(i, item, Py_LT) ) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    return lo;
}

int Graph_call_cb(Graph *graph, int type, PyObject *data)
{
    size_t i;
    for (i = 0; i < graph->cb[type].len; ++i) {
        PyObject *result = PyObject_CallFunctionObjArgs(graph->cb[type].arr[i], data, NULL);
        if (!result) {
            return -1;
        }
        Py_DECREF(result);
    }
    return 0;
}

PyObject *Graph_cache_pystring(Graph *graph, PyObject *string)
{
    PyObject *res = PyDict_GetItem(graph->idi, string);
    if (!res) {
        PyDict_SetItem(graph->idi, string, string);
        Py_INCREF(string);
        return string;
    }
    Py_INCREF(res);
    return res;
}

PyObject *Graph_cache_string(Graph *graph, const char *string)
{
    PyObject *res = PyDict_GetItemString(graph->idi, string);
    if (!res) {
        res = PyString_FromString(string);
        PyDict_SetItem(graph->idi, res, res);
        return res;
    }
    Py_INCREF(res);
    return res;
}

int Graph_insert_item(Graph *graph, PyObject *item)
{
    PyObject *k;
    PyObject *d;
    PyObject *items_list;

    if (Graph_call_cb(graph, GE_TRIPLE_INSERT, item)) {
        return -1;
    }

    k = PyTuple_GetItem(item, 0);
    items_list = PyOrderedDict_GetItem(graph->ks, k);
    if (!items_list) {
        items_list = PyList_New(1);
        Py_INCREF(item);
        PyList_SET_ITEM(items_list, 0, item);
        PyOrderedDict_SetItem(graph->ks, k, items_list);
        Py_DECREF(items_list);
    } else {
        int idx = bisect_left(items_list, item);
        if ((idx < PyList_Size(items_list)) && PyObject_RichCompareBool(PyList_GET_ITEM(items_list, idx), item, Py_EQ)) {
            return 0;
        }
        PyList_Insert(items_list, idx, item);
    }

    if (PyObject_TypeCheck(item, &ObjectTripleType)) {
        d = graph->ko;
    } else {
        d = graph->kl;
    }

    k = PyTuple_GetItem(item, 2);
    items_list = PyDict_GetItem(d, k);
    if (!items_list) {
        items_list = PyList_New(1);
        Py_INCREF(item);
        PyList_SET_ITEM(items_list, 0, item);
        PyDict_SetItem(d, k, items_list);
        Py_DECREF(items_list);
    } else {
        int idx = bisect_left(items_list, item);
        PyList_Insert(items_list, idx, item);
    }

    if (Graph_call_cb(graph, GE_TRIPLE_ADDED, item)) {
        return -1;
    }
    return 1;
}

int Graph_delete_item(Graph *graph, PyObject *item)
{
    PyObject *k;
    PyObject *items_list;

    if (Graph_call_cb(graph, GE_TRIPLE_DELETE, item)) {
        return -1;
    }

    k = PyTuple_GetItem(item, 0);
    items_list = PyOrderedDict_GetItem(graph->ks, k);
    if (items_list) {
        int idx = bisect_left(items_list, item);
        if ((idx < PyList_Size(items_list)) && PyObject_RichCompareBool(PyList_GET_ITEM(items_list, idx), item, Py_EQ)) {
            PyObject *d;
            PySequence_DelItem(items_list, idx);
            if (!PyList_Size(items_list)) {
                PyOrderedDict_DelItem(graph->ks, k);
            }
            if (PyObject_TypeCheck(item, &ObjectTripleType)) {
                d = graph->ko;
            } else {
                d = graph->kl;
            }
            k = PyTuple_GetItem(item, 2);
            items_list = PyDict_GetItem(d, k);
            idx = bisect_left(items_list, item);
            PySequence_DelItem(items_list, idx);
            if (!PyList_Size(items_list)) {
                PyDict_DelItem(d, k);
            }
            if (Graph_call_cb(graph, GE_TRIPLE_REMOVED, item)) {
                return -1;
            }
            return 1;
        }
    }
    return 0;
}

int Graph_has_item(Graph *graph, PyObject *item)
{
    PyObject *items_list = PyOrderedDict_GetItem(graph->ks, PyTuple_GetItem(item, 0));
    if (items_list) {
        int idx = bisect_left(items_list, item);
        if (idx < PyList_Size(items_list)) {
            return PyObject_RichCompareBool(PyList_GET_ITEM(items_list, idx), item, Py_EQ);
        }
    }
    return 0;
}

int Graph_insert_object(Graph *graph, const char *s, const char *p, const char *o)
{
    PyObject *item;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, Graph_cache_string(graph, compact_uri_str(s)));
    PyTuple_SetItem(values, 1, Graph_cache_string(graph, compact_uri_str(p)));
    PyTuple_SetItem(values, 2, Graph_cache_string(graph, compact_uri_str(o)));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject((PyObject *) &ObjectTripleType, params);
    Graph_insert_item(graph, item);
    Py_DECREF(item);
    Py_DECREF(params);
    return 1;
}

int Graph_insert_literal(Graph *graph, const char *s, const char *p, const char *l)
{
    int result;
    PyObject *item;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, Graph_cache_string(graph, compact_uri_str(s)));
    PyTuple_SetItem(values, 1, Graph_cache_string(graph, compact_uri_str(p)));
    PyTuple_SetItem(values, 2, Graph_cache_string(graph, l));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject((PyObject *) &LiteralTripleType, params);
    result = Graph_insert_item(graph, item);
    Py_DECREF(item);
    Py_DECREF(params);
    return result;
}

int Graph_insert_lang(Graph *graph, const char *s, const char *p, const char *l, const char *c)
{
    int result;
    PyObject *item;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, Graph_cache_string(graph, compact_uri_str(s)));
    PyTuple_SetItem(values, 1, Graph_cache_string(graph, compact_uri_str(p)));
    PyTuple_SetItem(values, 2, Graph_cache_string(graph, l));
    PyTuple_SetItem(values, 3, Graph_cache_string(graph, c));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject((PyObject *) &LangQuadType, params);
    result = Graph_insert_item(graph, item);
    Py_DECREF(item);
    Py_DECREF(params);
    return result;
}

int Graph_insert_datatype(Graph *graph, const char *s, const char *p, const char *l, const char *c)
{
    int result;
    PyObject *item;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, Graph_cache_string(graph, compact_uri_str(s)));
    PyTuple_SetItem(values, 1, Graph_cache_string(graph, compact_uri_str(p)));
    PyTuple_SetItem(values, 2, Graph_cache_string(graph, l));
    PyTuple_SetItem(values, 3, Graph_cache_string(graph, compact_uri_str(c)));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject((PyObject *) &DatatypeQuadType, params);
    result = Graph_insert_item(graph, item);
    Py_DECREF(item);
    Py_DECREF(params);
    return result;
}

int Graph_set_basens(Graph *graph, const char *ns)
{
    Py_XDECREF(graph->basens);
    graph->basens = PyString_FromString(ns);
    return 0;
}

int Graph_add_ns(Graph *graph, const char *prefix, const char *uri)
{
    PyObject *py_uri = PyString_FromString(uri);
    PyDict_SetItemString(graph->nslist, prefix, py_uri);
    Py_DECREF(py_uri);
    return 0;
}

static void Graph_dealloc(Graph *self)
{
    int i;
    size_t j;
    Py_XDECREF(self->ks);
    //Py_XDECREF(self->kp);
    Py_XDECREF(self->ko);
    Py_XDECREF(self->kl);
    Py_XDECREF(self->nslist);
    Py_XDECREF(self->basens);
    Py_XDECREF(self->idi);
    Py_XDECREF(self->ng);
    Py_XDECREF(self->gt);
    for (i = 0; i < GE_MAX; ++i){
        for (j = 0; j < self->cb[i].len; ++j) {
            Py_XDECREF(self->cb[i].arr[j]);
        }
        free(self->cb[i].arr);
    }
    self->ob_type->tp_free((PyObject *) self);
}

static PyObject *Graph_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    Graph *self;
    int i;
    self = (Graph *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->ks     = PyOrderedDict_New();
        //self->kp     = PyDict_New();
        self->ko     = PyDict_New();
        self->kl     = PyDict_New();
        self->nslist = PyDict_New();
        self->basens = PyString_FromString("");
        self->idi    = PyDict_New();
        self->ng     = PyDict_New();
        Py_INCREF(&GraphType);
        self->gt     = (PyObject *)&GraphType;
        for (i = 0; i < GE_MAX; ++i) {
            self->cb[i].arr = NULL;
            self->cb[i].len = 0;
        }
    }
    return (PyObject *) self;
}

static int Graph_init(Graph *self, PyObject *args, PyObject *kwds)
{
    return 0;
}

static PyObject *Graph_clear(Graph *self)
{
    PyOrderedDict_Clear(self->ks);
    //PyDict_Clear(self->kp);
    PyDict_Clear(self->ko);
    PyDict_Clear(self->kl);
    PyDict_Clear(self->nslist);
    PyDict_Clear(self->idi);
    PyDict_Clear(self->ng);
    Py_RETURN_NONE;
}

static PyObject *Graph_add_cb(Graph *self, PyObject *args)
{
  int type;
  PyObject *cb;
  if (!PyArg_ParseTuple(args, "iO", &type, &cb)) {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }
  if (type >= GE_MAX) {
    PyErr_SetString(PyExc_TypeError,
    "wrong callback index");
    return NULL;
  }
  if (!PyCallable_Check(cb)) {
    PyErr_SetString(PyExc_TypeError,
    "second argument must be callable");
    return NULL;
  }
  Py_INCREF(cb);
  self->cb[type].arr = realloc(self->cb[type].arr, (self->cb[type].len + 1) * sizeof(PyObject *));
  self->cb[type].arr[self->cb[type].len++] = cb;
  Py_RETURN_NONE;
}

static PyObject *Graph_remove_cb(Graph *self, PyObject *args)
{
  int type;
  size_t i;
  PyObject *cb;
  if (!PyArg_ParseTuple(args, "iO", &type, &cb)) {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }
  if (type >= GE_MAX) {
    PyErr_SetString(PyExc_TypeError,
    "wrong callback index");
    return NULL;
  }
  for (i = 0; i < self->cb[type].len; ++i) {
    if (self->cb[type].arr[i] == cb) {
        PyObject *tmp = self->cb[type].arr[--self->cb[type].len];
        self->cb[type].arr[self->cb[type].len] = self->cb[type].arr[i];
        self->cb[type].arr[i] = tmp;
        self->cb[type].arr = realloc(self->cb[type].arr, self->cb[type].len * sizeof(PyObject *));
        Py_DECREF(cb);
        break;
    }
  }
  Py_RETURN_NONE;
}

static PyMethodDef Graph_methods[] = {
    {
        "grClear", (PyCFunction) Graph_clear, METH_NOARGS, ""
    },
    {
        "grAddCallback", (PyCFunction) Graph_add_cb, METH_VARARGS, ""
    },
    {
        "grRemoveCallback", (PyCFunction) Graph_remove_cb, METH_VARARGS, ""
    },
    {NULL}  /* Sentinel */
};

static PyMemberDef Graph_members[] = {
    {
        "ks", T_OBJECT_EX, offsetof(Graph, ks), 0, ""
    },
    //{
    //    "kp", T_OBJECT_EX, offsetof(Graph, kp), 0, ""
    //},
    {
        "ko", T_OBJECT_EX, offsetof(Graph, ko), 0,  ""
    },
    {
        "kl", T_OBJECT_EX, offsetof(Graph, kl), 0,  ""
    },
    {
        "nslist", T_OBJECT_EX, offsetof(Graph, nslist), 0,  ""
    },
    {
        "basens", T_OBJECT_EX, offsetof(Graph, basens), 0,  ""
    },
    {
        "idi", T_OBJECT_EX, offsetof(Graph, idi), 0, ""
    },
    {
        "ng", T_OBJECT_EX, offsetof(Graph, ng), 0, ""
    },
    {
        "gt", T_OBJECT_EX, offsetof(Graph, gt), 0, ""
    },
    {NULL}  /* Sentinel */
};

static PyTypeObject GraphType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "graphlib.Graph",             /*tp_name*/
    sizeof(Graph),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) Graph_dealloc,   /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Graph objects",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    Graph_methods,             /* tp_methods */
    Graph_members,             /* tp_members */
    0,           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc) Graph_init,     /* tp_init */
    0,                         /* tp_alloc */
    Graph_new,                 /* tp_new */
};

int init_graph_types()
{
    PyObject *d = PyDict_New();
    PyObject *i = PyInt_FromLong(GE_TRIPLE_INSERT);
    PyDict_SetItemString(d, "TRIPLE_INSERT", i);
    Py_DECREF(i);
    i = PyInt_FromLong(GE_TRIPLE_DELETE);
    PyDict_SetItemString(d, "TRIPLE_DELETE", i);
    Py_DECREF(i);
    i = PyInt_FromLong(GE_TRIPLE_ADDED);
    PyDict_SetItemString(d, "TRIPLE_ADDED", i);
    Py_DECREF(i);
    i = PyInt_FromLong(GE_TRIPLE_REMOVED);
    PyDict_SetItemString(d, "TRIPLE_REMOVED", i);
    Py_DECREF(i);
    i = PyInt_FromLong(GE_LOG);
    PyDict_SetItemString(d, "LOG", i);
    Py_DECREF(i);
    i = PyInt_FromLong(GE_PROGRESS);
    PyDict_SetItemString(d, "PROGRESS", i);
    Py_DECREF(i);

    GraphType.tp_dict = d;
    if (PyType_Ready(&GraphType) < 0) {
        return 0;
    }
    return 1;
}
int public_graph_types(PyObject *m)
{
    Py_INCREF(&GraphType);
    if (PyModule_AddObject(m, "Graph", (PyObject *) &GraphType) < 0) {
        return 0;
    }
    return 1;
}