import sys, os, time, datetime
import threading
import queue
import multiprocessing
import subprocess
import logging
from threading import Thread
from tkinter import *
from tkinter import filedialog
from mttkinter import mtTkinter
from PIL import ImageTk, Image
import pandas as pd
import numpy as np

curdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('{}/libs'.format(curdir))
sys.path.append('{}/libs/Geno'.format(curdir))
sys.path.append('{}/libs/CNV'.format(curdir))
sys.path.append('{}/libs/RC'.format(curdir))
assert sys.version_info >= (3, 6)

import cfg
import options
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
def _gui_thread(root, initial_information, text_eve, PATHS):
    def _global_quit():
        root.destroy
        tools.kill_proc_tree(os.getpid())
        os._exit(1)

    def _inital():
        # root.geometry("680x550")
        root.iconbitmap(cfg.AG_logo)
        load = Image.open(cfg.MyScreen_png)
        render = ImageTk.PhotoImage(load)
        img = Label(root, image=render)
        img.image = render
        img.place(x=100, y=0)
        welcome = Label(root, text=cfg.Label)
        welcome.pack(side=BOTTOM)

    root.title(cfg.Label)
    w = 680 # width for the Tk root
    h = 550 # height for the Tk root
    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen
    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    # set the dimensions of the screen
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

    _inital()
    quit = Button(root, text="Exit", command=_global_quit)
    quit.pack(side=BOTTOM)

    # Choose what operation to Run
    options.choose(root)

    #Importing Bam Directory path and validating bam & bai
    PATHS["BAM_PATH"], PATHS["SAMPLE_DICT"] = inputVald.validate_bams(root)

    # Building directory tree
    DIR_TREE = inputVald.build_dir_tree(root, cfg.Main_Dir)
    PATHS["DIR_TREE"] = DIR_TREE

    log = tools.setup_logger('stdout', '{}/.out.log'.format(DIR_TREE[1], curDate), logging.DEBUG)
    # sys.stdout = tools.LoggerWriter(log.debug)
    # sys.stderr = tools.ProcessError("Unexpected error occured")

    main_logger = tools.setup_logger('main', '{}/MyScreen_Analysis-{}.log'.format(DIR_TREE[1], curDate))
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

    PATHS["Hospital"] = inputVald.getHospital_Panel(root, 'dir')
    main_logger.info("Hospital: {}".format(PATHS["Hospital"]))

    widget_list = all_children(root)
    for item in widget_list:
        item.pack_forget()
    _inital()
    quit = Button(root, text="Abort", command=_global_quit)
    quit.pack(side=BOTTOM)

    initial_information.set()

    while not text_eve.isSet():
        time.sleep(2)
    quit.destroy()
    # for dir in PATHS['DIR_TREE']:
    #     print(dir)
    # print(PATHS["SAMPLE_DICT"])

    # cnvCompl.set()

def _text(q, eve, root, txt, initial_information):
    while not initial_information.isSet():
        time.sleep(0.2)

    cur_tk = tools.TkMethods(root)
    processing_bar = cur_tk.processBar()
    cur_tk = tools.TkMethods(root)
    Output = cur_tk.text()

    cur = []
    while not eve.isSet():
        time.sleep(0.5)
        txt = q.get()
        for t in txt:
            if t not in cur:
                Output.insert(END, t + '\n')
                Output.yview_pickplace("end")
        cur.extend(txt)

    processing_bar.stop()
    processing_bar.destroy()


if __name__ == '__main__':

    threading.current_thread().name = "MainThread"
    PATHS = {}

    root = Tk(mt_debug=0)
    q = queue.Queue()
    txt = []

    initial_information = threading.Event()
    text_eve = threading.Event()
    genoCompl = threading.Event()
    cnvCompl = threading.Event()

    initThread = ThreadWithReturnValue(target = _gui_thread,
                                       name = 'InitThread',
                                       args = (root, initial_information,
                                               text_eve, PATHS,))
    initThread.start()

    textThread = ThreadWithReturnValue(target = _text,
                                       name = 'TextThread',
                                       args = (q, text_eve, root, txt,
                                               initial_information,))
    textThread.start()

    genoThread = ThreadWithReturnValue(target = geno.genoThread,
                                       name = 'GenoThread',
                                       args = (root, initial_information, PATHS,
                                              cfg.MyScreen_Ver, genoCompl, q, txt,))
    genoThread.start()

    cnvThread = ThreadWithReturnValue(target=cnv.cnvThread,
                                      name = 'CNVThread',
                                      args=(root, PATHS, cfg.MyScreen_Ver, curdir,
                                            genoCompl, cnvCompl, q, txt,))
    cnvThread.start()

    summaryThread = ThreadWithReturnValue(target = summary.summaryThread,
                                          name = 'summaryThread',
                                          args = (root, PATHS, cfg.MyScreen_Ver,
                                                  curdir, initial_information,
                                                  cnvCompl, text_eve, q, txt,))
    summaryThread.start()

    root.mainloop()
    initThread.join()
    textThread.join()
    genoThread.join()
    cnvThread.join()
    summaryThread.join()
