# main.py

from circuit import SeriesRCCircuit
from solver import RCCircuitSimulator
from ui import get_user_inputs
from visuals import CircuitVisualizer
from plots import show_simulation_plots


def main():
    try:
        params = get_user_inputs()

        circuit = SeriesRCCircuit(
            source_voltage=params["V_source"],
            resistors=params["resistors"],
            capacitors=params["capacitors"],
        )

        print("\n" + "=" * 60)
        print(circuit.summary())
        print(f"Initial mode: {params['mode']}")
        print(f"Initial capacitor voltage: {params['Vc_init']}")
        print("=" * 60 + "\n")

        simulator = RCCircuitSimulator(
            circuit=circuit,
            dt=params["dt"],
            mode=params["mode"],
            initial_capacitor_voltage=params["Vc_init"],
        )

        visualizer = CircuitVisualizer(
            circuit=circuit,
            simulator=simulator,
            total_time=params["total_time"],
            v_sim=params["v_sim"],
        )
        visualizer.loop()

        show_simulation_plots(simulator)

    except Exception as e:
        print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()