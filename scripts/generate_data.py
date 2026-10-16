"""Generate the Metro Operations relational dataset (18 tables) as CSV files.

The schema mirrors the Assessment 2 SQLite design exactly (one CSV per table,
same column names). The original sample rows (T101-T104, TR001-TR005,
Disruption 1 'Train Fault' affecting Trip 3 with 380 passengers) are preserved
and the dataset is expanded to a realistic 14-day operating window so that
graph analytics are meaningful.
"""
import csv, os, random
from datetime import date, datetime, timedelta

random.seed(21)
OUT = os.path.join(os.path.dirname(__file__), "..", "csv")
os.makedirs(OUT, exist_ok=True)

def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])

# ------------------------------------------------------------------ Stations
# (code, name, suburb, type, accessibility)
ST = [
    ("CHW", "Chatswood", "Chatswood", "Elevated", "Full"),
    ("ART", "Artarmon", "Artarmon", "Surface", "Partial"),
    ("STL", "St Leonards", "St Leonards", "Underground", "Full"),
    ("CRN", "Crows Nest", "Crows Nest", "Underground", "Full"),
    ("VCX", "Victoria Cross", "North Sydney", "Underground", "Full"),
    ("BRG", "Barangaroo", "Barangaroo", "Underground", "Full"),
    ("WYN", "Wynyard", "Sydney CBD", "Underground", "Full"),
    ("TWH", "Town Hall", "Sydney CBD", "Underground", "Full"),
    ("CEN", "Central", "Haymarket", "Surface", "Full"),
    ("RDF", "Redfern", "Redfern", "Surface", "Partial"),
    ("WTL", "Waterloo", "Waterloo", "Underground", "Full"),
    ("SYD", "Sydenham", "Sydenham", "Surface", "Partial"),
    ("GSQ", "Green Square", "Zetland", "Underground", "Full"),
    ("MSC", "Mascot", "Mascot", "Underground", "Full"),
    ("DOM", "Domestic Airport", "Mascot", "Underground", "Full"),
    ("INT", "International Airport", "Mascot", "Underground", "Full"),
    ("WOL", "Wolli Creek", "Wolli Creek", "Elevated", "Full"),
    ("ASH", "Ashfield", "Ashfield", "Surface", "Limited"),
    ("BUR", "Burwood", "Burwood", "Surface", "Partial"),
    ("STR", "Strathfield", "Strathfield", "Surface", "Partial"),
    ("LID", "Lidcombe", "Lidcombe", "Surface", "Partial"),
    ("GRV", "Granville", "Granville", "Surface", "Limited"),
    ("HRP", "Harris Park", "Harris Park", "Surface", "Limited"),
    ("PAR", "Parramatta", "Parramatta", "Elevated", "Full"),
    ("WMD", "Westmead", "Westmead", "Surface", "Full"),
    ("CCW", "Concord West", "Concord West", "Surface", "Limited"),
    ("RHD", "Rhodes", "Rhodes", "Elevated", "Full"),
    ("MDB", "Meadowbank", "Meadowbank", "Surface", "Partial"),
    ("EPP", "Epping", "Epping", "Underground", "Full"),
    ("MQU", "Macquarie University", "Macquarie Park", "Underground", "Full"),
    ("MQP", "Macquarie Park", "Macquarie Park", "Underground", "Full"),
    ("NRY", "North Ryde", "North Ryde", "Underground", "Full"),
]
SID = {c: i + 1 for i, (c, *_r) in enumerate(ST)}

