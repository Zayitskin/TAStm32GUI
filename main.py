#!/usr/bin/env python3
import zipfile
import json
import time
import serial
import serial.tools.list_ports
from pathlib import Path

from tkinter import font as tkFont
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import tkinter as tk
import tkinter.ttk as ttk
from multiprocessing import Process

from widgets import ControllerSelector, TransitionsTable
from hook import main

#Run Unpacker
def readRun(run: tk.StringVar) -> [dict, bytes]:

    with zipfile.ZipFile(run.get()) as z:
        with z.open("run.json") as j:
            data: dict = json.load(j)
            if data["movie"] == "":
                return data, b""
            with z.open(data["movie"]) as m:
                movie: bytes = m.read()
                return data, movie

def getSerialPorts() -> list:

    vid: bytes = 0x0B07
    pid: bytes = 0x07A5
    all_ports = serial.tools.list_ports.comports()
    if len(all_ports) == 0:
        return ["No serial ports available"]

    devs: list = []
    for dev in all_ports:
        if dev.vid == vid and dev.pid == pid:
            devs.append(dev)

    if len(devs) == 0:
        return ["No device located"]

    return [devs[i].device for i in range(len(devs))]

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

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill = "both", expand = True)
        self.playback = Playback(self.notebook)
        self.notebook.add(self.playback, text = "TAS Playback")
        self.creation = Creation(self.notebook)
        self.notebook.add(self.creation, text = "TAS File Creation")

