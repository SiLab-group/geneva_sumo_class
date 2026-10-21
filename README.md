# SUMO demo: a Geneva-style motorway on-ramp

A 1.8 km, 3-lane motorway segment with one on-ramp and a 300 m acceleration lane,
like the junctions on the Geneva motorway modelled in the *Digital Twin – Geneva Motorway*
project (Kušić, Schumann, Ivanjko, 2023). Loop detectors play the role of the FEDRO
traffic counters, and a traffic light on the ramp is used for ramp metering.

```
 main_up (3 lanes, 1 km)           accel (4 lanes)    main_down (3 lanes, 0.5 km)
 ======================[up]========|=============|==[down]=====================>
                                  /
              ramp_in    [signal]/ ramp_merge
             ------------- r1 --/
```

## Installation

You need **Python 3.9 or newer** and **SUMO**. The simplest way is to install SUMO
with `pip` inside a virtual environment (same on all systems); if the graphical
interface `sumo-gui` does not start, install SUMO with the system installer as well
(see your operating system below).

### Windows

1. Install Python from https://www.python.org/downloads/ (tick *Add python.exe to PATH*).
2. Open *Command Prompt* in the `geneva_demo` folder and run:

   ```bat
   py -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Optional – system installer: download the Windows installer (`.msi`) from
   https://sumo.dlr.de/docs/Downloads.php. It sets `SUMO_HOME` automatically.

### Linux (Ubuntu / Debian)

1. Install Python tools:

   ```bash
   sudo apt-get install python3 python3-venv python3-pip
   ```

2. In the `geneva_demo` folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Optional – system packages:

   ```bash
   sudo add-apt-repository ppa:sumo/stable
   sudo apt-get update
   sudo apt-get install sumo sumo-tools sumo-doc
   export SUMO_HOME=/usr/share/sumo
   ```

### macOS

1. Install Python from https://www.python.org/downloads/ or with Homebrew (`brew install python`).
2. In the `geneva_demo` folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. If `sumo-gui` does not start, install SUMO with Homebrew:

   ```bash
   brew tap dlr-ts/sumo
   brew install sumo
   export SUMO_HOME="$(brew --prefix sumo)/share/sumo"
   ```

   (Add the `export` line to `~/.zshrc` to keep it.) Alternatively use the macOS
   installer from https://sumo.dlr.de/docs/Downloads.php.

### Check the installation

With the virtual environment activated:

```bash
python run_demo.py --scenario peak --nogui
```

It should print one line per simulated minute and end with the *Total Time Spent*.

## Files

| File | What it is |
|---|---|
| `net/*.nod.xml`, `*.edg.xml`, `*.con.xml` | The road described as nodes, edges and lane connections |
| `net/geneva_merge.net.xml` | The SUMO network, built by `netconvert` (automatically) |
| `detectors.add.xml` | Induction loops upstream and downstream of the merge |
| `out/demand_*.rou.xml` | Traffic demand (cars + 10 % trucks), generated per scenario |
| `geneva_merge.sumocfg` | The SUMO configuration that ties it all together |
| `control_panel.py` | **Play mode:** sliders and buttons to change the traffic live |
| `phantom_jam.py` | **Phantom jam:** cars on a ring road, a jam appears out of nowhere |
| `run_demo.py` | Builds the network, writes demand, runs SUMO via **TraCI** |
| `compare.py` | Plots the runs against each other |

## Play mode: the control panel

```bash
python control_panel.py
```

This opens `sumo-gui` and a control window next to it. Everything changes live while
the cars are driving:

| Control | Try this |
|---|---|
| **Motorway traffic** / **On-ramp traffic** | Push the traffic up slowly. At what point does the merge jam? |
| **Share of trucks** | Same traffic, more trucks: is it worse? |
| **Speed limit** | During a jam, lower the limit to 80 km/h. Does traffic flow better? |
| **Ramp metering** + **one car every … s** | Hold back the ramp cars with the traffic light. Who wins, who loses? |
| **Close left lane (roadworks)** | An orange block closes the left lane after the merge. |
| **Pause** | Freeze the simulation to discuss what you see. |

The **Live** box shows the average speed (red when below 40 km/h), how many vehicles are
on the road, how many are waiting to enter, the queue on the ramp, the number of vehicles
that got through in the last minute, and a chart of the average speed.

Use the *Delay* field in the `sumo-gui` toolbar to make the simulation faster or slower.

> **Linux:** if you get `No module named tkinter`, run `sudo apt-get install python3-tk`.
> **macOS with Homebrew Python:** run `brew install python-tk`.

### Challenge: beat the jam

Set motorway traffic to **5000 veh/h** and on-ramp traffic to **1000 veh/h**. Using only the
*Traffic manager* controls (speed limit and ramp metering), which group can keep the most
vehicles going through per minute?

## Phantom traffic jam

```bash
python phantom_jam.py
```

Cars drive around a 300 m circle at up to 50 km/h. There is no merge, no accident and
no roadworks, yet after a while a **stop-and-go wave** appears and travels **backwards**
around the ring while the cars drive forwards. This repeats the famous experiment by
Sugiyama et al. (2008) with real drivers on a test track (search YouTube for
*"shockwave traffic jam experiment"*).

| Control | Try this |
|---|---|
| **Number of cars** + **Restart** | With 10 cars nothing happens. With 25 a jam appears. Where is the tipping point? |
| **Driver imperfection** | At *perfect* (0) the jam dissolves. The more drivers hesitate, the faster jams form. |
| **Brake!** | One random driver (pink circle) brakes hard for a moment. Watch the wave travel backwards. |
| **Pause** | Freeze the ring to point at the wave. |

Questions for the class: Who caused the jam? Why does the jam move backwards? How could
automated (perfect) cars help?

## Demo

**Introduction — how SUMO works.** Open the three files in `net/` and `detectors.add.xml`.
Network = nodes + edges + connections; demand = flows of vehicle types; TraCI = Python
controlling the simulation step by step.

**Act 1: free flow.**

```bash
python run_demo.py --scenario light
```

Vehicles are coloured **by speed** (red = slow, green = fast). If they are not, open
*Edit → Edit Visualisation…* (the colour-wheel button in the toolbar), go to the
*Vehicles* tab and choose **by speed** in the *Color* list. Vehicles from the ramp
use the acceleration lane and merge without problems. The terminal prints the detector
values for each simulated minute.

**Act 2: peak hour, the merge breaks down.**

```bash
python run_demo.py --scenario peak
```

Demand rises to its peak. Ramp vehicles force their way in at the end of the acceleration
lane, the mainline brakes, and a queue (red vehicles) grows **backwards** past the upstream
detector. Talk about capacity drop and stop-and-go waves. Note the TTS printed at the end.

**Act 3: ramp metering with ALINEA.**

```bash
python run_demo.py --scenario peak --control alinea
```

Every simulated minute the controller reads the downstream occupancy and updates the
metering rate:

  r(k) = r(k−1) + K_R · (o_target − o_down)

The ramp signal lets one vehicle through per green. Vehicles now wait on the ramp instead of
the mainline staying jammed. Show the `rate` column in the terminal changing.

**Compare and discuss.**

```bash
python compare.py
```

Questions for the class: Did total time spent go down? Who pays the price (ramp drivers vs.
motorway drivers)? What happens if the ramp queue spills back into the city?

Use `--delay 0` to speed up the GUI or `--delay 100` to slow it down.
If the GUI window looks empty, click **Recenter View** (the house icon in the toolbar),
then zoom in on the merge with the mouse wheel.

## Things to tune before class

The numbers have not been calibrated. Run the three acts once with `--nogui` and check:

* **Act 2 must jam.** If it does not, raise `"peak"` in `SCENARIOS` in `run_demo.py`
  (e.g. `(5000, 1100)`). If it jams too hard, lower it.
* **Act 3 should beat Act 2 on TTS.** If it does not, try another target occupancy,
  e.g. `--target 12` or `--target 20` (critical occupancy depends on the vehicle model).

## Exercises for students (after the demo)

1. Change the length of the acceleration lane (`n2` in `geneva_merge.nod.xml`). What happens?
2. Increase the truck share `TRUCK_SHARE`.
3. Change the gain `K_R` or the target occupancy. Is the controller stable?
4. Replace the car-following model with EIDM, used in the Geneva digital twin:
   add `carFollowModel="EIDM"` to the `vType`s.
5. Plot the fundamental diagram (flow vs. occupancy) from `out/loops.xml`.
