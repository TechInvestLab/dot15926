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
#include "graph.h"
#include "rdf.h"
#include "raptor2/inc/raptor2.h"
#include "zlib/inc/zlib.h"
#include "graphitem.h"
#include <stdarg.h>
#include "base.h"
#include "fcntl.h"
#ifndef _INC_WINDOWS
#   define WIN32_LEAN_AND_MEAN
#   include <windows.h>
#endif
#ifndef _INC_PROCESS
#   include <process.h>
#endif

#define DEFAULT_EVENT_SIZE 512

enum ParserEventTypes {
    PE_ParseFailed,
    PE_Base,
    PE_Namespace,
    PE_ObjectTriple,
    PE_LiteralTriple,
    PE_LangQuad,
    PE_DatatypeQuad,
    PE_Finished,
    PE_Progress,
    PE_Log,
    PE_Graph
};

typedef struct {
    int         type;
    char *buffer;
    size_t size;
    size_t pos;
} ParserEvent;

#define EVENT_BUF_SIZE 100

typedef struct {
    __declspec(align(4)) volatile long stop;
    __declspec(align(4)) volatile long ev_head;
    __declspec(align(4)) volatile long ev_tail;
    const char *syntax;
    const char *filename;
    const char *data;
    __int64 data_len;
    ParserEvent *parser_events;
} RDFParserData;

static void
event_reserve(ParserEvent *ev, size_t size)
{
    if (ev->size < ev->pos + size) {
        ev->buffer = (char *)realloc(ev->buffer, ev->pos + size);
        ev->size = size;
    }
}

static void
event_write(ParserEvent *ev, const char *fmt, ...)
{
    const char *p = fmt;
    va_list ap;
    va_start(ap, fmt);
    while (*p) {
        if (*p == 'i') {
            event_reserve(ev, sizeof(int));
            *(int *)(ev->buffer + ev->pos) = va_arg(ap, int);
            ev->pos += sizeof(int);
        } else if (*p == 's') {
            const char *str = va_arg(ap, const char *);
            size_t l = strlen(str);
            event_reserve(ev, l + 1);
            memcpy(ev->buffer + ev->pos, str, l + 1);
            ev->pos += l + 1;
        } else {
            printf("unsupported format flag\n");
            break;
        }
        ++p;
    }
    va_end(ap);
}

static void
event_read(ParserEvent *ev, const char *fmt, ...)
{
    const char *p = fmt;
    va_list ap;
    va_start(ap, fmt);
    while (*p) {
        if (*p == 'i') {
            *(va_arg(ap, int *)) = *(int *)(ev->buffer + ev->pos);
            ev->pos += sizeof(int);
        } else if (*p == 's') {
            size_t l;
            *va_arg(ap, const char **) = (const char *)(ev->buffer + ev->pos);
            l = strlen((const char *)(ev->buffer + ev->pos));
            ev->pos += l + 1;
        } else {
            printf("unsupported format flag\n");
            break;
        }
        ++p;
    }
    va_end(ap);
}

static RDFParserData *
parser_new_data()
{
    RDFParserData *data = NULL;
    int i;
    data = (RDFParserData *)calloc(1, sizeof(RDFParserData));
    data->parser_events = (ParserEvent *)calloc(EVENT_BUF_SIZE, sizeof(ParserEvent));
    for (i =0 ; i < EVENT_BUF_SIZE; ++i) {
       data->parser_events[i].buffer = (char *)malloc(DEFAULT_EVENT_SIZE);
       data->parser_events[i].size = DEFAULT_EVENT_SIZE;
    }
    return data;
}

static void
parser_free_data(RDFParserData *data)
{
    int i;
    for (i = 0; i < EVENT_BUF_SIZE; ++i) {
        free(data->parser_events[i].buffer);
    }
    free(data->parser_events);
    free(data);
}

static ParserEvent *
parser_get_event(RDFParserData *data)
{
    data->parser_events[data->ev_tail].pos = 0;
    return &data->parser_events[data->ev_tail];
}

static void
parser_send_event(RDFParserData *data)
{
    while ((data->ev_tail + 1) % EVENT_BUF_SIZE == data->ev_head) {
        Sleep(0);
    }
    data->ev_tail = (data->ev_tail + 1) % EVENT_BUF_SIZE;
}

static ParserEvent *
parser_acquire_event(RDFParserData *data)
{
    while (data->ev_head == data->ev_tail) {
        Py_BEGIN_ALLOW_THREADS
        Sleep(0);
        Py_END_ALLOW_THREADS
    }
    data->parser_events[data->ev_head].pos = 0;
    return &data->parser_events[data->ev_head];
}

