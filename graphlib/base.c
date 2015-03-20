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
#include <windows.h>

static DWORD _dwTlsIndex_buffer; // address of shared memory
static DWORD _dwTlsIndex_nscache; // address of shared memory

char _b64_encode[0x041] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
char _b64_decode[0x100];

const char * const bnode_prefix = "_#z";
const size_t bnode_prefix_len = 3;

typedef struct {
    char    **nsuri;
    size_t  *nslen;
    size_t  count;
} ns_data;

ns_data *_namespaces;
CRITICAL_SECTION _cs;

__declspec(align(4)) volatile long bnode_count = 100000;

static
int ns_data_push(ns_data *namespaces, const char *str, int num)
{
    char *ns = (char *)malloc(num + 1);
    strncpy(ns, str, num);
    ns[num] = '\0';
    namespaces->nsuri = (char **)realloc(namespaces->nsuri, (namespaces->count + 1) * sizeof(char *));
    namespaces->nsuri[namespaces->count] = ns;
    namespaces->nslen = (size_t *)realloc(namespaces->nslen, (namespaces->count + 1) * sizeof(size_t));
    namespaces->nslen[namespaces->count] = num;
    return namespaces->count++;
}

ns_data *ns_data_new()
{
    return (ns_data *)calloc(1, sizeof(ns_data));
}

void ns_data_free(ns_data *namespaces)
{
    size_t i;
    for (i = 0; i < namespaces->count; ++i) {
        free(namespaces->nsuri[i]);
    }
    free(namespaces->nsuri);
    free(namespaces->nslen);
    free(namespaces);
}

void ns_data_copy(ns_data *dst, ns_data *src)
{
    if (src->count > dst->count) {
        size_t i;
        for (i = dst->count; i < src->count; ++i) {
            ns_data_push(dst, src->nsuri[i], src->nslen[i]);
        }
    }
}

int ns_data_find(ns_data *namespaces, const char *str, int num)
{
    size_t i;
    for (i = 0; i < namespaces->count; ++i) {
        if (namespaces->nslen[i] == num && !strncmp(namespaces->nsuri[i], str, num)) {
            return i;
        }
    }
    return -1;
}

static
char * get_str_buffer() {
    char *buffer = (char *)TlsGetValue(_dwTlsIndex_buffer);
    if (!buffer) {
        buffer = (char *)malloc(MAX_URI_LENGTH + 1);
        TlsSetValue(_dwTlsIndex_buffer, buffer);
    }
    return buffer;
}

static
ns_data * get_ns_cache() {
    ns_data * cache = (ns_data *)TlsGetValue(_dwTlsIndex_nscache);
    if (!cache) {
        cache = ns_data_new();
        TlsSetValue(_dwTlsIndex_nscache, cache);
    }
    return cache;
}

void init_base()
{
    size_t i;
    for (i = 0; i < 0x100; ++i) {
        char j;
        _b64_decode[i] = -1;
        for (j = 0; j < 0x40; ++j)
            if (i == _b64_encode[j]) {
                _b64_decode[i] = j;
            }
    }
    _namespaces = ns_data_new();
    ns_data_push(_namespaces, "", 0);
    InitializeCriticalSection(&_cs);
}

void clear_base()
{
    ns_data_free(_namespaces);
    DeleteCriticalSection(&_cs);
}

char *IntToB64(int num, char *str)
{
    str[0] = _b64_encode[(num & 0xFC0) >> 6];
    str[1] = _b64_encode[(num & 0x3F)];
    return str + 2;
}

size_t B64ToInt(const char *str)
{
    return (_b64_decode[str[0]] << 6) + _b64_decode[str[1]];
}

char *compact_uri(const char *uri, char *out)
{
    ns_data *nscache = get_ns_cache();
    const char *tail;
    assert(strlen(uri) + 2 < MAX_URI_LENGTH);
    tail = max(strrchr(uri, '#'), strrchr(uri, '/'));
    if (tail != NULL) {
        int idx;
        ++tail;
        idx = ns_data_find(nscache, uri, tail - uri);
        if (idx == -1)  {
            EnterCriticalSection(&_cs);
            idx = ns_data_find(_namespaces, uri, tail - uri);
            if (idx == -1) {
                idx = ns_data_push(_namespaces, uri, tail - uri);
            }
            ns_data_copy(nscache, _namespaces);
            LeaveCriticalSection(&_cs);
        }
        strcpy(IntToB64(idx, out), tail);
    } else {
        strcpy(IntToB64(0, out), uri);
    }
    return out;
}

