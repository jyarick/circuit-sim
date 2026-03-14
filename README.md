# Circuit Simulation (Series RC Visualizer)

An interactive physics visualization of a **series RC circuit** built using Python and Turtle graphics.

This project simulates capacitor charging and discharging while visualizing:

- current flow
- capacitor voltage
- charge accumulation
- equivalent resistance and capacitance
- the RC time constant

The goal is to provide an **intuitive and educational view of transient circuit behavior**.

---

# Features

- Interactive **series RC circuit simulation**
- Visual circuit layout with:
  - battery
  - resistors
  - capacitors
  - current flow indicators
- Real-time simulation of:
  - capacitor voltage \(V_C\)
  - current \(I\)
  - charge \(Q\)
- Adjustable **simulation playback speed**
- Toggle between **charging and discharging modes**
- Numerical solver with **analytic solution comparison**
- Post-simulation plots for validation

---

# Physics Model

The simulation solves the standard RC differential equation.

### Charging

\[
\frac{dV_C}{dt} = \frac{V_{source}-V_C}{RC}
\]

\[
V_C(t)=V_{source} + (V_C(0)-V_{source})e^{-t/\tau}
\]

### Discharging

\[
\frac{dV_C}{dt} = -\frac{V_C}{RC}
\]

\[
V_C(t)=V_C(0)e^{-t/\tau}
\]

Where:

\[
\tau = RC
\]

is the **time constant** of the circuit.

---

# Controls

| Key | Action |
|----|------|
| `space` | Pause / resume simulation |
| `r` | Reset simulation |
| `m` | Toggle charge / discharge mode |
| `[` | Slow down simulation |
| `]` | Speed up simulation |
| `q` | Quit |

---

# How to Run

Clone the repository:

```bash
git clone https://github.com/yourusername/circuit-sim.git
cd circuit-sim

Run the simulation:
python3 main.py
```

After the visual simulation ends, plots of:
- capacitor voltage
- current
- charge
will be displayed.

## Project Strcuture
circuit_sim/
│
├── main.py          # Entry point
├── config.py        # Simulation constants
├── circuit.py       # Circuit model (R_eq, C_eq, tau)
├── solver.py        # RC differential equation solver
├── visuals.py       # Turtle visualization engine
├── plots.py         # Matplotlib validation plots
├── ui.py            # CLI parameter inputs

## Educational Purpose
This project was built as an educational tool for understanding transient circuit behavior.
The goal is to connect mathematical circuit models with visual intuition.

Students can explore:
- how resistance and capacitance affect charging rate
- how the RC time constant shapes transient response
- how current decays as the capacitor charges

## Acknowlegements
This work was developed by the EQuIPD Grant at the University of Florida in the Department of Materials Science and Engineering at the Herbert Wertheim College of Engineering.

All work CC4.0 Share Alike Non-Commercial.

Early versions of this code were developed during that work, and I would like to acknowledge the contributions of colleagues who helped review and improve the original implementation.

Special thanks to:

The EQuIPD Grant team for supporting the development of educational computational tools.

## Future Improvements
Planned extensions include:

- RLC circuit simulation
- inductors and oscillatory behavior
- AC source visualization
- improved circuit layout system
- additional circuit topologies

## License
Creative Commons CC BY_NC_SA 4.0
Attribution — Noncommercial — ShareAlike