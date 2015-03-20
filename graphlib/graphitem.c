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
#include"base.h"
#include "graphitem.h"
#include "graph.h"

static int
GraphItem_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    if (PyTuple_Type.tp_init(self, args, kwds) < 0) {
        return -1;
    }
    return 0;
}

static PyObject *
GraphItem_first_expand(PyObject *self, void *closure)
{
    PyObject *str  = py_expand_uri(PyTuple_GetItem(self, 0));
    return str;
}

static PyObject *
GraphItem_second_expand(PyObject *self, void *closure)
{
    PyObject *str  = py_expand_uri(PyTuple_GetItem(self, 1));
    return str;
}

static PyObject *
GraphItem_third_expand(PyObject *self, void *closure)
{
    PyObject *str  = py_expand_uri(PyTuple_GetItem(self, 2));
    return str;
}

static PyObject *
GraphItem_third(PyObject *self, void *closure)
{
    PyObject *v = PyTuple_GetItem(self, 2);
    Py_INCREF(v);
    return v;
}

static PyObject *
GraphItem_fourth(PyObject *self, void *closure)
{
    PyObject *v = PyTuple_GetItem(self, 3);
    Py_INCREF(v);
    return v;
}

static PyObject *
GraphItem_fourth_expand(PyObject *self, void *closure)
{
    PyObject *str  = py_expand_uri(PyTuple_GetItem(self, 3));
    return str;
}

static PyObject *
GraphItem_first(PyObject *self, void *closure)
{
    PyObject *v = PyTuple_GetItem(self, 0);
    Py_INCREF(v);
    return v;
}

static PyObject *
GraphItem_second(PyObject *self, void *closure)
{
    PyObject *v = PyTuple_GetItem(self, 1);
    Py_INCREF(v);
    return v;
}

static PyObject *
GraphItem_None(PyObject *self, void *closure)
{
    Py_RETURN_NONE;
}

static int
dummy_set(PyObject *self, PyObject *value, void *closure)
{
    return 0;
}

static PyObject *Triple_object_of(PyObject *cls, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, py_compact_uri(PyTuple_GetItem(args, 0)));
    PyTuple_SetItem(values, 1, py_compact_uri(PyTuple_GetItem(args, 1)));
    PyTuple_SetItem(values, 2, py_compact_uri(PyTuple_GetItem(args, 2)));
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Triple_literal_of(PyObject *cls, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, py_compact_uri(PyTuple_GetItem(args, 0)));
    PyTuple_SetItem(values, 1, py_compact_uri(PyTuple_GetItem(args, 1)));
    Py_INCREF(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 2, PyTuple_GetItem(args, 2));
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    return res;
}


