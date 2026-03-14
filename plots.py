# plots.py

import matplotlib.pyplot as plt


def show_simulation_plots(simulator):
    hist = simulator.history
    t_num = hist["t"]
    vc_num = hist["Vc"]
    i_num = hist["I"]
    q_num = hist["Q"]

    if not t_num:
        return

    vc_exact = [simulator.analytic_vc(t) for t in t_num]
    i_exact = [simulator.analytic_i(t) for t in t_num]
    q_exact = [simulator.analytic_q(t) for t in t_num]

    vc_err = [abs(a - b) for a, b in zip(vc_num, vc_exact)]
    i_err = [abs(a - b) for a, b in zip(i_num, i_exact)]
    q_err = [abs(a - b) for a, b in zip(q_num, q_exact)]

    print("\n=== Validation Summary ===")
    print(f"Mode: {simulator.mode}")
    print(f"tau = {simulator.circuit.tau:.6g} s")
    print(f"dt = {simulator.dt:.6g} s")
    print(f"dt/tau = {simulator.dt / simulator.circuit.tau:.6g}")
    print(f"max |Vc_num - Vc_exact| = {max(vc_err):.6e} V")
    print(f"max |I_num - I_exact|  = {max(i_err):.6e} A")
    print(f"max |Q_num - Q_exact|  = {max(q_err):.6e} C")

    plt.figure(figsize=(9, 5))
    plt.plot(t_num, vc_num, label="Vc numerical")
    plt.plot(t_num, vc_exact, linestyle="--", label="Vc analytic")
    plt.xlabel("Time (s)")
    plt.ylabel("Capacitor Voltage (V)")
    plt.title("Capacitor Voltage vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(9, 5))
    plt.plot(t_num, i_num, label="I numerical")
    plt.plot(t_num, i_exact, linestyle="--", label="I analytic")
    plt.xlabel("Time (s)")
    plt.ylabel("Current (A)")
    plt.title("Current vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(9, 5))
    plt.plot(t_num, q_num, label="Q numerical")
    plt.plot(t_num, q_exact, linestyle="--", label="Q analytic")
    plt.xlabel("Time (s)")
    plt.ylabel("Charge (C)")
    plt.title("Charge vs Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()