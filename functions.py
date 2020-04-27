from midi import Midi


def on_note(values):
    print(values)
    print('test1234')


class Functions:
    def __init__(self, midi: Midi):
        midi.add_event(on_note, 1, midi.Type.NOTE_ON)