static void
parser_release_event(RDFParserData *data)
{
    if( data->parser_events[data->ev_head].size > DEFAULT_EVENT_SIZE) {
        free(data->parser_events[data->ev_head].buffer);
        data->parser_events[data->ev_head].buffer = (char *)malloc(DEFAULT_EVENT_SIZE);
        data->parser_events[data->ev_head].size = DEFAULT_EVENT_SIZE;
    }
    data->ev_head = (data->ev_head + 1) % EVENT_BUF_SIZE;
}

static const char* const log_level_labels[RAPTOR_LOG_LEVEL_LAST + 1] = {
  "none",
  "trace",
  "debug",
  "info",
  "warning",
  "error",
  "fatal error"
};

static void 
graph_mark_handler(void *user_data, raptor_uri *graph, int flags)
{
    RDFParserData *data = (RDFParserData *)user_data;
    ParserEvent *ev = parser_get_event(data);
    ev->type = PE_Graph;
    if((flags & RAPTOR_GRAPH_MARK_START) && graph) {
        const char *uri = (char *)raptor_uri_as_string(graph);
        const char* name = strrchr(uri, '//');
        if(++name) {
            event_write(ev, "s", name);
        } else {
            event_write(ev, "s", uri);
        }
    } else {
        event_write(ev, "s", "");
    }
    parser_send_event(data);
}

static void 
log_handler(void *user_data, raptor_log_message *message)
{
    RDFParserData *data = (RDFParserData *)user_data;
    ParserEvent *ev = parser_get_event(data);
    char log_str[1000];
    char locator_str[250];
    if (raptor_locator_format(locator_str, 250, message->locator) == 0) {
        snprintf(log_str, 1000, "%s raptor %s - %s\n", locator_str,
                log_level_labels[message->level], message->text);
    } else {
        snprintf(log_str, 1000, "raptor %s - %s\n",
                log_level_labels[message->level], message->text);
    }
    ev->type = PE_Log;
    event_write(ev, "s", log_str);
    parser_send_event(data);
}

static unsigned char *
bnodeid_handler(void *user_data, unsigned char* user_bnodeid)
{
    if (user_bnodeid) {
        return user_bnodeid;
    } else {
        const char *value = new_bnodeid();
        size_t s = strlen(value) + 1;
        unsigned char *result = (unsigned char *)raptor_alloc_memory(s);
        memcpy(result, value, s);
        return result;
    }
}

static void
handle_namespace(void *user_data, raptor_namespace *nspace)
{
    RDFParserData *data = (RDFParserData *)user_data;
    const char *pre = (char *)raptor_namespace_get_prefix(nspace);
    raptor_uri *ruri = raptor_namespace_get_uri(nspace);
    const char *uri = (char *)raptor_uri_as_string(ruri);
    if (pre && uri) {
        ParserEvent *ev = parser_get_event(data);
        if(!strcmp(pre, "basens")) {
            ev->type = PE_Base;
            event_write(ev, "s", uri);
        } else {
            ev->type = PE_Namespace;
            event_write(ev, "ss", pre, uri);
        }
        parser_send_event(data);
    }
}

