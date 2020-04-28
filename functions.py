from typing import Callable
from threading import Event
from typing import Optional

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
        """ Play/pause media on tap, skip song on double tap, previous song on triple tap """
        double_tap = self.__wait_for_next(self.pad_1_4)
        if double_tap is not None:
            if double_tap:
                triple_tap = self.__wait_for_next(self.pad_1_4)
                if triple_tap is not None:
                    if triple_tap:
                        self.mpris.previous_auto()
                    else:
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

    def __wait_for_next(self, function: Callable[[tuple], None], timeout: float = 0.3) -> Optional[bool]:
        """
        Waits until the provided function is called again, with a given timeout
        :param function: the function that called this
        :param timeout: timeout
        :return: None if this is the second call,
            False if this is the first call and there has not been a 2nd call within the timeout,
            True if this is the first call and there has been a 2nd call within the timeout
        """
        if function in self.__function_events:
            self.__function_events.get(function).set()
            return
        e = Event()
        self.__function_events[function] = e
        e.wait(timeout)
        self.__function_events.pop(function)
        return e.is_set()
