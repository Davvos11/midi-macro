import pulsectl


class PulseControl:
    def __init__(self, name: str = "Python control"):
        self.pulse = pulsectl.Pulse(name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pulse.close()

    def get_stream_list(self) -> [pulsectl.PulseSinkInfo]:
        return self.pulse.sink_input_list()

    def get_stream(self, name: str) -> pulsectl.PulseSinkInfo:
        for stream in self.get_stream_list():
            if stream.name == name:
                return stream

    def set_stream_volume(self, name: str, level: float) -> None:
        stream = self.get_stream(name)
        if stream is not None:
            self.pulse.volume_set_all_chans(stream, level)

    def mute_default_output(self, mute: bool = None) -> None:
        default_output = self.pulse.server_info().default_sink_name
        output_index = [p.index for p in self.pulse.sink_list() if p.name == default_output][0]

        if mute is None:
            mute = not self.pulse.sink_info(output_index).mute

        if mute:
            self.pulse.sink_mute(output_index, True)
        else:
            self.pulse.sink_mute(output_index, False)

    def mute_default_input(self, mute: bool = None) -> None:
        default_input = self.pulse.server_info().default_source_name
        input_index = [p.index for p in self.pulse.source_list() if p.name == default_input][0]

        if mute is None:
            mute = not self.pulse.source_info(input_index).mute

        if mute:
            self.pulse.source_mute(input_index, True)
        else:
            self.pulse.source_mute(input_index, False)
