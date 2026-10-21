# SUMO demo: motorway traffic to play with

Two interactive traffic simulations built with [SUMO](https://eclipse.dev/sumo/).
Each opens the SUMO window with the moving cars and a control window with sliders
and buttons. Every change shows on the road within seconds.

| Program | What it shows |
|---|---|
| `control_panel.py` | A motorway on-ramp, modelled on the Geneva motorway digital twin. You control the traffic, the speed limit, the ramp traffic light and roadworks. |
| `phantom_jam.py` | Cars on a ring road. A traffic jam appears with no cause at all. |

Vehicles are coloured **by speed**: green is fast, red is slow or standing.

## Installation and running

You need **Python 3.9 or newer** and **SUMO 1.28**. `pip install -r requirements.txt`
installs SUMO 1.28 inside a virtual environment (`venv` folder) on every system.
Installation is done once; the run steps are repeated every time you open a new terminal.

### Windows

**Install (once)**

1. Install Python from https://www.python.org/downloads/ and tick
   *Add python.exe to PATH* in the installer.
2. Open *Command Prompt* (search for `cmd` in the Start menu).
3. Go to the `geneva_demo` folder, create the virtual environment and install SUMO:

   ```bat
   cd C:\path\to\geneva_demo
   py -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

**Run**

```bat
cd C:\path\to\geneva_demo
venv\Scripts\activate
python control_panel.py
```

or `python phantom_jam.py` for the ring road.

In *PowerShell*, activate with `venv\Scripts\Activate.ps1`. If PowerShell refuses to run
the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
*Command Prompt*.

If the SUMO window does not open, install SUMO 1.28 with the Windows installer
`sumo-win64-1.28.0.msi` from https://sumo.dlr.de/releases/1.28.0/. It sets `SUMO_HOME`
automatically; open a new *Command Prompt* afterwards.

### Linux (Ubuntu / Debian)

**Install (once)**

1. Install Python, the virtual-environment module and Tkinter for the control window:

   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-venv python3-pip python3-tk
   ```

2. Go to the `geneva_demo` folder, create the virtual environment and install SUMO:

   ```bash
   cd ~/path/to/geneva_demo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

**Run**

```bash
cd ~/path/to/geneva_demo
source venv/bin/activate
python control_panel.py
```

or `python phantom_jam.py` for the ring road.

If the SUMO window does not open, install the libraries `sumo-gui` uses:

```bash
sudo apt-get install libgl1 libglu1-mesa libxcursor1 libxft2 libxinerama1
```

### macOS

**Install (once)**

1. Install Python from https://www.python.org/downloads/. With Homebrew Python, also run
   `brew install python-tk` for the control window.
2. Open *Terminal*, go to the `geneva_demo` folder, create the virtual environment and
   install SUMO:

   ```bash
   cd ~/path/to/geneva_demo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

**Run**

```bash
cd ~/path/to/geneva_demo
source venv/bin/activate
python control_panel.py
```

or `python phantom_jam.py` for the ring road.

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

A 1.8 km, 3-lane motorway with one on-ramp and a 300 m acceleration lane, like the
junctions on the Geneva motorway in the *Digital Twin – Geneva Motorway* project
(Kušić, Schumann, Ivanjko, 2023). A traffic light on the ramp controls how many cars
enter the motorway.

```
 main_up (3 lanes, 1 km)           accel (4 lanes)    main_down (3 lanes, 0.5 km)
 ==================================|=============|=============================>
                                  /
              ramp_in    [signal]/ ramp_merge
             ------------- r1 --/
```

| Control | Try this |
|---|---|
| **Motorway traffic** / **On-ramp traffic** | Push the traffic up slowly. At what point does the merge jam? |
| **Share of trucks** | Same traffic, more trucks: is it worse? |
| **Speed limit** | During a jam, lower the limit to 80 km/h. Does traffic flow better? |
| **Ramp metering** + **one car every … s** | Hold back the ramp cars with the traffic light. Who wins, who loses? |
| **Close left lane (roadworks)** | An orange block closes the left lane after the merge. |
| **Pause** | Freeze the simulation to discuss what you see. |

The **Live** box shows the average speed (red below 40 km/h), the vehicles on the road,
the vehicles waiting to enter, the queue on the ramp, the vehicles that got through in
the last minute, and a chart of the average speed.

**Challenge: beat the jam.** Set motorway traffic to **5000 veh/h** and on-ramp traffic to
**1000 veh/h**. Using only the *Traffic manager* controls, which group gets the most
vehicles through per minute?

## Phantom traffic jam: `phantom_jam.py`

```bash
python phantom_jam.py
```

Cars drive around a 300 m ring at up to 50 km/h. There is no merge, no accident and no
roadworks, yet a **stop-and-go wave** forms and travels **backwards** around the ring
while the cars drive forwards. The program repeats the experiment by Sugiyama et al.
(2008) with real drivers on a test track (YouTube: *"shockwave traffic jam experiment"*).

| Control | Try this |
|---|---|
| **Number of cars** + **Restart** | Find the number of cars at which the jam appears. |
| **Driver imperfection** | At *perfect* (0) the jam dissolves. The more drivers hesitate, the faster jams form. |
| **Brake!** | One random driver (pink circle) brakes hard for 3 seconds. Watch the wave travel backwards. |
| **Pause** | Freeze the ring to point at the wave. |

Questions for the class: Who caused the jam? Why does the jam move backwards? How could
automated cars help?

## Tips

* The *Delay* field in the `sumo-gui` toolbar sets the simulation speed: 0 is fastest.
* If the SUMO window looks empty, click **Recenter View** (the house icon in the toolbar)
  and zoom in with the mouse wheel.
* Double-click a car, or right-click it and choose **Start Tracking**, to follow it.
* The message "no projection defined" means the road has no GPS coordinates. It does not
  affect the simulation.

## Files

| File | What it is |
|---|---|
| `control_panel.py` | Motorway on-ramp with live controls |
| `phantom_jam.py` | Ring road with live controls |
| `net/geneva_merge.nod.xml` | Junctions (nodes) of the motorway, in metres |
| `net/geneva_merge.edg.xml` | Road sections (edges): lanes and speed limits |
| `net/geneva_merge.con.xml` | Which lane connects to which lane |
| `geneva_merge.sumocfg` | SUMO configuration of the motorway |
| `gui.view.xml` | SUMO window settings: colour by speed |
| `out/` | Generated files: networks and routes, rebuilt on every start |
