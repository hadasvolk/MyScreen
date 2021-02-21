from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
from tkfilebrowser import askopendirname, askopenfilename
import pandas as pd
import numpy as np
import os
import copy

import combobox
import cfg
import tools


"""
Function to handle user input files
"""

bam_d = "Click to choose run directory \n(where bam, bai files)"
results_d = "Click to choose results directory \n(where analysis files are)"
samplesheet_d = "Click to import SampleSheet.csv"
extraInfo_d = "Do you wish to add extra information? Optinal Excel file\nIf not chosen all samples will be analyzed for Extended panel"
panel_d = 'Choose panel for ALL samples?'
hospital_d = "Do you wish to output PDF patient reports?"

#ERROR pop-up msg
def popupmsg(root, msg):
    label = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
    label.place(relx=.5, rely=.35, anchor="c")


def validate_bams(root, summary):
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
        t = results_d if summary else bam_d
        click_label = Label(root, text=t,  font=('calibre', 12, 'bold'))
        click_label.place(relx=.5, rely=.45, anchor="c")
        var_bam = IntVar()
        button_bam = Button(root, text="Click", command=lambda: var_bam.set(1))
        button_bam.place(relx=.5, rely=.7, anchor="c")
        button_bam.wait_variable(var_bam)
        # BAM_PATH = filedialog.askdirectory(title = "Please choose the results library")
        # top = Toplevel()
        # top.geometry("+{}+{}".format(root.winfo_x(), root.winfo_y()))
        BAM_PATH = askopendirname(parent=root, title = "Please choose the results library",
                                  filetypes = [("bam", "*.bam"), ("bai", "*.bai")])
        # top.mainloop()
        if len(BAM_PATH) == 0:
            Destroying()
            continue
        #Validation of bam and bai
        if not summary:
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
        else:
            try:
                SAMPLE_DICT = tools.decompress_pickle("/".join([BAM_PATH, "info/Summary/sample_dict.pbz2"]))
            except:
                msg = "No sample_dict.pbz2 file. Unable to determine analysis samples"
                Destroying()
                warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
                warning.place(relx=.5, rely=.35, anchor="c")
                continue
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


