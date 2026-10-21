#!/usr/bin/env python3
"""
Phantom traffic jam on a ring road (after Sugiyama et al., 2008).

    python phantom_jam.py

Cars drive around a 300 m circle with nothing in their way. With enough cars
and slightly imperfect drivers, a stop-and-go wave appears out of nowhere and
travels backwards around the ring.
"""
import math
import random
import subprocess
import tkinter as tk
from collections import deque
from pathlib import Path

import sumolib
import traci

from control_panel import draw_speed_chart

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"

RING_LENGTH = 300.0                  # circumference [m]
SPEED_LIMIT = 50 / 3.6               # [m/s]
STEP = 1.0                           # simulation step length [s]
LAPS = 500                           # route length in laps (more than enough)
CHART_SECONDS = 300
BRAKE_SPEED = 2.0                    # speed of the "Brake!" car [m/s]
BRAKE_TIME = 3                       # how long it brakes [s]


def build_ring():
    """Two half circles between two nodes, converted with netconvert."""
    r = RING_LENGTH / (2 * math.pi)
    upper = " ".join(f"{r * math.cos(a):.2f},{r * math.sin(a):.2f}"
                     for a in (math.pi * i / 24 for i in range(25)))
    lower = " ".join(f"{r * math.cos(a):.2f},{r * math.sin(a):.2f}"
                     for a in (math.pi + math.pi * i / 24 for i in range(25)))
    (OUT_DIR / "ring.nod.xml").write_text(
        '<nodes>\n'
        f'    <node id="east" x="{r:.2f}" y="0"/>\n'
        f'    <node id="west" x="{-r:.2f}" y="0"/>\n'
        '</nodes>\n')
    (OUT_DIR / "ring.edg.xml").write_text(
        '<edges>\n'
        f'    <edge id="top" from="east" to="west" numLanes="1" speed="{SPEED_LIMIT:.2f}" shape="{upper}"/>\n'
        f'    <edge id="bottom" from="west" to="east" numLanes="1" speed="{SPEED_LIMIT:.2f}" shape="{lower}"/>\n'
        '</edges>\n')
    subprocess.run([sumolib.checkBinary("netconvert"),
                    "-n", str(OUT_DIR / "ring.nod.xml"),
                    "-e", str(OUT_DIR / "ring.edg.xml"),
                    "-o", str(OUT_DIR / "ring.net.xml"),
                    "--no-turnarounds", "--offset.disable-normalization"], check=True)

    (OUT_DIR / "ring.rou.xml").write_text(
        '<routes>\n'
        '    <vType id="ringcar" vClass="passenger" length="4.5" minGap="2.0" speedFactor="1" sigma="0.5"/>\n'
        f'    <route id="from_top" edges="{" ".join(["top bottom"] * LAPS)}"/>\n'
        f'    <route id="from_bottom" edges="{" ".join(["bottom top"] * LAPS)}"/>\n'
        '</routes>\n')


