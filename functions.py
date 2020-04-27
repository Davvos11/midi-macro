from midi import Midi
from pulseaudio import PulseControl
from mpris import MprisControl


def knob_1_1(values):
    with PulseControl() as pulse:
        pulse.set_stream_volume('AudioStream', values[1]/127)


def knob_1_8(values):
    with PulseControl() as pulse:
        pulse.set_stream_volume('Spotify', values[1]/127)


def pad_1_4(values):
    with MprisControl() as mpris:
        mpris.play_pause_auto()


class Functions:
    def __init__(self, midi: Midi):
        midi.add_event(knob_1_1, 1, midi.Type.CC, 1)
        midi.add_event(knob_1_8, 1, midi.Type.CC, 8)
        midi.add_event(pad_1_4, 1, midi.Type.NOTE_ON, 39)
