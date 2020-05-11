# midi-macro
Simple script to run python functions on midi input, using an optional gui

How to run:
```python
from midi_macro import MidiMacro
import functions

if __name__ == "__main__":
    m = MidiMacro(functions.Functions)
    m.run()
    try:
        input('Press Enter to exit')
    except KeyboardInterrupt:
        pass
    m.close()
```
Optionally you can set gui=True if you want to have a window to choose a midi device.
You can also pass a Queue, which will get updated on midi events. 

In the `Functions` class you can add functions to run on midi events, for example:
```python
from midi_macro.midi import Midi
class Functions:
    @staticmethod
    # Functions should have a `values` argument which will
    # be a tuple containing both midi values (e.g. for a note: note and velocity)
    def function1(values):
        print(values)

    def __init__(self, midi: Midi):
        self.midi = midi

        # Map functions to midi events here:
        # parameters: function, midi_channel, midi_type, value1, value2)
        
        # Run function1 on all CC change on channel 1
        midi.add_event(self.function1, 1, midi.Type.CC)
        # Run function1 on CC 7 change on channel 1
        midi.add_event(self.function1, 1, midi.Type.CC, 7)
        # Run function1 on all note ON on channel 1
        midi.add_event(self.function1, 1, midi.Type.NOTE_ON)
        # Run function1 on note 37 ON on channel 1
        midi.add_event(self.function1, 1, midi.Type.NOTE_ON, 37)
``` 