class RingPanel:
    def __init__(self, root):
        self.root = root
        self.running = True
        self.generation = 0
        self.braking = None           # (vehicle id, release time)
        self.history = deque()
        self._build_ui()

    def _slider(self, parent, text, low, high, value, step, fmt, command=None):
        var = tk.DoubleVar(value=value)
        row = tk.Frame(parent)
        row.pack(fill="x")
        tk.Label(row, text=text, width=18, anchor="w").pack(side="left")
        shown = tk.Label(row, width=12, anchor="e")
        shown.pack(side="right")

        def changed(*_):
            shown.config(text=fmt(var.get()))
            if command:
                command()

        tk.Scale(row, variable=var, from_=low, to=high, resolution=step, orient="horizontal",
                 showvalue=False, length=220, command=changed).pack(side="left", fill="x", expand=True)
        shown.config(text=fmt(value))
        return var

    def _build_ui(self):
        cars = tk.LabelFrame(self.root, text="Cars on the ring", padx=10, pady=6)
        cars.pack(fill="x", padx=10, pady=5)
        self.n_cars = self._slider(cars, "Number of cars", 5, 35, 25, 1, lambda v: f"{v:.0f} cars")
        tk.Button(cars, text="Restart with this number of cars", command=self.restart).pack(fill="x", pady=2)

        drivers = tk.LabelFrame(self.root, text="Drivers", padx=10, pady=6)
        drivers.pack(fill="x", padx=10, pady=5)
        self.sigma = self._slider(drivers, "Driver imperfection", 0, 1, 0.5, 0.1,
                                  lambda v: "perfect" if v == 0 else f"{v:.1f}",
                                  command=self.apply_sigma)
        self.brake_btn = tk.Button(drivers, text="Brake! (one driver brakes hard)", command=self.brake)
        self.brake_btn.pack(fill="x", pady=2)

        live = tk.LabelFrame(self.root, text="Live", padx=10, pady=6)
        live.pack(fill="x", padx=10, pady=5)
        self.stats = {}
        for key, label in [("speed", "Average speed"), ("stopped", "Cars standing still")]:
            row = tk.Frame(live)
            row.pack(fill="x")
            tk.Label(row, text=label, anchor="w").pack(side="left")
            self.stats[key] = tk.Label(row, anchor="e", font=("Helvetica", 14, "bold"))
            self.stats[key].pack(side="right")
        tk.Label(live, text="Average speed, last 5 minutes", fg="gray").pack(anchor="w", pady=(6, 0))
        self.chart = tk.Canvas(live, width=360, height=110, bg="white", highlightthickness=1)
        self.chart.pack(fill="x")

        self.pause_btn = tk.Button(self.root, text="Pause", command=self.toggle_pause)
        self.pause_btn.pack(fill="x", padx=10, pady=8)

    def restart(self):
        """Remove all cars and place the chosen number evenly around the ring."""
        for vid in traci.vehicle.getIDList():
            traci.vehicle.remove(vid)
        traci.simulationStep()
        self.braking = None
        self.generation += 1
        n = int(self.n_cars.get())
        half = RING_LENGTH / 2
        for i in range(n):
            pos = i * RING_LENGTH / n
            route, edge_pos = ("from_top", pos) if pos < half else ("from_bottom", pos - half)
            traci.vehicle.add(f"car{self.generation}_{i}", route, typeID="ringcar",
                              departPos=f"{edge_pos:.1f}", departSpeed="0")

    def apply_sigma(self):
        traci.vehicletype.setImperfection("ringcar", self.sigma.get())

    def brake(self):
        cars = traci.vehicle.getIDList()
        if not cars or self.braking:
            return
        vid = random.choice(cars)
        traci.vehicle.setSpeed(vid, BRAKE_SPEED)
        traci.vehicle.highlight(vid, (255, 0, 255, 255), size=6, alphaMax=255, duration=BRAKE_TIME + 5)
        self.braking = (vid, traci.simulation.getTime() + BRAKE_TIME)

    def toggle_pause(self):
        self.running = not self.running
        self.pause_btn.config(text="Pause" if self.running else "Continue")

    def tick(self):
        if self.running:
            try:
                self.step()
            except traci.exceptions.FatalTraCIError:   # sumo-gui was closed
                self.root.destroy()
                return
        self.root.after(1 if self.running else 100, self.tick)

    def step(self):
        now = traci.simulation.getTime()
        if self.braking and now >= self.braking[1]:
            try:
                traci.vehicle.setSpeed(self.braking[0], -1)   # SUMO controls the speed
            except traci.exceptions.TraCIException:
                pass
            self.braking = None

        traci.simulationStep()

        speeds = [traci.vehicle.getSpeed(v) for v in traci.vehicle.getIDList()]
        avg = sum(speeds) / len(speeds) * 3.6 if speeds else 0.0
        stopped = sum(s < 1.0 for s in speeds)
        self.stats["speed"].config(text=f"{avg:.0f} km/h", fg="red" if avg < 20 else "green")
        self.stats["stopped"].config(text=f"{stopped}", fg="red" if stopped else "green")

        self.history.append((now, avg))
        while self.history and self.history[0][0] < now - CHART_SECONDS:
            self.history.popleft()
        draw_speed_chart(self.chart, self.history, now, CHART_SECONDS, (10, 30, 50))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    build_ring()
    traci.start([sumolib.checkBinary("sumo-gui"),
                 "-n", str(OUT_DIR / "ring.net.xml"),
                 "-r", str(OUT_DIR / "ring.rou.xml"),
                 "--gui-settings-file", str(HERE / "gui.view.xml"),
                 "--step-length", str(STEP),
                 "--start", "--quit-on-end", "--delay", "100"])

    root = tk.Tk()
    root.title("Phantom traffic jam")
    root.option_add("*Font", "Helvetica 13")
    panel = RingPanel(root)
    panel.restart()
    root.after(100, panel.tick)
    root.mainloop()

    try:
        traci.close()
    except traci.exceptions.FatalTraCIError:
        pass


if __name__ == "__main__":
    main()