static void
handle_triple(void *user_data, raptor_statement *triple)
{
    RDFParserData *data = (RDFParserData *)user_data;
    ParserEvent *ev = parser_get_event(data);
    if (triple->subject->type == RAPTOR_TERM_TYPE_URI) {
        event_write(ev, "s", (char *)raptor_uri_as_string(triple->subject->value.uri));
    } else if (triple->subject->type == RAPTOR_TERM_TYPE_BLANK) {
        if (!memcmp(triple->subject->value.blank.string, bnode_prefix, bnode_prefix_len)) {
            event_write(ev, "s", (char *)triple->subject->value.blank.string);
        } else {
            event_write(ev, "s", bnodeid((char *)triple->subject->value.blank.string));
        }
    } else {
        return;
    }
    if (triple->predicate->type == RAPTOR_TERM_TYPE_URI) {
        event_write(ev, "s", (char *)raptor_uri_as_string(triple->predicate->value.uri));
    } else if (triple->predicate->type == RAPTOR_TERM_TYPE_BLANK) {
        if (!memcmp(triple->predicate->value.blank.string, bnode_prefix, bnode_prefix_len)) {
            event_write(ev, "s", (char *)triple->predicate->value.blank.string);
        } else {
            event_write(ev, "s", bnodeid((char *)triple->predicate->value.blank.string));
        }
    } else {
        return;
    }
    if (triple->object->type == RAPTOR_TERM_TYPE_LITERAL) {
        event_write(ev, "s", (char *)triple->object->value.literal.string);
        if (triple->object->value.literal.datatype) {
            event_write(ev, "s", (char *)raptor_uri_as_string(triple->object->value.literal.datatype));
            ev->type = PE_DatatypeQuad;
        } else if (triple->object->value.literal.language) {
            event_write(ev, "s", (char *)triple->object->value.literal.language);
            ev->type = PE_LangQuad;
        } else {
            ev->type = PE_LiteralTriple;
        }
    } else if (triple->object->type == RAPTOR_TERM_TYPE_URI) {
        event_write(ev, "s", (char *)raptor_uri_as_string(triple->object->value.uri));
        ev->type = PE_ObjectTriple;
    } else if (triple->object->type == RAPTOR_TERM_TYPE_BLANK) {
        if (!memcmp(triple->object->value.blank.string, bnode_prefix, bnode_prefix_len)) {
            event_write(ev, "s", (char *)triple->object->value.blank.string);
        } else {
            event_write(ev, "s", bnodeid((char *)triple->object->value.blank.string));
        }
        ev->type = PE_ObjectTriple;
    }
    parser_send_event(data);
}

#define BUF_SIZE 4096
#define USE_GZIP

void RDFParserProc(void *user_data)
{
    RDFParserData *data = (RDFParserData *)user_data;
    ParserEvent *ev;
    raptor_world *world = NULL;
    raptor_parser *rdf_parser = NULL;
    raptor_uri *uri = NULL;
    int progress = -1;
    int done = 0;
    size_t size = 0;
    __int64 read = 0;
    world = raptor_new_world();
    rdf_parser = raptor_new_parser(world, data->syntax);
    raptor_world_set_generate_bnodeid_handler(world, NULL, bnodeid_handler);
    raptor_parser_set_namespace_handler(rdf_parser, data, handle_namespace);
    raptor_parser_set_statement_handler(rdf_parser, data, handle_triple);
    raptor_parser_set_option(rdf_parser, RAPTOR_OPTION_ALLOW_RDF_TYPE_RDF_LIST, NULL, 1);
    raptor_world_set_log_handler(world, data, log_handler);
    raptor_parser_set_graph_mark_handler(rdf_parser, data, graph_mark_handler);
    if (data->filename) {
        int fd;
        size_t len = MultiByteToWideChar(CP_UTF8, 0, data->filename, -1, NULL, 0);
        wchar_t *fn = malloc(sizeof(wchar_t) * len);
        MultiByteToWideChar(CP_UTF8, 0, data->filename, -1, fn, len);
        fd = _wopen(fn, O_RDONLY | O_BINARY);
        free(fn);
        if (fd != -1) {
            unsigned char *uri_string = NULL;
            unsigned char buf[BUF_SIZE];
            __int64 filesize;
#ifdef USE_GZIP
            gzFile gzf;
#endif
            uri_string = raptor_uri_filename_to_uri_string(data->filename);
            uri = raptor_new_uri(world, uri_string);
            raptor_parser_parse_start(rdf_parser, uri);
            _lseeki64(fd, 0, SEEK_END);
            filesize = _telli64(fd);
            _lseeki64(fd, 0, SEEK_SET);
            gzf = gzdopen(fd, "r");
            do {
#ifdef USE_GZIP
                size = gzread(gzf, buf, BUF_SIZE);
                if (gzeof(gzf)) 
                    done = 1;
                read = gzoffset(gzf);
#else
                size = _read(fd, buf, BUF_SIZE);
                if (eof(fd)) 
                    done = 1;
                read = _telli64(fd);
#endif
                if (raptor_parser_parse_chunk(rdf_parser, buf, size, done)) {
                    done = -1;
                }
                if (progress != (int)(100.f * read / filesize)) {
                    progress = (int)(100.f * read / filesize);
                    ev = parser_get_event(data);
                    ev->type = PE_Progress;
                    event_write(ev, "i", progress);
                    parser_send_event(data);
                }
            } while (!done && !data->stop);
#ifdef USE_GZIP
            gzclose(gzf);
#else
            close(fd);
#endif
            raptor_free_memory(uri_string);
        } else {
            done = -1;
        }
    } else if (data->data && data->data_len) {
        unsigned char *buf = (unsigned char *)data->data;
        uri = raptor_new_uri(world, "file://string");
        raptor_parser_parse_start(rdf_parser, uri);
        do {
            if (data->data_len - read <= BUF_SIZE) {
                size = (size_t)(data->data_len - read);
                done = 1;
            } else {
                size = BUF_SIZE;
            }
            if (raptor_parser_parse_chunk(rdf_parser, buf + read, size, done)) {
                done = -1;
            }
            read += size;
            //if (progress != (int)(100.f * read / data->data_len)) {
            //    progress = (int)(100.f * read / data->data_len);
            //    ev = parser_get_event(data);
            //    ev->type = PE_Progress;
            //    event_write(ev, "i", progress);
            //    parser_send_event(data);
            //}
        } while (!done && !data->stop);
    }
    raptor_free_parser(rdf_parser);
    raptor_free_uri(uri);
    raptor_free_world(world);
    ev = parser_get_event(data);
    ev->type = done == -1 ? PE_ParseFailed : PE_Finished;
    parser_send_event(data);
}

