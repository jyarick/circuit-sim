# ui.py

from config import (
    DEFAULT_DT,
    DEFAULT_TOTAL_TIME,
    DEFAULT_V_SIM,
    DEFAULT_SOURCE_VOLTAGE,
    DEFAULT_MODE,
)


def parse_float_list(raw: str):
    values = []
    for chunk in raw.split(","):
        item = chunk.strip()
        if item:
            values.append(float(item))
    return values


def normalize_mode(raw: str) -> str:
    val = raw.strip().lower()
    if val in {"c", "charge", "charging"}:
        return "charge"
    if val in {"d", "discharge", "discharging"}:
        return "discharge"
    raise ValueError("Mode must be 'charge' or 'discharge'.")


def get_user_inputs():
    print("\n=== Series RC Circuit Simulation v4 ===")
    print("Resistors in ohms, capacitors in farads.")
    print("Example resistors: 100, 220, 330")
    print("Example capacitors: 0.001, 0.002\n")

    voltage_raw = input(f"Source voltage V_source [default {DEFAULT_SOURCE_VOLTAGE}]: ").strip()
    resistors_raw = input("Series resistors (comma-separated): ").strip()
    capacitors_raw = input("Series capacitors (comma-separated): ").strip()
    mode_raw = input(f"Mode charge/discharge [default {DEFAULT_MODE}]: ").strip()
    vc_init_raw = input("Initial capacitor voltage Vc_init [blank -> auto by mode]: ").strip()
    dt_raw = input(f"Time step dt in seconds [default {DEFAULT_DT}]: ").strip()
    total_time_raw = input(f"Total simulated time [default {DEFAULT_TOTAL_TIME}]: ").strip()
    v_sim_raw = input(f"Visual speed multiplier v_sim [default {DEFAULT_V_SIM}]: ").strip()

    V_source = float(voltage_raw) if voltage_raw else DEFAULT_SOURCE_VOLTAGE
    resistors = parse_float_list(resistors_raw)
    capacitors = parse_float_list(capacitors_raw)
    mode = normalize_mode(mode_raw) if mode_raw else DEFAULT_MODE
    dt = float(dt_raw) if dt_raw else DEFAULT_DT
    total_time = float(total_time_raw) if total_time_raw else DEFAULT_TOTAL_TIME
    v_sim = float(v_sim_raw) if v_sim_raw else DEFAULT_V_SIM

    if not resistors:
        raise ValueError("You must enter at least one resistor.")
    if not capacitors:
        raise ValueError("You must enter at least one capacitor.")
    if dt <= 0:
        raise ValueError("dt must be positive.")
    if total_time <= 0:
        raise ValueError("total_time must be positive.")
    if v_sim <= 0:
        raise ValueError("v_sim must be positive.")

    if vc_init_raw:
        Vc_init = float(vc_init_raw)
    else:
        Vc_init = 0.0 if mode == "charge" else V_source

    return {
        "V_source": V_source,
        "resistors": resistors,
        "capacitors": capacitors,
        "mode": mode,
        "Vc_init": Vc_init,
        "dt": dt,
        "total_time": total_time,
        "v_sim": v_sim,
    }