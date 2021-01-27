#!/usr/bin/env python3
import zipfile
import os
import json
import pathlib

import tkinter as tk
from tkinter import font as tkFont
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

from widgets import ControllerSelector, TransitionsTable

def makeStackedFrame(parent):

    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight = 1)
    frame.grid_rowconfigure(1, weight = 1)
    frame.grid_columnconfigure(0, weight = 1)

    return frame

def makeDuoFrame(parent):

    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight = 1)
    frame.grid_columnconfigure(0, weight = 1)
    frame.grid_columnconfigure(1, weight = 1)

    return frame

class App(tk.Tk):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

         #Changing default font size
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size = 12)

        #Main Frame
        self.main = makeDuoFrame(self)
        
        self.left = tk.Frame(self.main)
        self.right = tk.Frame(self.main)
        self.left.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.right.grid(row = 0, column = 1, sticky = tk.E + tk.W)

        self.main.pack()

        #Run Name
        self.name_frame = makeStackedFrame(self.left)
        label = tk.Label(self.name_frame,
                         text = "Name")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.name = tk.StringVar(self, "")
        self.name_entry = tk.Entry(self.name_frame,
                                   textvariable = self.name)
        self.name_entry.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.name_frame.pack(fill = "x")

        #Console

        self.console_frame = makeStackedFrame(self.left)
        label = tk.Label(self.console_frame,
                         text = "Console")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.console = tk.StringVar(self, "")
        self.console_entry = tk.Entry(self.console_frame,
                                      textvariable = self.console)
        self.console_entry.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.console_frame.pack(fill = "x")
        
        #Author(s)
        self.authors_frame = makeStackedFrame(self.left)
        label = tk.Label(self.authors_frame,
                         text = "Author(s)")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.authors = tk.StringVar(self, "")
        self.authors_entry = tk.Entry(self.authors_frame,
                                     textvariable = self.authors)
        self.authors_entry.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.authors_frame.pack(fill = "x")

        #Run Description
        self.description_frame = makeStackedFrame(self.left)
        label = tk.Label(self.description_frame,
                         text = "Description")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.description = ScrolledText(self.description_frame)
        self.description.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.description_frame.pack(fill = "x")

        #Controllers
        self.controller_selector = ControllerSelector(self.right)
        self.controller_selector.pack(fill = "x")

        #Latch Filter
        self.latch_frame = makeDuoFrame(self.right)
        label = tk.Label(self.latch_frame,
                         text = "Latch Filter")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.latch = tk.BooleanVar(self, value = False)
        self.latch_checkbutton = tk.Checkbutton(self.latch_frame,
                                                onvalue = True,
                                                offvalue = False,
                                                variable = self.latch)
        self.latch_checkbutton.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.latch_frame.pack(fill = "x")

        #Clock Filter
        self.clock_frame = makeDuoFrame(self.right)
        label = tk.Label(self.clock_frame,
                         text = "Clock Filter")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.clock = tk.DoubleVar(self, 0)
        self.clock_spinbox = tk.Spinbox(self.clock_frame,
                                        format = "%.2f",
                                        increment = 0.25,
                                        from_ = 0,
                                        to = 15.75,
                                        textvariable = self.clock)
        self.clock_spinbox.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.clock_frame.pack(fill = "x")

        #Overread
        self.overread_frame = makeDuoFrame(self.right)
        label = tk.Label(self.overread_frame,
                         text = "Overread")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.overread = tk.BooleanVar(self, value = False)
        self.overread_checkbutton = tk.Checkbutton(self.overread_frame,
                                                   onvalue = True,
                                                   offvalue = False,
                                                   variable = self.overread)
        self.overread_checkbutton.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.overread_frame.pack(fill = "x")

        #Blank Frames
        self.blank_frame = makeDuoFrame(self.right)
        label = tk.Label(self.blank_frame,
                         text = "Blank Frames")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.blank = tk.IntVar(self, 0)
        self.blank_spinbox = tk.Spinbox(self.blank_frame,
                                        from_ = 0,
                                        to = 999999,
                                        textvariable = self.blank)
        self.blank_spinbox.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.blank_frame.pack(fill = "x")

        #Initial Power Setting
        self.initial_frame = makeDuoFrame(self.right)
        label = tk.Label(self.initial_frame,
                         text = "Initial Power Setting")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.initial = tk.StringVar(self, "none")
        self.initial_optionmenu = tk.OptionMenu(self.initial_frame,
                                                self.initial,
                                                *["none", "hard reset", "soft reset"])
        self.initial_optionmenu.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.initial_frame.pack(fill = "x")
        
        #Bulk Data Mode
        self.bulk_frame = makeDuoFrame(self.right)
        label = tk.Label(self.bulk_frame,
                         text = "Bulk Data Mode")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.bulk = tk.BooleanVar(self, value = True)
        self.bulk_checkbutton = tk.Checkbutton(self.bulk_frame,
                                               onvalue = True,
                                               offvalue = False,
                                               variable = self.bulk)
        self.bulk_checkbutton.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.bulk_frame.pack(fill = "x")

        #Transitions
        self.transitionsTable = TransitionsTable(self.right)
        self.transitionsTable.pack(fill = "x")

        #Latch Train
        self.train_frame = makeDuoFrame(self.right)
        label = tk.Label(self.train_frame,
                         text = "Latch Train")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.train = tk.StringVar(self, "")
        self.train_entry = tk.Entry(self.train_frame,
                                    textvariable = self.train)
        self.train_entry.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.train_frame.pack(fill = "x")

        #Movie Filename
        self.movie_frame = makeStackedFrame(self.right)
        label = tk.Label(self.movie_frame,
                         text = "Movie Filename")
        label.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        buffer = makeDuoFrame(self.movie_frame)
        buffer.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.movie = tk.StringVar(self, "")
        self.movie_entry = tk.Entry(buffer,
                                    textvariable = self.movie)
        self.movie_entry.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.movie_button = tk.Button(buffer,
                                      text = "Open",
                                      command = self.openMovie)
        self.movie_button.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.movie_frame.pack(fill = "x")

        #Write Button
        self.write_button = tk.Button(self,
                                      text = "Write TAS file",
                                      command = self.saveRun)
        self.write_button.pack(fill = "x", side = tk.BOTTOM)

        #Open Button
        self.open_button = tk.Button(self,
                                     text = "Open TAS file",
                                     command = self.openRun)
        self.open_button.pack(fill = "x", side = tk.BOTTOM)


    def saveRun(self):
        file = filedialog.asksaveasfilename(initialdir = os.getcwd(),
                                            title = "Save TAS File As",
                                            filetypes = (("TAS file", "*.tas"),
                                                         ("Zip archive", "*.zip")),
                                            defaultextension = ".tas")
        if file == "":
            return
        abspath = self.movie.get()
        relpath = ""
        if abspath != "":
                if pathlib.Path(abspath).exists():
                    relpath = pathlib.Path(abspath).parts[-1]
                else:
                    print("Error: movie not found.")
                    return
                
        data = {
            "name": self.name.get(),
            "console": self.console.get(),
            "authors": self.authors.get(),
            "description": self.description.get("1.0", "end").strip(),
            "console specific options": {
                "latch filter": self.latch.get(),
                "clock filter": self.clock.get(),
                "overread": self.overread.get()},
            "controllers": self.controller_selector.getStates(),
            "blank frames": self.blank.get(),
            "initial power setting": self.initial.get(),
            "bulk data mode": self.bulk.get(),
            "transitions": self.transitionsTable.get(),
            "latch train": self.train.get(),
            "movie": relpath,
            "version": "1.1"}
        with zipfile.ZipFile(file, "w") as z:
            z.writestr("run.json", json.dumps(data))
            if abspath != "":
                z.write(abspath, arcname = relpath)
            
            

    def openRun(self):
        file = filedialog.askopenfilename(initialdir = os.getcwd(),
                                          title = "Select TAS File",
                                          filetypes = (("TAS files", "*.tas"),
                                                       ("Zip archives", "*.zip"))
                                          )
        if file == "":
            return
        
        with zipfile.ZipFile(file, "r") as z:
            with z.open("run.json") as j:
                data = json.load(j)
                self.name.set(data["name"])
                self.console.set(data["console"])
                self.authors.set(data["authors"])
                self.description.delete("1.0", "end")
                self.description.insert("1.0", data["description"])
                if "latch filter" in data:
                    self.latch.set(data["latch filter"])
                if "clock filter" in data:
                    self.clock.set(data["clock filter"])
                if "overread" in data:
                    self.overread.set(data["overread"])
                self.controller_selector.setStates(data["controllers"])
                self.blank.set(data["blank frames"])
                self.initial.set(data["initial power setting"])
                self.bulk.set(data["bulk data mode"])
                self.transitionsTable.set(data["transitions"])
                self.train.set(data["latch train"])
                self.movie.set(data["movie"])

    def openMovie(self):
        self.movie.set(
            filedialog.askopenfilename(initialdir = os.getcwd(),
                                       title = "Select Movie File",
                                       filetypes = (("Common movie formats",
                                                     "*.r08 *.r16m *.m64 *.dtm *.rgen"),
                                                    ("r08 files", "*.r08"),
                                                    ("r16m files", "*.r16m"),
                                                    ("m64 files", "*.m64"),
                                                    ("dtm files", "*.dtm"),
                                                    ("rgen files", "*.rgen"))
                                       ))
                         

if __name__ == "__main__":

    app = App()
    app.title("TAS Format Constructor")
    app.geometry("900x800")
    app.mainloop()
