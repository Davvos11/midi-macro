from typing import Callable
from threading import Event
from typing import Optional

from midi_macro.midi import Midi
from pulseaudio import PulseControl
from mpris import MprisControl


class Functions:
    @staticmethod
    def __get_discord_stream():
        with PulseControl() as pulse:
            return pulse.get_stream_by_prop(('application.process.binary', 'Discord'),
                                            ('application.name', 'WEBRTC VoiceEngine'))

    @staticmethod
    def __get_spotify_stream():
        with PulseControl() as pulse:
            return pulse.get_stream('Spotify')

    def knob_1_7(self, values):
        """ Controls Discord volume"""
        with PulseControl() as pulse:
            pulse.set_stream_volume(self.__get_discord_stream(), values[1] / 127)

    def knob_1_8(self, values):
        """ Controls Spotify volume"""
        with PulseControl() as pulse:
            pulse.set_stream_volume(self.__get_spotify_stream(), values[1] / 127)

    def knobs_1(self, values):
        """ Controls all application volume except for Spotify and Discord"""
        with PulseControl() as pulse:
            try:
                ign_streams = []
                try:
                    ign_streams.append(self.__get_spotify_stream().index)
                    ign_streams.append(self.__get_discord_stream().index)
                except (AttributeError, IndexError):
                    pass

                streams = [s for s in pulse.get_stream_list() if s.index not in ign_streams]
                pulse.set_stream_volume(streams[values[0] - 1], values[1] / 127)
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

    def pad_1_3(self, values):
        """ Toggle mute on the default input"""
        with PulseControl() as pulse:
            pulse.mute_default_input()

    def pad_1_2(self, values):
        """ Toggle mute on the default output"""
        with PulseControl() as pulse:
            pulse.mute_default_output()

    def __init__(self, midi: Midi):
        self.midi = midi
        self.mpris = MprisControl()
        self.__function_events = dict()

        midi.add_event(self.knobs_1, 1, midi.Type.CC)
        midi.add_event(self.knob_1_8, 1, midi.Type.CC, 8)
        midi.add_event(self.knob_1_7, 1, midi.Type.CC, 7)
        midi.add_event(self.pad_1_2, 1, midi.Type.NOTE_ON, 37)
        midi.add_event(self.pad_1_3, 1, midi.Type.NOTE_ON, 38)
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
