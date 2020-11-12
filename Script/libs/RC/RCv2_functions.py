import sys
import os
import logging
import pandas as pd
import numpy as np

from getInfo_functions import strip_name, get_INFO_posRes, get_INFO_decon, get_sampleInfo
from docx_functions import createReports

import tools

genotypes = ['CARRIER', 'CARRIER-Non-Ashkenazi', 'CARRIER-Problem', 'HOM',
             'CARRIER-Georgian', 'CARRIER-Georgian - With soft-clipped reads', 'CARRIER-Druze',
             'CARRIER - With soft-clipped reads', 'CARRIER-Non-Ashkenazi - With soft-clipped reads',
             'CARRIER-Problem - With soft-clipped reads', 'HOM - With soft-clipped reads',
             'CARRIER-Georgian-Problem', 'CARRIER-Druze', 'CARRIER-Druze-Problem',] # For defineStatus().
cnvs = ['CNV', 'CNV Big Del Boundaries Different as Reported', 'CNV-Problem', 'CNV-Problem Big Del Boundaries Different as Reported'] # For defineStatus().

# Column names for sample summary and DB statistics file: #
# Used in createResultSummaries() and update_samplesummary() #
col_names = ['Sample', 'Date of Run', 'Disease', 'Gene', 'AGID', 'Mutation', 'MOH', 'Ethnicity', 'Classification', 'Clalit Disease Makat', 'Clalit Mutation Makat',
             'Genotype', 'GQX', 'Alt Variant Freq', 'Read Depth', 'Alt Read Depth', 'Allelic Depths', 'Correlation', 'N.comp', 'Custom.first', 'Custom.last', 'BF',
             'Reads.expected', 'Reads.observed', 'Reads.ratio', 'Sample Source', 'Gender', 'Sex', 'Mother Ethnicity', 'Father Ethnicity', 'Partner Sample']

"""
    Check run name exists and is valid. If not, ask user to input one.
    Used in:
        - createResultSummaries()
    INPUT:
        1) run_name - name of run as input by user (None if not specified).
    OUTPUT:
        1) run_name - original run name if existed and valid. Corrected or new run name otherwise.
"""
def CheckRunName(run_name):
    correct_name_format = False
    if run_name is None or "_M" not in run_name:
        while(not correct_name_format):
            print("Insert the name of the run library, including the date.")
            run_name = input("For example, a MiniSeq run from May 4th 2021 will look like 210504_MNXXXXX_YYYY_ZZZZZZZ: ")
            if "_M" not in run_name:
                print("# WARNING: Not a correct run name. Please try again.")
            else:
                correct_name_format = True
    return run_name


"""
    Create log file.
    Used in:
        - createResultSummaries()
    INPUT:
        1) out - full path to results folder.
    *NO OUTPUT - edits in place*
"""
def logger(out, logger_name):
    # log_file = "{}/RCv2.log".format(out)
    # logging.basicConfig(filename=log_file,
    #                     filemode='w',
    #                     level=logging.INFO,
    #                     format='%(asctime)s %(levelname)-8s %(message)s',
    #                     datefmt='%Y-%m-%d %H:%M:%S')
    global rc_logger
    rc_logger = logging.getLogger(logger_name)