static int
RDFParse(RDFParserData *data, Graph *graph)
{
    HANDLE thread;
    int done = 0;
    Graph *current_graph = graph;
    thread = (HANDLE)_beginthread(RDFParserProc, 0, data);
    do {
        int res = 0;
        ParserEvent *ev = parser_acquire_event(data);
        switch (ev->type) {
            case PE_ParseFailed:
                done = -1;
                break;
            case PE_Finished:
                done = 1;
                break;
            case PE_Base: {
                const char *basens;
                event_read(ev, "s", &basens);
                res = Graph_set_basens(current_graph, basens);
            }
            break;
            case PE_Namespace: {
                const char *prefix, *uri;
                event_read(ev, "ss", &prefix, &uri);
                res = Graph_add_ns(current_graph, prefix, uri);
            }
            break;
            case PE_ObjectTriple: {
                const char *s, *p, *o;
                event_read(ev, "sss", &s, &p, &o);
                res = Graph_insert_object(current_graph, s, p, o);
            }
            break;
            case PE_LiteralTriple: {
                const char *s, *p, *l;
                event_read(ev, "sss", &s, &p, &l);
                res = Graph_insert_literal(current_graph, s, p, l);
            }
            break;
            case PE_LangQuad: {
                const char *s, *p, *l, *c;
                event_read(ev, "ssss", &s, &p, &l, &c);
                res = Graph_insert_lang(current_graph, s, p, l, c);
            }
            break;
            case PE_DatatypeQuad: {
                const char *s, *p, *l, *c;
                event_read(ev, "ssss", &s, &p, &l, &c);
                res = Graph_insert_datatype(current_graph, s, p, l, c);
            }
            break;
            case PE_Log: {
                PyObject *value;
                const char *s;
                event_read(ev, "s", &s);
                value = Py_BuildValue("s", s);
                res = Graph_call_cb(graph, GE_LOG, value);
                Py_DECREF(value);
            }
            break;
            case PE_Graph: {
                const char *s;
                event_read(ev, "s", &s);
                if (strlen(s) == 0) {
                    current_graph = graph;
                } else {
                    current_graph = (Graph *)PyDict_GetItemString(graph->ng, s);
                    if (!current_graph) {
                        current_graph = (Graph *)PyObject_CallObject(graph->gt, NULL);
                        if (current_graph) {
                            PyDict_SetItemString(graph->ng, s, (PyObject *)current_graph);
                            Py_DECREF(current_graph);
                        } else {
                            res = -1;
                        }
                    }
                }
            }
            break;
            case PE_Progress: {
                PyObject *value;
                size_t progress;
                event_read(ev, "i", &progress);
                value = Py_BuildValue("I", progress);
                res = Graph_call_cb(graph, GE_PROGRESS, value);
                Py_DECREF(value);
            }
            break;
        }
        parser_release_event(data);
        if (res == -1 || PyErr_Occurred()) {
            data->stop = 1;
        }
    } while (!done);
    parser_free_data(data);
    return done == 1 ? 0 : -1;
}

int
_read_rdf_string(const char *str, size_t len, Graph *graph, const char *syntax)
{
    RDFParserData* data = parser_new_data();
    data->data = str;
    data->data_len = len;
    data->syntax = syntax;
    return RDFParse(data, graph);
}

int
_read_rdf_file(const char *filename, Graph *graph, const char *syntax)
{
    RDFParserData* data = parser_new_data();
    data->filename = filename;
    data->syntax = syntax;
    return RDFParse(data, graph);
}