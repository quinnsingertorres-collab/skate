# Stand-in for MBTA's internal HASTUS export, generated from public GTFS.
# Run from a folder containing g/ (unzipped MBTA_GTFS.zip) and h/ (empty). Writes hastus.zip.
import os; os.makedirs("h", exist_ok=True)
import csv, collections, zipfile
bus = {r['route_id'] for r in csv.DictReader(open('g/routes.txt')) if r['route_type']=='3'}
trips = {t['trip_id']: t for t in csv.DictReader(open('g/trips.txt')) if t['route_id'] in bus and t['block_id']}
first, last = {}, {}
for s in csv.DictReader(open('g/stop_times.txt')):
    tid = s['trip_id']
    if tid not in trips: continue
    seq = int(s['stop_sequence']); cp = s['checkpoint_id']
    if tid not in first or seq < first[tid][0]: first[tid] = (seq, s['departure_time'], cp)
    if tid not in last or seq > last[tid][0]: last[tid] = (seq, s['arrival_time'], cp)
hhmm = lambda t: ':'.join(t.split(':')[:2])
blocks = collections.defaultdict(list)
for tid, t in trips.items():
    if tid in first: blocks[(t['service_id'], t['block_id'].replace(' ', ''))].append(tid)
runs = {}
with open('h/trips.csv', 'w') as ft, open('h/activities.csv', 'w') as fa:
    ft.write('schedule_id;area;run_id;block_id;start_time;end_time;start_place;end_place;route_id;trip_id\n')
    fa.write('schedule_id;area;run_id;start_time;end_time;start_place;end_place;activity_type;activity_name\n')
    counter = collections.Counter()
    for (svc, blk), tids in sorted(blocks.items()):
        counter[svc] += 1; run = str(counter[svc])
        tids.sort(key=lambda x: first[x][1])
        for tid in tids:
            t = trips[tid]
            ft.write(f"{svc};100;{run};{blk};{hhmm(first[tid][1])};{hhmm(last[tid][1])};{first[tid][2]};{last[tid][2]};{t['route_id']};{tid}\n")
        a, b = tids[0], tids[-1]
        fa.write(f"{svc};100;{run};{hhmm(first[a][1])};{hhmm(last[b][1])};{first[a][2]};{last[b][2]};Operator;{blk}\n")
print(len(trips), 'trips', len(blocks), 'blocks')
z = zipfile.ZipFile('hastus.zip', 'w', zipfile.ZIP_DEFLATED); z.write('h/trips.csv', 'trips.csv'); z.write('h/activities.csv', 'activities.csv'); z.close()
