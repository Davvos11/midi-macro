import os
import threading
import time
from enum import Enum
from typing import Callable

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import midi


def get_devices() -> [tuple]:
    """ Returns a list of midi devices """
    midi.init()
    result = []
    for i in range(midi.get_count()):
        result.append(midi.get_device_info(i))
    midi.quit()
    return result


def print_devices() -> None:
    """ Prints a nicely formatted list of midi devices """
    devices = get_devices()
    for i, device in enumerate(devices):
        print(str(i) + ": " + device[0].decode() + " " + device[1].decode() + ", " + ("input" if device[2] else "") +
              ("output" if device[3] else "") + ", " + ("in use" if device[4] else "not in use"))


def get_id_pair(io_id: int) -> (int, int):
    """ Returns an input and output id based on either an input or an output"""
    devices = get_devices()
    in_id = [i for i, device in enumerate(devices) if device[1] == devices[io_id][1] and device[2]][0]
    out_id = [i for i, device in enumerate(devices) if device[1] == devices[io_id][1] and device[3]][0]
    return in_id, out_id


class Midi(threading.Thread):
    class Type(Enum):
        NOTE_OFF = 0
        NOTE_ON = 1
        NOTE_AFTERTOUCH = 2
        CC = 3
        PROGRAM_CHANGE = 4
        CHANNEL_AFTERTOUCH = 5
        PITCH_WHEEL = 6

    def __init_map(self) -> dict:
        """
        Create nested dicts for channel, type, value1, value2
        """
        c_dict = dict()
        for channel in range(1, 16):
            t_dict = dict()
            for m_type in self.Type:
                v1_dict = dict()
                for value1 in range(0, 127):
                    v2_dict = dict()
                    v1_dict[value1] = v2_dict
                t_dict[m_type] = v1_dict
            c_dict[channel] = t_dict
        return c_dict

    def __init__(self, mode='tui', input_id: int = None, output_id: int = None) -> None:
        super().__init__()

        if input_id is not None and output_id is not None:
            midi.init()
            self.__midi_in = midi.Input(input_id)
            self.__midi_out = midi.Output(output_id)
        elif mode == 'tui':
            midi.init()
            print_devices()  # List devices
            midi_io_ids = get_id_pair(int(input("Choose a midi device: ")))  # Ask for device
            self.__midi_in = midi.Input(midi_io_ids[0])
            self.__midi_out = midi.Output(midi_io_ids[1])
        elif mode == 'gui':
            return
        else:
            raise ValueError('Please set the mode to \'tui\' or \'gui\'')

        self.__mode = mode

        self.__channel_map = self.__init_map()
        self.__running = True
        self.start()

    def get_io_ids(self) -> (int, int):
        return self.__midi_in, self.__midi_out

    def run(self) -> None:
        quick_mode = True
        while self.__running:
            try:
                # Quick mode is used so that when there is no data coming, we can disable it as to
                # not hog the CPU by midi.poll()ing every cycle.
                # However, when there is more data coming after a poll we don't want to wait
                # because that would cause a lot of lag, for example when a knob is turned.
                # Thus, if there is more data queued, we disable quick mode and keep polling
                if not quick_mode:
                    # If we are not in quick mode: wait before proceeding
                    time.sleep(0.05)
                elif not self.__midi_in.poll():
                    # If we are in quick mode but there is no data: disable quick mode
                    quick_mode = False

                if midi.get_init() and self.__midi_in.poll():
                    # If there is data, enable quick mode
                    quick_mode = True

                    event = self.__midi_in.read(10)[0][0]
                    status = event[0]
                    if status not in range(128, 239):
                        continue

                    channel = (status - 127) % 16
                    m_type_int = (status - 128) // 16
                    m_type = self.Type(m_type_int)
                    value1 = event[1]
                    value2 = event[2]

                    function = self.__get_event(channel, m_type, value1, value2)
                    if function is not None:
                        t = threading.Thread(target=function, args=((value1, value2), ))
                        t.start()
            except (NameError, AttributeError, RuntimeError):
                return

    def close(self) -> None:
        self.__running = False
        self.__midi_in.close()
        self.__midi_out.close()
        midi.quit()

    def add_event(self, function: Callable[[tuple], None], channel: int, midi_type: Type,
                  value1: int = None, value2: int = None) -> None:
        name = "Midi listener for " + str(channel) + " " + str(midi_type)

        if value1 is None:
            self.__channel_map[channel][midi_type][-1] = function
        elif value2 is None:
            name += " " + str(value1)
            self.__channel_map[channel][midi_type][value1][-1] = function
        else:
            name += " " + str(value1) + " " + str(value2)
            self.__channel_map[channel][midi_type][value1][value2] = function

    def remove_event(self, channel: int, midi_type: Type, value1: int = None, value2: int = None) -> None:
        try:
            self.__channel_map[channel][midi_type][value1].pop(value2)
            return
        except KeyError:
            pass
        try:
            self.__channel_map[channel][midi_type][value1].pop(-1)
            return
        except KeyError:
            pass
        try:
            self.__channel_map[channel][midi_type].pop(-1)
            return
        except KeyError:
            pass

    def __get_event(self, channel: int, midi_type: Type,
                    value1: int = None, value2: int = None) -> Callable[[tuple], None]:
        try:
            return self.__channel_map[channel][midi_type][value1][value2]
        except KeyError:
            pass
        try:
            return self.__channel_map[channel][midi_type][value1][-1]
        except KeyError:
            pass
        try:
            return self.__channel_map[channel][midi_type][-1]
        except KeyError:
            pass

    def note_out(self, channel: int, note: int, on: bool = True):
        if on:
            self.__midi_out.note_on(note, 127, channel)
        else:
            self.__midi_out.note_off(note, 0, channel)
