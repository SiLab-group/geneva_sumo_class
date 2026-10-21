# SUMO demo: motorway traffic to play with

Two interactive traffic simulations built with [SUMO](https://eclipse.dev/sumo/).
Each opens the SUMO window with the moving cars and a control window with sliders
and buttons. Every change shows on the road within seconds.

| Program | What it shows |
|---|---|
| `control_panel.py` | A motorway on-ramp, modelled on the Geneva motorway digital twin. You control the traffic, the speed limit, the ramp traffic light and roadworks. |
| `phantom_jam.py` | Cars on a ring road. A traffic jam appears with no cause at all. |

Vehicles are coloured **by speed**: green is fast, red is slow or standing.

## Installation

You need **Python 3.9 or newer** and **SUMO 1.28**. The `pip` command below installs
SUMO 1.28 inside a virtual environment on every system. If the SUMO window (`sumo-gui`)
does not open, install SUMO 1.28 with the system installer for your operating system as
well; older SUMO releases are at https://sumo.dlr.de/releases/.

### Windows

1. Install Python from https://www.python.org/downloads/ (tick *Add python.exe to PATH*).
2. Open *Command Prompt* in the `geneva_demo` folder and run:

   ```bat
   py -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Optional system installer: the Windows installer (`.msi`) from
   https://sumo.dlr.de/docs/Downloads.php sets `SUMO_HOME` automatically.

### Linux (Ubuntu / Debian)

1. Install the Python tools:

   ```bash
   sudo apt-get install python3 python3-venv python3-pip python3-tk
   ```

2. In the `geneva_demo` folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Optional system packages:

   ```bash
   sudo add-apt-repository ppa:sumo/stable
   sudo apt-get update
   sudo apt-get install sumo sumo-tools sumo-doc
   export SUMO_HOME=/usr/share/sumo
   ```

### macOS

1. Install Python from https://www.python.org/downloads/. With Homebrew Python, also run
   `brew install python-tk` for the control window.
2. In the `geneva_demo` folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. If `sumo-gui` does not open, install SUMO with Homebrew:

   ```bash
   brew tap dlr-ts/sumo
   brew install sumo
   export SUMO_HOME="$(brew --prefix sumo)/share/sumo"
   ```

   Add the `export` line to `~/.zshrc` to keep it. The macOS installer from
   https://sumo.dlr.de/docs/Downloads.php is an alternative.

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
