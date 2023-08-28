import numpy as np
import os
import glob
import Tkinter as tk
import ttk
import ScrolledText
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
import ConfigParser
import toolbox
import processing
import pydoc

todo = '''
for the viewer, hold the 3 types of view permanently in memory and just swap in the active view as needed.
so when the gui starts, it will need to hold default views.
'''
import sys, inspect

def is_mod_function(mod, func):
    return inspect.isfunction(func) and inspect.getmodule(func) == mod

def list_functions(mod):
    return [func.__name__ for func in mod.__dict__.itervalues() 
            if is_mod_function(mod, func)]




class Controller(tk.PanedWindow):
    def __init__(self, parent, *args, **kwargs):
        tk.PanedWindow.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.cwd = os.getcwd()
        
        menubar = tk.Menu(parent)
        menubar.add_command(label="File", command=None)
        menubar.add_command(label="Edit", command=None)
        menubar.add_command(label="Run", command=None)
        menubar.add_command(label="Help", command=None)
        parent.config(menu=menubar)
        
        self.tree = TreeView(self, self.cwd)
        self.tree.tree.bind('<Double-Button-1>', self.view_file)
        self.add(self.tree)

        self.viewer = PanelView(self)
        self.add(self.viewer)
        
        self.viewer.fileView.tkraise()
        
    def view_file(self, event):
            curItem = self.tree.tree.focus()
            fname = self.tree.tree.item(curItem)['text']
            fpath= self.tree.tree.item(curItem)['values'][0]
            type = fname.split(".")[-1]
            if type == "su":
                self.viewer.plotView.update(fpath)
                #self.viewer.plotView.tkraise()
            elif type == "py":
                self.viewer.scriptView.update(fpath)


       
        
class PanelView(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.pack(side="top", fill="both", expand=True)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.fileView = FileView(self, self.parent.cwd)
        self.fileView.grid(row=0, column=0, sticky="nsew")
        
        self.scriptView = ScriptView(self)
        self.scriptView.grid(row=0, column=0, sticky="nsew")
        
        self.plotView = PlotView(self, None)
        self.plotView.grid(row=0, column=0, sticky="nsew")
        
        
class FileView(tk.Frame):
    def __init__(self, parent, cwd, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.cwd = cwd
        listbox = tk.Listbox(self)
        #for file in os.listdir(cwd+"/Projects"):
            #listbox.insert(tk.END, file)
        #for i in pydoc.render_doc(toolbox, "Help on %s").split('\n'):
        stuff = pydoc.plain(pydoc.render_doc(toolbox, "Help on %s"))
        for line in stuff.split('\n'):
            listbox.insert(tk.END, line)
        listbox.pack(fill=tk.BOTH, expand=tk.YES)
        
class ScriptView(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.pad = ScrolledText.ScrolledText(self, width=100, height=80)
        self.pad.pack(fill=tk.BOTH, expand=tk.YES)
    def update(self, fpath):
        self.pad.delete('1.0', tk.END)
        self.pad.insert('1.0', open(fpath, 'r').read())
        self.tkraise()
        

class PlotView(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.fig = fig = plt.figure()
        self.ax = ax = fig.add_subplot(111)

        # a tk.DrawingArea
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def update(self, fpath):
        dataset, params = processing.initialise(fpath, memmap=True)
        params['primary'] = None
        params['secondary'] = 'cdp'
        eventManager =  toolbox.KeyHandler(self.fig, self.ax, dataset, params)
        self.fig.canvas.mpl_connect('key_press_event',eventManager)
        #~ self.ax.set_data(dataset['trace'])
        #~ self.fig.canvas.draw()
        self.tkraise()
        
        

class TreeView(tk.Frame):
    def __init__(self, parent, cwd, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.cwd = cwd
        
        vsb = ttk.Scrollbar(self, orient="vertical")
        hsb = ttk.Scrollbar(self, orient="horizontal")

        self.tree = tree = ttk.Treeview(self, columns=("path", "type", "size", "date"),
            displaycolumns="size", yscrollcommand=lambda f, l: self.autoscroll(vsb, f, l),
            xscrollcommand=lambda f, l:self.autoscroll(hsb, f, l))

        vsb['command'] = tree.yview
        hsb['command'] = tree.xview

        tree.heading("#0", text="Projects", anchor='w')
        tree.heading("size", text="File Size", anchor='w')
        tree.column("size", stretch=0, width=100)

        self.populate_roots(tree)
        tree.bind('<<TreeviewOpen>>', self.update_tree)
        # Arrange the tree and its scrollbars in the toplevel
        tree.grid(column=0, row=0, sticky='nswe')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        
    def populate_tree(self, tree, node):
        if tree.set(node, "type") != 'directory':
            return

        path = tree.set(node, "path")
        tree.delete(*tree.get_children(node))

        parent = tree.parent(node)
        for p in  sorted(os.listdir(path)):
            ptype = None
            p = os.path.join(path, p).replace('\\', '/')
            if os.path.isdir(p): ptype = "directory"
            elif os.path.isfile(p): ptype = "file"

            fname = os.path.split(p)[1]
            id = tree.insert(node, "end", text=fname, values=[p, ptype])

            if ptype == 'directory':
                if fname not in ('.', '..'):
                    tree.insert(id, 0, text="dummy")
                    tree.item(id, text=fname)
            elif ptype == 'file':
                size = os.stat(p).st_size * 1e-3
                date = os.stat(p).st_mtime
                tree.set(id, "size", "%d Kb" % size)
                
    def populate_roots(self, tree):
        #dir = os.path.abspath('.').replace('\\', '/')
        dir = self.cwd+"/Projects"
        node = tree.insert('', 'end', text="Projects", values=[dir, "directory"])
        self.populate_tree(tree, node)

    def update_tree(self, event):
        tree = event.widget
        self.populate_tree(tree, tree.focus())

    def change_dir(self, event):
        tree = event.widget
        node = tree.focus()
        if tree.parent(node):
            path = os.path.abspath(tree.set(node, "path"))        
            if os.path.isdir(path):
                os.chdir(path)
                tree.delete(tree.get_children(''))
                self.populate_roots(tree)


    def autoscroll(self, sbar, first, last):
        """Hide and show scrollbar as needed."""
        first, last = float(first), float(last)
        if first <= 0 and last >= 1:
            sbar.grid_remove()
        else:
            sbar.grid()
        sbar.set(first, last)


def main():
    root = tk.Tk()
    a = Controller(root,orient=tk.HORIZONTAL)
    a.pack(side="top", fill="both", expand=True)
    root.geometry("1366x768")
    print( 'functions in current module:\n', list_functions(sys.modules[__name__]))
    print( 'functions in inspect module:\n', list_functions(inspect))
    root.mainloop()
    
if __name__ == "__main__":
    os.chdir("../")
    main()


