
import tkinter as tk
from collections import defaultdict as ddict
from typing import Optional, Callable         

class ControllerSelector(tk.Frame):

    def __init__(self, parent: tk.Frame, controllers: str = "1", console: Optional[str] = None, **kwargs) -> None:

        super().__init__(parent, kwargs)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        for i in range(8):
            self.grid_columnconfigure(i, weight = 1)
        
        tk.Label(self, text = "Controllers").grid(row = 0, column = 0, columnspan = 8, sticky = tk.E + tk.W)
        
        self.states: list = [tk.BooleanVar(self, False) for i in range(8)]

        boxes: list = [tk.Frame(self) for i in range(8)]

        labels: list = [tk.Label(boxes[i - 1], text = str(i)) for i in range(1, 9)]

        for index, box in enumerate(boxes):
            box.grid(row = 1, column = index, sticky = tk.E + tk.W)
            box.grid_rowconfigure(0, weight = 1)
            box.grid_columnconfigure(0, weight = 1)
            box.grid_columnconfigure(1, weight = 1)
        
        self.checkbuttons: list = [tk.Checkbutton(boxes[i],
                                                  onvalue = True,
                                                  offvalue = False,
                                                  variable = self.states[i]) for i in range(8)]
        
        self.setStates(controllers)

        self.lockBoxes(console)
        
        for i in range(8):
            labels[i].grid(row = 0, column = 0, sticky = tk.E)
            self.checkbuttons[i].grid(row = 0, column = 1, sticky = tk.W)
            if i % 2 == 0:
                boxes[i].configure(bg = "lightgrey")
                labels[i].configure(bg = "lightgrey")
                self.checkbuttons[i].configure(bg = "lightgrey")

    def setStates(self, controllers: str) -> None:

        for i in range(1, 9):
            if str(i) in str(controllers):
                
                self.checkbuttons[i - 1].select()
            else:
                self.checkbuttons[i - 1].deselect()

    def getStates(self) -> str:

        output: list = ""
        for i in range(8):
            if self.states[i].get() == True:
                if len(output) > 0:
                    output += ","
                output += str(i + 1)

        return output

    def lockBoxes(self, console: Optional[str] = None) -> None:

        if console == "nes":
            valid: list = [1, 5]
        elif console == "snes":
            valid = [1, 2, 3, 4, 5, 6, 7, 8]
        elif console == "n64":
            valid = [1]
        elif console == "gamecube":
            valid = [1]
        elif console == "genesis":
            valid = [1, 5]
        else:
            valid = [1, 2, 3, 4, 5, 6, 7, 8]
        for i in range(8):
            if i + 1 in valid:
                self.checkbuttons[i].config(state = tk.NORMAL)
            else:
                self.checkbuttons[i].config(state = tk.DISABLED)
                self.checkbuttons[i].deselect()

    def addCallback(self, func: Callable) -> None:

        for button in self.states:
            button.trace_add("write", func)

class TransitionsTable(tk.Frame):

    def __init__(self, parent: tk.Frame, transitions: Optional[str] = None, trace: Optional[Callable] = None, **kwargs) -> None:

        super().__init__(parent, kwargs)
        self.grid_columnconfigure(0, weight = 3)
        self.grid_columnconfigure(1, weight = 1)

        self.count: int = 0
        self.rows: list = []
        self.running: bool = False
        self.cb: Callable = self.register(self.tableUpdateCallback)
        self.trace = trace

        label: tk.Label = tk.Label(self, text = "Transitions")
        label.grid(row = 0, column = 0, columnspan = 2)

        if transitions != "" and transitions != None:
            split = transitions.split(" ")
            for i in range(0, len(split), 2):
                self.addRow(split[i:i + 2])
                
        self.addRow()   
        self.running = True

    def addRow(self, transition: Optional[list] = None) -> None:

        entryVar: tk.StringVar = tk.StringVar(self, transition[0] if transition != None else "")
        entry: tk.Entry = tk.Entry(self,
                                   name = str(self.count + 1),
                                   textvariable = entryVar,
                                   validate = "key",
                                   validatecommand = (self.cb, "%W", "%P"))
        optionsVar: tk.StringVar = tk.StringVar(self, transition[1] if transition != None else "")
        options: tk.OptionMenu = tk.OptionMenu(self,
                                               optionsVar,
                                               *["ACE mode",
                                                 "Normal mode",
                                                 "Soft reset",
                                                 "Hard reset"])
        entry.grid(row = self.count + 1, column = 0, sticky = tk.E + tk.W)
        options.grid(row = self.count + 1, column = 1, sticky = tk.E + tk.W)
        if self.trace != None:
            entryVar.trace_add("write", self.trace)
            optionsVar.trace_add("write", self.trace)
        self.rows.append({"entryVar": entryVar,
                          "entry": entry,
                          "optionsVar": optionsVar,
                          "options": options})
        self.count += 1

    def removeRow(self) -> None:

        del self.rows[-1]["entryVar"]
        self.rows[-1]["entry"].destroy()
        del self.rows[-1]["optionsVar"]
        self.rows[-1]["options"].destroy()
        self.rows.pop(-1)
        self.count -= 1

    def get(self) -> str:

        output: str = ""

        for row in self.rows:
            if output != "":
                output += " "
            frame: str = row['entryVar'].get()
            transition: str = row['optionsVar'].get()
            
            if transition == "ACE mode":
                transition = "A"
            elif transition == "Normal mode":
                transition = "N"
            elif transition == "Soft reset":
                transition = "S"
            elif transition == "Hard reset":
                transition = "H"
                
            if frame.isnumeric():
                output += f"{frame} {'X' if transition not in ['A', 'N', 'S', 'H'] else transition}"

        return output.strip()

    def set(self, transitions: str) -> None:

        self.running = False
        while self.count > 0:
            self.removeRow()
        if transitions != "":
            for transition in transitions.split(" "):
                self.addRow()
                self.rows[-1]["entryVar"].set(transition[0])
                ttype: str = transition[1]
                if ttype == "A":
                    ttype = "ACE mode"
                elif ttype == "N":
                    ttype = "Normal mode"
                elif ttype == "S":
                    ttype = "Soft reset"
                elif ttype == "H":
                    ttype = "Hard reset"
                self.rows[-1]["optionsVar"].set(ttype)
        self.addRow()
        self.running = True

    def tableUpdateCallback(self, who: str, what: str) -> bool:

        #First, we should probably actually validate the result
        if what.isnumeric() == False and what != "":
            return False

        #Do not add rows if the program is modifying the vars
        if not self.running:
            return True

        #Check if it needs to add a row
        if who.split(".")[-1] == str(self.count):
            if what != "":
                self.addRow()
            return True

        #Check if it needs to remove a row
        if who.split(".")[-1] == str(self.count - 1):
            if what == "":
                self.removeRow()
            return True

        #Always return a boolean
        return True

        

if __name__ == "__main__":
    
    cs = ControllerSelector(None, controllers = "124578", console = "snes")
    cs.pack()
    print(cs.getStates())
