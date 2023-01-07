import itertools
from collections import defaultdict, namedtuple
from datetime import datetime
from pathlib import Path

from ortools.sat.python import cp_model

from commudset import DSET
from midifile import MidiFile_


bpm = 130
key = 'aminor'
time_signature = '4/4'
num_measures = 8
genre = 'newage'
rhythm = 'standard'
chord_progression = 'Am-F-C-G-Am-F-C-G'

now = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
Path(f'out/{now}').mkdir(parents=True)

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
horizon = sum(time for times in role_to_times.values() for time in times)
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

tracks = [track for tracks in role_to_tracks.values() for track in tracks]
intervals = [interval for intervals in role_to_intervals.values() for interval in intervals]

# samples with same track role do not overlap
for track_role in role_to_intervals.keys():
    model.AddNoOverlap(role_to_intervals[track_role])

# play no more than x samples at the same time
role_to_demand = {
    'main_melody': 3,
    'sub_melody': 3,
    'riff': 3,
    'accompaniment': 2,
    'pad': 1,
    'bass': 1
}
demands = [role_to_demand[role] for role, intervals in role_to_intervals.items() for _ in intervals]
model.AddCumulative(intervals, demands, 6)

# if two samples overlap, make them start at the same time
for t1, t2 in itertools.combinations(tracks, 2):
    name1 = t1.start.Name().replace('start_', '')
    name2 = t2.start.Name().replace('start_', '')
    
    t1_before_t2 = model.NewBoolVar(f'{name1}_before_{name2}')
    t2_before_t1 = model.NewBoolVar(f'{name2}_before_{name1}')
    overlap = model.NewBoolVar(f'overlap_{name1}_{name2}')
    
    model.Add(t1.end <= t2.start).OnlyEnforceIf(t1_before_t2)
    model.Add(t1.end > t2.start).OnlyEnforceIf(t1_before_t2.Not())
    model.Add(t2.end <= t1.start).OnlyEnforceIf(t2_before_t1)
    model.Add(t2.end > t1.start).OnlyEnforceIf(t2_before_t1.Not())

    model.AddBoolOr([t1_before_t2, t2_before_t1]).OnlyEnforceIf(overlap.Not())
    model.AddBoolAnd([t1_before_t2.Not(), t2_before_t1.Not()]).OnlyEnforceIf(overlap)
    model.Add(t1.start == t2.start).OnlyEnforceIf(overlap)

    # otherwise, leave a minimum amount of space between them
    # model.Add(t2.start >= t1.end + 100).OnlyEnforceIf([t1_before_t2, overlap.Not()])
    # model.Add(t1.start >= t2.end + 100).OnlyEnforceIf([t2_before_t1, overlap.Not()])

makespan = model.NewIntVar(0, horizon, 'makespan')
model.AddMaxEquality(makespan, [track.end for track in tracks])
model.Minimize(makespan)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    midis = []
    for role, tracks in role_to_tracks.items():
        for i, track in enumerate(tracks):
            midis.append(role_to_midis[role][i].shift(solver.Value(track.start)))
    merged = MidiFile_.merge(midis)
    merged.save(f'out/{now}/merged.mid')

elif status == cp_model.INFEASIBLE:
    print(f'No solution found: the problem was proven infeasible')
elif status == cp_model.MODEL_INVALID:
    print('No solution found: invalid model')
else:
    print('No solution found: the solver was stopped before reaching an endpoint')
