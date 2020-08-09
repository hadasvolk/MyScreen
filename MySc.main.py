import sys
import threading
from tkinter import *
from mttkinter import mtTkinter
from PIL import ImageTk, Image
from tkinter import filedialog
import pandas as pd
import numpy as np
import time
import os
import subprocess
import multiprocessing
import logging
import datetime
import threading
from threading import Thread

curdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('{}/libs'.format(curdir))
sys.path.append('{}/libs/Geno'.format(curdir))
sys.path.append('{}/libs/CNV'.format(curdir))
sys.path.append('{}/libs/RC'.format(curdir))
assert sys.version_info >= (3, 6)

import cfg
import inputVald
import geno
import cnv
import summary
import tools
from tools import ThreadWithReturnValue

#PIPELINE PATHS
"""
BAM_PATH, SAMPLE_SHEET_PATH, EXTRA_INFO_PATH, DIR_TREE
"""

#Run information
"""
SAMPLE_DICT, RUN_NAME
"""
curDate = datetime.datetime.now().strftime("%d-%m-%Y")

def all_children(window):
    _list = window.winfo_children()
    for item in _list:
        if item.winfo_children():
            _list.extend(item.winfo_children())
    return _list

# GUI thread entry point.
def _gui_thread(root, initial_information, PATHS):
    def _global_quit():
        root.destroy
        os._exit(1)

    def _inital():
        root.title(cfg.Label)
        root.geometry("680x550")
        root.iconbitmap(cfg.AG_logo)
        load = Image.open(cfg.MyScreen_png)
        render = ImageTk.PhotoImage(load)
        img = Label(root, image=render)
        img.image = render
        img.place(x=100, y=0)
        welcome = Label(root, text=cfg.Label)
        welcome.pack(side=BOTTOM)
        quit = Button(root, text="QUIT", command=_global_quit)
        quit.pack(side=BOTTOM)

    _inital()

    #Importing Bam Directory path and validating bam & bai
    PATHS["BAM_PATH"], PATHS["SAMPLE_DICT"] = inputVald.validate_bams(root)

    # Building directory tree
    DIR_TREE = inputVald.build_dir_tree(root, cfg.Main_Dir)
    PATHS["DIR_TREE"] = DIR_TREE
    main_logger = tools.logger(DIR_TREE[1], 'MyScreen_Analysis-{}'.format(curDate))
    main_logger.info("MyScreen Analysis Started!\t\t{}".format(curDate))
    main_logger.info("Working Directory: {}".format(curdir))
    main_logger.info("Bam Directory: {}".format(PATHS["BAM_PATH"]))
    main_logger.info("Directory Tree: {}".format(PATHS["DIR_TREE"]))

    #Importing SampleSheet.csv getting RUN_NAME and extra info validating
    # against sample's bam bai
    # SAMPLE_SHEET_PATH, RUN_NAME = inputVald.validate_sampleSheet(root)
    # main_logger.info("SampleSheet.csv: {}".format(SAMPLE_SHEET_PATH))

    # Panel Specs
    PATHS["SAMPLE_DICT"] = inputVald.panel(root, PATHS["SAMPLE_DICT"], cfg.AG_logo)
    main_logger.info("Sample Dictionary: {}".format(PATHS["SAMPLE_DICT"]))

    # Importing additional information to incoorpate in sample_summary
    # validating samples
    PATHS["EXTRA_INFO_PATH"] = inputVald.validate_extraInfo(root)
    main_logger.info("Extra info: {}".format(PATHS["EXTRA_INFO_PATH"]))

    PATHS["RUN_NAME"] = inputVald.getRunName(root, PATHS["BAM_PATH"])
    main_logger.info("Run Name: {}".format(PATHS["RUN_NAME"]))

    widget_list = all_children(root)
    for item in widget_list:
        item.pack_forget()
    _inital()

    initial_information.set()

    for dir in PATHS['DIR_TREE']:
        print(dir)
    print(PATHS["SAMPLE_DICT"])

    # cnvCompl.set()


if __name__ == '__main__':
    PATHS = {}

    root = Tk(mt_debug=0)

    initial_information = threading.Event()
    genoCompl = threading.Event()
    cnvCompl = threading.Event()

    initThread = ThreadWithReturnValue(target=_gui_thread, args=(root,
                                                            initial_information,
                                                            PATHS,))
    initThread.start()

    genoThread = ThreadWithReturnValue(target=geno.genoThread, args=(root,
                                                            initial_information,
                                                            PATHS, 33,
                                                            cfg.MyScreen_Ver,
                                                            genoCompl,))
    genoThread.start()

    cnvThread = ThreadWithReturnValue(target=cnv.cnvThread, args=(root,
                                                            PATHS,
                                                            cfg.MyScreen_Ver,
                                                            curdir,
                                                            genoCompl,
                                                            cnvCompl,))
    cnvThread.start()

    summaryThread = ThreadWithReturnValue(target=summary.summaryThread,
                                                      args=(root,
                                                            PATHS,
                                                            cfg.MyScreen_Ver,
                                                            curdir,
                                                            cnvCompl,))
    summaryThread.start()

    root.mainloop()
    genoThread.join()
    initThread.join()
    cnvThread.join()
    summaryThread.join()