"""
    Use user input paths to import the specified results data. If 'None', prompt user for input.
    Used in:
        - createResultSummaries()
    INPUT:
        1) output - directory to output reports
        2) geno_file - Genotype results file name (if not specified then 'None').
        3) cnv_file - CNV results file name (if not specified then 'None').
        4) extraInfo_file - added information file name (if not specified then 'None').
    OUTPUT:
        1) geno - pd dataframe of genotyping results file (positiveResults.tsv).
        2) cnv - pd dataframe of CNV results file (DECoN_results.tsv).
        3) extraInfo - pd dataframe of extraInfo file (samplesSheet.xlsx), or 'None' if not specified.
"""
def getResults(output, geno_file, cnv_file, extraInfo_file):

    if geno_file is None: # No genotype file defined.
        geno_filepath = input("Insert full path to Genotyping results file (default = output_dir\positiveResults.tsv): ")
        if geno_filepath == '':
            geno_filepath = '{}\positiveResults.tsv'.format(output)
    else: # Genotype file name was given.
        # geno_filepath = "/".join([output, geno_file])
        geno_filepath = geno_file
    try:
        # geno = pd.read_csv(geno_filepath, sep='\t')
        geno = tools.decompress_pickle(geno_filepath)
    except Exception as e:
        print("Unable to read Genotyping results file.")
        logging.error("ERROR: Unable to read Genotyping result file\n{}".format(e))
        sys.exit(2)
    logging.info("Genotyping Results: {}".format(geno_filepath))

    if cnv_file is None: # No cnv file defined.
        cnv_filepath = input("Insert full path to CNV results file (default = output_dir\DECoN_results.tsv): ")
        if cnv_filepath == '':
            cnv_filepath = '{}\DECoN_results.tsv'.format(output)
    else: # cnv file name was given
        # cnv_filepath = "/".join([output, cnv_file])
        cnv_filepath = cnv_file
    try:
        # cnv = pd.read_csv(cnv_filepath, sep='\t')
        cnv = tools.decompress_pickle(cnv_filepath)
        cnv.sort_values(by=['Sample'], inplace=True)
        cnv.sort_values(by=['AGID'], inplace=True)
    except Exception as e:
        print("Unable to read CNV results file.")
        logging.error("ERROR: Unable to read CNV results file\n{}".format(e))
        sys.exit(2)
    logging.info("CNV Results: {}".format(cnv_filepath))

    if extraInfo_file is None: # No extraInfo file was defined.
        extraInfo_filepath = input("Optional - insert full path to samples sheet file. To skip, leave empty: ")
        if extraInfo_filepath == '':
            extraInfo = 'NONE'
    elif extraInfo_file == False:
        extraInfo_filepath = ''
        extraInfo = 'NONE'
    else: # extraInfo file name was given
        extraInfo_filepath = "/".join([output, extraInfo_file])
    if extraInfo_filepath != '': # Read only if extraInfo file was given. otherwise skip.
        try:
            extraInfo = pd.read_excel(extraInfo_file, sheet_name=0, converters={0: lambda x: str(x), 1: lambda x: str(x), 7: lambda x: str(x), 10: lambda x: str(x)})
        except Exception as e:
            print("Unable to read extraInfo file")
            logging.error("ERROR: Unable to read extraInfo file\n{}".format(e))
            sys.exit(2)
    logging.info("extraInfo file (BLANK = no file specified): {}".format(extraInfo_filepath))
    return geno, cnv, extraInfo


"""
    Decides for each sample whether it is healthy, carrier, sick or carrier & sick.
    Used in:
        - createResultSummaries()
    INPUT:
        1) indices - List of the sample's row numbers in the posResFiltered table.
        2) indices_decon - List of the sample's row numbers in the decon_filtered table.
        3) posResFiltered - Filtered pd dataframe of genotyping results data.
        4) decon_filtered - Filtered pd dataframe of CNV results data.
    OUTPUT:
        1) Status category for the respective sample - "NORM"/"CARRIER"/"SICK"/"CARRIER_SICK"
"""
def defineStatus(indices, indices_decon, posResFiltered, decon_filtered):
    if (indices == []) and (indices_decon == []): # Sample does not exist in 'positiveResults.tsv' and has no DECoN mutations.
        return "NORM"
    else: # Sample exists in 'positiveResults.tsv' and/or has DECoN mutations, extract relevant data.
        het = False
        hom = False
        for i in indices: # Check if hom, het or both.
            Classification = posResFiltered.iloc[i]['Classification'] # Get Classification.
            if Classification in genotypes: # Check if valid mutation.
                Genotype = posResFiltered.iloc[i]['Genotype'] # Get Genotype.
                if Genotype in 'het': # Check if exists het.
                    het = True
                if Genotype in 'hom': # Check if exists hom.
                    hom = True
        for i in indices_decon: # Check if CONVector found mutations.
            amp = str(decon_filtered.iloc[i]['Annotation1']) # Get amplicon name.
            clas_decon = decon_filtered.iloc[i]['Classification']
            decon_geno = decon_filtered.iloc[i]['Genotype']
            if clas_decon in cnvs and '_NC' not in amp:
                if decon_geno == 'het' or pd.isna(Genotype):
                    het = True
                if decon_geno == 'hom':
                    hom = True
            # if '_NC' not in amp:
            #     het = True # If so, exists a het mutation that is not NC.
    if het == False and hom == False: # Only NO-CALLS or WT or CONVector_NC.
        return "NORM"
    elif het == True and hom == False: # Only HET.
        return "CARRIER"
    elif het == False and hom == True: # Only HOM.
        return "SICK"
    else: # Is both HET and HOM.
        return "CARRIER_SICK"


