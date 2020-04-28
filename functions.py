from threading import Event

from midi import Midi
from pulseaudio import PulseControl
from mpris import MprisControl


class Functions:
    def knob_1_8(self, values):
        """ Controls Spotify volume"""
        with PulseControl() as pulse:
            pulse.set_stream_volume('Spotify', values[1] / 127)

    def knobs_1(self, values):
        """ Controls all application volume except for Spotify """
        with PulseControl() as pulse:
            try:
                stream_names = [stream.name for stream in pulse.get_stream_list() if stream.name != 'Spotify']
                pulse.set_stream_volume(stream_names[values[0]-1], values[1] / 127)
            except IndexError:
                pass

    def pad_1_4(self, values):
        if self.pad_1_4 in self.__function_events:
            self.__function_events.get(self.pad_1_4).set()
            return
        e = Event()
        self.__function_events[self.pad_1_4] = e
        e.wait(0.3)
        self.__function_events.pop(self.pad_1_4)
        if e.is_set():
            self.mpris.next_auto()
        else:
            self.mpris.play_pause_auto()

    def __init__(self, midi: Midi):
        self.midi = midi
        self.mpris = MprisControl()
        self.__function_events = dict()

        midi.add_event(self.knobs_1, 1, midi.Type.CC)
        midi.add_event(self.knob_1_8, 1, midi.Type.CC, 8)
        midi.add_event(self.pad_1_4, 1, midi.Type.NOTE_ON, 39)
