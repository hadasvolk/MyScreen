# -*- coding: utf-8 -*-
import sys, os, time, datetime
import psutil
from threading import Thread
import logging
import winreg
import subprocess
import bz2
import pickle
import _pickle as cPickle
import tkinter as tk
from tkinter import ttk
import pandas as pd


# Pickle a file and then compress it into a file with extension
def compressed_pickle(title, data):
    with bz2.BZ2File(title + '.pbz2', 'w') as f:
        cPickle.dump(data, f)

# Load any compressed pickle file
def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data

ver2_df = pd.read_csv(r'c:\Gamidor\MyScreen\Script\docs\ver2.agids', sep='\t')
ver2_nr_df = pd.read_csv(r'c:\Gamidor\MyScreen\Script\docs\ver2_sex_nr.agids', sep='\t')
cnv_df = pd.read_pickle(r'c:\Gamidor\MyScreen\Script\docs\CNVAnno.pkl')

ver2 = ver2_df.AGID.tolist()
ver2_nr = ver2_nr_df.AGID.tolist()
cnv = cnv_df.AGID.tolist()

reported = (set(cnv) | set(ver2)) - set(ver2_nr)
extended_repo_df = pd.DataFrame(data=list(reported), columns=['AGID'])
compressed_pickle(r'c:\Gamidor\MyScreen\Script\docs\Extended.AGID.reported', reported)
extended_repo_df.to_csv(r'c:\Gamidor\MyScreen\Script\docs\Extended.AGID.reported.txt', sep='\t', index=False)

final = pd.read_excel(r'c:\Users\hadas\AGcloud\AGshared\AG_DB\FINAL\Final.xlsx', sheet_name='Sheet1', engine='openpyxl')
clalit_repo_df = final[(final['is_duplicated'] == False) & (final['ver_2'] == True)]
clalit_repo_df = clalit_repo_df[(clalit_repo_df['panel'] == 'Clalit') | (clalit_repo_df['panel'] == 'Bedouin & Clalit')]
clalit_repo = set(clalit_repo_df.agid.tolist())
reported_clalit = set(clalit_repo) - set(ver2_nr)
compressed_pickle(r'c:\Gamidor\MyScreen\Script\docs\Clalit.AGID.reported', reported_clalit)
clalit_repo_df.rename(columns={"agid":"AGID"}, inplace=True)
clalit_repo_df["AGID"].to_csv(r'c:\Gamidor\MyScreen\Script\docs\Clalit.AGID.reported.txt', sep='\t', index=False)

bedouin_repo_df = final[(final['is_duplicated'] == False) & (final['ver_2'] == True)]
bedouin_repo_df = bedouin_repo_df[(bedouin_repo_df['panel'] == 'Bedouin') | (bedouin_repo_df['panel'] == 'Bedouin & Clalit')]
bedouin_repo = set(bedouin_repo_df.agid.tolist())
reported_bedouin = set(bedouin_repo) - set(ver2_nr)
compressed_pickle(r'c:\Gamidor\MyScreen\Script\docs\Bedouin.AGID.reported', reported_bedouin)
bedouin_repo_df.rename(columns={"agid":"AGID"}, inplace=True)
bedouin_repo_df["AGID"].to_csv(r'c:\Gamidor\MyScreen\Script\docs\Bedouin.AGID.reported.txt', sep='\t', index=False)