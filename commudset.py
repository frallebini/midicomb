from datetime import datetime
import random
from collections import defaultdict
from itertools import groupby
from typing import Any

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

    def get_midis(
            self,
            bpm: int, 
            key: str, 
            time_signature: str, 
            num_measures: int, 
            genre: str, 
            rhythm: str, 
            chord_progression: str,
            now: datetime) -> dict[str, list[CommuFile]]:
        df_samples = self.get_sample_foreach_track_role(
            bpm, 
            key, 
            time_signature, 
            num_measures, 
            genre, 
            rhythm, 
            chord_progression)
        
        valid_roles = set(df_samples.track_role.unique()) - {'riff'}  # we do not want more than one riff
        midi_count = len(df_samples)
        indexes = df_samples.index.tolist()

        while midi_count < len(self.get_track_roles()):
            try:
                track_role = random.choice(list(valid_roles))
                sample = self.get_sample(
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
            if sample.index.item() in indexes:  # do not sample same entry twice
                continue
            
            df_samples = pd.concat([df_samples, sample])
            indexes.append(sample.index.item())
            midi_count += 1
        
        role_counts = defaultdict(int)
        role_to_midis = defaultdict(list)

        for i in df_samples.index:
            sample = df_samples[df_samples.index == i]
            track_role = sample.track_role.item()
            name = f'{track_role}_{role_counts[track_role]}'
            midi = CommuFile(
                sample.id.item(), 
                sample.split.item(), 
                name, 
                sample.instrument.item())
            midi.save(f'out/{now}/{name}.mid')
            role_counts[track_role] += 1
            role_to_midis[track_role].append(midi)

        return role_to_midis

    def get_sample_foreach_track_role(
            self, 
            bpm: int, 
            key: str, 
            time_signature: str, 
            num_measures: int, 
            genre: str, 
            rhythm: str, 
            chord_progression: str) -> pd.DataFrame:
        df_query = self.df[
            (self.df.bpm == bpm) &
            (self.df.key == key) &
            (self.df.time_signature == time_signature) &
            (self.df.num_measures == num_measures) &
            (self.df.genre == genre) &
            (self.df.rhythm == rhythm) &
            (self.df.chord_progression == chord_progression)]
        samples = []
        for role in df_query.track_role.unique():
            df_role = df_query[df_query.track_role == role]
            samples.append(df_role.sample())
        return pd.concat(samples)

    def get_sample(
            self, 
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
    
    def get_track_roles(self) -> list[str]:
        return self.df.track_role.unique().tolist()

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