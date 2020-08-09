from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import numpy as np
import time
import os
import sys
import subprocess
import logging
import datetime
import xlsxwriter
import docx2pdf

import cfg
import tools
import RCv2
import formatExcel

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

label_start = "- - - Summarizing Results - - - "

def summaryThread(root, PATHS, ver, curDir, cnvCompl):
    while not cnvCompl.isSet():
        time.sleep(1)

    global main_logger
    main_logger = logging.getLogger('MyScreen_Analysis-{}.log'.format(curDate))
    main_logger.info("Summarizing Results")

    text_ = StringVar()
    start = Label(root, text=label_start, font=('calibre', 16, 'bold'))
    start.place(relx=.5, rely=.35, anchor="c")
    processing_bar = ttk.Progressbar(root, length=200, orient='horizontal', mode='indeterminate')
    processing_bar.place(relx=0.5, rely=0.8, anchor=CENTER)
    processing_bar.start()

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

    text_.set("Aggregating Results")
    label = Label(root, textvariable=text_, font=('calibre', 12, 'bold'))
    label.place(relx=.5, rely=.5, anchor="c")

    geno = tools.decompress_pickle(files[0])
    cnv = tools.decompress_pickle(files[1])
    cnv.rename(columns={'Annotation1': 'Custom Annotation', 'Chromosome': 'Chr',
                'Annotation2': 'Custom Annotation 2',
                'Annotation3': 'Custom Annotation 3',
                'Annotation4': 'Custom Annotation 4'}, inplace=True)
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
    tools.compressed_pickle("{}/AG_DB_{}".format(PATHS["DIR_TREE"][1], curDate), ag_db)

    panels = {}
    for panel in cfg.Panels:
        if panel != 'Extended':
            cur = "{}{}{}".format(cfg.path_to_panel, panel,'.AGID.pbz2')
            if not os.path.isfile(cur):
                 main_logger.error("Missing {} panel list".format(cur))
                 app = tools.ProcessError("{} \nMissing".format(cur))
            panels[panel] = tools.decompress_pickle(cur)

    results = cfg.full_results
    results.insert(0, 'temp')
    results.insert(0, 'temp')
    writer = pd.ExcelWriter("{}/Results.xlsx".format(PATHS["DIR_TREE"][1]), engine='xlsxwriter')
    for i in range(2, len(files)-2):
        df = tools.decompress_pickle(files[i])
        for s, info in PATHS["SAMPLE_DICT"].items():
            sample_panel = info[1]
            if sample_panel != 'Extended':
                sub = df.where(df.Sample == "{}_{}".format(info[0], s))
                sub.dropna(how = 'all', inplace = True)
                to_remove = []
                for index, row in sub.iterrows():
                    if row.AGID not in panels[sample_panel]:
                        to_remove.append(index)
                df.drop(to_remove, inplace = True)
        df.to_excel(writer, sheet_name=results[i], index=False)
        tools.compressed_pickle(files[i], df)
    df = tools.decompress_pickle(files[i+1])
    df.to_excel(writer, sheet_name=results[i+1], index=False)
    df = tools.decompress_pickle(files[i+2])
    df.to_excel(writer, sheet_name=results[i+2], index=False)
    writer.save()

    text_.set("Creating Final Reports")
    try:
        wordVer = "20{}".format(int(tools.getMicrosoftWordVersion()))
        main_logger.info("Office version {}".format(wordVer))
    except Exception as e:
        main_logger.info("Unable to get word version. Assuming 2016\n{}".format(e))
        word_ver = Label(root, text="Unable to get word version. Assuming 2016", font=('calibre', 12, 'bold'))
        word_ver.place(relx=.5, rely=.45, anchor="c")
        wordVer = "2016"

    try:
        sample_summary = RCv2.MAIN_RCv2wrapper(PATHS["DIR_TREE"][0], wordVer,
                PATHS["BAM_PATH"], cfg.MutPDF, PATHS["RUN_NAME"], files[3], files[1],
                PATHS["EXTRA_INFO_PATH"])
    except Exception as e:
        main_logger.error("Failed to exceute MAIN_RCv2wrapper\n{}".format(e))
        app = tools.ProcessError("Report Creator")

    text_.set("Formating Sample Summary")
    try:
        sample_summary = formatExcel.AddIgvLink(sample_summary, PATHS["BAM_PATH"], cfg.MyScreen_Ver)
    except Exception as e:
        main_logger.error("Failed to exceute AddIgvLink\n{}".format(e))

    try:
        formatExcel.excel_formatter(sample_summary, PATHS["DIR_TREE"][0], cfg.MyScreen_Ver)
    except Exception as e:
        main_logger.error("Failed to exceute format excel\n{}".format(e))
        app = tools.ProcessError("Format Sample Summary")

    text_.set("Converting Reports to PDF")
    try:
        docx2pdf.convert("{}/REPORTS/".format(PATHS["DIR_TREE"][0]))
    except Exception as e:
        main_logger.error("Failed to convert reports to PDF\n{}".format(e))

    processing_bar.destroy()
    label.destroy()
    start.destroy()

    finished = Label(root, text="Analysis Completed Successfully", font=('calibre', 12, 'bold'))
    finished.place(relx=.5, rely=.35, anchor="c")

    def _global_quit():
        root.destroy
        try:
            subprocess.Popen('explorer {}'.format(PATHS["DIR_TREE"][0].replace('/', '\\')))
        except:
            pass
        os._exit(1)

    quit = Button(root, text="Analysis Completed\nPress to open results directory", command=_global_quit, bg = "blue", fg='white')
    quit.place(relx=.5, rely=.55, anchor="c")
