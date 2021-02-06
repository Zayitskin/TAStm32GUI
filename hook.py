
import os
import psutil
import gc
import time
import sys

from tastm32 import TAStm32, RunObject
import r08, r16m, m64, dtm, rgen

from typing import Optional


def main(*,
         transitions: Optional[list] = None,
         latch_train: str,
         debug: bool,
         controllers: str,
         serial: str,
         reset: Optional[str] = None,
         clock: Optional[int] = None,
         movie: bytes,
         console: str,
         dpcm: bool,
         overread: bool,
         blank: int = 0,
         nobulk: bool) -> None:

    global DEBUG
    global buffer
    global run_id
    global fn

    int_buffer = 1024 # internal buffer size on replay device

    latches_per_bulk_command = 28
    packets = 4

    if(os.name == 'nt'):
        psutil.Process().nice(psutil.REALTIME_PRIORITY_CLASS)
    else:
        psutil.Process().nice(20)

    gc.disable()

    if transitions != None:
        for transition in transitions:
            transition[0] = int(transition[0])
            if transition[1] == 'A':
                transition[1] = b'A'
            elif transition[1] == 'N':
                transition[1] = b'N'
            elif transition[1] == 'S':
                transition[1] = b'S'
            elif transition[1] == 'H':
                transition[1] = b'H'

    if latch_train != "":
        latchtrain = [int(x) for x in latch_train.split(',')]
    else:
        latchtrain = []

    DEBUG = debug

    '''
    print("Lets see if we got everything:")
    print(f"{transitions=}")
    print(f"{latch_train=}")
    print(f"{debug=}")
    print(f"{controllers=}")
    print(f"{serial=}")
    print(f"{reset=}")
    print(f"{clock=}")
    print(f"{movie=}")
    print(f"{console=}")
    print(f"{dpcm=}")
    print(f"{overread=}")
    print(f"{blank=}")
    print(f"{nobulk=}")
    '''

    players = list(map(int, controllers.split(",")))

    dev = TAStm32(serial)

    if reset == "hard reset" or reset == "soft reset":
        dev.power_off()
        if reser == "hard reset":
            time.sleep(2.0) #TODO: FIXME?

    #No need for clock check cause the GUI did that already

    #TODO: Open movie
    data = movie

    dev.reset()

    #Setup Run
    run_id = dev.setup_run(console, players, dpcm, overread, clock)
    if run_id == None:
        raise RuntimeError("Failed to setup run.")
        sys.exit()

    #Setup Console
    if console == 'n64':
        buffer = m64.read_input(data)
        blankframe = b'\x00\x00\x00\x00' * len(players)
    elif console == 'snes':
        buffer = r16m.read_input(data, players)
        blankframe = b'\x00\x00' * len(players)
    elif console == 'nes':
        buffer = r08.read_input(data, players)
        blankframe = b'\x00' * len(players)
    elif console == 'gc':
        buffer = dtm.read_input(data)
        blankframe = b'\x00\x00\x00\x00\x00\x00\x00\x00' * len(players)
    elif console == 'genesis':
        buffer = rgen.read_input(data, players)
        blankframe = b'\x00\x00' * len(players)

    #Setup Transitions
    if transitions != None:
        for transition in transitions:
            dev.send_transition(run_id, *transition)

    #Send Blank Frames
    for _ in range(blank):
        data = run_id + blankframe
        dev.write(data)
    print(f"Sending Blank Latches: {blank}.") #TODO: Pipe?

    fn = 0
    for latch in range(int_buffer - blank):
        try:
            data = run_id + buffer[fn]
            dev.write(data)
            if fn % 100 == 0:
                print(f"Sending Latch: {fn}.") #TODO: Pipe?
            fn += 1
        except IndexError:
            pass

    err = dev.read(int_buffer)
    fn -= err.count(b"\xB0")
    if err.count(b"\xB0") != 0:
        print('Buffer Overflow x{}'.format(err.count(b'\xB0')))

    #Latch Trains
    if latchtrain != []:
        dev.send_latchtrain(run_id, latchtrain)

    run = RunObject(run_id, buffer, fn, blankframe)
    print("Main Loop Start.") #TODO: Pipe?
    if not nobulk:
        dev.set_bulk_data_mode(run_id, b"1")
    dev.power_on()
    dev.main_loop(run)
    print("Exiting.") #TODO: Pipe?
    sys.exit(0)
    
