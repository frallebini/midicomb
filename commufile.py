from __future__ import annotations

import copy

import yaml
from mido import MidiFile, MidiTrack, merge_tracks


class CommuFile(MidiFile):

    channel_count = -1
    
    def __init__(self, id: str, split: str, track_role: str, instrument: str) -> None:
        super().__init__(f'dataset/commu_midi/{split}/raw/{id}.mid')
        self._preprocess(track_role, instrument)

    @property
    def track(self) -> MidiTrack:
        assert len(self.tracks) == 1
        return self.tracks[0]

    @property
    def duration(self) -> int:
        return sum(message.time for message in self.track)

    def shift(self, time: int) -> CommuFile:
        shifted = copy.deepcopy(self)
        for message in shifted.track:
            if message.type == 'program_change':
                message.time += time
        return shifted
        
    def _preprocess(self, track_role: str, instrument: str) -> None:
        with open('cfg/programs.yaml') as f:
             inst_to_prog = yaml.safe_load(f)
        self._move_meta()
        self._set_name(track_role)
        self._set_program(inst_to_prog[instrument])
        self._set_channel()

    def _move_meta(self) -> None:
        assert len(self.tracks) == 2
        assert [message.is_meta for message in self.tracks[0]]
        self.tracks = [merge_tracks(self.tracks)]

    def _set_name(self, name: str) -> None:
        self.track.name = name 

    def _set_program(self, program: int) -> None:
        for message in self.track:
            if message.type == 'program_change':
                message.program = program

    def _set_channel(self) -> None:
        CommuFile.channel_count += 1
        if CommuFile.channel_count == 10:  
            # channel 10 is reserved to percussions, but there are no percussions in ComMU
            CommuFile.channel_count += 1
        for message in self.track:
            if message.type == 'program_change' or message.type == 'note_on':
                message.channel = CommuFile.channel_count


def merge(midis: list[CommuFile]) -> MidiFile:
    merged = MidiFile()
    merged.tracks = [midi.track for midi in midis]
    return merged
