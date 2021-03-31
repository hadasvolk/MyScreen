import sys
import logging
import pandas as pd
import numpy as np


NO_DATA = '' # For get_sampleInfo().
extraInfo_COLNUM = 11 # For get_sampleInfo().


"""
    Strips name of everything after '_S', and gets rid of 'Case_' if exists.
    Used in:
        - get_sampleInfo()
        - createResultSummaries() in RCv2_functions.py
    INPUT:
        1) full_name - full raw name.
    OUTPUT:
        1) final_name - only the sample name without unnecessary suffixes and prefixes.
"""
def strip_name(full_name):
    underscore_location = len(full_name)
    if ('_S' in full_name) or ('_h' in full_name):
        try:
            underscore_location = full_name.rindex('_S') # Location of last instance of '_S'.
        except:
            underscore_location = full_name.rindex('_h')
    final_name = full_name[:underscore_location]
    if 'Case_' in final_name:
        final_name = final_name.replace('Case_', '')
    return final_name


"""
    Function that extracts relevant information from posResFiltered for each mutation.
    Used in:
        - update_samplesummary() in RCv2_functions.py.
        - createReports() in docx_functions.py
    INPUT:
        1) i - the current row number in the posResFiltered table.
        2) posResFiltered - filtered pd dataframe of the genotyping results data.
    OUTPUT:
        * Relevenat data extracted from the posResFiltered file for the current sample and mutation (16 categories).
"""
def get_INFO_posRes(i, posResFiltered, logger_name):
    rc_logger = logging.getLogger(logger_name)
    agid = posResFiltered.iloc[i]['AGID']
    gene_CA = posResFiltered.iloc[i]['Custom Annotation']
    if type(gene_CA) == float or type(gene_CA) == np.float64: # EMPTY - Special variant (not included in files).
        gene = ''
        CA = ''
    else:
        try:
            gene_CA_split = gene_CA.split(':')
            gene = gene_CA_split[0] # Get gene name.
            CA = gene_CA_split[1] # Get Custom Annotation.
        except:
            gene = gene_CA # Get gene name.
            CA = gene_CA # Get Custom Annotation.
            rc_logger.info("\tWARNING: Custom Annotation in genotyping results file wrong format for AGID - " + agid)
            print("\tWARNING: Custom Annotation in genotyping results file wrong format for AGID - " + agid)
    CA2 = posResFiltered.iloc[i]['Custom Annotation 2'] # Get Custom Annotation 2.
    if type(CA2) == float or type(CA2) == np.float64: # EMPTY - Special variant (not included in files).
        CA2 = ''
    Genotype = posResFiltered.iloc[i]['Genotype'] # Get Genotype.
    Classification = posResFiltered.iloc[i]['Classification'] # Get Classification.
    location = posResFiltered.iloc[i]['gdna']
    gDNA = posResFiltered.iloc[i]['gdna']
    mutation = "{} \n {}".format(CA2, location) # Mutation for excel tables.
    mutation_gDNA = "{} \n {}".format(CA2, gDNA) # Mutation for reports.
    # mutation = CA2 + ' ' + '\n' + location # Mutation for excel tables.
    # mutation_gDNA = CA2 + ' ' + '\n' + gDNA # Mutation for reports.
    GQX = posResFiltered.iloc[i]['GQX'] # Get GQX.
    AVF = posResFiltered.iloc[i]['Alt Variant Freq'] # Get Alt Variant Freq.
    RD = posResFiltered.iloc[i]['Read Depth'] # Get Read Depth.
    ARD = posResFiltered.iloc[i]['Alt Read Depth'] # Get Alt Read Depth.
    AD = posResFiltered.iloc[i]['Allelic Depths'] # Get Allelic Depths.
    DM = posResFiltered.iloc[i]['Clalit Disease Makat'] # Get Disease Makat.
    MM = posResFiltered.iloc[i]['Clalit Mutation Makat'] # Get Mutation Makat.
    try:
        moh = posResFiltered.iloc[i]['Custom Annotation 3']
    except:
        moh = np.nan
    try:
        eth = posResFiltered.iloc[i]['Custom Annotation 4']
    except:
        eth = np.nan

    return CA, gene, agid, mutation, mutation_gDNA, Classification, Genotype, GQX, AVF, RD, ARD, AD, moh, eth, DM, MM