def validate_extraInfo(root, sample_dict):
    global EXTRA_INFO_PATH
    global BAM_PATH
    global SMAPLE_DICT
    #Help func to destroy GUI
    def Destroying():
        button_extraInfo_no.destroy()
        button_extraInfo_yes.destroy()
        extraInfo_label.destroy()

    def Destroying_warning():
        warning.pack_forget()

    warning_text = StringVar()
    warning_text.set("")
    warning = Label(root, textvariable=warning_text, font=('calibre', 12, 'bold'))
    warning.place(relx=.5, rely=.35, anchor="c")

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
            EXTRA_INFO_PATH = askopenfilename(initialdir = BAM_PATH,
                                            title = "Select Extra Info File",
                                            filetypes = (("xlsx files","*.xlsx"),
                                                         ("all files","*.*")))
            # EXTRA_INFO_PATH = filedialog.askopenfilename(initialdir = BAM_PATH,
            #                                 title = "Select Extra Info File",
            #                                 filetypes = (("xlsx files","*.xlsx"),
            #                                              ("all files","*.*")))
        else:
            EXTRA_INFO_PATH = False
            for k,v in sample_dict.items():
                sample_dict[k] = [v, cfg.Panels[0][0]]
            Destroying()
            warning_text.set("")
            return EXTRA_INFO_PATH, sample_dict

        #Validate extraInfoSheet
        try:
            msg = "Failed to open file"
            extraInfo = pd.read_excel(EXTRA_INFO_PATH, usecols="A:L", sheet_name='Sheet1', engine='openpyxl')
            extraInfo.dropna(how='all', inplace=True)
            extraInfo = extraInfo.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            column_names = ['Sample', 'ID_number', 'Name', 'Source', 'Gender',
                            'City', 'Street', 'Phone', 'Mother Ethnicity',
                            'Father Ethnicity', 'Spouse Sample Number', 'Panel']
            extraInfo.set_axis(column_names, axis=1, inplace=True)
            msg = "Invalid sample number\nPlease check input file"
            extraInfo.Sample = extraInfo.Sample.astype(str)

        except Exception as e:
            print(e)
            # warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            # warning.place(relx=.5, rely=.35, anchor="c")
            Destroying()
            warning_text.set("# WARNING {}".format(msg))
            continue

        samples = []
        for i in SAMPLE_DICT.values():
            samples.append(i)
        samples_file = extraInfo.Sample.tolist()

        if not (set(samples) == set(samples_file)):
            Destroying()
            msg = "Sample list error\n Missing samples in extra info file. Please review file"
            warning_text.set("# WARNING {}".format(msg))
            continue

        panels_file = extraInfo.Panel.tolist()
        panels_names = cfg.Panels_names
        panels_names.append(np.nan)
        if not set(panels_file).issubset(set(panels_names)):
            msg = "Panel list error\n Some samples are with unkown panel"
            Destroying()
            # warning = Label(root, text="# WARNING {}".format(msg), font=('calibre', 12, 'bold'))
            # warning.place(relx=.5, rely=.35, anchor="c")
            warning_text.set("# WARNING {}".format(msg))
            continue

        for k,v in sample_dict.items():
            x = extraInfo.loc[extraInfo.Sample == v, 'Panel'].item()
            if pd.isna(x):
                x = 'Extended'
            sample_dict[k] = [v, x]

        warning_text.set("")
        Destroying()
        return EXTRA_INFO_PATH, sample_dict


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
    illegal_label = Label(master,
        text = 'Illegal run name, e.g: 190504_MNXXXXX_YYYY_ZZZZZZZ\n or unknown MiSeq\Miniseq code',
        font=('calibre', 12, 'bold'))
    if illegal:
        illegal_label.place(relx=.5, rely=.35, anchor="c")
    run = Label(master, text="Insert the name of the run library, including the date",
        font=('calibre', 12, 'bold'))
    run.place(relx=.5, rely=.45, anchor="c")
    v = StringVar(master, value=bam_path.split('\\')[-1])
    e = Entry(master, textvariable=v, width=50)
    e.place(relx=.5, rely=.55, anchor="c")
    sub_btn = Button(master,text = 'Submit', command=lambda: var.set(1))
    sub_btn.place(relx=.5, rely=.65, anchor="c")
    sub_btn.wait_variable(var)
    s = e.get()
    Destroying()

    dict_hos = {}
    for k,v in cfg.HospitalCode.items():
        for i in v:
            dict_hos[i] = k
    try:
        res = [i for i in s.split('_') if 'M' in i][0]
    except:
        return getRunName(master, bam_path, illegal = True)

    if res == None or res not in list(dict_hos.keys()):
        return getRunName(master, bam_path, illegal = True)
    else:
        return s, dict_hos[res]


