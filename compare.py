#!/usr/bin/env python3
"""Plot all runs saved in out/results_*.csv side by side."""
import csv
from pathlib import Path

import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent / "out"

PANELS = [("speed_up_kmh", "Speed 300 m before merge [km/h]"),
          ("speed_down_kmh", "Speed after merge [km/h]"),
          ("ramp_queue", "Vehicles queued on the ramp"),
          ("tts_cum", "Cumulative Total Time Spent [veh·h]")]


def to_float(value):
    return float(value) if value != "" else float("nan")


files = sorted(OUT_DIR.glob("results_*.csv"))
if not files:
    raise SystemExit("No results yet - run run_demo.py first.")

fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
print(f"{'run':<20} {'TTS [veh·h]':>12}")
for path in files:
    with open(path) as f:
        rows = list(csv.DictReader(f))
    label = path.stem.removeprefix("results_")
    minutes = [int(r["minute"]) for r in rows]
    for ax, (column, title) in zip(axes.flat, PANELS):
        ax.plot(minutes, [to_float(r[column]) for r in rows], label=label)
        ax.set_title(title)
        ax.grid(alpha=0.3)
    print(f"{label:<20} {float(rows[-1]['tts_cum']):>12.1f}")

for ax in axes[1]:
    ax.set_xlabel("Simulation time [min]")
axes[0, 0].legend()
fig.tight_layout()
fig.savefig(OUT_DIR / "comparison.png", dpi=120)
print(f"\nSaved {OUT_DIR / 'comparison.png'}")
plt.show()
