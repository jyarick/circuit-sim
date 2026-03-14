# solver.py

import math
from dataclasses import dataclass
from circuit import SeriesRCCircuit


@dataclass
class SimulationState:
    t: float = 0.0
    Vc: float = 0.0
    I: float = 0.0
    Q: float = 0.0
    Vr: float = 0.0


class RCCircuitSimulator:
    """
    Series RC charging simulator using forward Euler time stepping.

    Governing equation:
        dVc/dt = (V0 - Vc) / (R_eq * C_eq)

    Then:
        I = (V0 - Vc) / R_eq
        Q = C_eq * Vc
        Vr = I * R_eq = V0 - Vc
    """

    def __init__(self, circuit: SeriesRCCircuit, dt: float = 0.01):
        if dt <= 0:
            raise ValueError("dt must be positive.")

        self.circuit = circuit
        self.dt = float(dt)
        self.state = SimulationState()
        self._update_derived()

    def reset(self):
        self.state = SimulationState()
        self._update_derived()

    def _update_derived(self):
        V0 = self.circuit.source_voltage
        R = self.circuit.R_eq
        C = self.circuit.C_eq

        self.state.I = (V0 - self.state.Vc) / R
        self.state.Q = C * self.state.Vc
        self.state.Vr = V0 - self.state.Vc

    def step(self, n_steps: int = 1):
        for _ in range(n_steps):
            V0 = self.circuit.source_voltage
            R = self.circuit.R_eq
            C = self.circuit.C_eq

            dVc_dt = (V0 - self.state.Vc) / (R * C)
            self.state.Vc += dVc_dt * self.dt
            self.state.t += self.dt

            # Clamp tiny numerical overshoot
            if V0 >= 0 and self.state.Vc > V0:
                self.state.Vc = V0
            elif V0 < 0 and self.state.Vc < V0:
                self.state.Vc = V0

            self._update_derived()

    def analytic_vc(self, t: float) -> float:
        V0 = self.circuit.source_voltage
        tau = self.circuit.tau
        return V0 * (1.0 - math.exp(-t / tau))

    def analytic_i(self, t: float) -> float:
        V0 = self.circuit.source_voltage
        R = self.circuit.R_eq
        tau = self.circuit.tau
        return (V0 / R) * math.exp(-t / tau)

    def analytic_q(self, t: float) -> float:
        return self.circuit.C_eq * self.analytic_vc(t)

    def is_effectively_finished(self, frac: float = 0.999) -> bool:
        V0 = self.circuit.source_voltage
        if abs(V0) < 1e-15:
            return True
        return abs(self.state.Vc / V0) >= frac