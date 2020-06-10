from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import numpy as np
import time
import os
import sys
import subprocess
import multiprocessing
import logging
import datetime
from multiprocessing import Pool
import concurrent.futures

import vcfParser

label_start = "************* Runing Genotyping Detection **************"

pisces_cmd = "dotnet C:/Gamidor/Appendix/Genotyping/5.2.8.44/Pisces/Pisces.dll \
    -SBFilter 1000 -Bam {} -G C:/Gamidor/Appendix/Genotyping --minvq 10 \
    -MinMapQuality 0 -diploidsnvgenotypeparameters 0.20,0.90,0.80 \
    -diploidindelgenotypeparameters 0.20,0.90,0.80 -MinBaseCallQuality 12  \
    -VQFilter 10 -CallMNVs false -MinDepth 5 -Ploidy diploid -OutFolder \
    \"{}_RESULTS/Genotyping/Logs\" -forcedalleles \
    C:/Gamidor/{}/Script/Genotyping/Norm.RC.sort.vcf -crushvcf false -IntervalPaths \
    C:/Gamidor/{}/Script/Genotyping/Norm.RC.sort.txt"

scylla_cmd = "dotnet C:/Gamidor/Appendix/Genotyping/5.2.5.20/Scylla/Scylla.dll -b 10 -bam {} -vcf \
        {}_RESULTS/Genotyping/Logs/{}.genome.vcf"

genome_vcf = "{}_RESULTS/Genotyping/Logs/{}.genome.vcf"
out_vs2 = "{}_RESULTS/Genotyping/{}.VS2.vcf"
norm = "C:/Gamidor/{}/Script/Genotyping/Norm.RC.sort.vcf"
curDate = datetime.datetime.now().strftime("%d-%m-%Y")
def create_log(path, ver):
    log_file = "{}/{}_RESULTS/Genotyping/Logs/Genotyping-{}.log".format(path, curDate, ver)
    logging.basicConfig(filename=log_file,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


def thread_function(name, ver, PATHS, master):
    short_name = name.split('.bam')[0]
    run = Label(master, text="Genotyping sample {}".format(name.split('.bam')[0]), font=('calibre', 12, 'bold'))
    run.place(relx=.5, rely=.3, anchor="c")
    logging.info("Sample %s: genotyping starting", name)
    with open("{}/PiscesLogs/{}.log".format(PATHS["DIR_TREE"][2], name), "w+") as file:

        pisces = Label(master, text="Running Pisces", font=('calibre', 12, 'bold'))
        pisces.place(relx=.5, rely=.35, anchor="c")
        subprocess.run(pisces_cmd.format(name, ver, ver, ver), shell=True, stdout=file)

        scylla = Label(master, text="Running Scylla", font=('calibre', 12, 'bold'))
        scylla.place(relx=.5, rely=.4, anchor="c")
        subprocess.run(scylla_cmd.format(name, ver, name.split('.bam')[0]), shell=True, stdout=file)

        parser = Label(master, text="Running Parser", font=('calibre', 12, 'bold'))
        parser.place(relx=.5, rely=.45, anchor="c")
        old_stdout = sys.stdout
        sys.stdout = file
        vcfParser.main(genome_vcf.format(ver, short_name), out_vs2.format(ver, short_name), norm.format(ver))
        sys.stdout = old_stdout

    logging.info("Sample %s: genotyping finished", name)
    run.destroy()
    pisces.destroy()
    scylla.destroy()
    parser.destroy()


def genoThread(root, initial_information, PATHS, val, ver):
    while not initial_information.isSet():
        time.sleep(1)
    create_log(PATHS["BAM_PATH"], ver)
    # print(val)
    # bams = []
    processing_bar = ttk.Progressbar(root, orient='horizontal', mode='indeterminate')
    processing_bar.place(relx=0.5, rely=0.5, anchor=CENTER)
    processing_bar.start()
    for filename in os.listdir(PATHS["BAM_PATH"]):
        if filename.endswith(".bam"):
            thread_function(filename, ver, PATHS, root)
            # bams.append(filename)
    processing_bar.stop()
    processing_bar.destroy()
    # with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    #     executor.daemon = True
    #     executor.map(thread_function, bams, ver)

if __name__ == '__main__':
    genoThread()
