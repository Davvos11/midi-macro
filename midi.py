import os
import threading
from queue import Queue
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

    __queue = Queue()
    __listeners_to_remove = []

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

                    self.__call_event(channel, m_type, value1, value2)
            except (NameError, AttributeError, RuntimeError):
                return

    def close(self) -> None:
        self.__running = False
        self.__midi_in.close()
        self.__midi_out.close()
        midi.quit()

    def __wait_for_event(self, event, function) -> None:
        event.wait()
        if event in self.__listeners_to_remove:
            self.__listeners_to_remove.remove(event)
            return
        values = self.__queue.get()
        function(values)
        self.__wait_for_event(event, function)

    def add_event(self, function: Callable[[tuple], None], channel: int, midi_type: Type,
                  value1: int = None, value2: int = None) -> None:
        e = threading.Event()
        name = "Midi listener for " + str(channel) + " " + str(midi_type)

        if value1 is None:
            self.__channel_map[channel][midi_type][-1] = e
            t = threading.Thread(name=name, target=self.__wait_for_event, args=(e, function))
        elif value2 is None:
            name += " " + str(value1)
            self.__channel_map[channel][midi_type][value1][-1] = e
            t = threading.Thread(name=name, target=self.__wait_for_event, args=(e, function))
        else:
            name += " " + str(value1) + " " + str(value2)
            self.__channel_map[channel][midi_type][value1][value2] = e
            t = threading.Thread(name=name, target=self.__wait_for_event, args=(e, function))

        t.start()

    def remove_event(self, channel: int, midi_type: Type, value1: int = None, value2: int = None) -> None:
        event = self.__get_event(channel, midi_type, value1, value2)
        self.__listeners_to_remove.append(event)
        event.set()

    def __get_event(self, channel: int, midi_type: Type, value1: int = None, value2: int = None) -> threading.Event:
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

    def __call_event(self, channel: int, midi_type: Type, value1: int = None, value2: int = None) -> None:
        event = self.__get_event(channel, midi_type, value1, value2)
        if event is not None:
            event.set()
            self.__queue.put((value1, value2))
