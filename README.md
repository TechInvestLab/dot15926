# dot15926

Welcome to the .15926 Platform and Editor (pronounced “dot 15926”).

.15925 Editor is a free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 3.0 of the License, or (at your option) any later version.

.15925 Editor is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

Compiled versions of the software can be downloaded from http://techinvestlab.ru/dot15926Editor . Both stable version 1.43 and experimental version 1.5beta release 3 are available for download. Initial commit to this repository corresponds to the version 1.5beta release 3.

.15926 Platform is a name for an architecture and a set of interfaces and libraries to work with semantic data in RDF format, and specifically with data compliant to the ISO 15926 standard. It is developed by TechInvestLab.ru to facilitate creation of semantic applications to work with data in all possible ways – read, visualize, explore, search, reason, map, write, exchange, etc.

In .15926 Editor you can: 

• Browse ISO 15926 upper ontology in three different namespaces: PCA, RDS/WIP or ISO.

• Search and navigate public ISO 15926 SPARQL endpoints, 

… or any other SPARQL endpoint you like, with authorization if required, 

… including search for legacy RDS/WIP identifiers.

• Search, navigate and edit reference data files distributed publicly, including ISO 15926-4, PCA RDL and ISO 15926-8 templates, 

... or any other RDF files you like in XML or Turtle.

• Build complex data project from local files and endpoints, bringing reference data, template definitions and project data together for integrated navigation and verification, customizing namespaces, properties and meta-data attributes.

• Design and run intricate semantic queries or whole data mining and verification algorithms for ISO 15926 data or any other RDF data, 

… using the power of Python general purpose programming language through full-featured REPL environment, 

… and accessing APIs of various .15926 Platform components to read, analyze and change reference and project data.

• Create from scratch your own reference classes and templates, create project data (including template instances) manually or through your own adapters, 

… in forms ready for file exchange or upload to triple store, 

… generating URI in your namespaces using UUID compliant with RFC 4122 / ITU-T X.667 / ISO/IEC 9834-8.

• Compare data sources, build diff files, review changes and create versioning system for reference and project data, or for any ontology. 

• Define data patterns, search for patterns in your data, and visualize search results, map spreadsheets to patterns.

• Extend .15926 Editor functionality (develop your own mapping adapters for example) using Python, any external Python libraries and APIs of .15926 Platform components, 

… testing and debugging them in the .15926 Editor environment, 

… registering them as .15926 Editor extensions.

• Use or modify extensions from TechInvestLab.ru: 

o pattern-based Linked Data semantic server with built-in web engine;

o spreadsheet mapping to create semantic data from Excel spreadsheets;

o conversion of reference and project data from TabLan.15926 data description tables (.xlsx) to ISO 15926 RDF; 

o import of reference data from JSON files created by engineering catalog application (third party); 

o creation or import of template definitions in iRING spreadsheet format.

• Explore (with somewhat limited capabilities) any large RDF datasets, 

… OpenCYC knowledge base, for example.

.15926 Editor is a tool designed with three major goals in mind: 

• explore existing sources of reference data in as many formats as possible; 

• verify reference data; 

• engineer and manage new reference data, including automated reference data creation through adaptors incorporating mapping from external sources.

The Editor is intended to become for ISO 15926 data what Protégé became for OWL data – a primary tool for data exploration.

The Editor is not designed to support any particular reference data management or data integration workflow. Specific applications for this can be built on .15926 Platform tailored to the requirements of organizations exchanging data – namespaces, endpoints, properties, databases, transport layers, etc.

Mapping components are integrated in .15926 Platform environment as extensions using external or internal pattern mapping descriptions and directly accessing APIs of source/target databases.

Please contact TechInvestLab.ru at dot15926@gmail.com for further details.
