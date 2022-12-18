from itertools import groupby
from typing import Any

import pandas as pd


class CommuDataset:

    def __init__(self) -> None:
        self.ds = pd.read_csv('dataset/commu_meta.csv')

    def get_chord_progression(self, id: str) -> str:
        return self._cleanup(self._get_value(id, 'chord_progressions'))

    def get_pitch_range(self, id: str) -> str:
        return self._get_value(id, 'pitch_range')

    def get_num_measures(self, id: str) -> int:
        return self._get_value(id, 'num_measures')

    def get_bpm(self, id: str) -> int:
        return self._get_value(id, 'bpm')

    def get_genre(self, id: str) -> str:
        return self._get_value(id, 'genre')

    def get_track_role(self, id: str) -> str:
        return self._get_value(id, 'track_role')

    def get_instrument(self, id: str) -> str:
        return self._get_value(id, 'inst')

    def get_sample_rhythm(self, id: str) -> str:
        return self._get_value(id, 'sample_rhythm')

    def get_time_signature(self, id: str) -> str:
        return self._get_value(id, 'time_signature')

    def get_min_velocity(self, id: str) -> int:
        return self._get_value(id, 'min_velocity')

    def get_max_velocity(self, id: str) -> int:
        return self._get_value(id, 'max_velocity')

    def get_split_data(self, id: str) -> str:
        return self._get_value(id, 'split_data')

    def _get_value(self, id: str, col: str) -> Any:
        return self.ds[self.ds['id'] == id][col].values[0]

    def _cleanup(chord_progression: str) -> str:
        # BEFORE:
        # "[['Am', 'Am', 'Am', 'Am', 'Am', 'Am', 'Am', 'Am', 
        #    'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 
        #    'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 
        #    'Dm', 'Dm', 'Dm', 'Dm', 'Dm', 'Dm', 'Dm', 'Dm', 
        #    'Am', 'Am', 'Am', 'Am', 'Am', 'Am', 'Am', 'Am', 
        #    'C', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 
        #    'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 
        #    'D', 'D', 'D', 'D', 'D', 'D', 'D', 'D']]"
        # AFTER:
        # 'Am-C-G-Dm-Am-C-G-D'
        return str(
            [key for key, _ in groupby(chord_progression[2:-2].replace('\'', '').split(', '))]
        )[1:-1].replace('\'', '').replace(', ', '-')


DSET = CommuDataset()
