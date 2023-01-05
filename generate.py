import itertools
from collections import defaultdict, namedtuple
from datetime import datetime
from pathlib import Path

from ortools.sat.python import cp_model

from commudset import DSET
from midifile import MidiFile_


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        super().__init__()
        self.__variables = variables

    def on_solution_callback(self):
        for v in self.__variables:
            print(f'{v}={self.Value(v)}')


now = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
Path(f'out/{now}').mkdir(parents=True)

bpm = 130
key = 'aminor'
time_signature = '4/4'
num_measures = 8
genre = 'newage'
rhythm = 'standard'
chord_progression = 'Am-F-C-G-Am-F-C-G'

role_to_midis = DSET.get_midis(
    bpm, 
    key, 
    time_signature, 
    num_measures, 
    genre, 
    rhythm, 
    chord_progression,
    now)

role_to_times = {role: [midi.get_track_time() for midi in midis] for role, midis in role_to_midis.items()}
horizon = sum(t for times in role_to_times.values() for t in times)

model = cp_model.CpModel()

Track = namedtuple('Track', 'start end interval')
role_to_tracks = defaultdict(list)
role_to_intervals = defaultdict(list)

for track_role, times in role_to_times.items():
    for i, time in enumerate(times):
        suffix = f'_{track_role}_{i}'
        
        start = model.NewIntVar(0, horizon, 'start' + suffix)
        end = model.NewIntVar(0, horizon, 'end' + suffix)
        interval = model.NewIntervalVar(start, time, end, 'interval' + suffix)
        
        role_to_tracks[track_role].append(Track(start, end, interval))
        role_to_intervals[track_role].append(interval)

tracks = [t for tracks in role_to_tracks.values() for t in tracks]
intervals = [i for intervals in role_to_intervals.values() for i in intervals]

# samples with same track role do not overlap
for track_role in DSET.get_track_roles():
    model.AddNoOverlap(role_to_intervals[track_role])

# play no more than two samples at the same time
model.AddCumulative(intervals, [1]*len(intervals), 2)

# if two samples overlap, make them start at the same time
overlaps = []
for t1, t2 in itertools.combinations(tracks, 2):
    name1 = t1.start.Name().replace('start_', '')
    name2 = t2.start.Name().replace('start_', '')
    
    t1_before_t2 = model.NewBoolVar(f'{name1}_before_{name2}')
    t2_before_t1 = model.NewBoolVar(f'{name2}_before_{name1}')
    overlap = model.NewBoolVar(f'overlap_{name1}_{name2}')
    overlaps.append(overlap)
    
    model.Add(t1.end <= t2.start).OnlyEnforceIf(t1_before_t2)
    model.Add(t1.end > t2.start).OnlyEnforceIf(t1_before_t2.Not())
    model.Add(t2.end <= t1.start).OnlyEnforceIf(t2_before_t1)
    model.Add(t2.end > t1.start).OnlyEnforceIf(t2_before_t1.Not())
    model.AddBoolOr([t1_before_t2, t2_before_t1]).OnlyEnforceIf(overlap.Not())
    model.AddBoolAnd([t1_before_t2.Not(), t2_before_t1.Not()]).OnlyEnforceIf(overlap)
    model.Add(t1.start == t2.start).OnlyEnforceIf(overlap)

makespan = model.NewIntVar(0, horizon, 'makespan')
model.AddMaxEquality(makespan, [t.end for t in tracks])
model.Minimize(makespan)

solver = cp_model.CpSolver()
printer = SolutionPrinter(overlaps)
status = solver.Solve(model, printer)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    midis = []
    for role, tracks in role_to_tracks.items():
        for i, track in enumerate(tracks):
            midis.append(role_to_midis[role][i].shift(solver.Value(track.start)))
    merged = MidiFile_.merge(midis)
    merged.save(f'out/{now}/merged.mid')
else:
    print(f'No solution found: {status}')
