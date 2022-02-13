from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import sys

from . import sii
from . import basictypes


def mk_widget(parent, item):
    if isinstance(item, basictypes.Enum):
        e1 = ttk.Combobox(parent)
        e1['values'] = list(item.options.values())
        e1.set(item.value)

        def update(_):
            try:
                item.value = e1.get()
            except:
                print('Bad value', e1.get())
                e1.set(item.value)
        e1.bind('<<ComboboxSelected>>', update)
        return (e1, None)
    if isinstance(item, basictypes.Int):
        if item.bits == 1:
            v = IntVar(value=item.value)
            cb = ttk.Checkbutton(parent, variable=v, command=lambda: v.get())

            def update(*args):
                item.value = v.get()
                print(item)
            v.trace("w", update)
            return (cb, None)
        else:
            e1 = ttk.Entry(parent)
            e1.insert(0, str(item.value))
            # show in hex as well
            e2 = ttk.Label(parent, text='0x{:X}'.format(item.value))

            def update(key=None):
                try:
                    item.value = int(e1.get(), base=0)
                except:
                    print('Bad value', e1.get())
                    item.value = 0
                    if key and key.keysym == 'Return':
                        e1.delete(0, END)
                        e1.insert(0, str(item.value))
                e2['text'] = '0x{:X}'.format(item.value)
            e1.bind('<KeyRelease>', update)
            return (e1, e2)
    else:
        return (ttk.Label(parent, text=str(item)), None)


def add_item_row(parent, item, name, rownum=0, depth=0):
    ttk.Label(parent, text="  " * depth + name).grid(column=0,
                                                     row=rownum, sticky=W, padx=2)
    rownum += 1
    if isinstance(item, basictypes.Struct):
        for k, v in item._members.items():
            rownum = add_item_row(parent, v, k, rownum, depth + 1)
    else:
        a, b = mk_widget(parent, item)
        if a:
            a.grid(column=1, row=rownum-1, sticky=W, padx=2)
        if b:
            b.grid(column=2, row=rownum-1, sticky=W, padx=2)
    return rownum


class App(ttk.Frame):

    def __init__(self, parent=None):
        ttk.Frame.__init__(self, parent)
        self.pack(fill=BOTH, expand=1)
        self.make_initial_widgets()
        self.model = None
        self.fname = None

    def make_initial_widgets(self):
        # create top level menubar
        menubar = Menu(self)
        self.master.config(menu=menubar)
        menu_file = Menu(menubar)
        menu_file.add_command(label='Open', command=self.open_file)
        menu_file.add_command(label='Save', command=self.save_file)
        menu_file.add_command(label='Save As', command=self.save_file_as)
        menubar.add_cascade(menu=menu_file, label='File')
        # create the placeholder
        self.mainframe = ttk.Frame(self)
        self.mainframe.pack(fill=BOTH, expand=1)
        ttk.Label(self.mainframe, text="Open an SII file to start").pack()

    def update_from_model(self):
        self.mainframe.destroy()
        self.mainframe = ttk.Notebook(self)
        self.mainframe.pack(fill=BOTH, expand=1)
        f = ttk.Frame(self, borderwidth=5)
        self.mainframe.add(f, text='Info')
        add_item_row(f, self.model.info, 'Info', 0)
        if self.model.general:
            self.add_strings()
            f = ttk.Frame(self)
            self.mainframe.add(f, text='General')
            add_item_row(f, self.model.general, 'General')
        if self.model.fmmu:
            f = ttk.Frame(self)
            self.mainframe.add(f, text='FMMU')
            rownum = 0
            for idx, fmmu in enumerate(self.model.fmmu):
                rownum = add_item_row(f, fmmu, 'FMMU {}'.format(idx), rownum)
        if self.model.syncm:
            f = ttk.Frame(self)
            self.mainframe.add(f, text='SyncM')
            rownum = 0
            for idx, syncm in enumerate(self.model.syncm):
                rownum = add_item_row(
                    f, self.model.syncm[idx], 'SyncM {}'.format(idx), rownum)
        if self.model.dc:
            f = ttk.Frame(self)
            self.mainframe.add(f, text='DC')
            add_item_row(f, self.model.dc, 'DC')

    def add_strings(self):
        f = ttk.Frame(self)
        self.mainframe.add(f, text='Strings')

        row = 0
        en = ttk.Entry(f)
        en.insert(0, str(self.model.general_name))
        en.grid(column=1, row=row)
        ttk.Label(f, text="Name").grid(column=0, row=row)

        row += 1
        eg = ttk.Entry(f)
        eg.insert(0, str(self.model.general_group))
        eg.grid(column=1, row=row)
        ttk.Label(f, text="Group").grid(column=0, row=row)

        row += 1
        eo = ttk.Entry(f)
        eo.insert(0, str(self.model.general_order))
        eo.grid(column=1, row=row)
        ttk.Label(f, text="Order").grid(column=0, row=row)

        def doit():
            self.model.general_name = en.get()
            self.model.general_group = eg.get()
            self.model.general_order = eo.get()
            # nuke it! This is shitty and slow but its the easy button right now
            self.update_from_model()

        row += 1
        ttk.Button(f, command=doit, text='Set').grid(column=1, row=row)

    def open_file(self):
        fname = filedialog.askopenfilename()
        if fname:
            self.load(fname)

    def load(self, fname):
        self.model = sii.from_file(fname)
        self.fname = fname
        self.update_from_model()

    def save(self, fname):
        sii.to_file(self.model, fname)

    def save_file(self):
        if self.fname:
            self.save(self.fname)

    def save_file_as(self):
        if self.model == None:
            print('No file open, cant save')
            return
        fname = filedialog.asksaveasfilename()
        if fname:
            self.save(fname)


def main(fname=None):
    # create the thing
    root = Tk()
    root.title('ECAT SII PROM Tool')
    root.geometry('500x900')
    app = App(root)
    # make menus behave
    app.option_add('*tearOff', FALSE)
    # check args
    if fname:
        app.load(fname)
    # go
    app.mainloop()


if __name__ == '__main__':
    target = None
    try:
        target = sys.argv[1]
    except IndexError:
        pass
    main()
