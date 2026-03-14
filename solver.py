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
    Series RC simulator with two modes:

    charge:
        dVc/dt = (V_source - Vc) / (R C)

    discharge:
        dVc/dt = -Vc / (R C)

    Conventions:
    - I > 0 means current in the charging direction
    - discharge therefore gives I < 0
    """

    def __init__(
        self,
        circuit: SeriesRCCircuit,
        dt: float = 0.01,
        mode: str = "charge",
        initial_capacitor_voltage: float = 0.0,
    ):
        if dt <= 0:
            raise ValueError("dt must be positive.")
        if mode not in {"charge", "discharge"}:
            raise ValueError("mode must be 'charge' or 'discharge'.")

        self.circuit = circuit
        self.dt = float(dt)
        self.mode = mode
        self.initial_capacitor_voltage = float(initial_capacitor_voltage)
        self.state = SimulationState()

        self.history = {
            "t": [],
            "Vc": [],
            "I": [],
            "Q": [],
            "Vr": [],
        }

        self.reset(mode=mode, initial_capacitor_voltage=self.initial_capacitor_voltage)

    def reset(self, mode: str | None = None, initial_capacitor_voltage: float | None = None):
        if mode is not None:
            if mode not in {"charge", "discharge"}:
                raise ValueError("mode must be 'charge' or 'discharge'.")
            self.mode = mode

        if initial_capacitor_voltage is not None:
            self.initial_capacitor_voltage = float(initial_capacitor_voltage)

        self.state = SimulationState()
        self.state.Vc = self.initial_capacitor_voltage
        self._update_derived()
        self._reset_history()
        self._record_state()

    def toggle_mode(self):
        new_mode = "discharge" if self.mode == "charge" else "charge"
        new_vc_init = 0.0 if new_mode == "charge" else self.circuit.source_voltage
        self.reset(mode=new_mode, initial_capacitor_voltage=new_vc_init)

    def _reset_history(self):
        self.history = {
            "t": [],
            "Vc": [],
            "I": [],
            "Q": [],
            "Vr": [],
        }

    def _record_state(self):
        self.history["t"].append(self.state.t)
        self.history["Vc"].append(self.state.Vc)
        self.history["I"].append(self.state.I)
        self.history["Q"].append(self.state.Q)
        self.history["Vr"].append(self.state.Vr)

    def _update_derived(self):
        V_source = self.circuit.source_voltage
        R = self.circuit.R_eq
        Vc = self.state.Vc

        if self.mode == "charge":
            self.state.I = (V_source - Vc) / R
            self.state.Vr = V_source - Vc
        else:
            self.state.I = -Vc / R
            self.state.Vr = -Vc

        self.state.Q = self.circuit.C_eq * Vc

    def _single_step(self, dt_step: float):
        V_source = self.circuit.source_voltage
        R = self.circuit.R_eq
        C = self.circuit.C_eq

        if self.mode == "charge":
            dVc_dt = (V_source - self.state.Vc) / (R * C)
        else:
            dVc_dt = -(self.state.Vc) / (R * C)

        self.state.Vc += dVc_dt * dt_step
        self.state.t += dt_step

        if self.mode == "charge":
            target = V_source
            if target >= 0 and self.state.Vc > target:
                self.state.Vc = target
            elif target < 0 and self.state.Vc < target:
                self.state.Vc = target
        else:
            if self.initial_capacitor_voltage >= 0 and self.state.Vc < 0:
                self.state.Vc = 0.0
            elif self.initial_capacitor_voltage < 0 and self.state.Vc > 0:
                self.state.Vc = 0.0

        self._update_derived()
        self._record_state()

    def step(self, n_steps: int = 1):
        for _ in range(n_steps):
            self._single_step(self.dt)

    def advance_by(self, delta_t: float):
        if delta_t <= 0:
            return

        remaining = float(delta_t)

        while remaining >= self.dt:
            self._single_step(self.dt)
            remaining -= self.dt

        if remaining > 1e-15:
            self._single_step(remaining)

    def advance_with_limit(self, delta_t: float, max_steps: int):
        """
        Advance by up to delta_t of simulated time, but stop early if max_steps
        have been taken.

        Returns:
            consumed_time (float)
            steps_taken (int)
        """
        if delta_t <= 0 or max_steps <= 0:
            return 0.0, 0

        remaining = float(delta_t)
        consumed = 0.0
        steps_taken = 0

        while remaining > 1e-15 and steps_taken < max_steps:
            dt_step = min(self.dt, remaining)
            self._single_step(dt_step)
            remaining -= dt_step
            consumed += dt_step
            steps_taken += 1

        return consumed, steps_taken

    def analytic_vc(self, t: float) -> float:
        tau = self.circuit.tau
        V_source = self.circuit.source_voltage
        Vc0 = self.initial_capacitor_voltage

        if self.mode == "charge":
            return V_source + (Vc0 - V_source) * math.exp(-t / tau)
        return Vc0 * math.exp(-t / tau)

    def analytic_i(self, t: float) -> float:
        R = self.circuit.R_eq
        V_source = self.circuit.source_voltage
        Vc0 = self.initial_capacitor_voltage
        tau = self.circuit.tau

        if self.mode == "charge":
            return ((V_source - Vc0) / R) * math.exp(-t / tau)
        return -(Vc0 / R) * math.exp(-t / tau)

    def analytic_q(self, t: float) -> float:
        return self.circuit.C_eq * self.analytic_vc(t)

    def is_effectively_finished(self, frac: float = 0.999) -> bool:
        V_source = self.circuit.source_voltage
        Vc0 = self.initial_capacitor_voltage

        if self.mode == "charge":
            scale = max(abs(V_source - Vc0), 1e-15)
            return abs(self.state.Vc - V_source) <= (1.0 - frac) * scale

        scale = max(abs(Vc0), 1e-15)
        return abs(self.state.Vc) <= (1.0 - frac) * scale