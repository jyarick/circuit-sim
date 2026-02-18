import turtle
import math
import random
from dataclasses import dataclass

# ----------------------------
# Polyline helpers
# ----------------------------

def polyline_lengths(pts):
    return [math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]

def position_dir_on_polyline(pts, seglens, s):
    """
    Return (x,y, ux,uy) at distance s along the polyline,
    where (ux,uy) is the unit tangent direction of the local segment.
    """
    for i, L in enumerate(seglens):
        if s <= L:
            x1,y1 = pts[i]
            x2,y2 = pts[i+1]
            if L == 0:
                return x1,y1, 1.0, 0.0
            u = s / L
            x = x1 + u*(x2-x1)
            y = y1 + u*(y2-y1)
            ux = (x2-x1)/L
            uy = (y2-y1)/L
            return x,y, ux,uy
        s -= L
    # fallback at end
    x1,y1 = pts[-2]
    x2,y2 = pts[-1]
    L = math.hypot(x2-x1, y2-y1) or 1.0
    return pts[-1][0], pts[-1][1], (x2-x1)/L, (y2-y1)/L

# ----------------------------
# Template geometry
# ----------------------------

class RectLoopTemplate:
    def __init__(self, width, height, margin=24, wire_thickness=12):
        self.W = width
        self.H = height
        self.margin = margin
        self.t = wire_thickness

        self.outer_inset = margin
        self.inner_inset = margin + wire_thickness
        self.mid_inset   = margin + wire_thickness/2

    def _rect_path(self, inset):
        x = self.W/2 - inset
        y = self.H/2 - inset
        return [(-x,-y), (-x, y), ( x, y), ( x,-y), (-x,-y)]

    def outer_path(self): return self._rect_path(self.outer_inset)
    def inner_path(self): return self._rect_path(self.inner_inset)
    def mid_path(self):   return self._rect_path(self.mid_inset)

# ----------------------------
# Components (data only)
# ----------------------------

@dataclass(frozen=True)
class Battery:
    V: float

@dataclass(frozen=True)
class Resistor:
    R: float
    name: str

@dataclass(frozen=True)
class Capacitor:
    C: float
    name: str

# ----------------------------
# Physics (series loop)
# ----------------------------

class SeriesRCPhysics:
    def __init__(self, V: float, resistors: list[Resistor], capacitors: list[Capacitor]):
        self.V = float(V)
        self.resistors = resistors
        self.capacitors = capacitors

        self.Req = sum(r.R for r in resistors) if resistors else float("inf")
        if capacitors:
            inv = sum(1.0/c.C for c in capacitors)
            self.Ceq = 1.0/inv if inv > 0 else 0.0
        else:
            self.Ceq = None

        self.tau = (self.Req * self.Ceq) if self.Ceq is not None else None

    def current(self, t: float) -> float:
        """Return I(t) in A for a step applied at t=0."""
        if not math.isfinite(self.Req) or self.Req <= 0:
            return 0.0
        if self.Ceq is None:
            return self.V / self.Req
        if self.tau is None or self.tau <= 0:
            return 0.0
        return (self.V / self.Req) * math.exp(-t / self.tau)

# ----------------------------
# Turtle rendering
# ----------------------------

