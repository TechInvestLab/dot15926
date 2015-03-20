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




ns_pcardl_rdf = 'http://posccaesar.org/rdl/'
ns_pcardl_sparql = 'http://posccaesar.org/rdl/'
annlist_pcardl = [
    'hasIdPCA', 'hasDesignation', 'hasDesignationAltern', 'hasDesignationAbbrev',
    'hasDefinition', 'hasDefinitionAdapted', 'hasStatus', 'hasCreationDate',
    'hasCreator', 'hasDeleted', 'hasSubmitter', 'hasSubmitterOrg', 'hasRegistrar',
    'hasRegistrarAuth', 'hasStewardship', 'hasStewardshipContact', 'hasNote',
    'hasNoteAdmin', 'hasNoteExplanatory', 'hasNoteExample', 'hasNoteChange',
    'hasNoteIssue', 'defaultRdsId',
]

pca_rdf_designation = ns_pcardl_rdf + 'hasDesignation'
pca_rdf_designation = ns_pcardl_rdf + 'hasDesignation'
pca_rdf_definition  = ns_pcardl_rdf + 'hasDefinition'

pca_sparql_designation = ns_pcardl_sparql + 'hasDesignation'
pca_sparql_definition  = ns_pcardl_sparql + 'hasDefinition'

labels_pca_rdf      = [pca_rdf_designation, pca_rdf_definition]
labels_pca_sparql   = [pca_sparql_designation, pca_sparql_definition]
labels_pca          = labels_pca_rdf + labels_pca_sparql

ns_rdswip = 'http://rdl.rdlfacade.org/data#'

annlist_meta = [
    'annUniqueName', 'annTextDefinition', 'annSource', 'annNotes',
    'annAdministrativeNote', 'annExplanatoryComment', 'annChangeDescription',
    'annRule', 'annAccessCode', 'annURI', 'annUniqueNumber', 'annSynonym',
    'annCreationDate', 'annEffectiveDate', 'annLastChangeDate', 'annRegistrationStatus',
    'annStewardshipContact', 'annStewardshipOrganization', 'annSubmissionContact',
    'annSubmittingOrganization', 'annUnresolvedIssues', 'annSymbol', 'annOperator',
    'annFirstOperand', 'annSecondOperand', 'annFactor_Prefix', 'annExponent'
]


ns_old_part4 = 'http://rds.posccaesar.org/2009/10/OWL/ISO-15926-4_2007#'
annlist_old_part4 = ['spreadsheet']

ns_old_part6 = 'http://rds.posccaesar.org/2008/02/OWL/ISO-15926-6_2008_Draft#'
annlist_old_part6 = ['designation', 'definition', 'source', 'notes']


ns_til = 'http://techinvestlab.ru/meta#'
annlist_til = ['label_ru', 'label_en']
