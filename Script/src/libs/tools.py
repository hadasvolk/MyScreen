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

import cfg

curDate = datetime.datetime.now().strftime("%d-%m-%Y")


class TkMethods():
    def __init__(self, root):
        self.root = root
        self._return = None

    def startLabel(self, label_text):
        start = tk.Label(self.root, text=label_text, font=('calibre', 16, 'bold'))
        start.place(relx=.5, rely=.3, anchor="c")
        return start

    def processBar(self):
        processing_bar = ttk.Progressbar(self.root, length=170, orient='horizontal', mode='indeterminate')
        processing_bar.place(relx=0.5, rely=0.8, anchor="c")
        processing_bar.start()
        return processing_bar

    def text(self):
        Output = tk.scrolledtext.ScrolledText(self.root, height = 10, width = 45)
        Output.place(relx=.5, rely=.55, anchor="c")
        return Output


def put_text(string, q, lis):
    lis.append(string)
    q.put(lis)


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


class ProcessError():
    def __init__(self, cmd):
        self.root = tk.Tk()
        self.root.iconbitmap(cfg.AG_logo)
        self.root.title(cfg.Label)
        # self.root.geometry()
        label = tk.Label(self.root,
                    text="# WARNING Unable to execute:\n{}\n\nPlease contact support".format(cmd))
        label.pack()
        button = tk.Button(self.root,text = 'Quit', command=self.quit)
        button.pack()
        self.root.mainloop()

    def quit(self):
        self.root.destroy()
        os._exit(1)


def safeProcess(cmd, log, root):
    try:
        subprocess.run(cmd, check=True, shell=True, stdout=log)
    except Exception as e:
        logging.error(e)
        print(e)
        root.destroy
        app = ProcessError(cmd)

def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.kill()
    gone, still_alive = psutil.wait_procs(children, timeout=5)
    if including_parent:
        parent.kill()
        parent.wait(5)

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    formatter = logging.Formatter("%(asctime)s"
        "| %(threadName)-11s"
        "| %(levelname)-5s"
        "| %(message)s", '%Y-%m-%d %H:%M:%S')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


class LoggerWriter(object):
    def __init__(self, writer):
        self._writer = writer
        self._msg = ''

    def write(self, message):
        self._msg = self._msg + message
        while '\n' in self._msg:
            pos = self._msg.find('\n')
            self._writer(self._msg[:pos])
            self._msg = self._msg[pos+1:]

    def flush(self):
        if self._msg != '':
            self._writer(self._msg)
            self._msg = ''


def logger(path, name):
    log_file = "{}/{}.log".format(path, name)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=log_file,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger('{}.log'.format(name))
    return log


# Pickle a file and then compress it into a file with extension
def compressed_pickle(title, data):
    with bz2.BZ2File(title + '.pbz2', 'w') as f:
        cPickle.dump(data, f)

# Load any compressed pickle file
def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = cPickle.load(data)
    return data


def getMicrosoftWordVersion():
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Office", 0, winreg.KEY_READ)
    versionNum = 0
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(key, i)
            i+=1
            if versionNum < float(subkey):
                versionNum = float(subkey)
        except: #relies on error handling WindowsError as e as well as type conversion when we run out of numbers
            break
    return versionNum


def global_quit(root):
    root.destroy
    os._exit(1)