"""
    Function that extracts relevant information from DECoN_results.tsv for each mutation.
    Used in:
        - update_samplesummary() in RCv2_functions.py.
        - createReports() in docx_functions.py
    INPUT:
        1) i - the current row number in the decon_filtered table.
        2) posResFiltered - filtered pd dataframe of the CNV results data.
    OUTPUT:
        * Relevenat data extracted from the decon_filtered file for the current sample and mutation (18 categories).
"""
def get_INFO_decon(i, decon_filtered, logger_name):
    rc_logger = logging.getLogger(logger_name)
    agid = str(decon_filtered.iloc[i]['AGID'])
    Annotation1 = decon_filtered.iloc[i]['Annotation1']
    try:
        Annotation1_split = Annotation1.split(':') # List containing -> [gene, disease name]
        CA = Annotation1_split[1] # Get disease.
        gene = Annotation1_split[0] # Get gene name.
    except:
        CA = Annotation1 # Get disease.
        gene = Annotation1 # Get gene name.
        rc_logger.info("\tWARNING: Custom Annotation in genotyping results file wrong format for AGID - " + agid)
        print("\tWARNING: Annotation1 in DECoN results file wrong format for AGID - " + agid)
    location = decon_filtered.iloc[i]['gdna']
    if gene == 'DMD':
        type = decon_filtered.iloc[i]['CNV.type']
        firstExon = str(int(decon_filtered.iloc[i]['Custom.first']))
        lastExon = str(int(decon_filtered.iloc[i]['Custom.last']))
        annotation ="NM_004006: " + type + "_Exon_" + firstExon + "_to_" + lastExon
    else:
        annotation = decon_filtered.iloc[i]['Annotation2'] # Get mutation annotation.
    mutation = annotation + ' ' + location
    Genotype = decon_filtered.iloc[i]['Genotype']
    Classification = decon_filtered.iloc[i]['Classification']
    Correlation = decon_filtered.iloc[i]['Correlation']
    Ncomp = decon_filtered.iloc[i]['N.comp']
    first = decon_filtered.iloc[i]['Custom.first']
    last = decon_filtered.iloc[i]['Custom.last']
    BF = decon_filtered.iloc[i]['BF']
    expected = decon_filtered.iloc[i]['Reads.expected']
    observed = decon_filtered.iloc[i]['Reads.observed']
    ratio = decon_filtered.iloc[i]['Reads.ratio']
    DM = decon_filtered.iloc[i]['Clalit Disease Makat']
    MM = decon_filtered.iloc[i]['Clalit Mutation Makat']
    try:
        moh = decon_filtered.iloc[i]['Annotation3']
    except:
        moh = np.nan
    try:
        eth = decon_filtered.iloc[i]['Annotation4']
    except:
        eth = np.nan
    return CA, gene, agid, mutation, Classification, Genotype, Correlation, Ncomp, first, last, BF, expected, observed, ratio, moh, eth, DM, MM



