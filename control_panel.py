#!/usr/bin/env python3
"""
Interactive control panel for the Geneva on-ramp demo.

    python control_panel.py

Opens sumo-gui together with a small window of sliders and buttons.
Change the traffic while the simulation runs and watch what happens on the road.
"""
import random
import tkinter as tk
from collections import deque

import sumolib
import traci

import run_demo

STEP = run_demo.STEP
MOTORWAY = ["main_up", "accel", "main_down"]
CLOSED_LANE = "main_down_2"          # left lane after the merge (roadworks)
CHART_SECONDS = 600                  # speed history shown in the chart [s]
GREEN_TIME = 2.0                     # ramp signal green per car [s]


def write_routes():
    """Vehicle types and the two routes; vehicles are added live by the panel."""
    lines = ['<routes>'] + run_demo.VTYPES + [
        '    <route id="r_main" edges="main_up accel main_down"/>',
        '    <route id="r_ramp" edges="ramp_in ramp_merge accel main_down"/>',
        '</routes>']
    path = run_demo.OUT_DIR / "panel.rou.xml"
    path.write_text("\n".join(lines) + "\n")
    return path


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

    # ------------------------------------------------------------------ UI
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

        self.pause_btn = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_btn.pack(fill="x", padx=10, pady=8)

    # ------------------------------------------------------------- buttons
    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.config(text="Pause" if self.running else "Continue")

    def toggle_lane(self):
        self.lane_closed = not self.lane_closed
        if self.lane_closed:
            traci.lane.setDisallowed(CLOSED_LANE, ["passenger", "truck"])
            # orange block on the closed lane so it is visible in the GUI
            (x0, y0), _ = traci.lane.getShape(CLOSED_LANE)[:2]
            traci.polygon.add("roadworks", [(x0, y0 - 1.6), (x0 + 60, y0 - 1.6),
                                            (x0 + 60, y0 + 1.6), (x0, y0 + 1.6)],
                              (255, 140, 0, 255), fill=True, layer=5)
            self.lane_btn.config(text="Open left lane again")
        else:
            traci.lane.setDisallowed(CLOSED_LANE, [])
            traci.polygon.remove("roadworks")
            self.lane_btn.config(text="Close left lane (roadworks)")

    # ---------------------------------------------------------- simulation
    def tick(self):
        if self.running:
            try:
                self.step()
            except traci.exceptions.FatalTraCIError:   # sumo-gui was closed
                self.root.destroy()
                return
        self.root.after(1 if self.running else 100, self.tick)

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
            traci.trafficlight.setRedYellowGreenState(run_demo.TLS_ID, new)
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
        if int(now / STEP) % 2 == 0:               # refresh the display every simulated second
            self.update_stats(now)

    def update_stats(self, now):
        counts = [traci.edge.getLastStepVehicleNumber(e) for e in MOTORWAY]
        speeds = [traci.edge.getLastStepMeanSpeed(e) for e in MOTORWAY]
        if sum(counts):
            avg = sum(c * s for c, s in zip(counts, speeds)) / sum(counts) * 3.6
        else:
            avg = self.speed.get()
        queue = (traci.edge.getLastStepHaltingNumber("ramp_in")
                 + traci.edge.getLastStepHaltingNumber("ramp_merge"))

        self.stats["speed"].config(text=f"{avg:.0f} km/h", fg="red" if avg < 40 else "green")
        self.stats["cars"].config(text=f"{traci.vehicle.getIDCount()}")
        self.stats["waiting"].config(text=f"{len(traci.simulation.getPendingVehicles())}")
        self.stats["queue"].config(text=f"{queue}")
        self.stats["flow"].config(text=f"{sum(n for _, n in self.arrivals)}")

        self.history.append((now, avg))
        while self.history and self.history[0][0] < now - CHART_SECONDS:
            self.history.popleft()
        draw_speed_chart(self.chart, self.history, now, CHART_SECONDS, (40, 80, 120))


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


def main():
    run_demo.OUT_DIR.mkdir(exist_ok=True)
    run_demo.build_network()
    routes = write_routes()
    traci.start([sumolib.checkBinary("sumo-gui"),
                 "-c", str(run_demo.HERE / "geneva_merge.sumocfg"),
                 "-r", str(routes), "--step-length", str(STEP),
                 "--start", "--quit-on-end", "--delay", "50"])
    run_demo.focus_view()
    traci.trafficlight.setRedYellowGreenState(run_demo.TLS_ID, "G")

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