def getHospital_Panel(root, x, PATHS):
    lab_hospital = "Choose hospital name"

    if x == 'dir':
        names = [d for d in os.listdir(cfg.Hospitals)]
    else:
        names = cfg.Panels_names
    buttons = [*range(len(names))]
    var_b = IntVar()
    global n
    n = None
    #Help func to destroy GUI
    def Destroying():
        try:
            button_no.destroy()
            button_yes.destroy()
            label.destroy()
            warning.destory()
        except:
            pass

    def func(name):
        global n
        n = name
        var_b.set(1)
        label.destroy()
        for h in names:
            for idx, h in enumerate(names):
                buttons[idx].destroy()

    while True:
        #GUI Message
        var = IntVar(value=0)
        if x == 'dir':
            label = Label(root, text=hospital_d,  font=('calibre', 12, 'bold'))
            label.place(relx=.5, rely=.45, anchor="c")

            button_yes = Button(root, text="Yes", command=lambda: var.set(1))
            button_yes.place(relx=.45, rely=.7, anchor="c")
            button_no = Button(root, text="No", command=lambda: var.set(0))
            button_no.place(relx=.55, rely=.7, anchor="c")
            button_no.wait_variable(var)
        else:
            var.set(1)

        if var.get():
            i = 1
            j = 0
            Destroying()
            if x == 'dir':
                return PATHS["Hospital"]
                # label = Label(root, text=lab_hospital,  font=('calibre', 12, 'bold'))
            else:
                label = Label(root, text=panel_d,  font=('calibre', 12, 'bold'))
            label.place(relx=.5, rely=.4, anchor="c")
            for idx, h in enumerate(names):
                buttons[idx] = Button(root, text=h, command=lambda x=h: func(x))
                if i % 4 != 0:
                    buttons[idx].place(relx=(0.1 + i/5), rely=(0.5 + j/10), anchor="c")
                    i+=1
                else:
                    i = 1
                    j+=1
                    buttons[idx].place(relx=(0.1 + i/5), rely=(0.5 + j/10), anchor="c")
            buttons[0].wait_variable(var_b)
            return n
        else:
            Destroying()
            return False


def build_dir_tree(root, ver):
    global BAM_PATH
    if BAM_PATH.split("\\")[-1] == ver:
        BAM_PATH = "\\".join(BAM_PATH.split("\\")[:-1])
    folder_list_up = []
    folder_list = ["{}".format(ver),
                   "{}/Info".format(ver),
                   "{}/Info/Genotyping".format(ver),
                   "{}/Info/Genotyping/Logs".format(ver),
                   "{}/Info/Genotyping/Logs/PiscesLogs".format(ver),
                   "{}/Info/CNV".format(ver),
                   "{}/Info/CNV/Logs".format(ver),
                   "{}/Info/Summary".format(ver)]
    os.chdir(BAM_PATH)
    for folder in folder_list:
        folder_list_up.append("/".join([BAM_PATH, folder]))
        try:
            os.mkdir(folder)
        except Exception as e:
            pass
    return folder_list_up


def panel(root, sample_dict, ag_logo):
    name = getHospital_Panel(root, 'pan')
    if name == 'Custom':
        x = root.winfo_x()
        y = root.winfo_y()
        combobox.combos(sample_dict, cfg.Panels_names[:-1], ag_logo, x, y)
    else:
        for k,v in sample_dict.items():
            sample_dict[k] = [v, name]

    return sample_dict

    # def Destroying():
    #     button_0.destroy()
    #     button_1.destroy()
    #     button_custom.destroy()
    #     label.destroy()
    #
    # while True:
    #     #GUI Message
    #     label = Label(root, text=panel_d, font=('calibre', 12, 'bold'))
    #     label.place(relx=.5, rely=.45, anchor="c")
    #     var = IntVar(value=0)
    #     button_0 = Button(root, text=cfg.Panels[0], command=lambda: var.set(0))
    #     button_0.place(relx=.35, rely=.7, anchor="c")
    #     button_1 = Button(root, text=cfg.Panels[1], command=lambda: var.set(1))
    #     button_1.place(relx=.5, rely=.7, anchor="c")
    #     button_custom = Button(root, text="Custom", command=lambda: var.set(2))
    #     button_custom.place(relx=.65, rely=.7, anchor="c")
    #     button_custom.wait_variable(var)
        # x = root.winfo_x()
        # y = root.winfo_y()
    #
    #     if var.get() == 2:
    #         combobox.combos(sample_dict, [item[0] for item in cfg.Panels], ag_logo, x, y)
    #     else:
    #         for k,v in sample_dict.items():
    #             sample_dict[k] = [v, [item[0] for item in cfg.Panels][var.get()]]
    #
    #     Destroying()
    #     return sample_dict
