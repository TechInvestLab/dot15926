"""
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
"""




from graphlib import *

import copy_reg, copy, pickle

def ObjectTripleCreator(s, p, v):
	return ObjectTriple.of(s, p, v)

def LiteralTripleCreator(s, p, v):
	return LiteralTriple.of(s, p, v)

def DatatypeQuadCreator(s, p, v, d):
	return DatatypeQuad.of(s, p, v, d)

def LangQuadCreator(s, p, v, d):
	return LangQuad.of(s, p, v, d)		

def pickle_ObjectTriple(triple):
    return ObjectTripleCreator, (triple.s,triple.p,triple.v)

def pickle_LiteralTriple(triple):
    return LiteralTripleCreator, (triple.s,triple.p,triple.v)

def pickle_DatatypeQuad(triple):
    return DatatypeQuadCreator, (triple.s,triple.p,triple.v,triple.d)

def pickle_LangQuad(triple):
    return LangQuadCreator, (triple.s,triple.p,triple.v,triple.d)

copy_reg.pickle(ObjectTriple, pickle_ObjectTriple)
copy_reg.pickle(LiteralTriple, pickle_LiteralTriple)
copy_reg.pickle(DatatypeQuad, pickle_DatatypeQuad)
copy_reg.pickle(LangQuad, pickle_LangQuad)
