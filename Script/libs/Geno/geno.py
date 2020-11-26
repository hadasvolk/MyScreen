import sys, os, time, datetime
import logging
import concurrent.futures
import threading
import pandas as pd
import numpy as np
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext

import vcfParser
import VS2handler
import cfg
import tools

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

label_start = "- - - Runing Genotyping Detection - - -"

def worker(name, ver, PATHS, root, q, txt):
    short_name = name.split('.bam')[0]
    threading.current_thread().name = short_name
    main_logger.info("\tGenotyping sample {}".format(short_name))
    tools.put_text("Genotyping sample {}".format(short_name), q, txt)
    with open("{}/PiscesLogs/{}.log".format(PATHS["DIR_TREE"][3], name), "w+") as file:
        geno_logger.info("Starting pisces {}".format(short_name))
        tools.safeProcess(cfg.pisces_cmd.format(name, ver), file, root)
        geno_logger.info("Starting scylla {}".format(short_name))
        tools.safeProcess(cfg.scylla_cmd.format(name, ver, short_name), file, root)
    try:
        vcfParser.MAIN_ParserWrapper("{}/{}.genome.vcf".format(PATHS["DIR_TREE"][3],short_name), PATHS["DIR_TREE"][2], ver, 'Geno', PATHS["BAM_PATH"])
    except Exception as e:
        main_logger.error("Failed to exceute vcfParser\n{}".format(e))
        app = tools.ProcessError("vcfParser/SoftClipsSolution")
    main_logger.info("\tCompleted genotyping sample {}".format(short_name))
    tools.put_text("Completed Genotyping sample {}".format(short_name), q, txt)

def genoThread(root, initial_information, PATHS, ver, genoCompl, q, txt):

    while not initial_information.isSet():
        time.sleep(1)

    # if PATHS["SUMMARY"]:
    #     genoCompl.set()
    #     return
    #
    # global main_logger
    # main_logger = logging.getLogger('main')
    # main_logger.info("Starting Genotyping multiprocessing")
    #
    # global geno_logger
    # geno_logger = tools.setup_logger('Geno', "{}/Genotyping.log".format(PATHS["DIR_TREE"][3]))
    # geno_logger.info("Starting Genotyping multiprocessing")
    #
    # cur_tk = tools.TkMethods(root)
    # start = cur_tk.startLabel(label_start)
    #
    # bams = ["{}_{}.bam".format(v[0], k) for k, v in PATHS['SAMPLE_DICT'].items()]
    # th = concurrent.futures.ThreadPoolExecutor(max_workers=cfg.n_workrs)
    # futures = []
    # for sample in bams:
    #     futures.append(th.submit(worker, sample, ver, PATHS, root, q, txt))
    # th.shutdown(wait=True)
    # main_logger.info("Completed Genotyping multithreading")
    #
    # main_logger.info("Starting multiprocessing annotation")
    # tools.put_text("Runing multiprocessing annotation", q, txt)
    #
    # try:
    #     VS2handler.VS2parser(PATHS["DIR_TREE"][2], PATHS["DIR_TREE"][0], PATHS["DIR_TREE"][3], 'Geno')
    # except Exception as e:
    #     main_logger.error("Failed to exceute VS2handler\n{}".format(e))
    #     app = tools.ProcessError("VS2 annotating")
    #
    # main_logger.info("Completed multiprocessing annotation")
    # tools.put_text("Completed multiprocessing annotation", q, txt)
    # tools.put_text("Successfully genotyped samples\n", q, txt)
    #
    # start.destroy()
    genoCompl.set()

if __name__ == '__main__':
    genoThread()
