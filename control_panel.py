#!/usr/bin/env python3
"""
Interactive control panel for an on-ramp of the Geneva motorway.

    python control_panel.py

Opens sumo-gui together with a window of sliders and buttons that change
the traffic while the simulation runs. The road is net/geneva_cut.net.xml,
cut from the DT-GM Geneva motorway network by tools/cut_geneva.py, on top of
the swisstopo aerial photo in net/aerial/ (tools/fetch_aerial.py).
"""
import json
import random
import tkinter as tk
from collections import deque
from pathlib import Path

import sumolib
import traci

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
AERIAL_DIR = HERE / "net" / "aerial"
VIEW_ANGLE = -108.5                  # view rotation [deg]; the motorway heads 108.5 deg (north-northwest)

STEP = 0.5                           # simulation step length [s]
MAIN_ROUTE = ["ES_N11", "ES_N12", "ES_N13"]
RAMP_ROUTE = ["ES_N56_onramp1.90", "ES_N57_onramp1", "ES_N57_onramp1.140", "ES_N12", "ES_N13"]
RAMP_EDGES = RAMP_ROUTE[:3]
MOTORWAY = MAIN_ROUTE
MERGE_NODE = "59962795"              # junction where the ramp joins the motorway
TLS_ID = "J19"                       # ramp signal, 60 m before the merge
CLOSED_LANE = "ES_N13_1"             # left lane after the merge (roadworks)
LANE_WIDTH = 3.2
CHART_SECONDS = 600                  # speed history shown in the chart [s]
GREEN_TIME = 2.0                     # ramp signal green per car [s]


def write_routes():
    """Vehicle types and the two routes; the panel adds the vehicles live."""
    lines = [
        '<routes>',
        '    <vType id="car" vClass="passenger" length="4.5" maxSpeed="36.1" speedFactor="normc(1,0.1,0.8,1.2)"/>',
        '    <vType id="truck" vClass="truck" length="12" maxSpeed="22.22" color="0.6,0.6,0.6"/>',
        f'    <route id="r_main" edges="{" ".join(MAIN_ROUTE)}"/>',
        f'    <route id="r_ramp" edges="{" ".join(RAMP_ROUTE)}"/>',
        '</routes>']
    path = OUT_DIR / "panel.rou.xml"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_view_settings():
    """gui.view.xml plus the aerial photo tiles as background images (decals)."""
    view = (HERE / "gui.view.xml").read_text()
    info = json.loads((AERIAL_DIR / "aerial.json").read_text())
    decals = "".join(
        f'    <decal file="{AERIAL_DIR / t["file"]}" centerX="{t["centerX"]:.2f}" centerY="{t["centerY"]:.2f}" '
        f'width="{t["width"]:.2f}" height="{t["height"]:.2f}" rotation="0"/>\n'
        for t in info["tiles"])
    path = OUT_DIR / "geneva.view.xml"
    path.write_text(view.replace("</viewsettings>", decals + "</viewsettings>"))
    return path


def draw_speed_chart(canvas, history, now, seconds, grid_kmh):
    """Line chart of (time, speed km/h) pairs over the last `seconds`."""
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    top = grid_kmh[-1] * 1.1
    for kmh in grid_kmh:
        y = h - kmh / top * h
        canvas.create_line(0, y, w, y, fill="#e0e0e0")
        canvas.create_text(4, y, text=f"{kmh}", anchor="sw", fill="gray")
    points = []
    for t, v in history:
        points += [(t - now + seconds) / seconds * w, h - v / top * h]
    if len(points) >= 4:
        canvas.create_line(*points, fill="#1f77b4", width=2)


