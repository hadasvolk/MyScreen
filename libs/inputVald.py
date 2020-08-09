from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
import pandas as pd
import numpy as np
import os

import combobox
import cfg


"""
Function to handle user input files
"""

bam_d = "Click to choose run directory \n(where bam, bai files)"
samplesheet_d = "Click to import SampleSheet.csv"
extraInfo_d = "Do you wish to add extra information? \nExcel file"
panel_d = 'Choose panel for ALL samples?'

#ERROR pop-up msg
def popupmsg(root, msg):
    label = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
    label.place(relx=.5, rely=.35, anchor="c")


def validate_bams(root):
    global BAM_PATH
    global SAMPLE_DICT
    SAMPLE_DICT = {}
    sample_dict_bai = {}

    #Help func to destroy GUI
    def Destroying():
        button_bam.destroy()
        click_label.destroy()
        try:
            warning.destroy()
        except:
            pass

    while True:
        #GUI Message
        click_label = Label(root, text=bam_d,  font=('calibre', 12, 'bold'))
        click_label.place(relx=.5, rely=.45, anchor="c")
        var_bam = IntVar()
        button_bam = Button(root, text="Click", command=lambda: var_bam.set(1))
        button_bam.place(relx=.5, rely=.7, anchor="c")
        button_bam.wait_variable(var_bam)
        BAM_PATH = filedialog.askdirectory(title = "Please choose the results library")
        if len(BAM_PATH) == 0:
            Destroying()
            continue
        #Validation of bam and bai
        for filename in os.listdir(BAM_PATH):
            if filename.endswith(".bam"):
                sample = (filename.split(".")[0]).split("_")
                SAMPLE_DICT[sample[1]] = sample[0]
            elif filename.endswith(".bai"):
                sample = (filename.split(".")[0]).split("_")
                sample_dict_bai[sample[1]] = sample[0]
        diff1 = SAMPLE_DICT.keys() - sample_dict_bai.keys()
        diff2 = sample_dict_bai.keys() - SAMPLE_DICT.keys()
        button_bam.destroy()
        if len(diff1) or len(diff2):
            msg = "Direcotry does not contain bam or bai for sample(s): {}".format(diff1.union(diff2))
            Destroying()
            warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            warning.place(relx=.5, rely=.35, anchor="c")
            continue
        elif len(SAMPLE_DICT) == 0:
            msg = "No bam files in choosen directory"
            Destroying()
            warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            warning.place(relx=.5, rely=.35, anchor="c")
            continue
        SAMPLE_DICT = {key:value for (key,value) in SAMPLE_DICT.items()}
        Destroying()
        return BAM_PATH, SAMPLE_DICT


def validate_sampleSheet(root):
    global BAM_PATH
    global RUN_NAME
    RUN_NAME = ""

    def Destroying():
        button_sampleSheet.destroy()

    while True:
        #GUI Message
        var_sampleSheet = IntVar()
        button_sampleSheet = Button(root, text=samplesheet_d,
                                    command=lambda: var_sampleSheet.set(1))
        button_sampleSheet.place(relx=.5, rely=.6, anchor="c")
        button_sampleSheet.wait_variable(var_sampleSheet)
        SAMPLE_SHEET_PATH = filedialog.askopenfilename(initialdir = BAM_PATH,
                                                       title = "Select SampleSheet.csv",
                                                       filetypes = (("csv files","*.csv"),
                                                                    ("all files","*.*")))
        button_sampleSheet.destroy()

        #Validate sampleSheet
        if len(SAMPLE_SHEET_PATH) == 0:
            popupmsg("SampleSheet.csv was not selected")
            Destroying()
            continue

        Destroying()
        return SAMPLE_SHEET_PATH, RUN_NAME


