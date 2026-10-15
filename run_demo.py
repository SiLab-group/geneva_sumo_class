#!/usr/bin/env python3
"""
SUMO demo: an on-ramp merge on a 3-lane motorway, inspired by the
Geneva motorway digital twin (Kusic, Schumann, Ivanjko, 2023).

  Act 1   python run_demo.py --scenario light                   free flow
  Act 2   python run_demo.py --scenario peak                    breakdown at the merge
  Act 3   python run_demo.py --scenario peak --control alinea   ramp metering
          python compare.py                                     compare the runs

Add --nogui to run without the GUI (fast, a few seconds).
"""
import argparse
import csv
import subprocess
from pathlib import Path

import sumolib
import traci

HERE = Path(__file__).resolve().parent
NET_DIR = HERE / "net"
NET_FILE = NET_DIR / "geneva_merge.net.xml"
OUT_DIR = HERE / "out"

STEP = 0.5          # simulation step length [s]
DURATION = 2400     # 40 simulated minutes [s]
TRUCK_SHARE = 0.10

# Peak demand in veh/h: (mainline, on-ramp)
SCENARIOS = {
    "light": (3000, 500),
    "peak": (4600, 1000),
}
# Demand profile: (begin [s], end [s], fraction of peak demand)
PROFILE = [(0, 600, 0.6), (600, 1800, 1.0), (1800, DURATION, 0.6)]

TLS_ID = "r1"                       # ramp-metering signal (node r1)
UP_LOOPS = ["up_0", "up_1", "up_2"]
DOWN_LOOPS = ["down_0", "down_1", "down_2"]

# ALINEA ramp metering (Papageorgiou et al., 1991):
#   r(k) = r(k-1) + K_R * (o_target - o_down(k))
K_R = 70.0                          # gain [veh/h per % occupancy]
RATE_MIN, RATE_MAX = 300.0, 1800.0  # metering rate bounds [veh/h]
GREEN_TIME = 2.0                    # green per cycle, about one vehicle [s]
QUEUE_LIMIT = 50                    # ramp queue that forces the ramp open [veh]


def build_network():
    """Convert the plain XML description (nodes, edges, connections) into a SUMO network."""
    netconvert = sumolib.checkBinary("netconvert")
    subprocess.run([netconvert,
                    "-n", str(NET_DIR / "geneva_merge.nod.xml"),
                    "-e", str(NET_DIR / "geneva_merge.edg.xml"),
                    "-x", str(NET_DIR / "geneva_merge.con.xml"),
                    "-o", str(NET_FILE),
                    "--no-turnarounds",
                    "--offset.disable-normalization"],  # keep the x/y of the .nod.xml file
                   check=True)


def write_routes(scenario):
    """Write the traffic demand (flows of cars and trucks) for a scenario."""
    main, ramp = SCENARIOS[scenario]
    lines = ['<routes>',
             '    <vType id="car" vClass="passenger" length="4.5" maxSpeed="36.1" speedFactor="normc(1,0.1,0.8,1.2)"/>',
             '    <vType id="truck" vClass="truck" length="12" maxSpeed="22.22" color="0.6,0.6,0.6"/>']
    for i, (begin, end, frac) in enumerate(PROFILE):
        for origin, peak in (("main_up", main), ("ramp_in", ramp)):
            for vtype, share in (("car", 1 - TRUCK_SHARE), ("truck", TRUCK_SHARE)):
                lines.append(f'    <flow id="{origin}_{vtype}_{i}" type="{vtype}" begin="{begin}" end="{end}" '
                             f'vehsPerHour="{peak * frac * share:.0f}" from="{origin}" to="main_down" '
                             f'departLane="best" departSpeed="max"/>')
    lines.append('</routes>')
    path = OUT_DIR / f"demand_{scenario}.rou.xml"
    path.write_text("\n".join(lines) + "\n")
    return path


def mean(values):
    return sum(values) / len(values) if values else None


