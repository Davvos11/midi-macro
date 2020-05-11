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

    def get_stream_by_prop(self, *props: (str, str)) -> pulsectl.PulseSinkInfo:
        candidate_sets = []

        # Loop through properties and generate sets of candidates that have those properties
        for i, prop in enumerate(props):
            candidate_sets.append([])
            for stream in self.get_stream_list():
                if stream.proplist[prop[0]] == prop[1]:
                    candidate_sets[i].append(stream)

        result = []
        # Get intersection of candidate sets
        for i, candidates in enumerate(candidate_sets):
            if i == 0:
                result = candidates
                continue
            for r in result:
                if r.index not in [c.index for c in candidates]:
                    result.remove(r)
        return result[0]

    def set_stream_volume(self, stream: pulsectl.PulseSinkInfo, level: float) -> None:
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