class Panel:
    def __init__(self, root):
        self.root = root
        self.running = True
        self.veh_count = 0
        self.lane_closed = False
        self.signal = "G"
        self.cycle_time = 0.0
        self.applied_speed = None
        self.arrivals = deque()       # (time, vehicles that left the road)
        self.history = deque()        # (time, average speed km/h)
        self._build_ui()

    def _section(self, title):
        frame = tk.LabelFrame(self.root, text=title, padx=10, pady=6)
        frame.pack(fill="x", padx=10, pady=5)
        return frame

    def _slider(self, parent, text, low, high, value, step, unit):
        var = tk.DoubleVar(value=value)
        row = tk.Frame(parent)
        row.pack(fill="x")
        tk.Label(row, text=text, width=20, anchor="w").pack(side="left")
        shown = tk.Label(row, width=11, anchor="e")
        shown.pack(side="right")

        def show(*_):
            shown.config(text=f"{var.get():.0f} {unit}")

        tk.Scale(row, variable=var, from_=low, to=high, resolution=step, orient="horizontal",
                 showvalue=False, length=240, command=show).pack(side="left", fill="x", expand=True)
        show()
        return var

    def _build_ui(self):
        traffic = self._section("Traffic")
        self.main = self._slider(traffic, "Motorway traffic", 0, 6000, 3000, 100, "veh/h")
        self.ramp = self._slider(traffic, "On-ramp traffic", 0, 1500, 600, 50, "veh/h")
        self.trucks = self._slider(traffic, "Share of trucks", 0, 40, 10, 5, "%")

        manager = self._section("Traffic manager")
        self.speed = self._slider(manager, "Speed limit", 60, 120, 120, 10, "km/h")
        self.metering = tk.BooleanVar(value=False)
        tk.Checkbutton(manager, text="Ramp metering (traffic light on the ramp)",
                       variable=self.metering).pack(anchor="w")
        self.gap = self._slider(manager, "  one car every", 3, 12, 5, 1, "s")

        roadworks = self._section("Roadworks")
        self.lane_btn = tk.Button(roadworks, text="Close left lane (roadworks)",
                                  command=self.toggle_lane)
        self.lane_btn.pack(fill="x", pady=2)
        self.status = tk.Label(roadworks, text="", fg="gray", anchor="w", justify="left", wraplength=380)
        self.status.pack(fill="x")

        live = self._section("Live")
        self.stats = {}
        for key, label in [("speed", "Average speed"), ("cars", "Vehicles on the road"),
                           ("waiting", "Waiting to enter"), ("queue", "Queue on the ramp"),
                           ("flow", "Vehicles through (last min)")]:
            row = tk.Frame(live)
            row.pack(fill="x")
            tk.Label(row, text=label, anchor="w").pack(side="left")
            self.stats[key] = tk.Label(row, anchor="e", font=("Helvetica", 14, "bold"))
            self.stats[key].pack(side="right")
        tk.Label(live, text="Average speed, last 10 minutes", fg="gray").pack(anchor="w", pady=(6, 0))
        self.chart = tk.Canvas(live, width=380, height=120, bg="white", highlightthickness=1)
        self.chart.pack(fill="x")

        simulation = self._section("Simulation")
        self.sim_speed = self._slider(simulation, "Simulation speed", 1, 20, 10, 1, "x real time")
        self.pause_btn = tk.Button(simulation, text="Pause", command=self.toggle_pause)
        self.pause_btn.pack(fill="x", pady=4)

    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.config(text="Pause" if self.running else "Continue")

    def toggle_lane(self):
        try:
            if not self.lane_closed:
                traci.lane.setDisallowed(CLOSED_LANE, ["passenger", "truck"])
                self.lane_closed = True
                self.lane_btn.config(text="Open left lane again")
                self.status.config(text="Left lane after the merge is closed.", fg="gray")
                # orange stripe along the whole closed lane
                traci.polygon.add("roadworks", traci.lane.getShape(CLOSED_LANE),
                                  (255, 140, 0, 255), fill=False, layer=5, lineWidth=LANE_WIDTH)
            else:
                traci.lane.setDisallowed(CLOSED_LANE, [])
                self.lane_closed = False
                self.lane_btn.config(text="Close left lane (roadworks)")
                self.status.config(text="Left lane is open.", fg="gray")
                if "roadworks" in traci.polygon.getIDList():
                    traci.polygon.remove("roadworks")
        except traci.exceptions.TraCIException as error:
            self.status.config(text=f"SUMO error: {error}", fg="red")
            print(f"SUMO error while switching the lane: {error}")

    def tick(self):
        """One simulation step, then idle until the next one so clicks get handled."""
        if self.running:
            try:
                self.step()
            except traci.exceptions.FatalTraCIError:   # sumo-gui was closed
                self.root.destroy()
                return
        wait_ms = round(STEP * 1000 / self.sim_speed.get()) if self.running else 100
        self.root.after(wait_ms, self.tick)

    def insert(self, route, veh_per_hour):
        if random.random() < veh_per_hour * STEP / 3600:
            vtype = "truck" if random.random() < self.trucks.get() / 100 else "car"
            self.veh_count += 1
            traci.vehicle.add(f"{route}_{self.veh_count}", route, typeID=vtype,
                              departLane="best", departSpeed="max")

    def update_ramp_signal(self):
        if self.metering.get():
            new = "G" if self.cycle_time < GREEN_TIME else "r"
            self.cycle_time = (self.cycle_time + STEP) % self.gap.get()
        else:
            new = "G"
        if new != self.signal:
            traci.trafficlight.setRedYellowGreenState(TLS_ID, new)
            self.signal = new

    def step(self):
        now = traci.simulation.getTime()
        if self.speed.get() != self.applied_speed:
            self.applied_speed = self.speed.get()
            for edge in MOTORWAY:
                traci.edge.setMaxSpeed(edge, self.applied_speed / 3.6)

        self.insert("r_main", self.main.get())
        self.insert("r_ramp", self.ramp.get())
        self.update_ramp_signal()

        traci.simulationStep()

        self.arrivals.append((now, traci.simulation.getArrivedNumber()))
        while self.arrivals and self.arrivals[0][0] < now - 60:
            self.arrivals.popleft()
        if int(now / STEP) % 2 == 0:               # display refreshes every simulated second
            self.update_stats(now)

    def update_stats(self, now):
        counts = [traci.edge.getLastStepVehicleNumber(e) for e in MOTORWAY]
        speeds = [traci.edge.getLastStepMeanSpeed(e) for e in MOTORWAY]
        if sum(counts):
            avg = sum(c * s for c, s in zip(counts, speeds)) / sum(counts) * 3.6
        else:
            avg = self.speed.get()
        queue = sum(traci.edge.getLastStepHaltingNumber(e) for e in RAMP_EDGES)

        self.stats["speed"].config(text=f"{avg:.0f} km/h", fg="red" if avg < 40 else "green")
        self.stats["cars"].config(text=f"{traci.vehicle.getIDCount()}")
        self.stats["waiting"].config(text=f"{len(traci.simulation.getPendingVehicles())}")
        self.stats["queue"].config(text=f"{queue}")
        self.stats["flow"].config(text=f"{sum(n for _, n in self.arrivals)}")

        self.history.append((now, avg))
        while self.history and self.history[0][0] < now - CHART_SECONDS:
            self.history.popleft()
        draw_speed_chart(self.chart, self.history, now, CHART_SECONDS, (40, 80, 120))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    routes = write_routes()
    traci.start([sumolib.checkBinary("sumo-gui"),
                 "-c", str(HERE / "geneva_merge.sumocfg"),
                 "-r", str(routes), "--step-length", str(STEP),
                 "--gui-settings-file", str(write_view_settings()),
                 "--start", "--quit-on-end", "--delay", "0"])
    traci.gui.setAngle(traci.gui.DEFAULT_VIEW, VIEW_ANGLE)
    traci.gui.setOffset(traci.gui.DEFAULT_VIEW, *traci.junction.getPosition(MERGE_NODE))
    traci.gui.setZoom(traci.gui.DEFAULT_VIEW, 300)
    traci.trafficlight.setRedYellowGreenState(TLS_ID, "G")

    root = tk.Tk()
    root.title("Traffic control panel")
    root.option_add("*Font", "Helvetica 13")
    panel = Panel(root)
    root.after(100, panel.tick)
    root.mainloop()

    try:
        traci.close()
    except traci.exceptions.FatalTraCIError:
        pass


if __name__ == "__main__":
    main()
