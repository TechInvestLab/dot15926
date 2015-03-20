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
#include "base.h"
#include "graph.h"
#include "graphitem.h"
#include "rdf.h"

static PyObject *
  read_rdf_file(PyObject *self, PyObject *args)
{
  const char *fname;
  const char *syntax="rdfxml";
  PyObject *graph;

  if (!PyArg_ParseTuple(args, "sO|s", &fname, &graph, &syntax))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  if(_read_rdf_file(fname, (Graph*)graph, syntax) == -1) {
    PyErr_SetString(PyExc_Exception,
    "Loading RDF failed.");
    return NULL;
  }

  Py_RETURN_NONE;
}

static PyObject *
  read_rdf_string(PyObject *self, PyObject *args)
{
  const char *data;
  size_t len;
  const char *syntax="rdfxml";
  PyObject *graph;

  if (!PyArg_ParseTuple(args, "slO|s", &data, &len, &graph, &syntax))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  if(_read_rdf_string(data, len, (Graph*)graph, syntax) == -1) {
    PyErr_SetString(PyExc_Exception,
    "Loading RDF failed.");
    return NULL;
  }

  Py_RETURN_NONE;
}

static PyObject *
new_bnodeid_func(PyObject *self)
{
  return py_new_bnodeid();
}

static PyObject *
bnodeid_func(PyObject *self, PyObject *args)
{
  PyObject *str;

  if (!PyArg_ParseTuple(args, "S", &str))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  return py_bnodeid(str);
}

static PyObject *
compact_uri_func(PyObject *self, PyObject *args)
{
  PyObject *str;

  if (!PyArg_ParseTuple(args, "S", &str))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  return py_compact_uri(str);
}

static PyObject *
expand_uri_func(PyObject *self, PyObject *args)
{
  PyObject *str;

  if (!PyArg_ParseTuple(args, "S", &str))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  return py_expand_uri(str);
}

static PyObject *
curi_head_func(PyObject *self, PyObject *args)
{
  PyObject *str;

  if (!PyArg_ParseTuple(args, "S", &str))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  return py_curi_head(str);
}

static PyObject *
curi_tail_func(PyObject *self, PyObject *args)
{
  PyObject *str;

  if (!PyArg_ParseTuple(args, "S", &str))
  {
    PyErr_SetString(PyExc_TypeError,
    "argument error");
    return NULL;
  }

  return py_curi_tail(str);
}

static PyObject *
rdf_parser_info(PyObject *self)
{
  _rdf_parser_info();
  Py_RETURN_NONE;
}

static PyMethodDef graphlib_functions[] = {
    { "new_bnodeid",	(PyCFunction)new_bnodeid_func,	METH_NOARGS,
        ""
    },
    { "bnodeid",	(PyCFunction)bnodeid_func,	METH_VARARGS,
        ""
    },
    { "compact_uri",	compact_uri_func,	METH_VARARGS,
        ""
    },
    { "expand_uri",	expand_uri_func,	METH_VARARGS,
        ""
    },
    { "curi_head",	curi_head_func,	METH_VARARGS,
        ""
    },
    { "curi_tail",	curi_tail_func,	METH_VARARGS,
        ""
    },
    { "read_rdf_file",	read_rdf_file,	METH_VARARGS,
        ""
    },
    { "read_rdf_string", read_rdf_string, METH_VARARGS,
        ""
    },
    { "rdf_parser_info",	(PyCFunction)rdf_parser_info,	METH_NOARGS,
        ""
    },
    {NULL,		NULL}		/* sentinel */
};

PyMODINIT_FUNC
initgraphlib()
{
    PyObject *m;

    m = PyImport_ImportModule("_ordereddict");
    Py_DECREF(m);

    init_graph_types();
    init_graphitem_types();

    m = Py_InitModule3("graphlib",
                       graphlib_functions,
                       ""
                       // , NULL, PYTHON_API_VERSION
                      );
    if (m == NULL)
        return;


    if (PyModule_AddObject(m, "bnode_prefix", (PyObject *) PyString_FromString(bnode_prefix)) < 0) {
        return;
    }

    public_graph_types(m);
    public_graphitem_types(m);
}