"""
    Get supplementary info about the samples from the sampleSex dictionary and user input extraInfo file (if exists).
    Used in:
        - createResultSummaries() in RCv2_functions.py.
    INPUT:
        1) extraInfo - pd dataframe of sample extra information data ('None' if was not specified).
        2) sampleSex - dictionary with KEY = sample name / VALUE = gender, as appears in the DECoN results file.
        3) sampleSet - set of all the sample names, as appear in the DECoN results file.
    OUTPUT:
        1) sampleInfoTable - pd table of every sample and its respective supplementary info (if exists).
"""
def get_sampleInfo(extraInfo, sampleSex, sampleSet, logger_name):
    rc_logger = logging.getLogger(logger_name)
    colNames = ['ID','name','source','gender','sex','city','street','phone','eth_m','eth_f','partner']
    sampleInfoTable = pd.DataFrame(columns = colNames)
    extraInfoSamples = [] # List of samples from extraInfo file (if no file exists, remains empty).

    if isinstance(extraInfo, pd.DataFrame): # extraInfo file was provided.

        if len(extraInfo.columns) != extraInfo_COLNUM:
            rc_logger.info("\tWARNING: extraInfo file has wrong number of columns. Please fix file.")
            print("\tWARNING: extraInfo file has wrong number of columns. Please fix file.")
        total_samples = extraInfo.iloc[:, 0].tolist() # Get list of all samples in extraInfo file for iteration boundary.
        if len(total_samples) < len(sampleSet):
            rc_logger.info("\tWARNING: extraInfo file has fewer samples than DECoN results file.")
            print("\tWARNING: extraInfo file has fewer samples than DECoN results file.")
        if len(total_samples) > len(sampleSet):
            rc_logger.info("\tWARNING: extraInfo file has more samples than DECoN results file.")
            print("\tWARNING: extraInfo file has more samples than DECoN results file.")

        row = 0 # Keep track of row number.
        for sam in total_samples:
            sampleName_raw = extraInfo.iloc[row, 0] # Get sample name as exists in file.
            sampleName = strip_name(sampleName_raw) # If has _S, remove it.
            if sampleName not in sampleSet: # Check sample name is valid.
                rc_logger.info("\tWARNING: Uncorrelated sample name between DECoN results file and extraInfo file.")
                rc_logger.info("\tWARNING: Sample " + sampleName + " will not be included in the analysis.")
                print("\tWARNING: Uncorrelated sample name between DECoN results file and extraInfo file.")
                print("\tWARNING: Sample " + sampleName + " will not be included in the analysis.")
                row = row+1 # NEXT row.
                continue # Skip problematic sample.
            sampleInfoTable.append(pd.Series(name=sampleName)) # Add empty sample row, row name = sample name.
            sampleInfoTable.at[sampleName,'ID'] = extraInfo.iloc[row, 1] # Add sample ID.
            sampleInfoTable.at[sampleName,'name'] = extraInfo.iloc[row, 2] # Add patient name.
            source = extraInfo.iloc[row, 3] # Get sample source.
            if type(source) == float or type(source) == np.float64: # Check if not filled out.
                source = NO_DATA # Create VALID entry for sample summary excel file.
            sampleInfoTable.at[sampleName,'source'] = source # Add source.
            gender = extraInfo.iloc[row, 4] # Get patient gender.
            if type(gender) == float or type(gender) == np.float64: # Check if not filled out.
                gender = NO_DATA # Create VALID entry for sample summary excel file.
            sampleInfoTable.at[sampleName,'gender'] = gender # Add patient gender.
            sampleInfoTable.at[sampleName,'sex'] = sampleSex[sampleName] # Add sex.
            sampleInfoTable.at[sampleName,'city'] = extraInfo.iloc[row, 5] # Add city.
            sampleInfoTable.at[sampleName,'street'] = extraInfo.iloc[row, 6] # Add street.
            sampleInfoTable.at[sampleName,'phone'] = extraInfo.iloc[row, 7] # Add phone.
            eth_m = extraInfo.iloc[row, 8] # Get mother ethnicity.
            if type(eth_m) == float or type(eth_m) == np.float64: # Check if not filled out.
                eth_m = NO_DATA # Create VALID entry for sample summary excel file.
            sampleInfoTable.at[sampleName,'eth_m'] = eth_m # Add mother ethnicity.
            eth_f = extraInfo.iloc[row, 9] # Get father ethnicity.
            if type(eth_f) == float or type(eth_f) == np.float64: # Check if not filled out.
                eth_f = NO_DATA # Create VALID entry for sample summary excel file.
            sampleInfoTable.at[sampleName,'eth_f'] = eth_f # Add father ethnicity.
            partner = extraInfo.iloc[row, 10] # Get partner sample.
            if type(partner) == float or type(partner) == np.float64: # Check if not filled out.
                partner = NO_DATA # Create VALID entry for sample summary excel file.
            sampleInfoTable.at[sampleName,'partner'] = partner # Add partner sample.
            extraInfoSamples.append(sampleName) # Add to extraInfo samples list.
            row = row+1 # NEXT row.

    for sample in sorted(sampleSet):
        if sample not in extraInfoSamples: # If extraInfoSamples list is empty will simply go over all samples, adding default data.
            sampleInfoTable.append(pd.Series(name=sample)) # Add empty sample row, row name = sample name.
            sampleInfoTable.at[sample,'ID'] = NO_DATA
            sampleInfoTable.at[sample,'name'] = NO_DATA
            sampleInfoTable.at[sample,'source'] = NO_DATA
            sampleInfoTable.at[sample,'gender'] = NO_DATA
            sampleInfoTable.at[sample,'sex'] = sampleSex[sample]
            sampleInfoTable.at[sample,'city'] = NO_DATA
            sampleInfoTable.at[sample,'street'] = NO_DATA
            sampleInfoTable.at[sample,'phone'] = NO_DATA
            sampleInfoTable.at[sample,'eth_m'] = NO_DATA
            sampleInfoTable.at[sample,'eth_f'] = NO_DATA
            sampleInfoTable.at[sample,'partner'] = NO_DATA

    return sampleInfoTable
