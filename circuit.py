# circuit.py

from dataclasses import dataclass, field
from typing import List
from config import MIN_RESISTANCE, MIN_CAPACITANCE


@dataclass
class SeriesRCCircuit:
    source_voltage: float
    resistors: List[float] = field(default_factory=list)
    capacitors: List[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.resistors:
            raise ValueError("At least one resistor is required.")
        if not self.capacitors:
            raise ValueError("At least one capacitor is required.")

        self.resistors = [float(r) for r in self.resistors]
        self.capacitors = [float(c) for c in self.capacitors]

        for r in self.resistors:
            if r <= 0:
                raise ValueError("All resistor values must be positive.")
        for c in self.capacitors:
            if c <= 0:
                raise ValueError("All capacitor values must be positive.")

    @property
    def R_eq(self) -> float:
        return max(sum(self.resistors), MIN_RESISTANCE)

    @property
    def C_eq(self) -> float:
        inv_sum = sum(1.0 / c for c in self.capacitors)
        if inv_sum <= 0:
            return MIN_CAPACITANCE
        return max(1.0 / inv_sum, MIN_CAPACITANCE)

    @property
    def tau(self) -> float:
        return self.R_eq * self.C_eq

    def summary(self) -> str:
        return (
            f"Series RC Circuit\n"
            f"Source Voltage: {self.source_voltage:.4g} V\n"
            f"Resistors: {self.resistors}\n"
            f"Capacitors: {self.capacitors}\n"
            f"Equivalent Resistance: {self.R_eq:.6g} ohm\n"
            f"Equivalent Capacitance: {self.C_eq:.6g} F\n"
            f"Time Constant tau = RC: {self.tau:.6g} s"
        )