# Physical line sequences (all-stops order) with segment distances (km)
LINES = {
    1: ("L1", "Harbour Line", ["SYD", "WTL", "RDF", "CEN", "TWH", "WYN", "BRG", "VCX", "CRN", "STL", "ART", "CHW"],
        [2.1, 1.6, 1.3, 1.1, 0.8, 1.0, 1.9, 1.2, 1.0, 1.7, 2.0]),
    2: ("L2", "Airport Line", ["WYN", "TWH", "CEN", "GSQ", "MSC", "DOM", "INT", "WOL", "SYD"],
        [0.8, 1.1, 2.6, 2.4, 1.5, 2.3, 2.9, 1.8]),
    3: ("L3", "Western Line", ["TWH", "CEN", "RDF", "ASH", "BUR", "STR", "LID", "GRV", "HRP", "PAR", "WMD"],
        [1.1, 1.3, 5.2, 2.3, 1.9, 3.6, 3.1, 1.8, 1.4, 2.0]),
    4: ("L4", "Northern Line", ["STR", "CCW", "RHD", "MDB", "EPP", "MQU", "MQP", "NRY", "CHW"],
        [3.2, 1.5, 2.2, 4.1, 2.6, 1.2, 1.6, 4.4]),
}
line_of_station = {}
for lid, (_, _, seq, _) in LINES.items():
    for s in seq:
        line_of_station.setdefault(s, set()).add(lid)

station_rows = []
for code, name, suburb, stype, acc in ST:
    inter = len(line_of_station[code]) > 1
    station_rows.append([SID[code], code, name, suburb, "Interchange Hub" if inter else stype,
                         1 if inter else 0, acc])
write("station.csv", ["StationID", "StationCode", "StationName", "Suburb", "StationType",
                      "IsInterchange", "AccessibilityRating"], station_rows)

# Platforms (weak entity: StationID + PlatformNo)
n_plat = {}
plat_rows = []
for code, *_ in ST:
    k = len(line_of_station[code])
    n = 6 if code == "CEN" else (2 * k if k > 1 else 2)
    n_plat[code] = n
    for p in range(1, n + 1):
        status = "Operational"
        if (code, p) in {("RDF", 2), ("ASH", 1)}:
            status = "Restricted"
        plat_rows.append([SID[code], p, random.choice([160.0, 170.0, 180.0, 210.0]), status])
write("platform.csv", ["StationID", "PlatformNo", "PlatformLengthM", "PlatformStatus"], plat_rows)

# MetroLine
line_rows = [[lid, c, n, round(sum(d), 1), "Operational"] for lid, (c, n, _, d) in LINES.items()]
write("metro_line.csv", ["LineID", "LineCode", "LineName", "RouteLengthKm", "OperatingStatus"], line_rows)

# ------------------------------------------------------------------ Routes
seg = {}
for lid, (_, _, seq, d) in LINES.items():
    for a, b, km in zip(seq, seq[1:], d):
        seg[(a, b)] = km
        seg[(b, a)] = km

def build(seq_all, stops):
    """cumulative km for a stopping subset of an all-stops sequence"""
    cum, out, prev = 0.0, [], None
    for s in seq_all:
        if prev is not None:
            cum += seg[(prev, s)]
        prev = s
        if s in stops:
            out.append((s, round(cum, 1)))
    return out

def rev(l):
    return list(reversed(l))

