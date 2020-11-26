import sys, os, time, datetime
import pandas as pd
import numpy as np
import subprocess
import logging
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

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


def cnvThread(root, PATHS, ver, curDir, genoCompl, cnvCompl, q, txt):
    while not genoCompl.isSet():
        time.sleep(1)

    if PATHS["SUMMARY"]:
        cnvCompl.set()
        return

    global main_logger
    main_logger = logging.getLogger('main')
    main_logger.info("Starting CNV DECoN Analysis")

    global cnv_logger
    cnv_logger = tools.setup_logger('CNV', "{}/CNV.log".format(PATHS["DIR_TREE"][6]))
    cnv_logger.info("Starting CNV DECoN Analysis")

    cur_tk = tools.TkMethods(root)
    start = cur_tk.startLabel(label_start)
    tools.put_text("Starting CNV detection", q, txt)

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
        tools.put_text("Calculating read depth...", q, txt)
        ReadInBams = "R CMD BATCH --no-save \"--args {} {} {} {}\" scripts\ReadInBams.R".format(PATHS["BAM_PATH"], cfg.cnvBED, cfg.hg19, out)
        main_logger.info("Calculating read depth...")
        cnv_logger.info("Calculating read depth...")
        tools.safeProcess(ReadInBams, file, root)
        pasteToLog('scripts\ReadInBams.Rout', decon_log)

        tools.put_text("Running quality checks...", q, txt)
        RData = "{}.RData".format(out)
        IdentifyFailures = "R CMD BATCH --no-save \"--args {} {} {} NULL FALSE {} {}\" scripts\IdentifyFailures.R".format(RData, cfg.mincorr, cfg.mincov, cfg.brca, out)
        main_logger.info("Running quality checks...")
        cnv_logger.info("Running quality checks...")
        tools.safeProcess(IdentifyFailures, file, root)
        pasteToLog('scripts\IdentifyFailures.Rout', decon_log)

        tools.put_text("Identifying exon deletions/duplications...", q, txt)
        makeCNVcalls = "R CMD BATCH \"--args {} {} {} TRUE {} None DECoNPlots {}\" scripts\makeCNVcalls.R".format(RData, cfg.tp, cfg.cnvCustomExons, cfg.brca, out)
        main_logger.info("Identifying exon deletions/duplications...")
        cnv_logger.info("Identifying exon deletions/duplications...")
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
                 cnv_logger.error("Missing {} in log directory".format(file))
                 app = tools.ProcessError("{} \nMissing".format(file))

        tools.put_text("Annotating CNVs", q, txt)
        main_logger.info("Starting DECoNparser session")
        cnv_logger.info("Starting DECoNparser session")
        try:
            PATHS["FAILED_SAMPLES"] = DECoNoutput.DECoNparser(PATHS, 'CNV', q, txt)
            tools.compressed_pickle("{}/failed_samples".format(PATHS["DIR_TREE"][6]), PATHS["FAILED_SAMPLES"])
        except Exception as e:
            main_logger.error("Failed to exceute DECoNparser\n{}".format(e))
            cnv_logger.error("Failed to exceute DECoNparser\n{}".format(e))
            app = tools.ProcessError("CNV annotating")
        main_logger.info("Completed CNV annotating session")
        cnv_logger.info("Completed CNV annotating session")
        tools.put_text("Completed CNV annotating session", q, txt)
        tools.put_text("Completed CNV detection\n", q, txt)

        start.destroy()
        cnvCompl.set()
