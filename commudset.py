from collections import defaultdict
from itertools import groupby
import random
from typing import Any

import numpy as np
import pandas as pd

from commufile import CommuFile


class CommuDataset:

    def __init__(self) -> None:
        self.df = pd.read_csv('dataset/commu_meta.csv')

        self.df.drop(columns=self.df.columns[0], inplace=True)
        self.df.rename(columns={
            'audio_key': 'key',
            'chord_progressions': 'chord_progression',
            'inst': 'instrument',
            'sample_rhythm': 'rhythm',
            'split_data': 'split'
        }, inplace=True)
        self._clean_chord_progression()

    def get_samples(self,
                    bpm: int, 
                    key: str, 
                    time_signature: str, 
                    num_measures: int, 
                    genre: str, 
                    rhythm: str, 
                    chord_progression: str) -> list[CommuFile]:
        track_roles = self.get_track_roles()
        valid_roles = set(track_roles)

        track_count = 0
        role_counts = defaultdict(int)
        midis = []
        indexes = []

        while track_count < len(track_roles):
            try:
                track_role = random.choice(list(valid_roles))
                sample = self.sample(
                    track_role, 
                    bpm, 
                    key, 
                    time_signature, 
                    num_measures, 
                    genre, 
                    rhythm, 
                    chord_progression)
            except IndexError:  # no more valid track roles
                break
            except ValueError:  # no sample satifies the query
                valid_roles = valid_roles - set(track_role)
                continue
            if sample.index.item() in indexes:  # the track has already been sampled
                continue
            midi = CommuFile(
                sample.id.item(), 
                sample.split.item(), 
                track_role, 
                sample.instrument.item())

            track_count += 1
            role_counts[track_role] += 1
            midis.append(midi)
            indexes.append(sample.index.item())
            midi.save(f'out/{track_role}_{role_counts[track_role]}.mid')

        return midis

    def sample(self, 
               track_role: str, 
               bpm: int, 
               key: str, 
               time_signature: str, 
               num_measures: int, 
               genre: str, 
               rhythm: str, 
               chord_progression: str) -> pd.DataFrame:
        return self.df[
            (self.df.track_role == track_role) &
            (self.df.bpm == bpm) &
            (self.df.key == key) &
            (self.df.time_signature == time_signature) &
            (self.df.num_measures == num_measures) &
            (self.df.genre == genre) &
            (self.df.rhythm == rhythm) &
            (self.df.chord_progression == chord_progression)
        ].sample()
    
    def get_track_roles(self) -> np.ndarray:
        return self.df.track_role.unique()

    def get_track_role(self, id: str) -> str:
        return self._get_value(id, 'track_role')

    def get_instrument(self, id: str) -> str:
        return self._get_value(id, 'instrument')

    def _get_value(self, id: str, col: str) -> Any:
        return self.df[self.df.id == id][col].item()

    def _clean_chord_progression(self) -> None:
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
        self.df.chord_progression = self.df.chord_progression.apply(
            lambda cp: str([key for key, _ in groupby(cp[2:-2].replace('\'', '').split(', '))]
                )[1:-1].replace('\'', '').replace(', ', '-'))


DSET = CommuDataset()