L = {k: v[2] for k, v in LINES.items()}
# RouteID: (code, name, line, direction, stopping pattern, all-stops seq, stopping set)
ROUTES = {
    1: ("R01", "Harbour Northbound", 1, "NB", "All Stops", L[1], set(L[1])),
    2: ("R02", "Harbour Southbound", 1, "SB", "All Stops", rev(L[1]), set(L[1])),
    3: ("R03", "Airport Express", 2, "OB", "Express", L[2], {"WYN", "TWH", "CEN", "DOM", "INT"}),
    4: ("R04", "Airport Outbound", 2, "OB", "All Stops", L[2], set(L[2])),
    5: ("R05", "Airport Inbound", 2, "IB", "All Stops", rev(L[2]), set(L[2])),
    6: ("R06", "Western Westbound", 3, "WB", "All Stops", L[3], set(L[3])),
    7: ("R07", "Western Eastbound", 3, "EB", "All Stops", rev(L[3]), set(L[3])),
    8: ("R08", "Northern Northbound", 4, "NB", "All Stops", L[4], set(L[4])),
    9: ("R09", "Northern Southbound", 4, "SB", "All Stops", rev(L[4]), set(L[4])),
    10: ("R10", "Western Express", 3, "WB", "Limited Stops", L[3], {"TWH", "CEN", "STR", "PAR", "WMD"}),
}
route_rows, rs_rows, route_stops, route_dur, cum_min = [], [], {}, {}, {}
for rid, (rc, rn, lid, dc, sp, seq, stops) in ROUTES.items():
    st = build(seq, stops)
    route_stops[rid] = st
    t, out, prevkm = 0.0, [], 0.0
    for i, (s, km) in enumerate(st):
        if i > 0:
            t += (km - prevkm) / 42.0 * 60 + 0.6  # run time + accel
        dwell = 60 if len(line_of_station[s]) > 1 else 35
        out.append(round(t, 1))
        t += dwell / 60.0
        prevkm = km
        rs_rows.append([rid, i + 1, SID[s], km, dwell])
    cum_min[rid] = out
    route_dur[rid] = int(round(out[-1]))
    route_rows.append([rid, rc, lid, dc, SID[st[0][0]], route_dur[rid], sp, rn])
write("route.csv", ["RouteID", "RouteCode", "LineID", "DirectionCode", "OriginStationID",
                    "ScheduledDurationMin", "StoppingPattern", "RouteName"], route_rows)
write("route_stop.csv", ["RouteID", "StopSequence", "StationID", "CumulativeDistanceKm", "DwellTimeSec"], rs_rows)

def platform_for(rid, scode):
    lid = ROUTES[rid][2]
    dirn = 0 if ROUTES[rid][3] in ("NB", "OB", "WB") else 1
    lines = sorted(line_of_station[scode])
    base = lines.index(lid) * 2 if len(lines) > 1 else 0
    return (base + dirn) % n_plat[scode] + 1

# ------------------------------------------------------------------ Trains
train_rows = []
TRAIN_LINE = {}
for i in range(24):
    tid = i + 1
    fleet = f"T{101 + i}"
    home = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4][i % 12]
    TRAIN_LINE[tid] = home
    comm = date(2014 + (i % 9), 1 + (i * 5) % 12, 1 + (i * 7) % 27)
    age = (date(2026, 9, 14) - comm).days / 365.25
    odo = round(age * random.uniform(16500, 21500) + random.uniform(0, 3000), 1)
    cap = random.choice([384, 400, 420, 432])
    status = "In Service"
    overhaul = (comm + timedelta(days=int(365 * random.uniform(3, 6)))) if age > 4 else None
    train_rows.append([tid, fleet, comm.isoformat(), odo, cap, status, overhaul.isoformat() if overhaul else None])
# Preserve Assessment 2 facts
train_rows[0][4] = 420                     # T101 capacity -> 380 pax at 91%
train_rows[2][3] = 176540.8                # T103 odometer from A2
train_rows[2][5] = "Maintenance"
train_rows[16][5] = "Out of Service"       # T117
train_rows[21][5] = "Standby"              # T122
train_rows[9][5] = "Maintenance"           # T110
write("train.csv", ["TrainID", "FleetNumber", "CommissionedDate", "OdometerKm", "SeatedCapacity",
                    "ServiceStatus", "LastOverhaulDate"], train_rows)
CAP = {r[0]: r[4] for r in train_rows}

# ------------------------------------------------------------------ Staff
FIRST = ["Liam", "Olivia", "Noah", "Charlotte", "Jack", "Amelia", "William", "Isla", "Oliver", "Mia",
         "Henry", "Ava", "Leo", "Grace", "Lucas", "Chloe", "Thomas", "Zoe", "James", "Ruby", "Ethan",
         "Sophie", "Arjun", "Priya", "Daniel", "Hannah", "Ryan", "Emily", "Samuel", "Lily", "Nathan",
         "Ella", "Ben", "Aisha", "Kai", "Mei", "Raj", "Sara", "Tom", "Nina", "Alex", "Jade", "Sam", "Ivy",
         "Max", "Lucy", "Omar", "Rosa", "Hugo", "Tara"]
