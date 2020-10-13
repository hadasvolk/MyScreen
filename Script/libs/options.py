from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
import pandas as pd
import numpy as np
import os
import copy

import combobox
import cfg

main = "Welcome to MyScreen Analysis!"

def choose(root):
    #Help func to destroy GUI
    def Destroying():
        but_analysis.destroy()
        postive.destroy()
        app_note.destroy()
        mutlist.destroy()
        main_label.destroy()
        try:
            warning.destroy()
        except:
            pass

    while True:
        #GUI Message
        main_label = Label(root, text=main,  font=('calibre', 14, 'bold'))
        main_label.place(relx=.5, rely=.35, anchor="c")

        var = IntVar(value=0)

        but_analysis = ttk.Style()
        but_analysis.configure('B1.TButton', foreground='blue', background='blue')
        but_analysis = ttk.Button(text="Run Analysis", command=lambda: var.set(1),
                                  style='B1.TButton', padding=12)
        but_analysis.place(relx=.5, rely=.5, anchor="c")

        postive = ttk.Style()
        postive.configure('B2.TButton', background='blue')
        postive = ttk.Button(text="MyScreen VALIDATED\n            Postive",
                             command=lambda: var.set(2),
                             style='B2.TButton', padding=6)
        postive.place(relx=.25, rely=.65, anchor="c")

        app_note = ttk.Style()
        app_note.configure('B2.TButton', background='blue')
        app_note = ttk.Button(text="Application Note", command=lambda: var.set(3),
                              style='B2.TButton', padding=6)
        app_note.place(relx=.5, rely=.65, anchor="c")

        mutlist = ttk.Style()
        mutlist.configure('B2.TButton', background='blue')
        mutlist = ttk.Button(text="Disease and Mutation\n\tList",
                             command=lambda: var.set(4),
                             style='B2.TButton', padding=6)
        mutlist.place(relx=.75, rely=.65, anchor="c")

        but_analysis.wait_variable(var)

        var_set = var.get()
        if var_set == 4:
            os.startfile(cfg.mut_list)
            Destroying()
        elif var_set == 3:
            os.startfile(cfg.appnote)
            Destroying()
        elif var_set == 2:
            os.startfile(cfg.vald_pos)
            Destroying()
        else:
            Destroying()
            return
