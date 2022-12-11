from typing import Any

import pandas as pd


class CommuDataset:

    def __init__(self) -> None:
        self.ds = pd.read_csv('dataset/commu_meta.csv')

    def get_chord_progressions(self, id: str) -> str:
        return self._get_value(id, 'chord_progressions')

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

    def get_inst(self, id: str) -> str:
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


DS = CommuDataset()