def validate_extraInfo(root):
    global EXTRA_INFO_PATH
    global BAM_PATH
    global SMAPLE_DICT

    #Help func to destroy GUI
    def Destroying():
        button_extraInfo_no.destroy()
        button_extraInfo_yes.destroy()
        extraInfo_label.destroy()
        try:
            warning.destory()
        except:
            pass

    while True:
        #GUI Message
        extraInfo_label = Label(root, text=extraInfo_d,  font=('calibre', 12, 'bold'))
        extraInfo_label.place(relx=.5, rely=.45, anchor="c")
        var_extraInfo = IntVar(value=0)
        button_extraInfo_yes = Button(root, text="Yes",
                                      command=lambda: var_extraInfo.set(1))
        button_extraInfo_yes.place(relx=.45, rely=.7, anchor="c")
        button_extraInfo_no = Button(root, text="No",
                                     command=lambda: var_extraInfo.set(0))
        button_extraInfo_no.place(relx=.55, rely=.7, anchor="c")
        button_extraInfo_no.wait_variable(var_extraInfo)
        if var_extraInfo.get():
            EXTRA_INFO_PATH = filedialog.askopenfilename(initialdir = BAM_PATH,
                                            title = "Select Extra Info File",
                                            filetypes = (("xlsx files","*.xlsx"),
                                                         ("all files","*.*")))
        else:
            EXTRA_INFO_PATH = False
            Destroying()
            return EXTRA_INFO_PATH

        #Validate extraInfoSheet
        try:
            msg = "Failed to open file"
            extraInfo = pd.read_excel(EXTRA_INFO_PATH, usecols="A:K")
            column_names = ['Sample', 'ID_number', 'Name', 'Source', 'Gender',
                            'City', 'Street', 'Phone', 'Mother Ethnicity',
                            'Father Ethnicity', 'Spouse Sample Number']
            extraInfo.set_axis(column_names, axis=1, inplace=True)
            msg = "Invalid sample number\nPlease check input file"
            extraInfo.Sample = extraInfo.Sample.astype(str)

        except Exception as e:
            print(e)
            warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            warning.place(relx=.5, rely=.35, anchor="c")
            Destroying()
            continue
        samples = []
        for i in SAMPLE_DICT.values():
            samples.append(i[0])
        if not (set(samples) == set(extraInfo.Sample.tolist())):
            msg = "Sample list error"
            Destroying()
            warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            warning.place(relx=.5, rely=.35, anchor="c")
            continue

        Destroying()
        return EXTRA_INFO_PATH


def getRunName(master, bam_path, illegal = False):

    def Destroying():
        run.destroy()
        e.destroy()
        sub_btn.destroy()
        try:
            illegal_label.destroy()
        except:
            pass

    var = IntVar()
    illegal_label = Label(master, text = 'Illegal run name, e.g: 190504_MNXXXXX_YYYY_ZZZZZZZ', font=('calibre', 12, 'bold'))
    if illegal:
        illegal_label.place(relx=.5, rely=.35, anchor="c")
    run = Label(master, text="Insert the name of the run library, including the date", font=('calibre', 12, 'bold'))
    run.place(relx=.5, rely=.45, anchor="c")
    v = StringVar(master, value=bam_path.split('/')[-1])
    e = Entry(master, textvariable=v, width=50)
    e.place(relx=.5, rely=.55, anchor="c")
    sub_btn = Button(master,text = 'Submit', command=lambda: var.set(1))
    sub_btn.place(relx=.5, rely=.6, anchor="c")
    sub_btn.wait_variable(var)
    s = e.get()
    Destroying()
    if s == None or "_M" not in s:
        return getRunName(master, bam_path, illegal = True)
    else:
        return s
    return s


def build_dir_tree(root, ver):
    global BAM_PATH
    folder_list_up = []
    folder_list = ["{}".format(ver),
                   "{}/Info".format(ver),
                   "{}/Info/Genotyping".format(ver),
                   "{}/Info/Genotyping/Logs".format(ver),
                   "{}/Info/Genotyping/Logs/PiscesLogs".format(ver),
                   "{}/Info/CNV".format(ver),
                   "{}/Info/CNV/Logs".format(ver)]
    os.chdir(BAM_PATH)
    for folder in folder_list:
        folder_list_up.append("/".join([BAM_PATH, folder]))
        try:
            os.mkdir(folder)
        except Exception as e:
            pass
    return folder_list_up


def panel(root, sample_dict, ag_logo):
    def Destroying():
        button_0.destroy()
        button_1.destroy()
        button_custom.destroy()
        label.destroy()

    while True:
        #GUI Message
        label = Label(root, text=panel_d, font=('calibre', 12, 'bold'))
        label.place(relx=.5, rely=.45, anchor="c")
        var = IntVar(value=0)
        button_0 = Button(root, text=cfg.Panels[0], command=lambda: var.set(0))
        button_0.place(relx=.35, rely=.7, anchor="c")
        button_1 = Button(root, text=cfg.Panels[1], command=lambda: var.set(1))
        button_1.place(relx=.5, rely=.7, anchor="c")
        button_custom = Button(root, text="Custom", command=lambda: var.set(2))
        button_custom.place(relx=.65, rely=.7, anchor="c")
        button_custom.wait_variable(var)

        if var.get() == 2:
            combobox.combos(sample_dict, cfg.Panels, ag_logo)
        else:
            for k,v in sample_dict.items():
                sample_dict[k] = [v, cfg.Panels[var.get()]]

        Destroying()
        return sample_dict
