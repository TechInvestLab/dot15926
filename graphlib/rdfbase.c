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

void _rdf_parser_info()
{
    raptor_world *world = NULL;
    int i;
    world = raptor_new_world();
    PySys_WriteStdout("Syntaxes:\n");
    for (i = 0; 1; i++) {
        const raptor_syntax_description *sd;
        sd = raptor_world_get_parser_description(world, i);
        if (!sd) {
            break;
        }
        PySys_WriteStdout("  %-14s for %s\n", sd->names[0], sd->label);
    }
    raptor_free_world(world);
}