from midi import Midi
from pulseaudio import PulseControl
from mpris import MprisControl


class Functions:
    def knob_1_1(self, values):
        with PulseControl() as pulse:
            pulse.set_stream_volume('AudioStream', values[1] / 127)

    def knob_1_8(self, values):
        with PulseControl() as pulse:
            pulse.set_stream_volume('Spotify', values[1] / 127)

    def pad_1_4(self, values):
        self.mpris.play_pause_auto()

    def __init__(self, midi: Midi):
        self.midi = midi
        self.mpris = MprisControl()

        midi.add_event(self.knob_1_1, 1, midi.Type.CC, 1)
        midi.add_event(self.knob_1_8, 1, midi.Type.CC, 8)
        midi.add_event(self.pad_1_4, 1, midi.Type.NOTE_ON, 39)