char *expand_uri(const char *curi, char *out)
{
    ns_data *nscache = get_ns_cache();
    size_t idx = B64ToInt(curi);
    const char *ns;
    size_t l;
    if (idx >= nscache->count) {
        EnterCriticalSection(&_cs);
        ns_data_copy(nscache, _namespaces);
        LeaveCriticalSection(&_cs);
    }
    ns = nscache->nsuri[idx];
    l = nscache->nslen[idx];
    assert(strlen(curi + 2) + l < MAX_URI_LENGTH);
    memcpy(out, ns, l);
    strcpy(out + l, curi + 2);
    return out;
}

char *curi_head(const char *curi, char *out)
{
    memcpy(out, curi, 2);
    out[2] = '\0';
    return out;
}

char *curi_tail(const char *curi, char *out)
{
    assert(strlen(curi + 2) < MAX_URI_LENGTH);
    strcpy(out, curi + 2);
    return out;
}

const char *compact_uri_str(const char *uri)
{
    char *out = get_str_buffer();
    return compact_uri(uri, out);
}

const char *expand_uri_str(const char *curi)
{
    char *out = get_str_buffer();
    return expand_uri(curi, out);
}

const char *new_bnodeid()
{
    char *out = get_str_buffer();
    long value = InterlockedIncrement(&bnode_count);
    memcpy(out, bnode_prefix, bnode_prefix_len);
    sprintf(out + bnode_prefix_len, "%u", value);
    return out;
}

const char *bnodeid(const char *id)
{
    char *out = get_str_buffer();
    assert(strlen(id) + bnode_prefix_len < MAX_URI_LENGTH);
    memcpy(out, bnode_prefix, bnode_prefix_len);
    strcpy(out + bnode_prefix_len, id);
    return out;
}

PyObject *py_new_bnodeid()
{
    return PyString_FromString(new_bnodeid());
}

PyObject *py_bnodeid(PyObject *id)
{
    return PyString_FromString(bnodeid(PyString_AsString(id)));
}

PyObject *py_compact_uri(PyObject *uri)
{
    char *out = get_str_buffer();
    return PyString_FromString(compact_uri(PyString_AsString(uri), out));
}

PyObject *py_expand_uri(PyObject *uri)
{
    char *out = get_str_buffer();
    return PyString_FromString(expand_uri(PyString_AsString(uri), out));
}

PyObject *py_curi_head(PyObject *curi)
{
    char *out = get_str_buffer();
    return PyString_FromString(curi_head(PyString_AsString(curi), out));
}

PyObject *py_curi_tail(PyObject *curi)
{
    char *out = get_str_buffer();
    return PyString_FromString(curi_tail(PyString_AsString(curi), out));
}

//#include <crtdbg.h>

BOOL WINAPI DllMain(HINSTANCE hinstDLL,
                    DWORD fdwReason,
                    LPVOID lpvReserved)
{
    char *buffer;
    ns_data *cache;
    switch (fdwReason) {
        case DLL_PROCESS_ATTACH:
            //_CrtSetDbgFlag(_CRTDBG_ALLOC_MEM_DF | _CRTDBG_CHECK_ALWAYS_DF | _CRTDBG_LEAK_CHECK_DF | _CRTDBG_DELAY_FREE_MEM_DF);
            if ((_dwTlsIndex_buffer = TlsAlloc()) == TLS_OUT_OF_INDEXES) {
                return FALSE;
            }
            if ((_dwTlsIndex_nscache = TlsAlloc()) == TLS_OUT_OF_INDEXES) {
                return FALSE;
            }
            init_base();
        case DLL_THREAD_ATTACH:
            TlsSetValue(_dwTlsIndex_buffer, NULL);
            TlsSetValue(_dwTlsIndex_nscache, NULL);
            break;
        case DLL_THREAD_DETACH:
            buffer = (char *)TlsGetValue(_dwTlsIndex_buffer);
            if (buffer != NULL) {
                free(buffer);
            }
            cache = (ns_data *)TlsGetValue(_dwTlsIndex_nscache);
            if (cache != NULL) {
                ns_data_free(cache);
            }
            break;
        case DLL_PROCESS_DETACH:
            clear_base();
            buffer = (char *)TlsGetValue(_dwTlsIndex_buffer);
            if (buffer != NULL) {
                free(buffer);
            }
            cache = (ns_data *)TlsGetValue(_dwTlsIndex_nscache);
            if (cache != NULL) {
                ns_data_free(cache);
            }
            TlsFree(_dwTlsIndex_buffer);
            TlsFree(_dwTlsIndex_nscache);
            break;
        default:
            break;
    }
    return TRUE;
    UNREFERENCED_PARAMETER(hinstDLL);
    UNREFERENCED_PARAMETER(lpvReserved);
}