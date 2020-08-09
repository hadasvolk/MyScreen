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

import cfg
import tools
import DECoNoutput

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

label_start = "- - - Runing CNV Detection - - -"

def pasteToLog(Rout, log):
    try:
        with open(Rout) as f:
            lines = f.readlines()
            lines = [l for l in lines]
            with open(log, "a") as f1:
                f1.writelines(lines)
    except Exception as e:
        main_logger.error("Failed to copy log {}\n{}".format(Rout, e))
        app = tools.ProcessError("Failed to copy log {}".format(Rout))

def cnvThread(root, PATHS, ver, curDir, genoCompl, cnvCompl):
    while not genoCompl.isSet():
        time.sleep(1)

    global main_logger
    main_logger = logging.getLogger('MyScreen_Analysis-{}.log'.format(curDate))
    main_logger.info("Starting CNV DECoN Analysis")

    start = Label(root, text=label_start, font=('calibre', 16, 'bold'))
    start.place(relx=.5, rely=.35, anchor="c")
    processing_bar = ttk.Progressbar(root, length=200, orient='horizontal', mode='indeterminate')
    processing_bar.place(relx=0.5, rely=0.8, anchor=CENTER)
    processing_bar.start()

    text = StringVar()

    try:
        curdir = os.getcwd()
        os.chdir(cfg.decon_master)
    except Exception as e:
        main_logger.error("Failed to change Directory to DECoN-master\n{}".format(e))
        app = tools.ProcessError("Change Directory to DECoN-master")

    log_dir = PATHS["DIR_TREE"][6]
    out = "{}/DECoN".format(log_dir)
    decon_log = "{}/DECoN-{}.log".format(log_dir, curDate)
    decon_error = "{}/DECoN-Errors.log".format(log_dir)
    with open(decon_error, "w+") as file:
        text.set("Calculating read depth...")
        decon_step = Label(root, textvariable=text, font=('calibre', 12, 'bold'))
        decon_step.place(relx=.5, rely=.5, anchor="c")
        ReadInBams = "R CMD BATCH --no-save \"--args {} {} {} {}\" scripts\ReadInBams.R".format(PATHS["BAM_PATH"], cfg.cnvBED, cfg.hg19, out)
        main_logger.info("Calculating read depth...")
        tools.safeProcess(ReadInBams, file, root)
        pasteToLog('scripts\ReadInBams.Rout', decon_log)

        text.set("Running quality checks...")
        RData = "{}.RData".format(out)
        IdentifyFailures = "R CMD BATCH --no-save \"--args {} {} {} NULL FALSE {} {}\" scripts\IdentifyFailures.R".format(RData, cfg.mincorr, cfg.mincov, cfg.brca, out)
        main_logger.info("Running quality checks...")
        tools.safeProcess(IdentifyFailures, file, root)
        pasteToLog('scripts\IdentifyFailures.Rout', decon_log)

        text.set("Identifying exon deletions/duplications...")
        makeCNVcalls = "R CMD BATCH \"--args {} {} {} TRUE {} None DECoNPlots {}\" scripts\makeCNVcalls.R".format(RData, cfg.tp, cfg.cnvCustomExons, cfg.brca, out)
        main_logger.info("Identifying exon deletions/duplications...")
        tools.safeProcess(makeCNVcalls, file, root)
        pasteToLog('scripts\makeCNVcalls.Rout', decon_log)

        os.chdir(curdir)
        main_logger.info("Finished CNV DECoN Analysis")

        files = [decon_log, decon_error, RData,
                 "{}/DECoN_{}.txt".format(log_dir, 'all'),
                 "{}/DECoN_{}.txt".format(log_dir, 'Failures'),
                 "{}/DECoN_{}.txt".format(log_dir, 'custom')]
        for file in files:
            if not os.path.isfile(file):
                 main_logger.error("Missing {} in log directory".format(file))
                 app = tools.ProcessError("{} \nMissing".format(file))

        parser_label = Label(root, text="Annotating CNVs", font=('calibre', 12, 'bold'))
        parser_label.place(relx=.5, rely=.5, anchor="c")
        main_logger.info("Starting DECoNparser session")
        try:
            DECoNoutput.DECoNparser(PATHS)
        except Exception as e:
            main_logger.error("Failed to exceute DECoNparser\n{}".format(e))
            app = tools.ProcessError("CNV annotating")
        main_logger = tools.logger(PATHS["DIR_TREE"][1], 'MyScreen_Analysis-{}'.format(curDate))
        main_logger.info("Completed CNV annotating session")
        parser_label.destroy()

        processing_bar.stop()
        processing_bar.destroy()
        decon_step.destroy()
        start.destroy()
        cnvCompl.set()
