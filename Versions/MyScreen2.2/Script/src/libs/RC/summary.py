import sys, os, time, datetime
import shutil
import subprocess
import logging
import xlsxwriter
import docx2pdf
import pythoncom
import pandas as pd
import numpy as np
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from pathlib import Path

import cfg
import libs.tools as tools
import libs.RC.RCv2 as RCv2
import libs.RC.formatExcel as formatExcel
import libs.RC.formatCSV as formatCSV

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

label_start = "- - - Summarizing Results - - - "

def summaryThread(root, PATHS, ver, curDir, initial_information, cnvCompl, text_eve, q, txt):
    while not cnvCompl.isSet() or not initial_information.isSet():
        time.sleep(1)

    global main_logger
    main_logger = logging.getLogger('main')
    main_logger.info("Summarizing Results")

    cur_tk = tools.TkMethods(root)
    start = cur_tk.startLabel(label_start)
    tools.put_text("Starting to summarize results", q, txt)

    files = []
    files.append('{}/{}.pbz2'.format(PATHS["DIR_TREE"][2], cfg.FullGeno))
    files.append('{}/{}.pbz2'.format(PATHS["DIR_TREE"][5], cfg.FullCNV))
    for file in cfg.GenoPickles:
        files.append('{}/{}.pbz2'.format(PATHS["DIR_TREE"][3], file))
    for file in cfg.CNVPickles:
        files.append('{}/{}.pbz2'.format(PATHS["DIR_TREE"][6], file))

    for file in files:
        if not os.path.isfile(file):
             main_logger.error("Missing {} in log directory".format(file))
             app = tools.ProcessError("{} \nMissing".format(file))

    tools.put_text("Aggregating Results", q, txt)

    geno = tools.decompress_pickle(files[0])
    cnv = tools.decompress_pickle(files[1])
    # cnv.rename(columns={'Annotation1': 'Custom Annotation', 'Chromosome': 'Chr',
    #             'Annotation2': 'Custom Annotation 2',
    #             'Annotation3': 'Custom Annotation 3',
    #             'Annotation4': 'Custom Annotation 4'}, inplace=True)
    combained = pd.concat([geno, cnv], ignore_index=True, sort=False)
    combained.insert(0, 'Analysis Date', curDate)
    combained.insert(0, 'Run Name', PATHS["RUN_NAME"])

    if os.path.isfile("{}.pbz2".format(cfg.AG_DB)):
        ag_db = tools.decompress_pickle("{}.pbz2".format(cfg.AG_DB))
        ag_db = pd.concat([ag_db, combained], ignore_index=True, sort=False)
        ag_db.drop_duplicates(keep='last', inplace=True)
    else:
        ag_db = combained
    tools.compressed_pickle("{}".format(cfg.AG_DB), ag_db)
    tools.compressed_pickle("{}/AG_DB_{}".format(PATHS["DIR_TREE"][-1], curDate), ag_db)

    panels = {}
    for panel in cfg.Panels_names[:-1]:
        if panel != 'Extended':
            cur = "{}{}{}{}".format(cfg.path_to_panel,'\\', panel,'.AGID.pbz2')
            if not os.path.isfile(cur):
                 main_logger.error("Missing {} panel list".format(cur))
                 app = tools.ProcessError("{} \nMissing".format(cur))
            temp = tools.decompress_pickle(cur)
            panels[panel] = [agid for line in temp for agid in line.split('/')]
            panels[panel].append(np.nan)

    results = cfg.full_results
    results.insert(0, 'temp')
    results.insert(0, 'temp')
    writer = pd.ExcelWriter("{}/Results.xlsx".format(PATHS["DIR_TREE"][1]), engine='xlsxwriter')
    for i in range(1, len(files)-2):
        df = tools.decompress_pickle(files[i])
        if i == 1:
            temp = df[['Sample', 'Gender']].drop_duplicates()
        for s, info in PATHS["SAMPLE_DICT"].items():
            sample_panel = info[1]
            if sample_panel != 'Extended':
                # print(s, sample_panel)
                sub = df.where(df.Sample == "{}_{}".format(info[0], s))
                sub.dropna(how = 'all', inplace = True)
                to_remove = []
                for index, row in sub.iterrows():
                    if row.AGID not in panels[sample_panel]:
                        to_remove.append(index)
                df.drop(to_remove, inplace = True)
        if i != 1:
            df.to_excel(writer, sheet_name=results[i], index=False)
        else:
            df = df.merge(temp, how='outer', on=['Sample', 'Gender'])
        tools.compressed_pickle(files[i].split('.pbz2')[0] + '.filtered', df)
        files[i] = files[i].split('.pbz2')[0] + '.filtered.pbz2'
    df = tools.decompress_pickle(files[i+1])
    df.to_excel(writer, sheet_name=results[i+1], index=False)
    df = tools.decompress_pickle(files[i+2])
    df.to_excel(writer, sheet_name=results[i+2], index=False)
    writer.save()

    tools.put_text("Creating Final Reports", q, txt)
    try:
        wordVer = "20{}".format(int(tools.getMicrosoftWordVersion()))
        main_logger.info("Office version {}".format(wordVer))
    except Exception as e:
        main_logger.info("Unable to get word version. Assuming 2016\n{}".format(e))
        tools.put_text("Unable to get word version. Assuming 2016", q, txt)

    try:
        sample_summary = RCv2.MAIN_RCv2wrapper(PATHS["DIR_TREE"][0], wordVer,
                PATHS["BAM_PATH"], PATHS["Hospital"], PATHS['SAMPLE_DICT'],
                cfg.MutPDF, 'main', PATHS["RUN_NAME"], files[3], files[1],
                PATHS["EXTRA_INFO_PATH"])
        sample_summary.to_pickle("{}/raw_sample_summary.pkl".format(PATHS["DIR_TREE"][-1]))
    except Exception as e:
        main_logger.error("Failed to exceute MAIN_RCv2wrapper\n{}".format(e))
        app = tools.ProcessError("Report Creator")
    tools.put_text("Formating Sample Summary", q, txt)

    try:
        sample_summary = formatExcel.AddIgvLink(sample_summary, PATHS["BAM_PATH"], cfg.MyScreen_Ver)
    except Exception as e:
        main_logger.error("Failed to exceute AddIgvLink\n{}".format(e))
    # formatExcel.excel_formatter(sample_summary, PATHS, cfg.MyScreen_Ver)
    try:
        sample_sum_excel, run = formatExcel.excel_formatter(sample_summary, PATHS, cfg.MyScreen_Ver)
    except Exception as e:
        main_logger.error("Failed to exceute format excel\n{}".format(e))
        app = tools.ProcessError("Format Sample Summary")

    try:
        csv_file, psv_file = formatCSV.create_summary_csv(All = files[2],
            summary = sample_sum_excel, v = cfg.MyScreen_Ver, r = run, d = curDate,
            out = PATHS["DIR_TREE"][-1])
    except Exception as e:
        main_logger.error("Failed to exceute format CSV\n{}".format(e))
        app = tools.ProcessError("Format Sample Summary CSV")


    main_logger.info("Additional CSV output directory {}".format(os.path.isdir(cfg.CSV_dir)))
    try:
        shutil.copy(csv_file, os.path.join(cfg.CSV_dir,
            "sample_summary-{}.csv".format(curDate)))
        shutil.copy(psv_file, os.path.join(cfg.CSV_dir,
            "sample_summary-{}.psv".format(curDate)))
        main_logger.info("Outputed CSV and PSV in {}".format(cfg.CSV_dir))
    except IOError as e:
        main_logger.info("Unable to copy file. %s" % e)
    except:
        main_logger.info("Unexpected error:", sys.exc_info())


    if PATHS["Hospital"] != False:
        tools.put_text("Converting Reports to PDF", q, txt)
        try:
            pythoncom.CoInitialize()
            docx2pdf.convert("{}/REPORTS/".format(PATHS["DIR_TREE"][0]))
        except Exception as e:
            main_logger.error("Failed to convert reports to PDF\n{}".format(e))

    start.destroy()

    cur_tk = tools.TkMethods(root)
    start = cur_tk.startLabel("Analysis Completed Successfully")

    text_eve.set()

    def _global_quit():
        root.destroy
        try:
            subprocess.Popen('explorer {}'.format(PATHS["DIR_TREE"][0].replace('/', '\\')))
        except:
            pass
        os._exit(1)

    quit = Button(root, text="Analysis Completed\nPress to open results directory", command=_global_quit, bg = "blue", fg='white')
    quit.place(relx=.5, rely=.8, anchor="c")