class TurtleRenderer:
    def __init__(self, screen):
        self.screen = screen

        self.wire = turtle.Turtle(visible=False)
        self.wire.color("black")
        self.wire.pensize(3)
        self.wire.speed(0)

        self.sym = turtle.Turtle(visible=False)
        self.sym.color("black")
        self.sym.pensize(3)
        self.sym.speed(0)

    def draw_polyline(self, pts):
        self.wire.up()
        self.wire.goto(*pts[0])
        self.wire.down()
        for p in pts[1:]:
            self.wire.goto(*p)

    def draw_wire(self, outer_pts, inner_pts):
        self.draw_polyline(outer_pts)
        self.draw_polyline(inner_pts)

    def draw_battery_at(self, x,y, ux,uy, plate_gap=7, short=10, long=18):
        # normal vector
        nx, ny = -uy, ux
        # plate centers along tangent
        c1x, c1y = x - ux*plate_gap, y - uy*plate_gap
        c2x, c2y = x + ux*plate_gap, y + uy*plate_gap

        def plate(cx, cy, length):
            hx, hy = nx*(length/2), ny*(length/2)
            self.sym.up(); self.sym.goto(cx-hx, cy-hy); self.sym.down(); self.sym.goto(cx+hx, cy+hy)

        plate(c1x, c1y, short)
        plate(c2x, c2y, long)

    def draw_resistor_at(self, x,y, ux,uy, length=28, zigzags=5, amp=4):
        """
        Smaller resistor: reduced amp + slightly shorter length.
        """
        nx, ny = -uy, ux
        half = length/2
        # endpoints along tangent
        x1, y1 = x - ux*half, y - uy*half
        x2, y2 = x + ux*half, y + uy*half

        # zigzag points
        steps = zigzags*2
        stepL = length / steps

        self.sym.up(); self.sym.goto(x1, y1); self.sym.down()
        for k in range(1, steps):
            px = x1 + ux*(k*stepL)
            py = y1 + uy*(k*stepL)
            sign = 1 if (k % 2 == 1) else -1
            px += nx * amp * sign
            py += ny * amp * sign
            self.sym.goto(px, py)
        self.sym.goto(x2, y2)

    def draw_capacitor_at(self, x,y, ux,uy, gap=6, plate=16):
        """
        Two plates perpendicular to wire direction.
        """
        nx, ny = -uy, ux
        c1x, c1y = x - ux*gap, y - uy*gap
        c2x, c2y = x + ux*gap, y + uy*gap

        def plate_line(cx, cy):
            hx, hy = nx*(plate/2), ny*(plate/2)
            self.sym.up(); self.sym.goto(cx-hx, cy-hy); self.sym.down(); self.sym.goto(cx+hx, cy+hy)

        plate_line(c1x, c1y)
        plate_line(c2x, c2y)

# ----------------------------
# Electron markers
# ----------------------------

@dataclass
class Electron:
    s: float
    t: turtle.Turtle

class ElectronSystem:
    def __init__(self, path_pts, n=35):
        self.pts = path_pts
        self.seglens = polyline_lengths(path_pts)
        self.totalL = sum(self.seglens) or 1.0

        self.electrons = []
        for _ in range(n):
            tt = turtle.Turtle()
            tt.shape("circle")
            tt.shapesize(0.25, 0.25, 0.1)
            tt.color("#1f77b4")
            tt.up()
            self.electrons.append(Electron(s=random.random()*self.totalL, t=tt))

    def update(self, dt, speed):
        for e in self.electrons:
            e.s = (e.s + speed*dt) % self.totalL
            x,y,_,_ = position_dir_on_polyline(self.pts, self.seglens, e.s)
            e.t.goto(x,y)

# ----------------------------
# Layout of components along path
# ----------------------------

def component_centers_along_path(totalL, n_components, start_frac=0.08, end_frac=0.92):
    """
    Returns s positions for component centers spaced along the loop.
    """
    if n_components <= 0:
        return []
    a = totalL*start_frac
    b = totalL*end_frac
    if n_components == 1:
        return [(a+b)/2]
    step = (b-a)/(n_components-1)
    return [a + i*step for i in range(n_components)]

# ----------------------------
# Prompts
# ----------------------------

def parse_floats_csv(s):
    s = s.strip()
    if not s:
        return []
    return [float(x.strip()) for x in s.split(",") if x.strip()]

