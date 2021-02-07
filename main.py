#!/usr/bin/env python3
import zipfile
import json
import time
import serial
import serial.tools.list_ports
from pathlib import Path

from tkinter import font as tkFont
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
        

def makeDuoFrame(parent):

    frame = tk.Frame(parent)
    frame.grid_rowconfigure(0, weight = 1)
    frame.grid_columnconfigure(0, weight = 1)
    frame.grid_columnconfigure(1, weight = 1)
    return frame

class App(tk.Tk):
    
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
            
        

    def commandReadoutCallback(self, *args):

        cmd = "python3 tastm32.py "
        if self.debug.get() == True:
            cmd += "--debug "
        if self.serial.get() != "":
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
        cmd += self.run.get().split("\\")[-1]
        self.readout.set(cmd)
        #TODO: Add run validation so invalid runs cannot be sent to the TAStm32

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