"""
    Update sample summary table with relevant rows for current sample.
    Used in:
        - createReports()
    INPUT:
        1) sample_summary - current sample summary pd table.
        2) sample - current sample.
        3) run_name - run name.
        4) sampleStatus - dictionary with KEY = sample / VALUE = [sample's status, geno indices, cnv indices].
        5) posResFiltered - filtered pd dataframe of genotyping results data.
        6) decon_filtered - filtered pd dataframe of CNV results data.
        7) sampleInfoTable - pd dataframe of sample extra information data.
    OUTPUT:
        1) sample_summary - updated sample summary pd table.
"""
def update_samplesummary(sample_summary, sample, run_name, sampleStatus, posResFiltered, decon_filtered, sampleInfoTable, logger_name):
    source = sampleInfoTable.at[sample, 'source']
    gender = sampleInfoTable.at[sample, 'gender']
    sexBam = sampleInfoTable.at[sample, 'sex']
    eth_m = sampleInfoTable.at[sample, 'eth_m']
    eth_f = sampleInfoTable.at[sample, 'eth_f']
    partner = sampleInfoTable.at[sample, 'partner']
    current_status = sampleStatus[sample][0] # Get status.
    geno_indices = sampleStatus[sample][1] # Get indices of occurences in 'positiveResults.tsv'.
    cnv_indices = sampleStatus[sample][2] # Get indices of occurences in 'DECoN_results.tsv'.

    if (geno_indices==[]) and (cnv_indices==[]): # Sample does not exist in 'positiveResults.tsv' and has no DECoN mutations:
        cur_sumrow = pd.DataFrame(np.array([[sample, run_name, 'No mutations identified (WT).', '---', '---', '---', '---', '---', '---', '---', '---', '---',
                                             '---', '---', '---', '---', '---', '---', '---', '---', '---', '---', '---', '---', '---',
                                             source, gender, sexBam, eth_m, eth_f, partner]]), columns = col_names) # Create row for summary table.
        sample_summary = sample_summary.append(cur_sumrow) # Add row to summary table.

    else: # Sample has at least one none-WT, in 'positiveResults.tsv' and/or 'DECoN_results.tsv':
        for i in geno_indices: # from 'positiveResults.tsv'.
            try:
                CA, gene, agid, mutation, mutation_gDNA, Classification, Genotype, GQX, AVF, RD, ARD, AD, moh, eth, DM, MM = get_INFO_posRes(i, posResFiltered, logger_name)
            except Exception as e:
                print("Error when trying to get sample's " + sample + " genotype data.")
                logging.error("ERROR: when running get_INFO_posRes() function.\n{}".format(e))
                sys.exit(2)
            cur_sumrow = pd.DataFrame(np.array([[sample, run_name, CA, gene, agid, mutation_gDNA, moh, eth, Classification, DM, MM, Genotype, GQX, AVF, RD, ARD, AD,
                                    '---', '---', '---', '---', '---', '---', '---', '---', source, gender, sexBam, eth_m, eth_f, partner]]), columns = col_names) # Create row for summary table.
            sample_summary = sample_summary.append(cur_sumrow) # Add row to summary table.
        for i in cnv_indices: # from 'DECoN_results.tsv'.
            try:
                CA, gene, agid, mutation, Classification, Genotype, Correlation, Ncomp, first, last, BF, expected, observed, ratio, moh, eth, DM, MM = get_INFO_decon(i, decon_filtered, logger_name)
            except Exception as e:
                print("Error when trying to get sample's " + sample + " CNV data.")
                logging.error("ERROR: when running get_INFO_decon() function.\n{}".format(e))
                sys.exit(2)
            cur_sumrow = pd.DataFrame(np.array([[sample, run_name, CA, gene, agid, mutation, moh, eth, Classification, DM, MM, Genotype, '---', '---', '---', '---', '---',
                                    Correlation, Ncomp, first, last, BF, expected, observed, ratio, source, gender, sexBam, eth_m, eth_f, partner]]), columns = col_names) # Create row for summary table.
            sample_summary = sample_summary.append(cur_sumrow) # Add row to summary table.

    return sample_summary


