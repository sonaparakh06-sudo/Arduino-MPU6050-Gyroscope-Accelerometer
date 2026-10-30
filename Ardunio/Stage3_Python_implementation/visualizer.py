#!/usr/bin/env python3
"""
Real-time visualizer for the self-leveling platform.

Reads lines like:
    roll:12.34,pitch:-3.20,servo:77.66,dist:101.50
and shows:
  - roll & pitch over time
  - servo angle and distance over time
  - a live "front view" of the tilted board and the self-leveled platform

Data sources (pick one):
  --port COM3        live data from a real Arduino over serial
  --log  data.txt    replay a text log (e.g. copied from the Wokwi Serial Monitor)
  --demo             synthetic data, only for testing the visualizer itself

Add --save out.gif to render a GIF instead of opening a window (log/demo only).
"""

import argparse
import collections
import math
import re
import sys
import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon

SAMPLE_DT = 0.05          # firmware prints every 50 ms
WINDOW = 400              # samples kept on the time plots
FRAME_MS = 50

FIELD = re.compile(r"(\w+)\s*:\s*(-?\d+(?:\.\d+)?)")


def parse_line(line):
    """Return a dict of floats if the line has roll and pitch, else None."""
    d = {k: float(v) for k, v in FIELD.findall(line)}
    if "roll" in d and "pitch" in d:
        d.setdefault("servo", 90.0)
        d.setdefault("dist", 0.0)
        return d
    return None


# ----------------------------- data sources -----------------------------

class SerialSource:
    live = True

    def __init__(self, port, baud):
        try:
            import serial
        except ImportError:
            sys.exit("pyserial is required for --port:  pip install pyserial")
        self.ser = serial.Serial(port, baud, timeout=0.05)
        self.t0 = time.time()

    def poll(self):
        out = []
        while self.ser.in_waiting:
            line = self.ser.readline().decode(errors="ignore")
            s = parse_line(line)
            if s:
                s["t"] = time.time() - self.t0
                out.append(s)
        return out


class LogSource:
    live = False

    def __init__(self, path, speed):
        with open(path, "r", errors="ignore") as f:
            self.samples = [s for s in map(parse_line, f) if s]
        if not self.samples:
            sys.exit(f"No 'roll:...,pitch:...' lines found in {path}")
        self.i = 0
        self.speed = speed

    def total_frames(self):
        return math.ceil(len(self.samples) / self.speed)

    def poll(self):
        out = []
        for _ in range(self.speed):
            if self.i >= len(self.samples):
                break
            s = dict(self.samples[self.i])
            s["t"] = self.i * SAMPLE_DT
            out.append(s)
            self.i += 1
        return out


class DemoSource:
    """Synthetic data to test the visualizer. NOT real sensor data."""
    live = False

    def __init__(self, duration):
        self.n = int(duration / SAMPLE_DT)
        self.i = 0

    def total_frames(self):
        return self.n

    def poll(self):
        if self.i >= self.n:
            return []
        t = self.i * SAMPLE_DT
        roll = 35 * math.sin(2 * math.pi * t / 8)
        pitch = 15 * math.sin(2 * math.pi * t / 5 + 1)
        servo = max(0, min(180, 90 - roll))
        dist = 120 + 60 * math.sin(2 * math.pi * t / 6)
        self.i += 1
        return [{"t": t, "roll": roll, "pitch": pitch, "servo": servo, "dist": dist}]


# ------------------------------- plotting -------------------------------

