# SUMO demo: the Geneva motorway to play with

An interactive traffic simulation built with [SUMO](https://eclipse.dev/sumo/): an
on-ramp of the Geneva motorway, cut from the Geneva digital twin. `control_panel.py`
opens the SUMO window with the moving cars and a control window with sliders and
buttons for the traffic, the speed limit, the ramp traffic light and roadworks. Every
change shows on the road within seconds.

Vehicles are coloured **by speed** (SUMO's default scale):

| Colour | Speed |
|---|---|
| red | standing or very slow |
| yellow | about 20 km/h |
| green | about 40 km/h |
| cyan | about 80 km/h |
| blue | about 120 km/h |

The scale is listed in `sumo-gui` under *Edit → Edit Visualisation… → Vehicles*.

## Background

This is a simplified demo for students. The motorway on-ramp is a small piece cut out of
the SUMO network of previous work: a digital twin of the Geneva motorway that feeds live
data from the traffic counters of the Swiss Federal Roads Office (FEDRO / OFROU / ASTRA)
into the simulation. The data is open and available on the Open Data Platform Mobility
Switzerland: https://opentransportdata.swiss

> K. Kušić, R. Schumann, E. Ivanjko, *A digital twin in transportation: Real-time synergy
> of traffic data streams and simulation for virtualizing motorway dynamics*,
> Advanced Engineering Informatics 55, 2023.
> https://doi.org/10.1016/j.aei.2022.101858

The cut keeps the real road shape, lengths and map position (A1, south-west Geneva,
46.1874 N / 6.0812 E). Behind the road lies the swisstopo aerial photo of the same area
(SWISSIMAGE, © swisstopo). The view is rotated so the motorway runs from left to right on
screen. The demo uses its own traffic: the vehicles come from the sliders, not from
traffic counter data. The DT-GM project is published under the GNU General Public
License v3.

## Installation and running

You need **Python 3.9 or newer** and **SUMO 1.28**. `pip install -r requirements.txt`
installs SUMO 1.28 inside a virtual environment (`.venv` folder) on every system.
Installation is done once; the run steps are repeated every time you open a new terminal.

### Windows

**Install (once)**

1. Install Python from https://www.python.org/downloads/ and tick
   *Add python.exe to PATH* in the installer.
2. Install Git from https://git-scm.com/downloads/win.
3. Open *Command Prompt* (search for `cmd` in the Start menu).
4. Clone the repository into the folder of your choice:

   ```bat
   cd C:\path\to\your\folder
   git clone https://github.com/SiLab-group/geneva_sumo_class.git
   ```

5. Go to the `geneva_sumo_class` folder, create the virtual environment and install SUMO:

   ```bat
   cd geneva_sumo_class
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

**Run**

```bat
cd C:\path\to\your\folder\geneva_sumo_class
.venv\Scripts\activate
python control_panel.py
```

In *PowerShell*, activate with `.venv\Scripts\Activate.ps1`. If PowerShell refuses to run
the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
*Command Prompt*.

If the SUMO window does not open, install SUMO 1.28 with the Windows installer
`sumo-win64-1.28.0.msi` from https://sumo.dlr.de/releases/1.28.0/. It sets `SUMO_HOME`
automatically; open a new *Command Prompt* afterwards.

### Linux (Ubuntu / Debian)

**Install (once)**

1. Install Git, Python, the virtual-environment module and Tkinter for the control window:

   ```bash
   sudo apt-get update
   sudo apt-get install git python3 python3-venv python3-pip python3-tk
   ```

2. Clone the repository into the folder of your choice:

   ```bash
   cd ~/path/to/your/folder
   git clone https://github.com/SiLab-group/geneva_sumo_class.git
   ```

3. Go to the `geneva_sumo_class` folder, create the virtual environment and install SUMO:

   ```bash
   cd geneva_sumo_class
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

**Run**

```bash
cd ~/path/to/your/folder/geneva_sumo_class
source .venv/bin/activate
python control_panel.py
```

If the SUMO window does not open, install the libraries `sumo-gui` uses:

```bash
sudo apt-get install libgl1 libglu1-mesa libxcursor1 libxft2 libxinerama1
```

### macOS

**Install (once)**

1. Install Python from https://www.python.org/downloads/. With Homebrew Python, also run
   `brew install python-tk` for the control window.
2. Install **XQuartz** from https://www.xquartz.org (or `brew install --cask xquartz`).
   The SUMO window (`sumo-gui`) runs on XQuartz. Log out and back in after installing it.
3. Open *Terminal* and clone the repository into the folder of your choice. If macOS
   asks to install the command line developer tools for `git`, click *Install* and run
   the command again:

   ```bash
   cd ~/path/to/your/folder
   git clone https://github.com/SiLab-group/geneva_sumo_class.git
   ```

4. Go to the `geneva_sumo_class` folder, create the virtual environment and install SUMO:

   ```bash
   cd geneva_sumo_class
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

**Run**

```bash
cd ~/path/to/your/folder/geneva_sumo_class
source .venv/bin/activate
python control_panel.py
```

If the terminal keeps printing `Could not connect to TraCI server … Retrying`, the SUMO
window has not started yet. On the first start XQuartz takes a while:

1. Stop the program with **Ctrl+C**.
2. With the virtual environment active, start the SUMO window on its own and wait until
   it appears (up to 30 seconds; it can open behind other windows):

   ```bash
   sumo-gui
   ```

3. Close the SUMO window and run `python control_panel.py` again.

If the SUMO window does not open, install SUMO 1.28 with the macOS installer from
https://sumo.dlr.de/releases/1.28.0/ and set `SUMO_HOME` as the installer describes.

### Check the installation

With the virtual environment active, this shows `Version: 1.28.0`:

```bash
pip show eclipse-sumo
```

## Motorway on-ramp: `control_panel.py`

```bash
python control_panel.py
```

About 1 km of the Geneva motorway, northbound: 2 lanes at 120 km/h and one on-ramp
(870 m with 2 lanes, then a 1-lane loop) that joins through a 310 m acceleration lane.
A traffic light at the end of the loop, 60 m before the merge, controls how many cars
enter the motorway. On screen the cars drive from left to right and the ramp joins from
below.

```
 ES_N11 (2 lanes, 300 m)   ES_N12 (3 lanes, 310 m)   ES_N13 (2 lanes, 340 m)
 ==========================|=======================|==========================>
                          /
                [J19] ---/  ES_N57_onramp1.140
                  |
          ( loop ramp ES_N57_onramp1, 1 lane, 60 km/h )
                  |
 ===== ES_N56_onramp1.90 (2 lanes, 870 m) =====
```

The jam starts at the merge and grows backwards from about **3800 veh/h** on the motorway
plus **1000 veh/h** on the ramp. When it reaches the start of the road, new cars show up
as *Waiting to enter* in the panel.

| Control | Try this |
|---|---|
| **Motorway traffic** / **On-ramp traffic** | Push the traffic up slowly. At what point does the merge jam? |
| **Share of trucks** | Same traffic, more trucks: is it worse? |
| **Speed limit** | During a jam, lower the limit to 80 km/h. Does traffic flow better? |
| **Ramp metering** + **one car every … s** | Hold back the ramp cars with the traffic light. Who wins, who loses? |
| **Close left lane (roadworks)** | The left lane after the merge closes and turns orange. All cars squeeze into the right lane. |
| **Pause** | Freeze the simulation to discuss what you see. |

The **Live** box shows the average speed (red below 40 km/h), the vehicles on the road,
the vehicles waiting to enter, the queue on the ramp, the vehicles that got through in
the last minute, and a chart of the average speed.

**Challenge: beat the jam.** Set motorway traffic to **5000 veh/h** and on-ramp traffic to
**1000 veh/h**. Using only the *Traffic manager* controls, which group gets the most
vehicles through per minute?

## Tips

* The **Simulation speed** slider in the panel sets how fast the simulation runs.
* If the SUMO window looks empty, click **Recenter View** (the house icon in the toolbar)
  and zoom in with the mouse wheel.
* Right-click a car and choose **Start Tracking** to follow it.

## Files

| File | What it is |
|---|---|
| `control_panel.py` | Motorway on-ramp with live controls |
| `net/geneva_cut.net.xml` | The on-ramp cut from the Geneva motorway network |
| `net/aerial/` | swisstopo aerial photo tiles behind the road (© swisstopo) |
| `geneva_merge.sumocfg` | SUMO configuration of the motorway |
| `gui.view.xml` | SUMO window settings: colour by speed |
| `out/` | Generated files: routes and view settings, rebuilt on every start |
| `../tools/cut_geneva.py` | Script that makes the cut from the DT-GM project |
| `../tools/fetch_aerial.py` | Script that downloads the aerial photo tiles from swisstopo |