LAST = ["Nguyen", "Smith", "Patel", "Williams", "Brown", "Chen", "Wilson", "Taylor", "Singh", "Martin",
        "Kelly", "Lee", "Walker", "Harris", "Wong", "King", "Shrestha", "Wright", "Thompson", "Khan",
        "White", "Clarke", "Robinson", "Hall", "Young", "Allen", "Scott", "Green", "Baker", "Adams",
        "Hill", "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner", "Torres",
        "Parker", "Collins", "Edwards", "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Gupta", "Bell", "Ward"]
N_DRV, N_TECH = 36, 14
staff_rows, phone_rows, drv_rows, tech_rows = [], [], [], []
DRIVER_HOME = {}
for i in range(N_DRV + N_TECH):
    sid = i + 1
    cat = "Driver" if i < N_DRV else "Technician"
    hire = date(2010 + (i * 3) % 15, 1 + (i * 7) % 12, 1 + (i * 11) % 27)
    staff_rows.append([sid, f"E{1001 + i}", FIRST[i], LAST[i], hire.isoformat(),
                       random.choice(["Full-time"] * 4 + ["Part-time", "Contract"]), cat])
    phone_rows.append([sid, f"04{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"])
    if i % 3 == 0:
        phone_rows.append([sid, f"02 9{random.randint(100, 999)} {random.randint(1000, 9999)}"])
    if cat == "Driver":
        DRIVER_HOME[sid] = 1 + (i % 4)
        exp = date(2026, 10, 1) + timedelta(days=random.randint(-10, 900))
        drv_rows.append([sid, f"DL{720000 + i * 37}", exp.isoformat(),
                         random.choice(["Level 1", "Level 2", "Level 2", "Level 3"]),
                         round((date(2026, 9, 14) - hire).days / 365.25 * random.uniform(1300, 1650), 1)])
TRADES = ["Electrical", "Mechanical", "Brakes", "Signalling", "HVAC", "Doors", "Traction"]
TECH_TRADE = {}
for j, sid in enumerate(range(N_DRV + 1, N_DRV + N_TECH + 1)):
    tr = TRADES[j % len(TRADES)]
    TECH_TRADE[sid] = tr
    tech_rows.append([sid, tr, 1 + j % 4, f"TK-{5000 + j * 13}"])
write("staff.csv", ["StaffID", "EmployeeNumber", "FirstName", "LastName", "HireDate", "EmploymentType",
                    "StaffCategory"], staff_rows)
write("staff_phone.csv", ["StaffID", "PhoneNumber"], phone_rows)
write("driver.csv", ["StaffID", "LicenceNumber", "LicenceExpiryDate", "CertificationLevel",
                     "AccumulatedServiceHours"], drv_rows)
write("technician.csv", ["StaffID", "TradeSpecialisation", "SafetyClearanceLevel", "ToolkitAssetTag"], tech_rows)

# ------------------------------------------------------------------ Shifts
D0 = date(2026, 9, 1)
DAYS = [D0 + timedelta(days=k) for k in range(14)]
SNAP = datetime(2026, 9, 14, 12, 0)  # data snapshot time: later trips are 'Scheduled'
shift_rows, SHIFT = [], {}
sh_id = 0
for d in DAYS:
    for code, s, e in [("AM", "04:30", "12:30"), ("PM", "12:00", "20:00"), ("NT", "19:30", "02:00")]:
        sh_id += 1
        SHIFT[(d, code)] = sh_id
        shift_rows.append([sh_id, f"SH{d.strftime('%m%d')}-{code}", d.isoformat(), s, e,
                           {"AM": "Morning", "PM": "Afternoon", "NT": "Night"}[code]])
