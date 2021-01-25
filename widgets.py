
import tkinter as tk
from collections import defaultdict as ddict
from typing import Optional, Callable         

class ControllerSelector(tk.Frame):

    def __init__(self, parent: tk.Frame, controllers: str = "1", console: Optional[str] = None, **kwargs) -> None:

        super().__init__(parent, kwargs)
        self.grid_rowconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        for i in range(16):
            self.grid_columnconfigure(i, weight = 1)
        
        tk.Label(self, text = "Controllers").grid(row = 0, column = 0, columnspan = 16, sticky = tk.E + tk.W)
        
        self.states: list = [tk.BooleanVar(self, False) for i in range(8)]
        
        labels: list = [tk.Label(self, text = str(i)) for i in range(1, 9)]
        
        self.checkbuttons: list = [tk.Checkbutton(self,
                                                  onvalue = True,
                                                  offvalue = False,
                                                  variable = self.states[i]) for i in range(8)]
        
        self.setStates(controllers)

        self.lockBoxes(console)
        
        for i in range(8):
            labels[i].grid(row = 1, column = 2 * i, sticky = tk.E + tk.W)
            self.checkbuttons[i].grid(row = 1, column = 2 * i + 1, sticky = tk.E + tk.W)

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

    def __init__(self, parent: tk.Frame, transitions: list = [], trace: Optional[Callable] = None, **kwargs) -> None:

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

        for transition in transitions:
            self.addRow(transition)
            #self.rows[-1]["entryVar"].set(transition[0])
            #self.rows[-1]["optionsVar"].set(transition[1])
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
                                               *["A", "N", "S", "H"])
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
            if frame.isnumeric():
                output += f"{frame} {'X' if transition not in ['A', 'N', 'S', 'H'] else transition}"

        return output

    def set(self, transitions: list) -> None:

        self.running = False
        while self.count > 0:
            self.removeRow()
        for transition in transitions:
            self.addRow()
            self.rows[-1]["entryVar"].set(transition[0])
            self.rows[-1]["optionsVar"].set(transition[1])
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
    
    #cs = ControllerSelector(None, controllers = "124578", console = "snes")
    #cs.pack()
    #print(cs.getStates())
    tt: TransitionsTable = TransitionsTable(None, [("12345", "A"), ("24680", "B")])
    tt.pack(fill = "both")
    tt.set([("55555", "A"), ("56565", "C"), ("99999", "D")])
    print(tt.get())
