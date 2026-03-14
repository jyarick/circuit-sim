# visuals.py

import math
import time
import turtle

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BG_COLOR,
    WIRE_COLOR,
    TEXT_COLOR,
    ACCENT_COLOR,
    CURRENT_COLOR,
    CAP_POS_COLOR,
    CAP_NEG_COLOR,
    RESISTOR_COLOR,
    BATTERY_COLOR,
    CHARGE_COLOR,
    GRID_COLOR,
    WARNING_COLOR,
    LOOP_LEFT,
    LOOP_RIGHT,
    LOOP_TOP,
    LOOP_BOTTOM,
    BOTTOM_WIRE_Y,
    NUM_CHARGE_MARKERS,
    FPS_BASE_DELAY_MS,
    MAX_PHYSICS_STEPS_PER_FRAME,
    INFO_POS,
    TITLE_POS,
    HELP_POS,
    COMPONENT_LABEL_OFFSET_Y,
)


class CircuitVisualizer:
    def __init__(self, circuit, simulator, total_time, v_sim):
        self.circuit = circuit
        self.simulator = simulator
        self.total_time = total_time
        self.v_sim = v_sim

        self.paused = False
        self.quit_requested = False
        self.finished = False
        self.flash_message = ""
        self.flash_message_expire_time = 0.0
        

        self.last_wall_time = time.perf_counter()
        self.sim_time_accumulator = 0.0

        self.screen = turtle.Screen()
        self.screen.setup(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.screen.bgcolor(BG_COLOR)
        self.screen.title("Series RC Circuit Simulation v4")
        self.screen.tracer(0, 0)

        self.drawer = turtle.Turtle(visible=False)
        self.drawer.speed(0)
        self.drawer.pensize(3)

        self.info_writer = turtle.Turtle(visible=False)
        self.info_writer.speed(0)
        self.info_writer.color(TEXT_COLOR)
        self.info_writer.penup()

        self.title_writer = turtle.Turtle(visible=False)
        self.title_writer.speed(0)
        self.title_writer.color(ACCENT_COLOR)
        self.title_writer.penup()

        self.help_writer = turtle.Turtle(visible=False)
        self.help_writer.speed(0)
        self.help_writer.color(TEXT_COLOR)
        self.help_writer.penup()

        self.status_writer = turtle.Turtle(visible=False)
        self.status_writer.speed(0)
        self.status_writer.color(WARNING_COLOR)
        self.status_writer.penup()

        self.component_positions = self._compute_component_positions()
        self.path_points, self.path_lengths, self.total_path_length = self._build_loop_path()
        self.marker_distances = [
            i * self.total_path_length / NUM_CHARGE_MARKERS
            for i in range(NUM_CHARGE_MARKERS)
        ]
        self.markers = [self._make_charge_marker() for _ in range(NUM_CHARGE_MARKERS)]

        self._bind_keys()
        self.refresh()

    def decrease_speed(self):
        old_speed = self.v_sim

        if self.v_sim <= 0.125:
            self.set_flash_message(f"speed min = {self.v_sim:g}x")
            self.last_wall_time = time.perf_counter()
            self.refresh()
            return

        self.v_sim = max(0.125, self.v_sim / 2.0)
        self.last_wall_time = time.perf_counter()

        if self.v_sim != old_speed:
            self.set_flash_message(f"speed = {self.v_sim:g}x")

        self.refresh()

    def increase_speed(self):
        old_speed = self.v_sim

        if self.v_sim >= 64.0:
            self.set_flash_message(f"speed max = {self.v_sim:g}x")
            self.last_wall_time = time.perf_counter()
            self.refresh()
            return

        self.v_sim = min(64.0, self.v_sim * 2.0)
        self.last_wall_time = time.perf_counter()

        if self.v_sim != old_speed:
            self.set_flash_message(f"speed = {self.v_sim:g}x")

        self.refresh()

    def _bind_keys(self):
        self.screen.listen()

        self.screen.onkey(self.toggle_pause, "space")
        self.screen.onkey(self.reset_simulation, "r")
        self.screen.onkey(self.toggle_mode, "m")
        self.screen.onkey(self.request_quit, "q")

        # Speed controls: bind both Tk-style names and literal keys
        self.screen.onkey(self.decrease_speed, "bracketleft")
        self.screen.onkey(self.increase_speed, "bracketright")
        self.screen.onkey(self.decrease_speed, "[")
        self.screen.onkey(self.increase_speed, "]")

    def _make_charge_marker(self):
        marker = turtle.Turtle()
        marker.shape("circle")
        marker.shapesize(0.55, 0.55)
        marker.penup()
        marker.speed(0)
        marker.color(CHARGE_COLOR)
        return marker

    def toggle_pause(self):
        self.paused = not self.paused
        self.last_wall_time = time.perf_counter()
        self.set_flash_message("paused" if self.paused else "running")
        self.refresh()

    def reset_simulation(self):
        self.simulator.reset(mode=self.simulator.mode)
        self._reset_markers()
        self.sim_time_accumulator = 0.0
        self.last_wall_time = time.perf_counter()
        self.finished = False
        self.set_flash_message("reset")
        self.refresh()

    def toggle_mode(self):
        self.simulator.toggle_mode()
        self._reset_markers()
        self.sim_time_accumulator = 0.0
        self.last_wall_time = time.perf_counter()
        self.finished = False
        self.set_flash_message(f"mode = {self.simulator.mode}")
        self.refresh()

    def request_quit(self):
        self.quit_requested = True
        try:
            self.screen.bye()
        except turtle.Terminator:
            pass

    def _reset_markers(self):
        self.marker_distances = [
            i * self.total_path_length / NUM_CHARGE_MARKERS
            for i in range(NUM_CHARGE_MARKERS)
        ]

    def set_flash_message(self, message, duration=1.2):
        self.flash_message = message
        self.flash_message_expire_time = time.perf_counter() + duration

    def _update_flash_message(self):
        now = time.perf_counter()

        if now <= self.flash_message_expire_time and self.flash_message:
            self.status_writer.goto(-40, 315)
            self.status_writer.color(ACCENT_COLOR)
            self.status_writer.write(
                self.flash_message,
                align="left",
                font=("Arial", 14, "bold"),
            )

    def _compute_component_positions(self):
        positions = {}

        nR = len(self.circuit.resistors)
        nC = len(self.circuit.capacitors)

        top_margin = 120
        top_span = (LOOP_RIGHT - LOOP_LEFT) - 2 * top_margin

        if nR == 1:
            resistor_xs = [(LOOP_LEFT + LOOP_RIGHT) / 2]
        else:
            resistor_xs = [
                LOOP_LEFT + top_margin + i * top_span / (nR - 1)
                for i in range(nR)
            ]
        positions["resistors"] = [(x, LOOP_TOP) for x in resistor_xs]

        right_x = LOOP_RIGHT
        cap_margin = 70
        cap_span = (LOOP_TOP - LOOP_BOTTOM) - 2 * cap_margin

        if nC == 1:
            capacitor_ys = [(LOOP_TOP + LOOP_BOTTOM) / 2]
        else:
            capacitor_ys = [
                LOOP_TOP - cap_margin - i * cap_span / (nC - 1)
                for i in range(nC)
            ]
        positions["capacitors"] = [(right_x, y) for y in capacitor_ys]

        positions["battery"] = (LOOP_LEFT, 0)
        return positions

    def _build_loop_path(self):
        pts = [
            (LOOP_LEFT, BOTTOM_WIRE_Y),
            (LOOP_RIGHT, BOTTOM_WIRE_Y),
            (LOOP_RIGHT, LOOP_TOP),
            (LOOP_LEFT, LOOP_TOP),
            (LOOP_LEFT, BOTTOM_WIRE_Y),
        ]

        lengths = []
        total = 0.0
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            seg_len = math.hypot(x2 - x1, y2 - y1)
            lengths.append(seg_len)
            total += seg_len

        return pts, lengths, total

    def _point_on_path(self, distance):
        distance %= self.total_path_length
        accumulated = 0.0

        for i, seg_len in enumerate(self.path_lengths):
            if accumulated + seg_len >= distance:
                x1, y1 = self.path_points[i]
                x2, y2 = self.path_points[i + 1]
                frac = (distance - accumulated) / seg_len if seg_len > 0 else 0.0
                return x1 + frac * (x2 - x1), y1 + frac * (y2 - y1)
            accumulated += seg_len

        return self.path_points[-1]

    def _draw_line(self, x1, y1, x2, y2, color=WIRE_COLOR, pensize=3):
        self.drawer.penup()
        self.drawer.goto(x1, y1)
        self.drawer.pendown()
        self.drawer.color(color)
        self.drawer.pensize(pensize)
        self.drawer.goto(x2, y2)
        self.drawer.penup()

    def _draw_text(self, x, y, text, color=TEXT_COLOR, align="center", font=("Arial", 11, "normal")):
        self.drawer.penup()
        self.drawer.goto(x, y)
        self.drawer.color(color)
        self.drawer.write(text, align=align, font=font)

    def _draw_grid(self):
        spacing = 80
        for x in range(-560, 561, spacing):
            self._draw_line(x, -360, x, 360, color=GRID_COLOR, pensize=1)
        for y in range(-320, 321, spacing):
            self._draw_line(-580, y, 580, y, color=GRID_COLOR, pensize=1)

    def _draw_battery(self):
        x, y = self.component_positions["battery"]

        self._draw_line(LOOP_LEFT, LOOP_BOTTOM, LOOP_LEFT, y - 80, color=WIRE_COLOR, pensize=3)
        self._draw_line(LOOP_LEFT, y + 80, LOOP_LEFT, LOOP_TOP, color=WIRE_COLOR, pensize=3)

        self._draw_line(x - 20, y - 50, x - 20, y + 50, color=BATTERY_COLOR, pensize=3)
        self._draw_line(x + 20, y - 80, x + 20, y + 80, color=BATTERY_COLOR, pensize=5)

        self._draw_text(x + 55, y + 95, f"Battery\n{self.circuit.source_voltage:.3g} V", color=BATTERY_COLOR)

    def _draw_resistor(self, x, y, value, label):
        self._draw_line(x - 45, y, x - 30, y, color=WIRE_COLOR, pensize=3)
        self._draw_line(x + 30, y, x + 45, y, color=WIRE_COLOR, pensize=3)

        pts = [
            (x - 30, y),
            (x - 20, y + 12),
            (x - 10, y - 12),
            (x, y + 12),
            (x + 10, y - 12),
            (x + 20, y + 12),
            (x + 30, y),
        ]
        self.drawer.penup()
        self.drawer.goto(pts[0])
        self.drawer.pendown()
        self.drawer.color(RESISTOR_COLOR)
        self.drawer.pensize(3)
        for pt in pts[1:]:
            self.drawer.goto(pt)
        self.drawer.penup()

        self._draw_text(x, y + COMPONENT_LABEL_OFFSET_Y, f"{label}: {value:.3g} Ω", color=RESISTOR_COLOR)

    def _draw_capacitor(self, x, y, value, label):
        self._draw_line(x, y + 40, x, y + 12, color=WIRE_COLOR, pensize=3)
        self._draw_line(x, y - 12, x, y - 40, color=WIRE_COLOR, pensize=3)

        self._draw_line(x - 18, y + 12, x + 18, y + 12, color=CAP_POS_COLOR, pensize=4)
        self._draw_line(x - 18, y - 12, x + 18, y - 12, color=CAP_NEG_COLOR, pensize=4)

        self._draw_text(x + 92, y - 6, f"{label}: {value:.3g} F", color=ACCENT_COLOR, align="left")

    def _draw_outer_wires(self):
        self._draw_line(LOOP_LEFT, LOOP_BOTTOM, LOOP_RIGHT, LOOP_BOTTOM, color=WIRE_COLOR, pensize=3)
        self._draw_line(LOOP_LEFT, LOOP_TOP, LOOP_RIGHT, LOOP_TOP, color=WIRE_COLOR, pensize=2)
        self._draw_line(LOOP_RIGHT, LOOP_TOP, LOOP_RIGHT, LOOP_BOTTOM, color=WIRE_COLOR, pensize=2)

    def _draw_static_scene(self):
        self.drawer.clear()
        self._draw_grid()
        self._draw_outer_wires()
        self._draw_battery()

        for i, ((x, y), r) in enumerate(zip(self.component_positions["resistors"], self.circuit.resistors), start=1):
            self._draw_resistor(x, y, r, f"R{i}")

        for i, ((x, y), c) in enumerate(zip(self.component_positions["capacitors"], self.circuit.capacitors), start=1):
            self._draw_capacitor(x, y, c, f"C{i}")

        self.title_writer.clear()
        self.title_writer.goto(*TITLE_POS)
        self.title_writer.write(
            "Series RC Circuit Simulation v4",
            align="left",
            font=("Arial", 18, "bold"),
        )

    def _update_info_panel(self):
        s = self.simulator.state
        self.info_writer.clear()
        self.info_writer.goto(*INFO_POS)

        text = (
            f"mode = {self.simulator.mode}\n"
            f"t = {s.t:.4f} s\n"
            f"I = {s.I:.6g} A\n"
            f"V_C = {s.Vc:.6g} V\n"
            f"V_R = {s.Vr:.6g} V\n"
            f"Q = {s.Q:.6g} C\n"
            f"V_source = {self.circuit.source_voltage:.6g} V\n"
            f"Vc_init = {self.simulator.initial_capacitor_voltage:.6g} V\n"
            f"R_eq = {self.circuit.R_eq:.6g} Ω\n"
            f"C_eq = {self.circuit.C_eq:.6g} F\n"
            f"τ = RC = {self.circuit.tau:.6g} s\n"
            f"dt_phys = {self.simulator.dt:.6g} s\n"
            f"v_sim = {self.v_sim:.3g}x"
        )
        self.info_writer.write(text, align="left", font=("Arial", 13, "normal"))

    def _update_help_panel(self):
        self.help_writer.clear()
        self.help_writer.goto(*HELP_POS)
        self.help_writer.write(
            "[space] pause/resume    [r] reset    [m] mode    "
            "[ / ] speed down/up    [q] quit",
            align="left",
            font=("Arial", 12, "normal"),
        )

    def _update_status_panel(self):
        self.status_writer.clear()
        status = "PAUSED" if self.paused else "RUNNING"
        color = WARNING_COLOR if self.paused else CURRENT_COLOR
        self.status_writer.goto(250, 315)
        self.status_writer.color(color)
        self.status_writer.write(status, align="left", font=("Arial", 14, "bold"))

    def _update_capacitor_visual_state(self):
        s = self.simulator.state
        scale = max(abs(self.circuit.source_voltage), abs(self.simulator.initial_capacitor_voltage), 1e-15)
        frac = max(0.0, min(1.0, abs(s.Vc) / scale))

        x = LOOP_RIGHT + 110
        y = 100
        width = 24 + 55 * frac

        self._draw_text(x - 20, y + 65, "Capacitor Charge", color=TEXT_COLOR)
        self._draw_line(x - width / 2, y + 20, x + width / 2, y + 20, color=CAP_POS_COLOR, pensize=6)
        self._draw_line(x - width / 2, y - 20, x + width / 2, y - 20, color=CAP_NEG_COLOR, pensize=6)
        self._draw_text(x, y - 60, f"|Vc| scale: {100 * frac:.1f}%", color=ACCENT_COLOR)

    def _update_markers(self, wall_dt):
        current = self.simulator.state.I
        speed_pixels_per_sec = 60.0 + 500.0 * abs(current)
        direction = -1 if current < 0 else 1
        delta_distance = direction * speed_pixels_per_sec * wall_dt

        for i, marker in enumerate(self.markers):
            self.marker_distances[i] = (self.marker_distances[i] + delta_distance) % self.total_path_length
            x, y = self._point_on_path(self.marker_distances[i])
            marker.goto(x, y)

    def refresh(self):
        self._draw_static_scene()
        self._update_capacitor_visual_state()
        self._update_info_panel()
        self._update_help_panel()
        self._update_status_panel()
        self._update_flash_message()
        self.screen.update()

    def _finished_banner(self):
        self.status_writer.clear()
        self.status_writer.goto(170, 315)
        self.status_writer.color(ACCENT_COLOR)
        self.status_writer.write("TRANSIENT COMPLETE — press q to close", align="left", font=("Arial", 14, "bold"))

    def loop(self):
        def tick():
            if self.quit_requested:
                return

            now = time.perf_counter()
            wall_dt = now - self.last_wall_time
            self.last_wall_time = now

            if not self.paused and self.simulator.state.t < self.total_time:
                target_sim_dt = self.v_sim * wall_dt
                remaining_to_finish = max(0.0, self.total_time - self.simulator.state.t)
                self.sim_time_accumulator += min(target_sim_dt, remaining_to_finish)

                steps_taken = 0
                remaining_to_finish = max(0.0, self.total_time - self.simulator.state.t)
                requested_advance = min(self.sim_time_accumulator, remaining_to_finish)
                
                consumed, steps_taken = self.simulator.advance_with_limit(
                    requested_advance,
                    MAX_PHYSICS_STEPS_PER_FRAME,
                )
                
                self.sim_time_accumulator -= consumed

                self._update_markers(wall_dt)

            self.refresh()

            if self.simulator.state.t >= self.total_time:
                self.finished = True
                self._finished_banner()
                self.screen.update()

            if not self.quit_requested:
                self.screen.ontimer(tick, FPS_BASE_DELAY_MS)

        tick()
        self.screen.mainloop()