import pandas as pd
import yaml
from mido import MidiTrack, merge_tracks

from midifile import MidiFile_


class CommuFile(MidiFile_):

    channel_count = -1
    
    def __init__(self, filename: str, track_role: str, instrument: str) -> None:
        super().__init__(filename)
        self._move_meta()
        self._set_role(track_role)
        with open('gm1.yaml') as f:
            inst_to_prog = yaml.safe_load(f)
        self._set_program(inst_to_prog[instrument])
        self._set_channel()

    def _move_meta(self) -> None:
        assert len(self.tracks) == 2
        assert [message.is_meta for message in self.tracks[0]]
        self.tracks = [merge_tracks(self.tracks)]

    def _set_role(self, role: str) -> None:
        self._get_track().name = role 

    def _set_program(self, program: int) -> None:
        for message in self._get_track():
            if message.type == 'program_change':
                message.program = program

    def _set_channel(self) -> None:
        CommuFile.channel_count += 1
        if CommuFile.channel_count == 10:  
            # channel 10 is reserved to percussions — there are no percussions in ComMU
            CommuFile.channel_count += 1
        for message in self._get_track():
            if message.type == 'program_change' or message.type == 'note_on':
                message.channel = CommuFile.channel_count

    def _get_track(self) -> MidiTrack:
        assert len(self.tracks) == 1
        return self.tracks[0]


if __name__ == '__main__':
    ds = pd.read_csv('dataset/commu_meta.csv')
    get_value = lambda id, col: ds[ds['id'] == id][col].values[0]

    ids = ['commu00001', 'commu00002', 'commu00003', 'commu00004']
    midis = [
        CommuFile(
            f'dataset/commu_midi/train/raw/{id}.mid',
            get_value(id, 'track_role'), 
            get_value(id, 'inst')
        ) for id in ids
    ]
    merged = midis[0].merge(midis[1]).concat(midis[2].merge(midis[3]))
    merged.save('merged.mid')