write("shift.csv", ["ShiftID", "ShiftCode", "ShiftDate", "ShiftStart", "ShiftEnd", "ShiftType"], shift_rows)

# ------------------------------------------------------------------ Trips
BLOCKS = {1: [1, 2, 1, 2], 2: [3, 5, 4, 5], 3: [6, 7, 10, 7], 4: [8, 9, 8, 9]}
STARTS = [("AM", "05:30"), ("AM", "06:20"), ("PM", "13:00"), ("PM", "14:10")]
trips = []      # dicts
pool = {lid: [t for t in TRAIN_LINE if TRAIN_LINE[t] == lid] for lid in LINES}
drivers_by_line = {lid: [d for d in DRIVER_HOME if DRIVER_HOME[d] == lid] for lid in LINES}

def hhmm(dt):
    return dt.strftime("%H:%M")

# Assessment 2 original trips (all on the snapshot day, morning block for T101/T102/T104)
ORIG = [  # code, route, train, depart, status, occupancy
    ("TR001", 1, 1, "06:05", "Completed", 76.0),
    ("TR002", 1, 2, "06:35", "Completed", 81.0),
    ("TR003", 2, 1, "07:00", "Delayed", 91.0),
    ("TR004", 3, 4, "07:40", "Completed", 64.0),
    ("TR005", 3, 2, "13:30", "Scheduled", 0.0),
]
for code, rid, tid, dep, status, occ in ORIG:
    d = DAYS[-1]
    depdt = datetime.combine(d, datetime.strptime(dep, "%H:%M").time())
    trips.append(dict(code=code, rid=rid, tid=tid, date=d, dep=depdt, status=status, occ=occ,
                      shift="AM" if depdt.hour < 12 else "PM", block=None))

blk = 0
for d in DAYS:
    for lid, pattern in BLOCKS.items():
        avail = [t for t in pool[lid] if not (t in (3, 10) and d >= date(2026, 9, 10))
                 and not (t in (1, 2, 4) and d == DAYS[-1])]  # A2 sample trains run TR001-TR005
        random.shuffle(avail)
        for bi, (sh, st) in enumerate(STARTS):
            blk += 1
            tid = avail[bi % len(avail)]
            t = datetime.combine(d, datetime.strptime(st, "%H:%M").time()) + timedelta(minutes=random.randint(0, 9))
            for rid in pattern:
                trips.append(dict(code=None, rid=rid, tid=tid, date=d, dep=t, status=None, occ=None,
                                  shift=sh, block=blk))
                t = t + timedelta(minutes=route_dur[rid] + random.choice([8, 10, 12]))
trips.sort(key=lambda x: (x["code"] is None, x["dep"]))
n = 5
for i, tr in enumerate(trips):
    tr["id"] = i + 1
    if tr["code"] is None:
        n += 1
        tr["code"] = f"TR{n:03d}"
    tr["arr"] = tr["dep"] + timedelta(minutes=route_dur[tr["rid"]])
    tr["delay"] = 0
    if tr["status"] is None:
        if tr["dep"] >= SNAP:
            tr["status"], tr["occ"] = "Scheduled", 0.0
        else:
            tr["status"] = "Completed"
            peak = 7 <= tr["dep"].hour <= 9 or 16 <= tr["dep"].hour <= 18
            base = 72 if peak else 48
            if ROUTES[tr["rid"]][2] == 2:
                base -= 6
            tr["occ"] = float(max(18, min(99, round(random.gauss(base, 11)))))

# Train run chains (for NEXT_TRIP) are derived in Neo4j from ServiceDate + departure ordering.

# ------------------------------------------------------------------ Disruptions
TRAIN_TYPES = [("Train Fault", "Mechanical"), ("Door Fault", "Doors"), ("Brake Fault", "Brakes"),
               ("HVAC Failure", "HVAC"), ("Traction Fault", "Traction")]
