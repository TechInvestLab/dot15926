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


#ifndef _RDFPARSER_H_
#define _RDFPARSER_H_

void _rdf_parser_info();
int _read_rdf_file(const char *filename, Graph *graph, const char* syntax);
int _read_rdf_string(const char *str, size_t len, Graph *graph, const char* syntax);
int _write_rdf_file(const char *filename, Graph *graph, const char *syntax);

#endif
