import sys
import os
import subprocess
import bz2
import pickle
import _pickle as cPickle
import winreg
from threading import Thread
import logging
import datetime
import tkinter as tk

import cfg

curDate = datetime.datetime.now().strftime("%d-%m-%Y")

def foo(bar):
    print('hello {}'.format(bar))
    return "foo"


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