class Playback(tk.Frame):
    
    def __init__(self, *args, **kwargs):

        #Child Process Containers
        self.child = None
        
        super().__init__(*args, **kwargs)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)

        #Changing default font size
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(size = 12)

        #Load valid serial devices
        self.devices = getSerialPorts()
        
        #Frames
        self.controlFrame = tk.Frame(self, bg = "red")
        self.controlFrame.grid(row = 0, column = 0, rowspan = 2, sticky = "nswe")
        self.infoFrame = tk.Frame(self, bg = "green")
        self.infoFrame.grid(row = 0, column = 1, sticky = "nswe")
        self.tastm32Frame = tk.Frame(self, bg = "blue")
        self.tastm32Frame.grid(row = 1, column = 1, sticky = "nswe")
        
        #Control Frame
        #Run Selector
        self.runs = sorted(Path(".").glob("runs/**/*.tas"))
        if len(self.runs) == 0:
            self.runs.append("No runs found")
        self.run = tk.StringVar(self, self.runs[0])
        self.runSelector = tk.OptionMenu(self.controlFrame, self.run, *self.runs)
        self.runSelector.pack(fill = "x")
        if self.run.get() != "No runs found":
            info, self.movie = readRun(self.run) #Get the info for the run to populate other widgets
        else:
            info = {
                "name": "",
                "authors": "",
                "description": "",
                "console": "",
                "console specific options": {
                    "latch filter": False,
                    "clock filter": 0,
                    "overread": False},
                "controllers": "",
                "blank frames": 0,
                "initial power setting": "none",
                "bulk data mode": False,
                "transitions": "",
                "latch train": "",
                "movie": ""}
            self.movie = None
        cso = info["console specific options"]

        self.movie_name = info["movie"]
        
        #Dynamic Information

        #Console Specifics
        #Controllers
        self.controllerSelector = ControllerSelector(self.controlFrame,
                                                     info["controllers"],
                                                     info["console"].lower()
                                                     )
        self.controllerSelector.pack(fill = "x")
        
        #Latch Filter
        self.latch_filter_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.latch_filter_frame, text = "Latch Filter")
        label.grid(row = 0, column = 0)
        if "latch filter" in cso:
            self.latch_filter = tk.BooleanVar(self, cso["latch filter"])
            enabled = tk.ACTIVE
        else:
            self.latch_filter = tk.BooleanVar(self, False)
            enabled = tk.DISABLED
        self.latch_filter_checkbutton = tk.Checkbutton(self.latch_filter_frame,
                                                       onvalue = True,
                                                       offvalue = False,
                                                       state = enabled,
                                                       variable = self.latch_filter)      
        self.latch_filter_checkbutton.grid(row = 0, column = 1)
        self.latch_filter_frame.pack(fill = "x")
        
        #Clock Filter
        #TODO: Validate input to avoid an exception
        self.clock_filter_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.clock_filter_frame, text = "Clock Filter")
        label.grid(row = 0, column = 0)
        if "clock filter" in cso:
            self.clock_filter = tk.DoubleVar(self, cso["clock filter"])
            enabled = tk.NORMAL
        else:
            self.clock_filter = tk.DoubleVar(self, 0)
            enabled = tk.DISABLED
        self.clock_filter_spinbox = tk.Spinbox(self.clock_filter_frame,
                                               format = "%.2f",
                                               increment = 0.25,
                                               from_ = 0,
                                               to = 15.75,
                                               state = enabled,
                                               textvariable = self.clock_filter)
        self.clock_filter_spinbox.grid(row = 0, column = 1)
        self.clock_filter_frame.pack(fill = "x")

        #Overread
        self.overread_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.overread_frame, text = "Overread")
        label.grid(row = 0, column = 0)
        if "overread" in cso:
            self.overread = tk.BooleanVar(self, cso["overread"])
            enabled = tk.ACTIVE
        else:
            self.overread = tk.BooleanVar(self, False)
            enabled = tk.DISABLED
        self.overread_checkbutton = tk.Checkbutton(self.overread_frame,
                                                   onvalue = True,
                                                   offvalue = False,
                                                   state = enabled,
                                                   variable = self.overread)
        self.overread_checkbutton.grid(row = 0, column = 1)
        self.overread_frame.pack(fill = "x")

        #Generics
        #Blank Frames
        self.blank_frames_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.blank_frames_frame, text = "Blank Frames")
        label.grid(row = 0, column = 0)
        self.blank_frames = tk.IntVar(self, info["blank frames"])
        self.blank_frames_spinbox = tk.Spinbox(self.blank_frames_frame,
                                               increment = 1,
                                               from_ = 0,
                                               to = 9999999,
                                               textvariable = self.blank_frames)
        self.blank_frames_spinbox.grid(row = 0, column = 1)
        self.blank_frames_frame.pack(fill = "x")
        
        #Intiial Power Setting
        self.initial_power_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.initial_power_frame, text = "Initial Power Setting")
        label.grid(row = 0, column = 0)
        self.initial_power = tk.StringVar(self, info["initial power setting"])
        self.initial_power_menu = tk.OptionMenu(self.initial_power_frame,
                                                self.initial_power,
                                                *["none", "hard reset", "soft reset"])
        self.initial_power_menu.grid(row = 0, column = 1)
        self.initial_power_frame.pack(fill = "x")
        
        #Bulk Data Mode
        self.bulk_data_frame = makeDuoFrame(self.controlFrame)
        label = tk.Label(self.bulk_data_frame, text = "Bulk Data Mode")
        label.grid(row = 0, column = 0)
        self.bulk_data = tk.BooleanVar(self, info["bulk data mode"])
        self.bulk_data_checkbutton = tk.Checkbutton(self.bulk_data_frame,
                                                    onvalue = True,
                                                    offvalue = False,
                                                    variable = self.bulk_data)
        self.bulk_data_checkbutton.grid(row = 0, column = 1)
        self.bulk_data_frame.pack(fill = "x")

        #Transitions
        self.transitionsTable = TransitionsTable(self.controlFrame,
                                                 transitions = info["transitions"],
                                                 trace = self.commandReadoutCallback)
        self.transitionsTable.pack(fill = "x")

        #Latch Train
        label = tk.Label(self.controlFrame, text = "Latch Train")
        label.pack(fill = "x")
        self.latch_train = tk.StringVar(self, info["latch train"])
        self.latch_train_entry = tk.Entry(self.controlFrame,
                                              textvariable = self.latch_train)
        self.latch_train_entry.pack(fill = "x")
        #TODO: Add scrollbar
        
        #Information Frame
        #Static Information
        
        self.name = tk.StringVar(self, info["name"])
        name = tk.Label(self.infoFrame, textvariable = self.name)
        name.pack(fill = "x")
        self.console = tk.StringVar(self, info["console"])
        console = tk.Label(self.infoFrame, textvariable = self.console)
        console.pack(fill = "x")
        self.authors = tk.StringVar(self, info["authors"])
        authors = tk.Label(self.infoFrame, textvariable = self.authors)
        authors.pack(fill = "x")
        self.description = tk.StringVar(self, info["description"])
        description = tk.Label(self.infoFrame, textvariable = self.description)
        description.pack(fill = "x")

        #TAStm32 Frame

        self.progress = ttk.Progressbar(self.tastm32Frame, mode = "determinate")
        self.progress.pack(fill = "x")

        self.readout = tk.StringVar(self, "")
        readout = tk.Entry(self.tastm32Frame,
                           textvariable = self.readout,
                           state="readonly")
        readout.pack(fill = "x")
        
        self.readoutScrollbar = tk.Scrollbar(self.tastm32Frame,
                                             command = readout.xview,
                                             orient = tk.HORIZONTAL)
        readout.config(xscrollcommand = self.readoutScrollbar.set)
        self.readoutScrollbar.pack(fill = "x")

        #When packing to the bottom, it needs to be done in reverse order

        #Buttons
        self.buttonFrame = tk.Frame(self.tastm32Frame)
        self.buttonFrame.grid_rowconfigure(0, weight = 1)
        self.buttonFrame.grid_columnconfigure(0, weight = 1)
        self.buttonFrame.grid_columnconfigure(1, weight = 1)
        self.buttonFrame.grid_columnconfigure(2, weight = 1)
        self.saveButton = tk.Button(self.buttonFrame,
                                    text = "Save",
                                    command = self.saveRun)
        self.saveButton.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.stopButton = tk.Button(self.buttonFrame,
                                    text = "Stop",
                                    command = self.stopRun)
        self.stopButton.grid(row = 0, column = 1, sticky = tk.E + tk.W)
        self.runButton = tk.Button(self.buttonFrame,
                                   text = "Run",
                                   state = tk.DISABLED,
                                   command = self.doRun)
        self.runButton.grid(row = 0, column = 2, sticky = tk.E + tk.W)
        self.buttonFrame.pack(fill = "x", side = tk.BOTTOM)
        
        #Debug Selector
        self.debug_frame = makeDuoFrame(self.tastm32Frame)
        label = tk.Label(self.debug_frame, text = "Debug")
        label.grid(row = 0, column = 0)
        self.debug = tk.BooleanVar(self, value = False)
        self.debug_checkbutton = tk.Checkbutton(self.debug_frame,
                                                onvalue = True,
                                                offvalue = False,
                                                variable = self.debug)
        self.debug_checkbutton.grid(row = 0, column = 1)
        self.debug_frame.pack(fill = "x", side = tk.BOTTOM)

        #Serial Port Selector
        self.serial = tk.StringVar(self, self.devices[0])
        self.serial_optionmenu = tk.OptionMenu(self.tastm32Frame,
                                               self.serial,
                                               *self.devices)
        self.serial_optionmenu.pack(fill = "x", side = tk.BOTTOM)
        label = tk.Label(self.tastm32Frame, text = "Serial Port")
        label.pack(fill = "x", side = tk.BOTTOM)

        #Call callback to get intial text for readout
        self.commandReadoutCallback()
        
        #Callback Registers
        self.run.trace_add("write", self.runSelectorCallback)

        self.console.trace_add("write", self.commandReadoutCallback)
        self.controllerSelector.addCallback(self.commandReadoutCallback)
        self.blank_frames.trace_add("write", self.commandReadoutCallback)
        self.initial_power.trace_add("write", self.commandReadoutCallback)
        self.latch_filter.trace_add("write", self.commandReadoutCallback)
        self.clock_filter.trace_add("write", self.commandReadoutCallback)
        self.overread.trace_add("write", self.commandReadoutCallback)
        self.latch_train.trace_add("write", self.commandReadoutCallback)
        self.bulk_data.trace_add("write", self.commandReadoutCallback)
        self.serial.trace_add("write", self.commandReadoutCallback)
        self.debug.trace_add("write", self.commandReadoutCallback)
        
    #runSelector Callback
    def runSelectorCallback(self, *args):
        info, self.movie = readRun(self.run) #Get the info for the run to populate other widgets
        cso = info["console specific options"]
        #Dynamic Info
        self.controllerSelector.setStates(info["controllers"])
        self.controllerSelector.lockBoxes(info["console"])
        #Console Specifics
        #Latch Filter
        if "latch filter" in cso:
            self.latch_filter.set(cso["latch filter"])
            self.latch_filter_checkbutton.config(state = tk.ACTIVE)
        else:
            self.latch_filter.set(False)
            self.latch_filter_checkbutton.config(state = tk.DISABLED)

        #Clock Filter
        if "clock filter" in cso:
            self.clock_filter.set(cso["clock filter"])
            self.clock_filter_spinbox.config(state = tk.NORMAL)
        else:
            self.clock_filter.set(0)
            self.clock_filter_spinbox.config(state = tk.DISABLED)

        #Overread
        if "overread" in cso:
            self.overread.set(cso["overread"])
            self.overread_checkbutton.config(state = tk.ACTIVE)
        else:
            self.overread.set(False)
            self.overread_checkbutton.config(state = tk.DISABLED)

        #Generics
        #Blank Frames
        self.blank_frames.set(info["blank frames"])

        #Initial Power Setting
        self.initial_power.set(info["initial power setting"])

        #Bulk Data Mode
        self.bulk_data.set(info["bulk data mode"])

        #Transitions
        self.transitionsTable.set(info["transitions"])

        #Latch Train
        self.latch_train.set(info["latch train"])

        #Static Info
        self.name.set(info["name"])
        self.console.set(info["console"])
        self.authors.set(info["authors"])
        self.description.set(info["description"])

        self.movie_name = info["movie"]
            
        

    def commandReadoutCallback(self, *args):

        cmd = "python3 tastm32.py "
        if self.debug.get() == True:
            cmd += "--debug "
        if self.serial.get() != "No device located":
            cmd += f"--serial {self.serial.get()} "
        cmd += f"--console {self.console.get().lower()} "
        if self.controllerSelector.getStates() != "1":
            cmd += f"--players {self.controllerSelector.getStates()} "
        if self.blank_frames.get() > 0:
            cmd += f"--blank {self.blank_frames.get()} "
        if self.latch_filter.get() == True:
            cmd += "--dpcm "
        if self.initial_power.get() == "hard reset":
            cmd += "--hardreset "
        elif self.initial_power.get() == "soft reset":
            cmd += "--softreset "
        #TODO: Fix _tkinter.TclError: expected floating-point number but got ""
        if self.clock_filter.get() > 0:
            cmd += f"--clock {int(self.clock_filter.get() * 4)} "
        transitions = self.transitionsTable.get().split(" ")
        if transitions != [""]:
            for i in range(len(transitions) // 2):
                cmd += f"--transition {transitions[2 * i]} {transitions[2 * i + 1]} "
        if self.overread.get() == True:
            cmd += f"--overread "
        if self.latch_train.get() != "":
            cmd += f"--latchtrain {self.latch_train.get()} "
        if self.bulk_data.get() == False:
            cmd += f"--nobulk "
        cmd += self.movie_name
        self.readout.set(cmd)

        valid = True

        if self.serial.get() == "No device located":
            valid = False
        for i in range(len(transitions) // 2):
            if transitions[2 * i + 1] == "X":
                valid = False
        if self.movie_name == "":
            valid = False

        if valid == True:
            self.runButton.configure(state = tk.ACTIVE)
        else:
            self.runButton.configure(state = tk.DISABLED)

    def doRun(self):

        if self.child != None:
            if self.child.is_alive():
                return

        transitions = self.transitionsTable.get().split(" ")
        if transitions != [""]:
            out = []
            for i in range(len(transitions) // 2):
                out.append([transitions[2 * i], transitions[2 * i + 1]])
            transitions = out
        
        kwargs = {
            "transitions": None if transitions == [""] else transitions,
            "latch_train": self.latch_train.get(),
            "debug": self.debug.get(),
            "controllers": self.controllerSelector.getStates(),
            "serial": self.serial.get(),
            "reset": None if self.initial_power.get() == "none" else self.initial_power.get(),
            "clock": None if self.clock_filter.get() == 0 else self.clock_filter.get(),
            "movie": self.movie,
            "console": self.console.get().lower(),
            "dpcm": self.latch_filter.get(),
            "overread": self.overread.get(),
            "blank": self.blank_frames.get(),
            "nobulk": not self.bulk_data.get()
            }        

        self.child = Process(target = main, kwargs = kwargs)
        self.child.start()

    def stopRun(self):

        if self.child != None:
            if self.child.is_alive():
                self.child.terminate()

    def saveRun(self):

        info, movie = readRun(self.run)
        cso = "console specific options"
        info[cso]["latch filter"] = self.latch_filter.get()
        info[cso]["clock filter"] = self.clock_filter.get()
        info[cso]["overread"] = self.overread.get()
        info["controllers"] = self.controllerSelector.getStates()
        info["blank frames"] = self.blank_frames.get()
        info["initial power setting"] = self.initial_power.get()
        info["bulk data mode"] = self.bulk_data.get()
        info["transitions"] = self.transitionsTable.get()
        info["latch train"] = self.latch_train.get()
        
        with zipfile.ZipFile(self.run.get(), "w") as z:
            z.writestr("run.json", json.dumps(info))
            if info["movie"] != None:
                z.writestr(info["movie"], movie)

class Creation(tk.Frame):

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
        self.console = tk.StringVar(self, "Choose a console")
        self.console_optionmenu = tk.OptionMenu(self.console_frame,
                                                self.console,
                                                *["NES",
                                                  "SNES",
                                                  "N64",
                                                  "Gamecube",
                                                  "Genesis"])
        self.console_optionmenu.grid(row = 1, column = 0, sticky = tk.E + tk.W)
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
        self.movie_frame = tk.Frame(self.right)
        self.movie_frame.grid_rowconfigure(0, weight = 1)
        self.movie_frame.grid_rowconfigure(1, weight = 1)
        self.movie_frame.grid_rowconfigure(2, weight = 1)
        self.movie_frame.grid_columnconfigure(0, weight = 1)
        self.movie_button = tk.Button(self.movie_frame,
                                      text = "Select Movie",
                                      command = self.openMovie)
        self.movie_button.grid(row = 0, column = 0, sticky = tk.E + tk.W)
        self.movie = None
        self.movie_name = tk.StringVar(self, "No movie selected")
        self.movie_label = tk.Entry(self.movie_frame,
                                    textvariable = self.movie_name,
                                    state = "readonly")
        self.movie_label.grid(row = 1, column = 0, sticky = tk.E + tk.W)
        self.movie_scrollbar = tk.Scrollbar(self.movie_frame,
                                            command = self.movie_label.xview,
                                            orient = tk.HORIZONTAL)
        self.movie_label.config(xscrollcommand = self.movie_scrollbar.set)
        self.movie_scrollbar.grid(row = 2, column = 0, sticky = tk.E + tk.W)
        self.movie_frame.pack(fill = "x")

        #Write Button
        self.write_button = tk.Button(self,
                                      text = "Write TAS file",
                                      command = self.saveRun,
                                      state = tk.DISABLED)
        self.write_button.pack(fill = "x", side = tk.BOTTOM)

        #Open Button
        self.open_button = tk.Button(self,
                                     text = "Open TAS file",
                                     command = self.openRun)
        self.open_button.pack(fill = "x", side = tk.BOTTOM)

        self.console.trace_add("write", self.lockBoxes)
        
        self.console.trace_add("write", self.validateRun)
        self.movie_name.trace_add("write", self.validateRun)

    def lockBoxes(self, *args):

        console = self.console.get().lower()
        self.controller_selector.lockBoxes(console)

    def validateRun(self, *args):

        valid = True

        console = self.console.get()

        if console not in ["NES", "SNES", "N64", "Gamecube", "Genesis"]:
            valid = False

        print(self.movie_name)
        if self.movie_name.get() == "No movie selected":
            valid = False

        if valid == False:
            self.write_button.configure(state = tk.DISABLED)
        else:
            self.write_button.configure(state = tk.ACTIVE)

    def saveRun(self):
        file = filedialog.asksaveasfilename(initialdir = os.getcwd(),
                                            title = "Save TAS File As",
                                            filetypes = (("TAS file", "*.tas"),
                                                         ("Zip archive", "*.zip")),
                                            defaultextension = ".tas")
        if file == "":
            return
        
        if self.movie_name.get() != "No movie selected":
            path = Path(self.movie_name.get()).parts[-1]
        else:
            path = None
                
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
            "movie": path,
            "version": "1.1"}
        with zipfile.ZipFile(file, "w") as z:
            z.writestr("run.json", json.dumps(data))
            if path != None:
                z.writestr(path, self.movie)
            
            

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
                self.movie_name.set(data["movie"])
            with z.open(self.movie_name.get(), "r") as m:
                self.movie = m.read()

    def openMovie(self):
        self.movie_name.set(
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
        if self.movie_name.get() == "":
            self.movie_name.set("No movie selected")
            self.movie = None
        else:
            with open(self.movie_name.get(), "rb") as m:
                self.movie = m.read()

def runGUI():

    app = App()
    app.title("TAStm32 Controller")
    #TODO: Configurable default window size
    app.geometry("1000x800")
    app.mainloop()
        
if __name__ == "__main__":
    
    gui = Process(target = runGUI)
    gui.start()
    try:
        while True:
            time.sleep(0.5)
            if gui.is_alive() == False:
                break
    except KeyboardInterrupt:
        gui.terminate()
