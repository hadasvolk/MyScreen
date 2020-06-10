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
assert sys.version_info >= (3, 6)

import cfg
import inputVald
import geno
from returnThread import ThreadWithReturnValue


#Global Strings to incoopraite in GUI
label = cfg.label

ag_logo = '{}/{}'.format(curdir, cfg.ag_logo)
myscreen_png = '{}/{}'.format(curdir, cfg.myscreen_png)     

main_dir = "{}_RESULTS".format(cfg.myscreen_ver)

#PIPELINE PATHS
"""
BAM_PATH, SAMPLE_SHEET_PATH, EXTRA_INFO_PATH, DIR_TREE
"""

#Run information
"""
SAMPLE_DICT, RUN_NAME
"""
curDate = datetime.datetime.now().strftime("%d-%m-%Y")

def create_log(path):
    log_file = "{}/Analysis-{}.log".format(path, curDate)
    logging.basicConfig(filename=log_file,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Analysis Started!")

# GUI thread entry point.
def _gui_thread(root, initial_information, PATHS):
    root.title(label)
    root.geometry("680x550")
    root.iconbitmap(ag_logo)
    load = Image.open(myscreen_png)
    render = ImageTk.PhotoImage(load)
    img = Label(root, image=render)
    img.image = render
    img.place(x=100, y=0)
    welcome = Label(root, text=label)
    welcome.pack(side=BOTTOM)
    quit = Button(root, text="QUIT", command=root.destroy)
    quit.pack(side=BOTTOM)
    #Importing Bam Directory path and validating bam & bai
    PATHS["BAM_PATH"], PATHS["SAMPLE_DICT"] = inputVald.validate_bams(root)

    # Building directory tree
    DIR_TREE = inputVald.build_dir_tree(root, main_dir)
    PATHS["DIR_TREE"] = DIR_TREE
    create_log(DIR_TREE[0])
    logging.info("Directory: {}".format(PATHS["BAM_PATH"]))

    #Importing SampleSheet.csv getting RUN_NAME and extra info validating
    # against sample's bam bai
    # SAMPLE_SHEET_PATH, RUN_NAME = inputVald.validate_sampleSheet(root)
    # logging.info("SampleSheet.csv: {}".format(SAMPLE_SHEET_PATH))

    # Panel Specs
    PATHS["SAMPLE_DICT"] = inputVald.panel(root, PATHS["SAMPLE_DICT"])

    # Importing additional information to incoorpate in sample_summary
    # validating samples
    PATHS["EXTRA_INFO_PATH"] = inputVald.validate_extraInfo(root)
    logging.info("Extra info: {}".format(PATHS["EXTRA_INFO_PATH"]))

    PATHS["RUN_NAME"] = inputVald.getRunName(root)
    logging.info("Run Name: {}".format(PATHS["RUN_NAME"]))


    initial_information.set()
    return PATHS

if __name__ == '__main__':
    PATHS = {}

    root = Tk(mt_debug=0)

    initial_information = threading.Event()

    initThread = ThreadWithReturnValue(target=_gui_thread, args=(root, initial_information, PATHS,))
    initThread.start()

    # genoThread = ThreadWithReturnValue(target=geno.genoThread, args=(root, initial_information, PATHS, 33, myscreen_ver,))
    # genoThread.start()
    # genoThread.join()

    root.mainloop()
    initThread.join()
