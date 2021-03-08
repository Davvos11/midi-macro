import os
import threading
import time
from enum import Enum
from typing import Callable
from queue import Queue

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import midi


def get_devices(pygame_init=True) -> [tuple]:
    """ Returns a list of midi devices """
    if pygame_init:
        midi.init()
    result = []
    for i in range(midi.get_count()):
        result.append(midi.get_device_info(i))
    if pygame_init:
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

    def _init_map(self) -> dict:
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

    def __init__(self, input_id: int = None, output_id: int = None, queue: Queue = None) -> None:
        super().__init__()
        self.queue = queue
        self.try_to_reconnect = False

        if input_id is not None and output_id is not None:
            midi.init()
            self._midi_in = midi.Input(input_id)
            self._midi_out = midi.Output(output_id)
        else:
            print_devices()  # List devices
            midi_io_ids = get_id_pair(int(input("Choose a midi device: ")))  # Ask for device
            midi.init()
            self._midi_in = midi.Input(midi_io_ids[0])
            self._midi_out = midi.Output(midi_io_ids[1])

        midi_devices = get_devices(False)
        self._midi_in_name = midi_devices[self._midi_in.device_id]
        self._midi_out_name = midi_devices[self._midi_out.device_id]

        self._channel_map = self._init_map()
        self._running = True
        self.start()

    def wait_for_reconnect(self):
        while True:
            time.sleep(0.2)
            # Refresh pygame midi
            midi.quit()
            midi.init()
            # Check if the device is back in the list
            devices = get_devices()
            device_names = [device[1] for device in devices]
            if self._midi_in_name[1] in device_names:
                # Return the new IDs
                return [self.get_device_index(self._midi_in_name), self.get_device_index(self._midi_out_name)]

    @staticmethod
    def get_device_index(device_name) -> int:
        # Set 'in use' parameter to 0 because it is not important in this case
        device_name = Midi._ignore_in_use(device_name)
        devices = [Midi._ignore_in_use(device) for device in get_devices()]
        # Return the index
        return devices.index(device_name)

    @staticmethod
    def _ignore_in_use(device: tuple) -> tuple:
        device = list(device)
        device[4] = 0
        return tuple(device)

    def set_queue(self, queue: Queue):
        self.queue = queue

    def get_io_ids(self) -> (int, int):
        return self._midi_in.device_id, self._midi_out.device_id

    def run(self) -> None:
        quick_mode = True
        while self._running:
            try:
                # Quick mode is used so that when there is no data coming, we can disable it as to
                # not hog the CPU by midi.poll()ing every cycle.
                # However, when there is more data coming after a poll we don't want to wait
                # because that would cause a lot of lag, for example when a knob is turned.
                # Thus, if there is more data queued, we disable quick mode and keep polling
                if not quick_mode:
                    # If we are not in quick mode: wait before proceeding
                    time.sleep(0.05)
                elif not self._midi_in.poll():
                    # If we are in quick mode but there is no data: disable quick mode
                    quick_mode = False

                # Send an "Active Sensing" message. If the device disconnects, this will throw an exception
                # noinspection PyBroadException
                try:
                    self._midi_out.write_short(0b11111110)
                except Exception as e:
                    # Sadly Pygame does not throw a specific Exception so we have to catch all of them :/
                    if any(x in str(e.args[0]) for x in ["PortMidi", "Bad Pointer"]):
                        self.try_to_reconnect = True
                        return

                if self._midi_in.poll():
                    # If there is data, enable quick mode
                    quick_mode = True

                    events = self._midi_in.read(10)
                    for event in events:
                        event = event[0]
                        status = event[0]
                        if status not in range(128, 239):
                            continue

                        channel = (status - 127) % 16
                        m_type_int = (status - 128) // 16
                        m_type = self.Type(m_type_int)
                        value1 = event[1]
                        value2 = event[2]

                        if self.queue is not None:
                            self.queue.put((channel, m_type, value1, value2))

                        function = self._get_event(channel, m_type, value1, value2)
                        if function is not None:
                            t = threading.Thread(target=function, args=((value1, value2), ))
                            t.setDaemon(True)
                            t.start()
            except (NameError, AttributeError, RuntimeError):
                # traceback.print_exc()
                return
            except midi.MidiException:
                pass

    def close(self) -> None:
        try:
            self._running = False
            self._midi_in.close()
            self._midi_out.close()
            midi.quit()
        except(NameError, AttributeError, RuntimeError):
            pass

    def add_event(self, function: Callable[[tuple], None], channel: int, midi_type: Type,
                  value1: int = None, value2: int = None) -> None:
        name = "Midi listener for " + str(channel) + " " + str(midi_type)

        if value1 is None:
            self._channel_map[channel][midi_type][-1] = function
        elif value2 is None:
            name += " " + str(value1)
            self._channel_map[channel][midi_type][value1][-1] = function
        else:
            name += " " + str(value1) + " " + str(value2)
            self._channel_map[channel][midi_type][value1][value2] = function

    def remove_event(self, channel: int, midi_type: Type, value1: int = None, value2: int = None) -> None:
        try:
            self._channel_map[channel][midi_type][value1].pop(value2)
            return
        except KeyError:
            pass
        try:
            self._channel_map[channel][midi_type][value1].pop(-1)
            return
        except KeyError:
            pass
        try:
            self._channel_map[channel][midi_type].pop(-1)
            return
        except KeyError:
            pass

    def _get_event(self, channel: int, midi_type: Type,
                   value1: int = None, value2: int = None) -> Callable[[tuple], None]:
        try:
            return self._channel_map[channel][midi_type][value1][value2]
        except KeyError:
            pass
        try:
            return self._channel_map[channel][midi_type][value1][-1]
        except KeyError:
            pass
        try:
            return self._channel_map[channel][midi_type][-1]
        except KeyError:
            pass

    def note_out(self, channel: int, note: int, on: bool = True):
        if on:
            self._midi_out.note_on(note, 127, channel)
        else:
            self._midi_out.note_off(note, 0, channel)