def prompt_order(resistors, capacitors):
    """
    Ask for an order like: B R1 R2 C1
    If blank, auto-order: B then all R then all C.
    """
    tokens = []
    if resistors:
        tokens += [r.name for r in resistors]
    if capacitors:
        tokens += [c.name for c in capacitors]

    print("\nOrder controls drawing placement ONLY (series physics uses totals).")
    print("Available tokens:", "B", *tokens)
    s = input("Enter order (e.g., 'B R1 R2 C1'), or press Enter for default: ").strip()
    if not s:
        return ["B"] + tokens

    order = s.split()
    # validate: must include B exactly once and use each token at most once
    if order.count("B") != 1:
        print("Invalid order (must include exactly one 'B'). Using default.")
        return ["B"] + tokens

    allowed = set(["B"] + tokens)
    if any(tok not in allowed for tok in order):
        print("Invalid token found. Using default.")
        return ["B"] + tokens

    # If user omitted some tokens, append them at end
    used = set(order)
    for tok in ["B"] + tokens:
        if tok not in used:
            order.append(tok)
            used.add(tok)
    return order

# ----------------------------
# Canvas / simulation
# ----------------------------

class Canvas:
    def __init__(self, width=240, height=240, pixel_size=700):
        self.W = width
        self.H = height
        self.screen = turtle.Screen()
        self.screen.bgcolor("white")
        self.screen.title("Series Circuit (turtle) — centered coords")
        self.screen.setup(pixel_size, pixel_size)
        self.screen.setworldcoordinates(-width/2, -height/2, width/2, height/2)
        self.screen.tracer(0)
        self.renderer = TurtleRenderer(self.screen)

    def run(self, template, physics, order, speed_scale=1.0, time_scale=1.0):
        outer_pts = template.outer_path()
        inner_pts = template.inner_path()
        mid_pts   = template.mid_path()

        self.renderer.draw_wire(outer_pts, inner_pts)

        # Systems
        electrons = ElectronSystem(mid_pts, n=35)

        # Precompute component placement
        seglens = polyline_lengths(mid_pts)
        totalL = sum(seglens) or 1.0
        centers_s = component_centers_along_path(totalL, len(order))

        # Draw components at their assigned centers
        # We'll draw once (static symbols). Motion is only electrons.
        for tok, s0 in zip(order, centers_s):
            x,y,ux,uy = position_dir_on_polyline(mid_pts, seglens, s0)
            if tok == "B":
                self.renderer.draw_battery_at(x,y,ux,uy)
            elif tok.startswith("R"):
                self.renderer.draw_resistor_at(x,y,ux,uy)
            elif tok.startswith("C"):
                self.renderer.draw_capacitor_at(x,y,ux,uy)

        # Animation loop
        dt_wall = 1/60  # seconds per frame (wall-clock target)
        t_phys = 0.0

        # Map current (A) -> world-units/sec
        # k sets visibility; speed_scale is the user knob.
        k = 60.0

        while True:
            # advance physics time (time_scale lets you speed up / slow down charging)
            t_phys += dt_wall * time_scale
            I = physics.current(t_phys)  # amps

            speed = k * abs(I) * speed_scale
            electrons.update(dt_wall, speed=speed)

            self.screen.update()

# ----------------------------
# Main
# ----------------------------

if __name__ == "__main__":
    print("=== Series Circuit (Templates) ===")
    V = float(input("Battery voltage V (e.g., 9): ").strip() or "9")
    R_list = parse_floats_csv(input("Resistors in ohms (comma-separated, e.g., 3,2,5): "))
    C_list = parse_floats_csv(input("Capacitors in farads (comma-separated, e.g., 0.01,0.02) or blank: "))

    resistors = [Resistor(R=R_list[i], name=f"R{i+1}") for i in range(len(R_list))]
    capacitors = [Capacitor(C=C_list[i], name=f"C{i+1}") for i in range(len(C_list))]

    speed_scale = float(input("Visual speed scale (e.g., 1 = normal, 0.3 = slow, 3 = fast): ").strip() or "1")
    time_scale  = float(input("Physics time scale (e.g., 1 = real math time, 5 = faster charging): ").strip() or "1")

    order = prompt_order(resistors, capacitors)

    template = RectLoopTemplate(width=240, height=240, margin=24, wire_thickness=12)
    physics = SeriesRCPhysics(V=V, resistors=resistors, capacitors=capacitors)

    canvas = Canvas(width=240, height=240, pixel_size=700)
    canvas.run(template, physics, order=order, speed_scale=speed_scale, time_scale=time_scale)
