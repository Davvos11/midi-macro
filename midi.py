import os
import threading
from enum import Enum
from typing import Callable

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import midi


def get_devices():
    midi.init()
    result = []
    for i in range(midi.get_count()):
        result.append(midi.get_device_info(i))
    midi.quit()
    return result


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

    def __init__(self, input_id: int, output_id: int) -> None:
        super().__init__()

        self.__channel_map = self.__init_map()

        midi.init()
        self.__midi_in = midi.Input(input_id)
        self.__midi_out = midi.Output(output_id)
        self.__running = True

        self.start()

    def run(self) -> None:
        while self.__running:
            try:
                if midi.get_init() and self.__midi_in.poll():
                    event = self.__midi_in.read(10)[0][0]
                    status = event[0]

                    channel = (status - 127) % 16
                    m_type_int = (status - 128) // 16
                    m_type = self.Type(m_type_int)
                    value1 = event[1]
                    value2 = event[2]

                    function = self.__get_event(channel, m_type, value1, value2)
                    if function is not None:
                        function((value1, value2))
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