def run(scenario, control, gui, delay, target):
    OUT_DIR.mkdir(exist_ok=True)
    build_network()
    routes = write_routes(scenario)

    binary = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    cmd = [binary, "-c", str(HERE / "geneva_merge.sumocfg"),
           "-r", str(routes), "--step-length", str(STEP)]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
    traci.start(cmd)

    if gui:
        # Point the camera at the merge (node n1 at x=1500, y=0)
        traci.gui.setOffset(traci.gui.DEFAULT_VIEW, 1550, -40)
        traci.gui.setZoom(traci.gui.DEFAULT_VIEW, 400)

    # Ramp signal: permanently green unless ALINEA controls it
    traci.trafficlight.setRedYellowGreenState(TLS_ID, "G")
    signal = "G"
    rate = RATE_MAX
    cycle_time = 0.0

    tts = 0.0                       # total time spent [veh*h]
    rows = []
    occ_samples, up_speeds, down_speeds, arrived = [], [], [], 0
    steps_per_minute = int(60 / STEP)

    print(f"\n=== scenario={scenario}  control={control} ===")
    print(" min  occ_down  rate[veh/h]  ramp_queue  v_up[km/h]  v_down[km/h]")

    for step in range(1, int(DURATION / STEP) + 1):
        if control == "alinea":
            # Fixed-time cycle derived from the metering rate: GREEN_TIME green, rest red
            new_signal = "G" if cycle_time < GREEN_TIME else "r"
            if new_signal != signal:
                traci.trafficlight.setRedYellowGreenState(TLS_ID, new_signal)
                signal = new_signal
            cycle_time += STEP
            if cycle_time >= 3600.0 / rate:
                cycle_time = 0.0

        traci.simulationStep()

        # Vehicles in the network + vehicles waiting to enter it
        n_veh = traci.vehicle.getIDCount() + len(traci.simulation.getPendingVehicles())
        tts += n_veh * STEP / 3600.0
        arrived += traci.simulation.getArrivedNumber()

        occ_samples.append(mean([traci.inductionloop.getLastStepOccupancy(d) for d in DOWN_LOOPS]))
        up_speeds += [s for s in (traci.inductionloop.getLastStepMeanSpeed(d) for d in UP_LOOPS) if s >= 0]
        down_speeds += [s for s in (traci.inductionloop.getLastStepMeanSpeed(d) for d in DOWN_LOOPS) if s >= 0]

        if step % steps_per_minute == 0:
            minute = int(step * STEP / 60)
            occ_down = mean(occ_samples)
            queue = (traci.edge.getLastStepHaltingNumber("ramp_in")
                     + traci.edge.getLastStepHaltingNumber("ramp_merge"))

            if control == "alinea":
                rate = rate + K_R * (target - occ_down)
                rate = max(RATE_MIN, min(RATE_MAX, rate))
                if queue > QUEUE_LIMIT:     # protect the city streets from spillback
                    rate = RATE_MAX

            v_up = mean(up_speeds)
            v_down = mean(down_speeds)
            row = {"minute": minute,
                   "occ_down": round(occ_down, 2),
                   "rate": round(rate),
                   "ramp_queue": queue,
                   "speed_up_kmh": round(v_up * 3.6, 1) if v_up is not None else "",
                   "speed_down_kmh": round(v_down * 3.6, 1) if v_down is not None else "",
                   "outflow_vehh": arrived * 60,
                   "tts_cum": round(tts, 2)}
            rows.append(row)
            print(f"{minute:4d}  {occ_down:7.1f}%  {rate:11.0f}  {queue:10d}  "
                  f"{row['speed_up_kmh']:>10}  {row['speed_down_kmh']:>12}")

            occ_samples, up_speeds, down_speeds, arrived = [], [], [], 0

    traci.close()

    out_csv = OUT_DIR / f"results_{scenario}_{control}.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTotal Time Spent (TTS): {tts:.1f} veh*h   ->  saved {out_csv.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", choices=SCENARIOS, default="peak")
    parser.add_argument("--control", choices=["none", "alinea"], default="none")
    parser.add_argument("--nogui", action="store_true", help="run without sumo-gui")
    parser.add_argument("--delay", type=int, default=20, help="GUI delay per step [ms]")
    parser.add_argument("--target", type=float, default=15.0,
                        help="ALINEA target occupancy downstream of the merge [%%]")
    args = parser.parse_args()
    run(args.scenario, args.control, not args.nogui, args.delay, args.target)
