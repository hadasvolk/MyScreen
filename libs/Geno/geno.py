from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import numpy as np
import time
import os
import sys
import datetime
import subprocess
import multiprocessing
import logging
from multiprocessing import Pool
import concurrent.futures

import vcfParser
import VS2handler
import cfg
import tools

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

label_start = "- - - Runing Genotyping Detection - - -"

pisces_cmd = cfg.pisces_cmd
scylla_cmd = cfg.scylla_cmd


class Engine():
    def __init__(self, ver, PATHS, main_logger):
        self.ver = ver
        self.PATHS = PATHS
        self.main_logger = main_logger

    def __call__(self, name):
        short_name = name.split('.bam')[0]
        self.main_logger.info("Sample %s: genotyping starting", name)
        with open("{}/PiscesLogs/{}.log".format(self.PATHS["DIR_TREE"][3], name), "w+") as file:
            subprocess.run(pisces_cmd.format(name, self.ver), shell=True, check=True, stdout=file)
            subprocess.run(scylla_cmd.format(name, self.ver, short_name), shell=True, check=True, stdout=file)
        self.main_logger.info("Sample %s: genotyping finished", name)


def genoThread(root, initial_information, PATHS, val, ver, genoCompl):
    while not initial_information.isSet():
        time.sleep(1)
    global main_logger
    main_logger = logging.getLogger('MyScreen_Analysis-{}.log'.format(curDate))

    start = Label(root, text=label_start, font=('calibre', 16, 'bold'))
    start.place(relx=.5, rely=.35, anchor="c")
    processing_bar = ttk.Progressbar(root, length=200, orient='horizontal', mode='indeterminate')
    processing_bar.place(relx=0.5, rely=0.8, anchor=CENTER)
    processing_bar.start()

    bams = []
    for filename in os.listdir(PATHS["BAM_PATH"]):
        if filename.endswith(".bam"):
            bams.append(filename)

    try:
        pool = Pool(4)
        engine = Engine(ver, PATHS, main_logger)
        data_outputs = pool.map(engine, bams)
    except Exception as e:
        main_logger.error("# WARNING: Error occured while excuting multiprocessing Pisces\n{}".format(e))
        app = tools.ProcessError("Failed During Pisces\nPlease see log")
    finally:
        pool.close()
        pool.join()

    parser_label = Label(root, text="Parsing raw vcf files", font=('calibre', 12, 'bold'))
    parser_label.place(relx=.5, rely=.5, anchor="c")
    main_logger.info("Starting parser session")
    try:
        vcfParser.MAIN_ParserWrapper(PATHS["DIR_TREE"][3], PATHS["DIR_TREE"][2], ver, PATHS["BAM_PATH"])
    except Exception as e:
        main_logger.error("Failed to exceute vcfParser\n{}".format(e))
        app = tools.ProcessError("vcfParser")
    main_logger = tools.logger(PATHS["DIR_TREE"][1], 'MyScreen_Analysis-{}'.format(curDate))
    main_logger.info("Completed parser session")
    parser_label.destroy()

    vs2_label = Label(root, text="Annotating variants", font=('calibre', 12, 'bold'))
    vs2_label.place(relx=.5, rely=.55, anchor="c")
    main_logger.info("Starting VS2 annotating session")
    try:
        VS2handler.VS2parser(PATHS["DIR_TREE"][2], PATHS["DIR_TREE"][3])
    except Exception as e:
        main_logger.error("Failed to exceute VS2handler\n{}".format(e))
        app = tools.ProcessError("VS2 annotating")
    main_logger = tools.logger(PATHS["DIR_TREE"][1], 'MyScreen_Analysis-{}'.format(curDate))
    main_logger.info("Completed VS2 annotating session")
    vs2_label.destroy()

    processing_bar.stop()
    processing_bar.destroy()
    start.destroy()
    genoCompl.set()

if __name__ == '__main__':
    genoThread()