def rect(angle_deg, w=1.0, h=0.07, cy=0.0):
    """Corners of a flat rectangle rotated counter-clockwise by angle_deg."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    pts = [(-w, -h), (w, -h), (w, h), (-w, h)]
    return [(x * c - y * s, x * s + y * c + cy) for x, y in pts]


def build_figure():
    fig = plt.figure(figsize=(11, 6))
    gs = fig.add_gridspec(2, 2, width_ratios=[2, 1])
    ax_ang = fig.add_subplot(gs[0, 0])
    ax_srv = fig.add_subplot(gs[1, 0], sharex=ax_ang)
    ax_view = fig.add_subplot(gs[:, 1])

    ax_ang.set_ylabel("Angle (deg)")
    ax_ang.set_ylim(-100, 100)
    ax_ang.grid(alpha=0.3)
    (l_roll,) = ax_ang.plot([], [], label="roll")
    (l_pitch,) = ax_ang.plot([], [], label="pitch")
    ax_ang.legend(loc="upper left")

    ax_srv.set_xlabel("Time (s)")
    ax_srv.set_ylabel("Servo (deg)")
    ax_srv.set_ylim(0, 180)
    ax_srv.grid(alpha=0.3)
    (l_srv,) = ax_srv.plot([], [], color="tab:green", label="servo")
    ax_dst = ax_srv.twinx()
    ax_dst.set_ylabel("Distance (cm)")
    ax_dst.set_ylim(0, 400)
    (l_dst,) = ax_dst.plot([], [], color="tab:red", label="distance")
    ax_srv.legend(handles=[l_srv, l_dst], loc="upper left")

    ax_view.set_xlim(-1.4, 1.4)
    ax_view.set_ylim(-1.4, 1.4)
    ax_view.set_aspect("equal")
    ax_view.set_title("Front view")
    ax_view.axis("off")
    ax_view.axhline(0, color="gray", lw=0.8, ls="--")
    board = Polygon(rect(0), closed=True, fc="tab:blue", alpha=0.7, label="sensor board")
    platform = Polygon(rect(0, cy=0.45), closed=True, fc="tab:green", alpha=0.7, label="platform")
    ax_view.add_patch(board)
    ax_view.add_patch(platform)
    ax_view.legend(loc="lower center", ncol=2, fontsize=8)
    txt = ax_view.text(0, -1.25, "", ha="center", fontsize=10)

    fig.suptitle("Self-leveling platform: MPU6050 + servo + HC-SR04")
    fig.tight_layout()
    return fig, dict(ax_ang=ax_ang, ax_srv=ax_srv, ax_dst=ax_dst, l_roll=l_roll,
                     l_pitch=l_pitch, l_srv=l_srv, l_dst=l_dst,
                     board=board, platform=platform, txt=txt)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--port", help="serial port, e.g. COM3 or /dev/ttyUSB0")
    g.add_argument("--log", help="text file with serial output to replay")
    g.add_argument("--demo", action="store_true", help="synthetic data (testing only)")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--speed", type=int, default=1, help="samples per frame for --log replay")
    p.add_argument("--duration", type=float, default=20, help="seconds for --demo")
    p.add_argument("--save", help="write a GIF instead of opening a window (log/demo only)")
    args = p.parse_args()

    if args.port:
        src = SerialSource(args.port, args.baud)
    elif args.log:
        src = LogSource(args.log, max(1, args.speed))
    else:
        src = DemoSource(args.duration)

    if args.save and src.live:
        p.error("--save works with --log or --demo, not --port")

    fig, a = build_figure()
    t = collections.deque(maxlen=WINDOW)
    roll = collections.deque(maxlen=WINDOW)
    pitch = collections.deque(maxlen=WINDOW)
    servo = collections.deque(maxlen=WINDOW)
    dist = collections.deque(maxlen=WINDOW)

    def update(_frame):
        for s in src.poll():
            t.append(s["t"])
            roll.append(s["roll"])
            pitch.append(s["pitch"])
            servo.append(s["servo"])
            dist.append(s["dist"])
        if not t:
            return
        a["l_roll"].set_data(t, roll)
        a["l_pitch"].set_data(t, pitch)
        a["l_srv"].set_data(t, servo)
        a["l_dst"].set_data(t, dist)
        a["ax_ang"].set_xlim(max(0, t[-1] - WINDOW * SAMPLE_DT), max(1, t[-1]))

        r, pt, sv, d = roll[-1], pitch[-1], servo[-1], dist[-1]
        a["board"].set_xy(rect(r))
        # platform tilt = board roll + servo correction (0 when perfectly leveled)
        a["platform"].set_xy(rect(r + (sv - 90.0), cy=0.45))
        dist_txt = f"{d:.0f} cm" if d > 0 else "out of range"
        a["txt"].set_text(f"roll {r:+.1f}°   pitch {pt:+.1f}°   dist {dist_txt}")

    if args.save:
        frames = src.total_frames()
        anim = FuncAnimation(fig, update, frames=frames, interval=FRAME_MS, repeat=False)
        anim.save(args.save, writer=PillowWriter(fps=int(1000 / FRAME_MS)))
        print(f"Saved {args.save} ({frames} frames)")
    else:
        anim = FuncAnimation(fig, update, interval=FRAME_MS, cache_frame_data=False)
        plt.show()


if __name__ == "__main__":
    main()