import itertools
from collections import defaultdict, namedtuple
from typing import Dict, List

import yaml
from ortools.sat.python import cp_model

from commufile import CommuFile, merge


class MidiComb():

    def __init__(self, role_to_midis: Dict[str, List[CommuFile]], timestamp: str) -> None:
        self.role_to_midis = role_to_midis
        self.timestamp = timestamp

        self.role_to_tracks = defaultdict(list)
        self.role_to_tracks_opt = defaultdict(list)
        self.role_to_repeats = defaultdict(list)

        self.model = cp_model.CpModel()

        self._add_constraints()

    def _add_constraints(self) -> None:
        with open('cfg/midicomb.yaml') as f:
             cfg = yaml.safe_load(f)

        Track = namedtuple('Track', 'start end interval is_present')
        TrackPairInfo = namedtuple('TrackPairInfo', 't1_before_t2 t2_before_t1 overlap')
        
        role_to_intervals = defaultdict(list)
        track_to_overlaps = defaultdict(list)
        role_to_demand = cfg['demands']
        pairs_to_info = {}

        role_to_durations = {role: [midi.duration for midi in midis] for role, midis in self.role_to_midis.items()}
        horizon = sum(duration for durations in role_to_durations.values() for duration in durations)

        for role, durations in role_to_durations.items():
            for i, duration in enumerate(durations):
                suffix = f'{role}_{i}'
                
                start = self.model.NewIntVar(0, horizon, f'start_{suffix}')
                end = self.model.NewIntVar(0, horizon, f'end_{suffix}')
                is_present = self.model.NewBoolVar(f'is_present_{suffix}')
                interval = self.model.NewIntervalVar(start, duration, end, f'interval_{suffix}')

                start_opt = self.model.NewIntVar(0, horizon, f'start_opt_{suffix}')
                end_opt = self.model.NewIntVar(0, horizon, f'end_opt_{suffix}')
                is_present_opt = self.model.NewBoolVar(f'is_present_opt_{suffix}')
                interval_opt = self.model.NewOptionalIntervalVar(
                    start_opt, duration, end_opt, 
                    is_present_opt, f'interval_opt_{suffix}')

                self.role_to_tracks[role].append(Track(start, end, interval, is_present))
                self.role_to_tracks_opt[role].append(Track(start_opt, end_opt, interval_opt, is_present_opt))

                role_to_intervals[role].append(interval)
                role_to_intervals[role].append(interval_opt)

                self.role_to_repeats[role].append(is_present_opt)

                # play at least one sample for each track role
                self.model.Add(is_present == 1)
                # do not repeat riffs
                if role == 'riff':
                    self.model.Add(is_present_opt == 0)

        tracks = \
            [track for tracks in self.role_to_tracks.values() for track in tracks] + \
            [track for tracks in self.role_to_tracks_opt.values() for track in tracks]
        intervals = [interval for intervals in role_to_intervals.values() for interval in intervals]
        repeats = [repeat for repeats in self.role_to_repeats.values() for repeat in repeats]

        # samples with the same track role do not overlap
        for role in role_to_intervals.keys():
            self.model.AddNoOverlap(role_to_intervals[role])

        # play no more than x samples at the same time, where x depends on the track role
        demands = [role_to_demand[role] for role, intervals in role_to_intervals.items() for _ in intervals]
        self.model.AddCumulative(intervals, demands, cfg['capacity'])

        # if two samples overlap, make them start at the same time
        for t1, t2 in itertools.combinations(tracks, 2):
            name1 = t1.start.Name().replace('start_', '')
            name2 = t2.start.Name().replace('start_', '')
            
            t1_before_t2 = self.model.NewBoolVar(f'{name1}_before_{name2}')
            t2_before_t1 = self.model.NewBoolVar(f'{name2}_before_{name1}')
            overlap = self.model.NewBoolVar(f'overlap_{name1}_{name2}')
            
            self.model.Add(t1.end <= t2.start).OnlyEnforceIf(t1_before_t2)
            self.model.Add(t1.end > t2.start).OnlyEnforceIf(t1_before_t2.Not())
            self.model.Add(t2.end <= t1.start).OnlyEnforceIf(t2_before_t1)
            self.model.Add(t2.end > t1.start).OnlyEnforceIf(t2_before_t1.Not())

            self.model.AddBoolOr([
                t1_before_t2, 
                t2_before_t1, 
                t1.is_present.Not(), 
                t2.is_present.Not()]).OnlyEnforceIf(overlap.Not())
            self.model.AddBoolAnd([
                t1_before_t2.Not(), 
                t2_before_t1.Not(), 
                t1.is_present, 
                t2.is_present]).OnlyEnforceIf(overlap)
            self.model.Add(t1.start == t2.start).OnlyEnforceIf(overlap)

            pairs_to_info[t1, t2] = TrackPairInfo(t1_before_t2, t2_before_t1, overlap)
            track_to_overlaps[t1].append(overlap)
            track_to_overlaps[t2].append(overlap)

        # if a sample is played on its own, leave some silence before it begins and after it ends
        # (it sounds more dramatic and less out of place)
        for track in tracks:
            alone = self.model.NewBoolVar(f'alone_{track.start.Name().replace("start_", "")}')
            self.model.AddBoolAnd([var.Not() for var in track_to_overlaps[track]]).OnlyEnforceIf(alone)
            self.model.AddBoolOr(track_to_overlaps[track]).OnlyEnforceIf(alone.Not())

            for (t1, t2), info in pairs_to_info.items():
                if t1 is track or t2 is track:
                    self.model.Add(t2.start >= t1.end + cfg['padding']).OnlyEnforceIf([info.t1_before_t2, alone])
                    self.model.Add(t1.start >= t2.end + cfg['padding']).OnlyEnforceIf([info.t2_before_t1, alone])

        # repeat half of the samples
        self.model.Add(sum(repeats) == len(repeats)//2)

        # objective
        makespan = self.model.NewIntVar(0, horizon, 'makespan')
        self.model.AddMaxEquality(makespan, [track.end for track in tracks])
        self.model.Minimize(makespan)

    def solve(self) -> None:
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            shifted_midis = []
            
            for role, midis in self.role_to_midis.items():
                for i, midi in enumerate(midis):
                    shifted_midis.append(midi.shift(solver.Value(self.role_to_tracks[role][i].start)))
                    
                    if solver.Value(self.role_to_repeats[role][i]):
                        shifted_midis.append(midi.shift(solver.Value(self.role_to_tracks_opt[role][i].start)))

            merged = merge(shifted_midis)
            merged.save(f'out/{self.timestamp}/tune.mid')

        elif status == cp_model.INFEASIBLE:
            print(f'No solution found: the problem was proven infeasible')
        elif status == cp_model.MODEL_INVALID:
            print('No solution found: invalid model')
        else:
            print('No solution found: the solver was stopped before reaching an endpoint')