STATION_TYPES = ["Signal Failure", "Platform Overcrowding", "Power Outage", "Medical Emergency",
                 "Track Works", "Security Incident"]
SEV = ["Low", "Medium", "High", "Critical"]
trip_by_id = {t["id"]: t for t in trips}
calls = {}   # trip id -> list of (station code, seq, datetime)
for tr in trips:
    rid = tr["rid"]
    calls[tr["id"]] = [(s, i + 1, tr["dep"] + timedelta(minutes=cum_min[rid][i]))
                       for i, (s, km) in enumerate(route_stops[rid])]
by_train_day = {}
for tr in trips:
    by_train_day.setdefault((tr["tid"], tr["date"]), []).append(tr)
for v in by_train_day.values():
    v.sort(key=lambda x: x["dep"])

src_rows, src_key = [], {}
def source_for(kind, ref):
    if (kind, ref) not in src_key:
        sid = len(src_rows) + 1
        src_key[(kind, ref)] = sid
        src_rows.append([sid, kind, ref if kind == "Train" else None, ref if kind == "Station" else None])
    return src_key[(kind, ref)]

driver_of_trip = {}  # filled later, reporter resolved after allocation
disr, affects = [], []
completed = [t for t in trips if t["status"] in ("Completed", "Delayed") and t["date"] < DAYS[-1]]

# Disruption 1 (from Assessment 2): Train Fault on T101 during TR003, High, 380 pax, 15 min
t3 = trip_by_id[3]
disr.append(dict(id=1, src=source_for("Train", 1), type="Train Fault", sev="High",
                 start=t3["dep"] + timedelta(minutes=9), dur=48, est=15, trip=3, kind="Train", ref=1))
affects.append([1, 3, "Direct", 15, 380])
t3["delay"] = 15