"""
    Extract all results data, creates raw Sample Summary dataframe and calls report creator functions.
    Used in:
        - RCv2.py
    INPUT:
        1) output - path to output directory as input by user.
        2) office_version - office version as input by user.
        3) MyScreen_version - program version and version date (for reports).
        4) Results_Folder - name of results folder as specified in RCv2.py.
        5) run_name - name of run as input by user (None if not specified).
        6) geno_file - Genotype results file name as input by user (None if not specified).
        7) cnv_file - CNV results file name as input by user (None if not specified).
        8) extraInfo_file - added information file name as input by user (None if not specified).
    OUTPUT:
        1) sample_summary - pd dataframe of Sample Summary table.
        2) cnv - pd dataframe of CNV results (DECoN_results.tsv).
        3) run_name - name of run after CheckRunName() function.
"""
def createResultSummaries(output, office_version, MyScreen_version, logger_name, Results_Folder, hospital, run_name = None, geno_file = None,
                  cnv_file = None, extraInfo_file = None):
    office = bool(int(office_version) < 2016)
    run_name = CheckRunName(run_name)
    # output_folder = "\\".join([output, Results_Folder])
    output_folder = output
    try:
        os.mkdir(output_folder)
    except FileExistsError:
        pass
    except:
        print("Creation of the results directory failed")
        sys.exit(2)

    logger(output_folder, logger_name)
    rc_logger.info("Starting RCv2_functions session:")
    rc_logger.info("MyScreen version: {}".format(MyScreen_version))
    rc_logger.info("Output directory: {}".format(output_folder))
    rc_logger.info("Office version: {}".format(office_version))
    rc_logger.info("Run name: {}".format(run_name))

    geno, cnv, extraInfo = getResults(output, geno_file, cnv_file, extraInfo_file)

    print("Extracting data...")
    # --- Genotyping results extraction --- #
    rc_logger.info("Extracting data from Genotyping Results file...")
    try:
        posResFiltered = geno[['Sample', 'AGID', 'Variant', 'Chr', 'Coordinate', 'Custom Annotation', 'Custom Annotation 2',
                            'Custom Annotation 3', 'Custom Annotation 4', 'gdna', 'Classification', 'Genotype', 'GQX',
                            'Alt Variant Freq', 'Read Depth', 'Alt Read Depth', 'Allelic Depths', 'Clalit Disease Makat', 'Clalit Mutation Makat']] # Filter only relevant data.
    except Exception as e:
        print("Genotyping Results file wrong format (check column names).")
        rc_logger.error("ERROR: Genotyping Results file wrong format\n{}".format(e))
        sys.exit(2)
    posSamples_raw = geno['Sample'].tolist() # List of all positive samples (with duplicates).
    posSamples = [] # List of all positive samples (with duplicates), without pisces ending.
    for raw_sample in posSamples_raw: # Strip pisces ending.
        try:
            name = strip_name(raw_sample)
        except Exception as e:
            print("Error in sample names.")
            rc_logger.error("ERROR: strip_name() function failed.\n{}".format(e))
            sys.exit(2)
        posSamples.append(name)
    rc_logger.info("Data extraction successful.")

    # --- CNV results extraction --- #
    rc_logger.info("Extracting data from CNV Results file...")
    try:
        decon_filtered = cnv[['AGID', 'Annotation1', 'Sample', 'CNV.type',
                            'Gene', 'Genotype', 'Custom.first',
                            'Custom.last', 'Chromosome', 'Observed Start',
                            'Observed Stop', 'Correlation','N.comp', 'BF',
                            'Reads.expected', 'Reads.observed', 'Reads.ratio',
                            'Gender', 'Classification', 'Info', 'Annotation2',
                            'Annotation3', 'Annotation4', 'gdna', 'Clalit Disease Makat', 'Clalit Mutation Makat']]
    except Exception as e:
        print("CNV results file wrong format (check column names).")
        rc_logger.error("ERROR: CNV results file wrong format\n{}".format(e))
        sys.exit(2)
    posSamples_decon = []
    sampleSet = set()
    sampleSex = {}
    for index, row in cnv.iterrows():
        try:
            name = strip_name(str(row['Sample']))
        except Exception as e:
            print("Error in sample names.")
            rc_logger.error("ERROR: strip_name() function failed.\n{}".format(e))
            sys.exit(2)
        if isinstance(row['AGID'], str):
            posSamples_decon.append(name)
        sampleSet.add(name)
        sampleSex[name] = row['Gender']
    rc_logger.info("Data extraction successful.")

    # --- Check sample names are correlated beween Genotyping and CNV results --- #
    rc_logger.info("Checking genotyping and CNV files sample names are correlated...")
    for posSamp in posSamples:
        if posSamp not in sampleSet:
            print("Uncorrelated sample names between Genotyping results file and DECoN results file.")
            print("Please fix sample name: " + posSamp)
            rc_logger.info("FAILED")
            sys.exit(2)
    rc_logger.info("Genotyping and CNV files sample names are valid.")

    # --- sample info extraction --- #
    rc_logger.info("Extracting data from extraInfo file...")
    try:
        sampleInfoTable = get_sampleInfo(extraInfo, sampleSex, sampleSet, logger_name)
    except Exception as e:
        print("Error when extracting data from extraInfo file. Please check table format, column names and table contents.")
        rc_logger.error("ERROR: when running get_sampleInfo() function.\n{}".format(e))
        sys.exit(2)
    rc_logger.info("Data extraction successful.")
    print("Done extracting data.")

    # --- Define sample status --- #
    print("Defining samples' genotypic status...")
    rc_logger.info("Defining each sample's genotypic status...")
    sampleStatus = {}
    for cur_sample in sorted(sampleSet):
        rc_logger.info("\tIn sample " + cur_sample + "...")
        indices = [i for i, x in enumerate(posSamples) if x == cur_sample] # Get sample rows in postiveResults file.
        indices_decon = [i for i, x in enumerate(posSamples_decon) if x == cur_sample] # Get sample rows in DECoN file.
        try:
            sampStat = defineStatus(indices, indices_decon, posResFiltered, decon_filtered)
        except Exception as e:
            print("Error when trying to define sample's " + cur_sample + " status.")
            rc_logger.error("ERROR: when running defineStatus() function.\n{}".format(e))
            sys.exit(2)
        sampleStatus[cur_sample] = (sampStat, indices, indices_decon)
        print("\tSample " + cur_sample + " is " + sampStat + ".")
        rc_logger.info("\tSample " + cur_sample + " is " + sampStat + ".")
    rc_logger.info("DONE.")
    print("Done defning each sample's status.")

    ### EXCEL SUMMARY TABLE CREATION ###
    print("Summarizing results for each sample...")
    rc_logger.info("Creating sample summary pd dataframe...")
    sample_summary = pd.DataFrame(columns = col_names) # Create empty summary table.
    for cur_sample in sorted(sampleSet): # Iterate over every sample.
        rc_logger.info("\tIn sample " + cur_sample + "...")
        try:
            sample_summary = update_samplesummary(sample_summary, cur_sample, run_name, sampleStatus, posResFiltered, decon_filtered, sampleInfoTable, logger_name)
        except Exception as e:
            print("Error when trying to summarize sample's " + cur_sample + " results.")
            rc_logger.error("ERROR: when running update_samplesummary() function.\n{}".format(e))
            sys.exit(2)
        rc_logger.info("\tSample " + cur_sample + " done.")
    rc_logger.info("Finished filling out sample summary pd dataframe.")
    print("Results summarization successful.")

    ### REPORT CREATOR ###
    if hospital != False:
        print("Creating Microsoft word reports...")
        rc_logger.info("Creating docx reports...")
        for cur_sample in sorted(sampleSet): # Iterate over every sample.
            rc_logger.info("\tIn sample " + cur_sample + "...")
            try:
                createReports(cur_sample, sampleStatus, posResFiltered, decon_filtered, sampleInfoTable, office, output_folder, MyScreen_version, logger_name, hospital)
            except Exception as e:
                print("Error when trying to create report for sample " + cur_sample + ".")
                rc_logger.error("ERROR: when running createReports() function.\n{}".format(e))
                sys.exit(2)
            rc_logger.info("\tSample " + cur_sample + " done.")
        rc_logger.info("Finished Microsoft word reports.")
    rc_logger.info("Continuing to sample summary excel creation, formatExcel.py and DB_statistics file creation.")
    rc_logger.info("---------------------------")
    print("Finished Microsoft word reports.")

    return sample_summary, cnv, run_name, output_folder
