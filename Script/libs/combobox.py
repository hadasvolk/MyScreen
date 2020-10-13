import os
import tkinter as tk
import tkinter.ttk as ttk

import cfg

all_comboboxes = []

def on_select():
    # if event:
    #     print("event.widget:", event.widget.get())
    result = []
    for i, x in enumerate(all_comboboxes):
        result.append(x.get())
    return result

def combos(samples, panels, ag_logo, x, y):
        def _global_quit():
            result = on_select()
            for i, sample in enumerate(samples):
                samples[sample] = [samples[sample], result[i]]
            var.set(1)
            master.destroy()
            # os._exit(1)

        master = tk.Toplevel()
        # master.iconbitmap(ag_logo)
        # master.title("Panel Selector")
        master.geometry("+%d+%d" % (x + 700, y))
        master.overrideredirect(True)

        var = tk.IntVar(value=0)
        glabel = tk.Label(master, text="Choose panel for each sample ", font=('calibre', 12))
        glabel.grid(column=1, row=0)
        for i, sample in enumerate(samples.values()):
            label = tk.Label(master, text=sample, font=('calibre', 12))
            label.grid(column=0, row=i+1)
            cb = ttk.Combobox(master, values=panels)
            cb.set(panels[0])
            cb.grid(column=1, row=i+1)
            cb.bind('<<ComboboxSelected>>')
            all_comboboxes.append(cb)

        b = tk.Button(master, text="Submit", command=_global_quit)
        b.grid(column=1, row=i+2)
        b.wait_variable(var)
        # master.protocol("WM_DELETE_WINDOW", print("delete_window"))
        return samples
        master.mainloop()

if __name__ == '__main__':
    print(combos({'1-1':'1',2:'2-1',3:'3-1'}, ('Bedouin', 'Extended'), 'c:\\Gamidor\\MyScreen\\images\\ag_logo.ico'), 100, 200)