hot_trains = [1, 5, 8, 13, 20, 7]          # recurring fault trains (realistic skew)
hot_stations = ["CEN", "RDF", "STR", "TWH", "DOM", "SYD", "PAR", "CHW"]
did = 1
for k in range(46):
    did += 1
    if k % 2 == 0:  # train-sourced
        tid = random.choice(hot_trains) if random.random() < 0.7 else random.randint(1, 24)
        cand = [t for t in completed if t["tid"] == tid] or completed
        trip = random.choice(cand)
        dtype, _ = random.choice(TRAIN_TYPES)
        sev = random.choices(SEV, [3, 4, 3, 1])[0]
        start = (trip["dep"] + timedelta(minutes=random.randint(3, 15))).replace(second=0)
        est = {"Low": 4, "Medium": 9, "High": 18, "Critical": 32}[sev] + random.randint(0, 6)
        dur = est + random.randint(10, 60)
        disr.append(dict(id=did, src=source_for("Train", trip["tid"]), type=dtype, sev=sev, start=start,
                         dur=dur, est=est, trip=trip["id"], kind="Train", ref=trip["tid"]))
        delay = est + random.randint(-2, 6)
        pax = int(CAP[trip["tid"]] * trip["occ"] / 100)
        affects.append([did, trip["id"], "Direct", max(delay, 2), pax])
        trip["delay"] = max(trip["delay"], max(delay, 2))
        # knock-on: next trip of the same train (recorded for most, not all -> analysis gap)
        chain = by_train_day[(trip["tid"], trip["date"])]
        idx = chain.index(trip)
        if idx + 1 < len(chain) and sev in ("High", "Critical") and random.random() < 0.8:
            nxt = chain[idx + 1]
            kd = max(1, delay // 2)
            affects.append([did, nxt["id"], "Knock-on", kd, int(CAP[nxt["tid"]] * nxt["occ"] / 100)])
            nxt["delay"] = max(nxt["delay"], kd)
        if sev == "Critical" and random.random() < 0.5:
            trip["status"] = "Cancelled"
            affects[-1 if affects[-1][1] == trip["id"] else -2][2] = "Cancellation"
    else:  # station-sourced
        sc = random.choice(hot_stations) if random.random() < 0.75 else random.choice(ST)[0]
        ref = SID[sc]
        dtype = random.choice(STATION_TYPES)
        sev = random.choices(SEV, [3, 4, 2, 1])[0]
        anchor = random.choice([t for t in completed if any(c[0] == sc for c in calls[t["id"]])])
        start = [c[2] for c in calls[anchor["id"]] if c[0] == sc][0] - timedelta(minutes=2)
        start = start.replace(second=0, microsecond=0)
        est = {"Low": 3, "Medium": 7, "High": 14, "Critical": 25}[sev] + random.randint(0, 5)
        dur = est + random.randint(15, 70)
        end = start + timedelta(minutes=dur)
        disr.append(dict(id=did, src=source_for("Station", ref), type=dtype, sev=sev, start=start,
                         dur=dur, est=est, trip=anchor["id"], kind="Station", ref=ref))
        for t in completed:
            for (s, seq, at) in calls[t["id"]]:
                if s == sc and start <= at <= end:
                    delay = max(1, est + random.randint(-3, 4))
                    affects.append([did, t["id"], "Direct", delay, int(CAP[t["tid"]] * t["occ"] / 100)])
                    t["delay"] = max(t["delay"], delay)
                    break

for t in trips:
    if t["status"] == "Completed" and t["delay"] >= 3:
        t["status"] = "Delayed"
    if t["status"] == "Completed" and random.random() < 0.15:
        t["delay"] = random.randint(1, 2)

# ------------------------------------------------------------------ Driver allocations
alloc_rows = []
aid = 0
block_driver = {}
used = {}  # (driver, date, shift) busy
for t in trips:
    key = t["block"] if t["block"] is not None else ("orig", t["code"])
    if key not in block_driver:
        lid = ROUTES[t["rid"]][2]
        home = drivers_by_line[lid]
        others = [d for d in DRIVER_HOME if d not in home]
        for _ in range(60):
            cand = random.choice(home) if random.random() < 0.82 else random.choice(others)
            if (cand, t["date"], t["shift"]) not in used:
                break
        used[(cand, t["date"], t["shift"])] = True
        block_driver[key] = cand
    drv = block_driver[key]
    if t["code"] in ("TR001", "TR003"):
        drv = 1   # T101 driven by Liam Nguyen in the A2 sample block
    if t["code"] in ("TR002",):
        drv = 2
    aid += 1
    son = t["dep"] - timedelta(minutes=15)
    soff = t["arr"] + timedelta(minutes=10)
    alloc_rows.append([aid, t["id"], drv, SHIFT[(t["date"], t["shift"])], "Primary Driver", hhmm(son), hhmm(soff)])
    driver_of_trip[t["id"]] = drv
    if t["occ"] and t["occ"] > 85 and random.random() < 0.35:  # second driver on crowded peak trips
        aid += 1
        trainee = random.choice([d for d in DRIVER_HOME if d != drv])
        alloc_rows.append([aid, t["id"], trainee, SHIFT[(t["date"], t["shift"])], "Second Driver", hhmm(son), hhmm(soff)])
write("driver_allocation.csv", ["AllocationID", "TripID", "StaffID", "ShiftID", "DutyRole", "SignOnTime",
                                "SignOffTime"], alloc_rows)

trip_rows = []
for t in trips:
    actual = None
    if t["status"] in ("Completed", "Delayed"):
        actual = hhmm(t["arr"] + timedelta(minutes=t["delay"]))
    trip_rows.append([t["id"], t["code"], t["rid"], t["tid"], t["date"].isoformat(), hhmm(t["arr"]), actual,
                      t["status"], t["occ"], t["delay"] if t["status"] != "Scheduled" else 0])
write("trip.csv", ["TripID", "TripCode", "RouteID", "TrainID", "ServiceDate", "ScheduledArrival", "ActualArrival",
                   "TripStatus", "OccupancyPercent", "DelayMinutes"], trip_rows)

calls_rows = []
for t in trips:
    for (s, seq, at) in calls[t["id"]]:
        calls_rows.append([t["id"], seq, SID[s], platform_for(t["rid"], s), at.strftime("%H:%M")])
write("calls_at.csv", ["TripID", "StopSequence", "StationID", "PlatformNo", "ScheduledArrival"], calls_rows)

write("disruption_source.csv", ["SourceID", "SourceType", "TrainID", "StationID"], src_rows)
sd_rows = []
techs_by_trade = {}
for s, tr in TECH_TRADE.items():
    techs_by_trade.setdefault(tr, []).append(s)
for dsp in disr:
    end = dsp["start"] + timedelta(minutes=dsp["dur"])
    reporter = driver_of_trip[dsp["trip"]] if dsp["kind"] == "Train" else random.choice(
        [driver_of_trip[dsp["trip"]]] + list(TECH_TRADE))
    sd_rows.append([dsp["id"], dsp["src"], dsp["type"], dsp["sev"], dsp["start"].strftime("%Y-%m-%dT%H:%M:%S"),
                    end.strftime("%Y-%m-%dT%H:%M:%S") if dsp["id"] != len(disr) else None,
                    reporter, dsp["est"]])
write("service_disruption.csv", ["DisruptionID", "SourceID", "DisruptionType", "SeverityLevel", "StartDateTime",
                                 "EndDateTime", "ReportedByStaffID", "EstimatedDelayMin"], sd_rows)
write("affects.csv", ["DisruptionID", "TripID", "ImpactType", "DelayMinutes", "PassengersAffected"], affects)

# ------------------------------------------------------------------ Maintenance
ml_rows, mid = [], 0
TYPE_TRADE = dict(TRAIN_TYPES)
TECHS = list(TECH_TRADE)
for tid in range(1, 25):
    for _ in range(random.randint(2, 4)):
        mid += 1
        d = date(2026, 3, 1) + timedelta(days=random.randint(0, 175))
        cat = random.choice(["Preventive", "Preventive", "Inspection", "Corrective"])
        tech = random.choice(TECHS)
        cost = round(random.uniform(800, 4500) if cat != "Corrective" else random.uniform(3000, 14000), 2)
        ml_rows.append([mid, tid, tech, d.isoformat(), cat, cost, round(random.uniform(2, 10) if cat != "Corrective" else random.uniform(6, 30), 1), "Resolved"])
for dsp in disr:
    if dsp["kind"] == "Train":
        mid += 1
        trade = TYPE_TRADE[dsp["type"]]
        tech = random.choice(techs_by_trade.get(trade, TECHS))
        d = dsp["start"].date() + timedelta(days=random.randint(0, 2))
        outcome = random.choice(["Resolved", "Resolved", "Resolved", "Monitoring", "Deferred"])
        ml_rows.append([mid, dsp["ref"], tech, d.isoformat(), "Corrective", round(random.uniform(2500, 16000), 2),
                        round(random.uniform(5, 36), 1), outcome])
for tid in (3, 10):
    mid += 1
    ml_rows.append([mid, tid, random.choice(TECHS), "2026-09-10", "Overhaul", round(random.uniform(42000, 68000), 2),
                    round(random.uniform(90, 140), 1), "Pending"])
ml_rows.sort(key=lambda r: r[3])
for i, r in enumerate(ml_rows):
    r[0] = i + 1
write("maintenance_log.csv", ["MaintenanceID", "TrainID", "TechnicianID", "MaintenanceDate", "MaintenanceCategory",
                              "CostAUD", "DowntimeHours", "OutcomeStatus"], ml_rows)

for f in sorted(os.listdir(OUT)):
    with open(os.path.join(OUT, f)) as fh:
        print(f"{f:28s}{sum(1 for _ in fh) - 1:6d} rows")