static PyObject *Quad_lang_of(PyObject *cls, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, py_compact_uri(PyTuple_GetItem(args, 0)));
    PyTuple_SetItem(values, 1, py_compact_uri(PyTuple_GetItem(args, 1)));
    Py_INCREF(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 2, PyTuple_GetItem(args, 2));
    Py_INCREF(PyTuple_GetItem(args, 3));
    PyTuple_SetItem(values, 3, PyTuple_GetItem(args, 3));
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Quad_datatype_of(PyObject *cls, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyTuple_SetItem(values, 0, py_compact_uri(PyTuple_GetItem(args, 0)));
    PyTuple_SetItem(values, 1, py_compact_uri(PyTuple_GetItem(args, 1)));
    Py_INCREF(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 2, PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 3, py_compact_uri(PyTuple_GetItem(args, 3)));
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Triple_insert_object(PyObject *cls, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *item, *v;
    v = py_compact_uri(PyTuple_GetItem(args, 1));
    PyTuple_SetItem(values, 0, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    v = py_compact_uri(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 1, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    v = py_compact_uri(PyTuple_GetItem(args, 3));
    PyTuple_SetItem(values, 2, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    result = Graph_insert_item(g, item);
    if (result == 1) {
        return item;
    }
    Py_DECREF(item);
    if (result == -1) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *Triple_insert_literal(PyObject *cls, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *item, *v;
    v = py_compact_uri(PyTuple_GetItem(args, 1));
    PyTuple_SetItem(values, 0, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    v = py_compact_uri(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 1, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    PyTuple_SetItem(values, 2, Graph_cache_pystring(g, PyTuple_GetItem(args, 3)));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    result = Graph_insert_item(g, item);
    if (result == 1) {
        return item;
    }
    Py_DECREF(item);
    if (result == -1) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *Quad_insert_lang(PyObject *cls, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyObject *item, *v;
    v = py_compact_uri(PyTuple_GetItem(args, 1));
    PyTuple_SetItem(values, 0, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    v = py_compact_uri(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 1, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    PyTuple_SetItem(values, 2, Graph_cache_pystring(g, PyTuple_GetItem(args, 3)));
    PyTuple_SetItem(values, 3, Graph_cache_pystring(g, PyTuple_GetItem(args, 4)));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    result = Graph_insert_item(g, item);
    if (result == 1) {
        return item;
    }
    Py_DECREF(item);
    if (result == -1) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *Quad_insert_datatype(PyObject *cls, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyObject *item, *v;
    v = py_compact_uri(PyTuple_GetItem(args, 1));
    PyTuple_SetItem(values, 0, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    v = py_compact_uri(PyTuple_GetItem(args, 2));
    PyTuple_SetItem(values, 1, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    PyTuple_SetItem(values, 2, Graph_cache_pystring(g, PyTuple_GetItem(args, 3)));
    v = py_compact_uri(PyTuple_GetItem(args, 4));
    PyTuple_SetItem(values, 3, Graph_cache_pystring(g, v));
    Py_DECREF(v);
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject(cls, params);
    Py_DECREF(params);
    result = Graph_insert_item(g, item);
    if (result == 1) {
        return item;
    }
    Py_DECREF(item);
    if (result == -1) {
        return NULL;
    }
    Py_RETURN_NONE;
}

static PyObject *GraphItem_insertto(PyObject *self, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    result = Graph_insert_item(g, self);
    if (result == -1) {
        return NULL;
    } else if (result == 1) {
        Py_INCREF(self);
        return self;
    }
    Py_RETURN_NONE;
}

static PyObject *GraphItem_deletefrom(PyObject *self, PyObject *args)
{
    int result;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    result = Graph_delete_item(g, self);
    if (result == -1) {
        return NULL;
    } else if (result == 1) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

static PyObject *Triple_test_object(PyObject *cls, PyObject *args)
{
    int has;
    Graph *g = (Graph *)PyTuple_GetItem(args, 0);
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *item;
    PyTuple_SetItem(values, 0, py_compact_uri(PyTuple_GetItem(args, 1)));
    PyTuple_SetItem(values, 1, py_compact_uri(PyTuple_GetItem(args, 2)));
    PyTuple_SetItem(values, 2, py_compact_uri(PyTuple_GetItem(args, 3)));
    PyTuple_SetItem(params, 0, values);
    item = PyObject_CallObject(cls, params);
    has = Graph_has_item(g, item);
    Py_DECREF(item);
    Py_DECREF(params);
    if (has) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

static PyObject *Triple_with_s(PyObject *self, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *s = py_compact_uri(PyTuple_GetItem(args, 0));
    PyObject *p = PyTuple_GetItem(self, 1);
    PyObject *o = PyTuple_GetItem(self, 2);
    Py_INCREF(p);
    Py_INCREF(o);
    PyTuple_SetItem(values, 0, s);
    PyTuple_SetItem(values, 1, p);
    PyTuple_SetItem(values, 2, o);
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject((PyObject *)self->ob_type, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Quad_with_s(PyObject *self, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyObject *s = py_compact_uri(PyTuple_GetItem(args, 0));
    PyObject *p = PyTuple_GetItem(self, 1);
    PyObject *l = PyTuple_GetItem(self, 2);
    PyObject *c = PyTuple_GetItem(self, 3);
    Py_INCREF(p);
    Py_INCREF(l);
    Py_INCREF(c);
    PyTuple_SetItem(values, 0, s);
    PyTuple_SetItem(values, 1, p);
    PyTuple_SetItem(values, 2, l);
    PyTuple_SetItem(values, 3, c);
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject((PyObject *)self->ob_type, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Triple_with_o(PyObject *self, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *s = PyTuple_GetItem(self, 0);
    PyObject *p = PyTuple_GetItem(self, 1);
    PyObject *o = py_compact_uri(PyTuple_GetItem(args, 0));
    Py_INCREF(s);
    Py_INCREF(p);
    PyTuple_SetItem(values, 0, s);
    PyTuple_SetItem(values, 1, p);
    PyTuple_SetItem(values, 2, o);
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject((PyObject *)self->ob_type, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Triple_with_l(PyObject *self, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(3);
    PyObject *params = PyTuple_New(1);
    PyObject *s = PyTuple_GetItem(self, 0);
    PyObject *p = PyTuple_GetItem(self, 1);
    PyObject *l = PyTuple_GetItem(args, 0);
    Py_INCREF(s);
    Py_INCREF(p);
    Py_INCREF(l);
    PyTuple_SetItem(values, 0, s);
    PyTuple_SetItem(values, 1, p);
    PyTuple_SetItem(values, 2, l);
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject((PyObject *)self->ob_type, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Quad_with_l(PyObject *self, PyObject *args)
{
    PyObject *res;
    PyObject *values = PyTuple_New(4);
    PyObject *params = PyTuple_New(1);
    PyObject *s = PyTuple_GetItem(self, 0);
    PyObject *p = PyTuple_GetItem(self, 1);
    PyObject *l = PyTuple_GetItem(args, 0);
    PyObject *c = PyTuple_GetItem(self, 3);
    Py_INCREF(s);
    Py_INCREF(p);
    Py_INCREF(l);
    Py_INCREF(c);
    PyTuple_SetItem(values, 0, s);
    PyTuple_SetItem(values, 1, p);
    PyTuple_SetItem(values, 2, l);
    PyTuple_SetItem(values, 3, c);
    PyTuple_SetItem(params, 0, values);
    res = PyObject_CallObject((PyObject *)self->ob_type, params);
    Py_DECREF(params);
    return res;
}

static PyObject *Object_collect_ns_to(PyObject *self, PyObject *args)
{
    PyObject *nslist = PyTuple_GetItem(args, 0);
    PyObject *v = py_curi_head(PyTuple_GetItem(self, 0));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    v = py_curi_head(PyTuple_GetItem(self, 1));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    v = py_curi_head(PyTuple_GetItem(self, 2));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    Py_RETURN_NONE;
}

static PyObject *Literal_collect_ns_to(PyObject *self, PyObject *args)
{
    PyObject *nslist = PyTuple_GetItem(args, 0);
    PyObject *v = py_curi_head(PyTuple_GetItem(self, 0));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    v = py_curi_head(PyTuple_GetItem(self, 1));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    Py_RETURN_NONE;
}

static PyObject *Datatype_collect_ns_to(PyObject *self, PyObject *args)
{
    PyObject *nslist = PyTuple_GetItem(args, 0);
    PyObject *v = py_curi_head(PyTuple_GetItem(self, 0));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    v = py_curi_head(PyTuple_GetItem(self, 1));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    v = py_curi_head(PyTuple_GetItem(self, 3));
    PySet_Add(nslist, v);
    Py_DECREF(v);
    Py_RETURN_NONE;
}


static PyGetSetDef ObjectTriple_getseters[] = {
    {
        "s",
        (getter)GraphItem_first_expand, (setter)NULL,
        "subject",
        NULL
    },
    {
        "p",
        (getter)GraphItem_second_expand, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "o",
        (getter)GraphItem_third_expand, (setter)NULL,
        "object",
        NULL
    },
    {
        "v",
        (getter)GraphItem_third_expand, (setter)NULL,
        "value",
        NULL
    },
    {
        "d",
        (getter)GraphItem_None, (setter)NULL,
        "none",
        NULL
    },
    {
        "cs",
        (getter)GraphItem_first, (setter)NULL,
        "subject",
        NULL
    },
    {
        "cp",
        (getter)GraphItem_second, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "co",
        (getter)GraphItem_third, (setter)NULL,
        "object",
        NULL
    },
    
    {NULL}  /* Sentinel */
};

static PyMethodDef ObjectTripleMethods[] = {
    {
        "of", (PyCFunction)Triple_object_of, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insert", (PyCFunction)Triple_insert_object, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "test", (PyCFunction)Triple_test_object, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insertto", (PyCFunction)GraphItem_insertto, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "deletefrom", (PyCFunction)GraphItem_deletefrom, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_o", (PyCFunction)Triple_with_o, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_s", (PyCFunction)Triple_with_s, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "collect_ns_to", (PyCFunction)Object_collect_ns_to, METH_VARARGS,
        PyDoc_STR("")
    },
    {NULL,    NULL},
};


PyTypeObject ObjectTripleType = {
    PyObject_HEAD_INIT(NULL)
    0,                       /* ob_size */
    "graphlib.ObjectTriple",          /* tp_name */
    sizeof(GraphItem),    /* tp_basicsize */
    0,                       /* tp_itemsize */
    0,                       /* tp_dealloc */
    0,                       /* tp_print */
    0,                       /* tp_getattr */
    0,                       /* tp_setattr */
    0,                       /* tp_compare */
    0,                       /* tp_repr */
    0,                       /* tp_as_number */
    0,                       /* tp_as_sequence */
    0,                       /* tp_as_mapping */
    0,                       /* tp_hash */
    0,                       /* tp_call */
    0,                       /* tp_str */
    0,                       /* tp_getattro */
    0,                       /* tp_setattro */
    0,                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,   /* tp_flags */
    0,                       /* tp_doc */
    0,                       /* tp_traverse */
    0,                       /* tp_clear */
    0,                       /* tp_richcompare */
    0,                       /* tp_weaklistoffset */
    0,                       /* tp_iter */
    0,                       /* tp_iternext */
    ObjectTripleMethods,          /* tp_methods */
    0,                       /* tp_members */
    ObjectTriple_getseters,                       /* tp_getset */
    0,                       /* tp_base */
    0,                       /* tp_dict */
    0,                       /* tp_descr_get */
    0,                       /* tp_descr_set */
    0,                       /* tp_dictoffset */
    (initproc)GraphItem_init,   /* tp_init */
    0,                       /* tp_alloc */
    0,                       /* tp_new */
};


static PyGetSetDef LiteralTriple_getseters[] = {
    {
        "s",
        (getter)GraphItem_first_expand, (setter)NULL,
        "subject",
        NULL
    },
    {
        "p",
        (getter)GraphItem_second_expand, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "l",
        (getter)GraphItem_third, (setter)NULL,
        "literal",
        NULL
    },
    {
        "v",
        (getter)GraphItem_third, (setter)NULL,
        "value",
        NULL
    },
    {
        "d",
        (getter)GraphItem_None, (setter)NULL,
        "none",
        NULL
    },
    {
        "cs",
        (getter)GraphItem_first, (setter)NULL,
        "subject",
        NULL
    },
    {
        "cp",
        (getter)GraphItem_second, (setter)NULL,
        "predicate",
        NULL
    },
    
    {NULL}  /* Sentinel */
};

static PyMethodDef LiteralTripleMethods[] = {
    {
        "of", (PyCFunction)Triple_literal_of, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insert", (PyCFunction)Triple_insert_literal, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insertto", (PyCFunction)GraphItem_insertto, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "deletefrom", (PyCFunction)GraphItem_deletefrom, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_l", (PyCFunction)Triple_with_l, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_s", (PyCFunction)Triple_with_s, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "collect_ns_to", (PyCFunction)Literal_collect_ns_to, METH_VARARGS,
        PyDoc_STR("")
    },
    {NULL,    NULL},
};


PyTypeObject LiteralTripleType = {
    PyObject_HEAD_INIT(NULL)
    0,                       /* ob_size */
    "graphlib.LiteralTriple",          /* tp_name */
    sizeof(GraphItem),    /* tp_basicsize */
    0,                       /* tp_itemsize */
    0,                       /* tp_dealloc */
    0,                       /* tp_print */
    0,                       /* tp_getattr */
    0,                       /* tp_setattr */
    0,                       /* tp_compare */
    0,                       /* tp_repr */
    0,                       /* tp_as_number */
    0,                       /* tp_as_sequence */
    0,                       /* tp_as_mapping */
    0,                       /* tp_hash */
    0,                       /* tp_call */
    0,                       /* tp_str */
    0,                       /* tp_getattro */
    0,                       /* tp_setattro */
    0,                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,   /* tp_flags */
    0,                       /* tp_doc */
    0,                       /* tp_traverse */
    0,                       /* tp_clear */
    0,                       /* tp_richcompare */
    0,                       /* tp_weaklistoffset */
    0,                       /* tp_iter */
    0,                       /* tp_iternext */
    LiteralTripleMethods,          /* tp_methods */
    0,                       /* tp_members */
    LiteralTriple_getseters,                       /* tp_getset */
    0,                       /* tp_base */
    0,                       /* tp_dict */
    0,                       /* tp_descr_get */
    0,                       /* tp_descr_set */
    0,                       /* tp_dictoffset */
    (initproc)GraphItem_init,   /* tp_init */
    0,                       /* tp_alloc */
    0,                       /* tp_new */
};

PyGetSetDef LangQuad_getseters[] = {
    {
        "s",
        (getter)GraphItem_first_expand, (setter)NULL,
        "subject",
        NULL
    },
    {
        "p",
        (getter)GraphItem_second_expand, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "l",
        (getter)GraphItem_third, (setter)NULL,
        "literal",
        NULL
    },
    {
        "v",
        (getter)GraphItem_third, (setter)NULL,
        "value",
        NULL
    },
    {
        "lang",
        (getter)GraphItem_fourth, (setter)NULL,
        "lang",
        NULL
    },
    {
        "d",
        (getter)GraphItem_fourth, (setter)NULL,
        "lang",
        NULL
    },
    {
        "cs",
        (getter)GraphItem_first, (setter)NULL,
        "subject",
        NULL
    },
    {
        "cp",
        (getter)GraphItem_second, (setter)NULL,
        "predicate",
        NULL
    },
    
    {NULL}  /* Sentinel */
};

static PyMethodDef LangQuadMethods[] = {
    {
        "of", (PyCFunction)Quad_lang_of, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insert", (PyCFunction)Quad_insert_lang, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insertto", (PyCFunction)GraphItem_insertto, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "deletefrom", (PyCFunction)GraphItem_deletefrom, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_l", (PyCFunction)Quad_with_l, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_o", (PyCFunction)Quad_with_l, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_s", (PyCFunction)Quad_with_s, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "collect_ns_to", (PyCFunction)Literal_collect_ns_to, METH_VARARGS,
        PyDoc_STR("")
    },
    {NULL,    NULL},
};


PyTypeObject LangQuadType = {
    PyObject_HEAD_INIT(NULL)
    0,                       /* ob_size */
    "graphlib.LangQuad",          /* tp_name */
    sizeof(GraphItem),    /* tp_basicsize */
    0,                       /* tp_itemsize */
    0,                       /* tp_dealloc */
    0,                       /* tp_print */
    0,                       /* tp_getattr */
    0,                       /* tp_setattr */
    0,                       /* tp_compare */
    0,                       /* tp_repr */
    0,                       /* tp_as_number */
    0,                       /* tp_as_sequence */
    0,                       /* tp_as_mapping */
    0,                       /* tp_hash */
    0,                       /* tp_call */
    0,                       /* tp_str */
    0,                       /* tp_getattro */
    0,                       /* tp_setattro */
    0,                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,   /* tp_flags */
    0,                       /* tp_doc */
    0,                       /* tp_traverse */
    0,                       /* tp_clear */
    0,                       /* tp_richcompare */
    0,                       /* tp_weaklistoffset */
    0,                       /* tp_iter */
    0,                       /* tp_iternext */
    LangQuadMethods,          /* tp_methods */
    0,                       /* tp_members */
    LangQuad_getseters,                       /* tp_getset */
    0,                       /* tp_base */
    0,                       /* tp_dict */
    0,                       /* tp_descr_get */
    0,                       /* tp_descr_set */
    0,                       /* tp_dictoffset */
    (initproc)GraphItem_init,   /* tp_init */
    0,                       /* tp_alloc */
    0,                       /* tp_new */
};

static PyGetSetDef DatatypeQuad_getseters[] = {
    {
        "s",
        (getter)GraphItem_first_expand, (setter)NULL,
        "subject",
        NULL
    },
    {
        "p",
        (getter)GraphItem_second_expand, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "l",
        (getter)GraphItem_third, (setter)NULL,
        "literal",
        NULL
    },
    {
        "v",
        (getter)GraphItem_third, (setter)NULL,
        "value",
        NULL
    },
    {
        "datatype",
        (getter)GraphItem_fourth_expand, (setter)NULL,
        "datatype",
        NULL
    },
    {
        "d",
        (getter)GraphItem_fourth_expand, (setter)NULL,
        "datatype",
        NULL
    },
    {
        "cs",
        (getter)GraphItem_first, (setter)NULL,
        "subject",
        NULL
    },
    {
        "cp",
        (getter)GraphItem_second, (setter)NULL,
        "predicate",
        NULL
    },
    {
        "cdatatype",
        (getter)GraphItem_fourth, (setter)NULL,
        "datatype",
        NULL
    },
    {NULL}  /* Sentinel */
};

static PyMethodDef DatatypeQuadMethods[] = {
    {
        "of", (PyCFunction)Quad_datatype_of, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insert", (PyCFunction)Quad_insert_datatype, METH_CLASS,
        PyDoc_STR("")
    },
    {
        "insertto", (PyCFunction)GraphItem_insertto, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "deletefrom", (PyCFunction)GraphItem_deletefrom, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_l", (PyCFunction)Quad_with_l, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_o", (PyCFunction)Quad_with_l, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "with_s", (PyCFunction)Quad_with_s, METH_VARARGS,
        PyDoc_STR("")
    },
    {
        "collect_ns_to", (PyCFunction)Datatype_collect_ns_to, METH_VARARGS,
        PyDoc_STR("")
    },
    {NULL,    NULL},
};


PyTypeObject DatatypeQuadType = {
    PyObject_HEAD_INIT(NULL)
    0,                       /* ob_size */
    "graphlib.DatatypeQuad",          /* tp_name */
    sizeof(GraphItem),    /* tp_basicsize */
    0,                       /* tp_itemsize */
    0,                       /* tp_dealloc */
    0,                       /* tp_print */
    0,                       /* tp_getattr */
    0,                       /* tp_setattr */
    0,                       /* tp_compare */
    0,                       /* tp_repr */
    0,                       /* tp_as_number */
    0,                       /* tp_as_sequence */
    0,                       /* tp_as_mapping */
    0,                       /* tp_hash */
    0,                       /* tp_call */
    0,                       /* tp_str */
    0,                       /* tp_getattro */
    0,                       /* tp_setattro */
    0,                       /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT |
    Py_TPFLAGS_BASETYPE,   /* tp_flags */
    0,                       /* tp_doc */
    0,                       /* tp_traverse */
    0,                       /* tp_clear */
    0,                       /* tp_richcompare */
    0,                       /* tp_weaklistoffset */
    0,                       /* tp_iter */
    0,                       /* tp_iternext */
    DatatypeQuadMethods,          /* tp_methods */
    0,                       /* tp_members */
    DatatypeQuad_getseters,                       /* tp_getset */
    0,                       /* tp_base */
    0,                       /* tp_dict */
    0,                       /* tp_descr_get */
    0,                       /* tp_descr_set */
    0,                       /* tp_dictoffset */
    (initproc)GraphItem_init,   /* tp_init */
    0,                       /* tp_alloc */
    0,                       /* tp_new */
};

int init_graphitem_types()
{
    PyObject *d = PyDict_New();
    PyDict_SetItemString(d, "has_object", Py_True);
    PyDict_SetItemString(d, "has_literal", Py_False);
    PyDict_SetItemString(d, "has_lang", Py_False);
    PyDict_SetItemString(d, "has_datatype", Py_False);
    ObjectTripleType.tp_base = &PyTuple_Type;
    ObjectTripleType.tp_dict = d;
    if (PyType_Ready(&ObjectTripleType) < 0) {
        return 0;
    }
    d = PyDict_New();
    PyDict_SetItemString(d, "has_object", Py_False);
    PyDict_SetItemString(d, "has_literal", Py_True);
    PyDict_SetItemString(d, "has_lang", Py_False);
    PyDict_SetItemString(d, "has_datatype", Py_False);
    LiteralTripleType.tp_base = &PyTuple_Type;
    LiteralTripleType.tp_dict = d;
    if (PyType_Ready(&LiteralTripleType) < 0) {
        return 0;
    }
    d = PyDict_New();
    PyDict_SetItemString(d, "has_object", Py_False);
    PyDict_SetItemString(d, "has_literal", Py_True);
    PyDict_SetItemString(d, "has_lang", Py_True);
    PyDict_SetItemString(d, "has_datatype", Py_False);
    LangQuadType.tp_base = &PyTuple_Type;
    LangQuadType.tp_dict = d;
    if (PyType_Ready(&LangQuadType) < 0) {
        return 0;
    }
    d = PyDict_New();
    PyDict_SetItemString(d, "has_object", Py_False);
    PyDict_SetItemString(d, "has_literal", Py_True);
    PyDict_SetItemString(d, "has_lang", Py_False);
    PyDict_SetItemString(d, "has_datatype", Py_True);
    DatatypeQuadType.tp_base = &PyTuple_Type;
    DatatypeQuadType.tp_dict = d;
    if (PyType_Ready(&DatatypeQuadType) < 0) {
        return 0;
    }
    return 1;
}

int public_graphitem_types(PyObject *m)
{
    Py_INCREF(&ObjectTripleType);
    if (PyModule_AddObject(m, "ObjectTriple", (PyObject *) &ObjectTripleType) < 0) {
        return 0;
    }
    Py_INCREF(&LiteralTripleType);
    if (PyModule_AddObject(m, "LiteralTriple", (PyObject *) &LiteralTripleType) < 0) {
        return 0;
    }
    Py_INCREF(&LangQuadType);
    if (PyModule_AddObject(m, "LangQuad", (PyObject *) &LangQuadType) < 0) {
        return 0;
    }
    Py_INCREF(&DatatypeQuadType);
    if (PyModule_AddObject(m, "DatatypeQuad", (PyObject *) &DatatypeQuadType) < 0) {
        return 0;
    }
    return 1;
}