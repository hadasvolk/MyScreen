# -*- coding: utf-8 -*-
#!/usr/bin/python

import sys
import os
import logging
import argparse
import datetime
import pandas as pd
import numpy as np

from RCv2_functions import createResultSummaries
from formatExcel import excel_formatter, AddIgvLink

date = datetime.datetime.now().strftime("%d-%m-%Y")


"""
    Format the Sample Summary excel table (using formatExcel.py functions).
    Used in:
        - MAIN
    INPUT:
        1) summary_table - pd dataframe of Sample Summary table.
        2) decon_positive - pd dataframe of CNV results (DECoN_results.tsv).
        3) out_dir - path to output directory.
        4) bam_path - path to bam directory.
        5) MyScreen_version - Current MyScreen program version.
        6) Results_Folder - Folder to output excel table.
    *NO OUTPUT - edits in place*
"""
def formatSampleSummary(summary_table, decon_positive, out_dir, bam_path, MyScreen_version, Results_Folder):

    logging.info("Bam file directory: {}".format(bam_path))
    print("Creating sample summary excel file...")
    logging.info("Creating sample summary excel file...")

    summary_table = summary_table.set_index('Sample')
    folder_name = Results_Folder
    output_path = os.path.join(out_dir, folder_name)
    table_doc = 'sample_summary_' + date + '.xlsx'
    table_path = os.path.join(output_path, table_doc)
    summary_table.insert(0,'S', np.nan, allow_duplicates=True)
    for index, row in decon_positive.iterrows():
        name = (str(row['Sample'])).split('_')
        name[1] = name[1].split('S')[1]
        summary_table.loc[name[0], 'S'] = name[1]
    summary_table = summary_table.replace('nan', '')
    try:
        summary_table = AddIgvLink(summary_table, bam_path)
    except:
        print ("\tWARNING: Failed to add IGV links to sample summary.")
        logging.info("\tWARNING: Failed to add IGV links to sample summary.")
    writer = pd.ExcelWriter(table_path)
    summary_table.to_excel(writer, 'Sheet1')
    writer.save()
    try:
        excel_formatter(table_path, MyScreen_version)
    except:
        print("\tWARNING: Unable to reformat sample summry\n reverting to default...")
        logging.info("\tWARNING: Unable to reformat sample summry\n reverting to default...")

    logging.info("DONE")
    print("Successfully created sample summary excel file.")


"""
    Update db_statistics-v2.xlsx with current run. If run exists, replace that run with new stats.
    Used in:
        - MAIN
    INPUT:
        1) summary_table - pd dataframe of Sample Summary table.
        2) out_dir - path to output directory.
        3) run_name - name of current run.
        4) MyScreen_version - Current MyScreen program version.
        5) Results_Folder - Folder to output excel table.
    *NO OUTPUT - edits in place*
"""
def createDBstatistics(summary_table, out_dir, run_name, output_folder, MyScreen_version, Results_Folder):

    print("Updating DB statistics excel file...")
    logging.info("Updating DB statistics excel file...")

    updateDB = True
    try:
        raw_stat_file = pd.read_excel('C:\Gamidor\Appendix\db_statistics-v2.xlsx') # Upload statistics file with past runs (or empty statistic file if first analysis).
    except:
        updateDB = False
        print ("\tWARNING: DB_statistics file not in appendix. Will not update file.")
        logging.info("\tWARNING: DB_statistics file not in appendix. Will not update file.")
    if updateDB:
        rows_to_remove = []
        for index, row in raw_stat_file.iterrows():
            past_run = str(row['Date of Run']) # Extract row date.
            if past_run == run_name: # Row is from current run date.
                rows_to_remove.append(index) # Must remove row.
        if rows_to_remove != []: # Current run already existed in DB_statistics file (at least once). Remove and log.
            print ("\tWARNING: Current run already found in DB_statistics file. Replaced old data with the current analysis.")
            logging.info("\tWARNING: Current run already found in DB_statistics file. Replaced old data with the current analysis.")
        run_stat_file = raw_stat_file.drop(rows_to_remove)
        summary_table = summary_table.set_index('Sample')
        run_stat_file = run_stat_file.set_index('Sample')
        frames = [run_stat_file, summary_table]
        try:
            result = pd.concat(frames, sort=False)
        except Exception as e:
            print ("\tERROR: Could not update DB_statistics file with sample summary data.")
            logging.error("\tERROR: Could not update DB_statistics file with sample summary data.\n{}".format(e))
            sys.exit(2)
        folder_name = Results_Folder
        output_path = os.path.join(out_dir, folder_name)
        # Create user full run statistics excel file:
        result['Analysis Version'] = MyScreen_version
        stat_doc = 'db_statistics_' + date + '.xlsx'
        stat_path = os.path.join(output_path, stat_doc)
        writer = pd.ExcelWriter(stat_path)
        result.to_excel(writer, 'Sheet1')
        writer.save()
        # Create internal full run statistics excel file (for future analysis):
        writer = pd.ExcelWriter('C:\Gamidor\Appendix\db_statistics-v2.xlsx')
        result.to_excel(writer, 'Sheet1')
        writer.save()

    logging.info("DONE")
    logging.info("Analysis and report creation completed!")
    logging.info("Results saved in: " + output_folder)
    print("Successfully created DB statistics excel file.")
    print("Finished analysis and report creation!")
    print("Please look at the results in: " + output_folder)


"""
    Wrapper for all functions. Allows to call externally and not run MAIN.
"""
def MAIN_RCv2wrapper(output_dir, office_version, bam_dir, MyScreen_version, run_name, geno_file, cnv_file, extraInfo_file):

    # Results_Folder = 'MyScreen_Analysis_' + MyScreen_version + '_RESULTS' # Folder for output.
    Results_Folder = output_dir
    sample_summary, decon_positive, run_name, output_folder = createResultSummaries(output_dir, office_version, MyScreen_version, Results_Folder,
           run_name, geno_file, cnv_file, extraInfo_file)

    #formatSampleSummary(sample_summary, decon_positive, output_dir, bam_dir, MyScreen_version, Results_Folder)

    createDBstatistics(sample_summary, output_dir, run_name, output_folder, MyScreen_version, Results_Folder)

    return sample_summary
    # writer = pd.ExcelWriter("{}/{}/clean_sample_summary-{}.xlsx".format(output_dir, Results_Folder, date))
    # sample_summary.to_excel(writer, 'Sheet1')
    # writer.save()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', help='Directory to output reports')
    parser.add_argument('office_version', help='office version')
    parser.add_argument('bam_dir', help='Directory where bam files reside')
    parser.add_argument('MyScreen_version', help='MyScreen version and version date (for reports)')
    parser.add_argument('--run_name', help='name of the run library, including the date')
    parser.add_argument('--geno', help='Insert the Genotype results file name')
    parser.add_argument('--cnv', help='Insert the CNV results file name')
    parser.add_argument('--samples', help='Insert the added information file name')
    args = parser.parse_args()

    MAIN_RCv2wrapper(args.output_dir, args.office_version, args.bam_dir, args.MyScreen_version, run_name=args.run_name,
                geno_file=args.geno, cnv_file=args.cnv, extraInfo_file=args.samples)
