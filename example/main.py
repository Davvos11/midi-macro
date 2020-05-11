from midi_macro import MidiMacro
from example import functions

if __name__ == "__main__":
    m = MidiMacro(functions.Functions)
    m.run()
