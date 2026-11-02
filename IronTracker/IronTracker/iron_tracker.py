"""
Iron Project Companion Tracker
A manual tracker for stamina, boosts and weight progression.
Does NOT read or control the game.
"""
import json, os, time, tkinter as tk
from tkinter import ttk, messagebox
try:
    import keyboard  # optional: global hotkeys (pip install keyboard)
except Exception:
    keyboard = None

SAVE = os.path.join(os.path.expanduser("~"), "iron_tracker_save.json")

# ---------- theme (matches in-game panel) ----------
BG = "#121416"; PANEL = "#1b1e21"; CARD = "#242830"
ORANGE = "#e48a3c"; GREEN = "#5fd36b"; RED = "#ff5c5c"; YEL = "#e6c75c"
TXT = "#f2f2f2"; DIM = "#9aa0a6"; BLUE = "#4fb3ff"; PINK = "#ff7cd0"
FONT = ("Segoe UI", 11, "bold"); BIG = ("Segoe UI", 20, "bold"); SMALL = ("Segoe UI", 9)

STAMINA_PER_LIFT = 8
BOOSTS = [("Protein powder", TXT), ("Creatine", BLUE), ("Pre-workout", RED), ("Electrolytes", BLUE)]


def fmt_mmss(sec):
    sec = max(0, int(sec)); return f"{sec // 60:02d}:{sec % 60:02d}"


def load():
    try:
        with open(SAVE) as f: return json.load(f)
    except Exception:
        return {}


def save(data):
    try:
        with open(SAVE, "w") as f: json.dump(data, f, indent=2)
    except Exception:
        pass


class Panel(tk.Frame):
    """Card with orange outline like the game UI."""
    def __init__(self, master, title, **kw):
        super().__init__(master, bg=ORANGE, padx=2, pady=2, **kw)
        self.inner = tk.Frame(self, bg=PANEL, padx=12, pady=10)
        self.inner.pack(fill="both", expand=True)
        tk.Label(self.inner, text=title.upper(), bg=PANEL, fg=TXT, font=("Segoe UI", 13, "bold")).pack(anchor="w")


class Bar(tk.Canvas):
    def __init__(self, master, color=GREEN, h=16):
        super().__init__(master, height=h, bg="#0c0d0f", highlightthickness=1, highlightbackground="#333")
        self.color = color; self.v = 1.0
        self.bind("<Configure>", lambda e: self.redraw())

    def set(self, v):
        self.v = max(0, min(1, v)); self.redraw()

    def redraw(self):
        self.delete("all"); w = self.winfo_width(); h = self.winfo_height()
        self.create_rectangle(2, 2, 2 + (w - 4) * self.v, h - 2, fill=self.color, outline="")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iron Project Companion"); self.configure(bg=BG); self.geometry("470x900")
        self.attributes("-topmost", True)
        self.data = load()
        self.data.setdefault("boosts", {}); self.data.setdefault("weights", {}); self.data.setdefault("regen", 1.0)
        self.data.setdefault("session", {"lifts": 0, "strength": 0.0})
        self.stamina = 100.0; self.last_tick = time.time(); self.alerted = set()
        self.build(); self.tick()
        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------- UI ----------------
    def build(self):
        top = tk.Frame(self, bg=BG); top.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(top, text="IRON PROJECT COMPANION", bg=BG, fg=ORANGE, font=("Segoe UI", 14, "bold")).pack(side="left")
        self.pin = tk.BooleanVar(value=True)
        tk.Checkbutton(top, text="Always on top", variable=self.pin, bg=BG, fg=DIM, selectcolor=CARD,
                       activebackground=BG, command=lambda: self.attributes("-topmost", self.pin.get())).pack(side="right")

        # ---- Stamina ----
        p = Panel(self, "Stamina"); p.pack(fill="x", padx=10, pady=6); f = p.inner
        self.stam_lbl = tk.Label(f, text="Stamina 100%", bg=PANEL, fg=GREEN, font=FONT); self.stam_lbl.pack()
        self.stam_bar = Bar(f); self.stam_bar.pack(fill="x", pady=4)
        row = tk.Frame(f, bg=PANEL); row.pack(fill="x", pady=4)
        tk.Label(row, text="Set current %:", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.stam_entry = tk.Entry(row, width=5, bg=CARD, fg=YEL, insertbackground=TXT, font=FONT, justify="center", relief="flat")
        self.stam_entry.pack(side="left", padx=4); self.stam_entry.insert(0, "100")
        self.stam_entry.bind("<Return>", lambda e: self.set_stamina())
        self.btn(row, "SET", self.set_stamina).pack(side="left")
        self.btn(row, f"LIFT (-{STAMINA_PER_LIFT})", self.lift, fill=True).pack(side="left", padx=6)
        self.btn(row, "FULL", lambda: self.set_stamina(100)).pack(side="left")
        row2 = tk.Frame(f, bg=PANEL); row2.pack(fill="x")
        tk.Label(row2, text="Regen %/sec (while resting):", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.regen = tk.DoubleVar(value=self.data["regen"])
        tk.Spinbox(row2, from_=0.1, to=20, increment=0.1, textvariable=self.regen, width=5, bg=CARD, fg=TXT,
                   font=SMALL, relief="flat", buttonbackground=CARD).pack(side="left", padx=4)
        self.resting = tk.BooleanVar(value=False)
        tk.Checkbutton(row2, text="Resting (regen)", variable=self.resting, bg=PANEL, fg=TXT, selectcolor=CARD,
                       activebackground=PANEL).pack(side="left")
        self.stam_info = tk.Label(f, text="", bg=PANEL, fg=DIM, font=SMALL, justify="left"); self.stam_info.pack(anchor="w", pady=(4, 0))

        # ---- Boosts ----
        p = Panel(self, "Boosts"); p.pack(fill="x", padx=10, pady=6); f = p.inner
        self.boost_rows = {}
        for name, col in BOOSTS:
            r = tk.Frame(f, bg=PANEL); r.pack(fill="x", pady=2)
            tk.Label(r, text=name, bg=PANEL, fg=col, font=FONT, width=14, anchor="w").pack(side="left")
            t = tk.Label(r, text="--:--", bg=PANEL, fg=DIM, font=FONT, width=6); t.pack(side="left")
            e = tk.Entry(r, width=6, bg=CARD, fg=YEL, insertbackground=TXT, font=SMALL, justify="center", relief="flat")
            e.insert(0, "25:00"); e.pack(side="left", padx=4)
            e.bind("<Return>", lambda ev, n=name: self.start_boost(n))
            self.btn(r, "START", lambda n=name: self.start_boost(n)).pack(side="left")
            self.btn(r, "X", lambda n=name: self.clear_boost(n)).pack(side="left", padx=2)
            self.boost_rows[name] = (t, e)
        self.boost_status = tk.Label(f, text="", bg=PANEL, fg=GREEN, font=FONT); self.boost_status.pack(pady=(6, 0))
        self.boost_bar = Bar(f, color=ORANGE, h=8); self.boost_bar.pack(fill="x")

        # ---- Weight ----
        p = Panel(self, "Weight Planner"); p.pack(fill="x", padx=10, pady=6); f = p.inner
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x")
        tk.Label(r, text="Exercise:", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.ex = ttk.Combobox(r, values=sorted(self.data["weights"].keys()) or ["Sit-up", "Push-up"], width=16)
        self.ex.set((sorted(self.data["weights"].keys()) or ["Sit-up"])[0]); self.ex.pack(side="left", padx=4)
        self.ex.bind("<<ComboboxSelected>>", lambda e: self.refresh_weight())
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x", pady=4)
        self.btn(r, "-", lambda: self.step_weight(-1), w=3).pack(side="left")
        self.w_entry = tk.Entry(r, bg=CARD, fg=YEL, insertbackground=TXT, font=BIG, justify="center", relief="flat", width=10)
        self.w_entry.pack(side="left", padx=6, ipady=4); self.w_entry.insert(0, "120000")
        self.btn(r, "+", lambda: self.step_weight(1), w=3).pack(side="left")
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x")
        tk.Label(r, text="Step:", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.step = tk.Entry(r, width=8, bg=CARD, fg=TXT, font=SMALL, justify="center", relief="flat"); self.step.insert(0, "1000"); self.step.pack(side="left", padx=4)
        tk.Label(r, text="Max lb:", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.max_entry = tk.Entry(r, width=10, bg=CARD, fg=TXT, font=SMALL, justify="center", relief="flat"); self.max_entry.pack(side="left", padx=4)
        self.btn(r, "LOG MAX", self.log_max).pack(side="left")
        self.w_info = tk.Label(f, text="", bg=PANEL, fg=DIM, font=SMALL, justify="left"); self.w_info.pack(anchor="w", pady=4)
        self.graph = tk.Canvas(f, height=90, bg="#0c0d0f", highlightthickness=1, highlightbackground="#333"); self.graph.pack(fill="x")
        self.graph.bind("<Configure>", lambda e: self.refresh_weight())

        # ---- Hold timer + hotkeys ----
        p = Panel(self, "Hold timer & hotkeys"); p.pack(fill="x", padx=10, pady=6); f = p.inner
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x")
        self.hold_btn = tk.Label(r, text="  E  ", bg=CARD, fg=TXT, font=BIG, relief="flat", padx=10, pady=4,
                                 highlightthickness=2, highlightbackground=ORANGE)
        self.hold_btn.pack(side="left")
        self.hold_btn.bind("<ButtonPress-1>", self.hold_start); self.hold_btn.bind("<ButtonRelease-1>", self.hold_stop)
        col = tk.Frame(r, bg=PANEL); col.pack(side="left", fill="x", expand=True, padx=8)
        self.hold_lbl = tk.Label(col, text="Hold the E button 2.0 s (practice timer)", bg=PANEL, fg=DIM, font=SMALL); self.hold_lbl.pack(anchor="w")
        self.hold_bar = Bar(col, color=BLUE, h=10); self.hold_bar.pack(fill="x", pady=2)
        self.hold_t0 = None
        hk = "F8 = LIFT   F9 = Resting on/off   F10 = Full stamina   F7 = restart all boosts"
        hk += "   (global)" if keyboard else "   (only while this window is focused — pip install keyboard for global)"
        tk.Label(f, text=hk, bg=PANEL, fg=DIM, font=("Segoe UI", 8), wraplength=400, justify="left").pack(anchor="w", pady=(4, 0))
        self.alerts = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="Pop-up alerts (stamina full / boost expiring)", variable=self.alerts, bg=PANEL, fg=TXT,
                       selectcolor=CARD, activebackground=PANEL).pack(anchor="w")
        self.setup_hotkeys()

        # ---- Session ----
        p = Panel(self, "Session"); p.pack(fill="x", padx=10, pady=6); f = p.inner
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x")
        self.sess_lbl = tk.Label(r, text="", bg=PANEL, fg=TXT, font=SMALL, justify="left"); self.sess_lbl.pack(side="left")
        self.btn(r, "RESET", self.reset_session).pack(side="right")
        r = tk.Frame(f, bg=PANEL); r.pack(fill="x", pady=4)
        tk.Label(r, text="+Strength per lift:", bg=PANEL, fg=DIM, font=SMALL).pack(side="left")
        self.str_gain = tk.Entry(r, width=7, bg=CARD, fg=GREEN, font=SMALL, justify="center", relief="flat"); self.str_gain.insert(0, "5.45"); self.str_gain.pack(side="left", padx=4)
        self.refresh_weight(); self.refresh_session()

    def btn(self, master, text, cmd, fill=False, w=None):
        b = tk.Button(master, text=text, command=cmd, bg="#3a2f27" if fill else CARD, fg=TXT, font=SMALL,
                      activebackground=ORANGE, relief="flat", highlightthickness=1, highlightbackground=ORANGE, padx=8, width=w)
        return b

    # ---------------- stamina ----------------
    def set_stamina(self, v=None):
        try:
            v = float(self.stam_entry.get()) if v is None else v
        except ValueError:
            return
        self.stamina = max(0, min(100, v)); self.refresh_stamina()

    def lift(self):
        if self.stamina < STAMINA_PER_LIFT:
            messagebox.showwarning("Stamina", "Not enough stamina for a lift."); return
        self.stamina -= STAMINA_PER_LIFT
        self.data["session"]["lifts"] += 1
        try: self.data["session"]["strength"] += float(self.str_gain.get())
        except ValueError: pass
        self.refresh_stamina(); self.refresh_session()

    def refresh_stamina(self):
        s = self.stamina; col = GREEN if s > 40 else (YEL if s > 16 else RED)
        self.stam_lbl.config(text=f"Stamina {s:.0f}%", fg=col); self.stam_bar.color = col; self.stam_bar.set(s / 100)
        left = int(s // STAMINA_PER_LIFT)
        regen = max(0.01, self.regen.get()); to_full = (100 - s) / regen
        self.stam_info.config(text=f"Lifts left: {left}   |   Full in ~{fmt_mmss(to_full)} at {regen:.1f}%/s rest")
        self.stam_entry.delete(0, "end"); self.stam_entry.insert(0, f"{s:.0f}")

    # ---------------- boosts ----------------
    def start_boost(self, name):
        _, e = self.boost_rows[name]; txt = e.get().strip()
        try:
            if ":" in txt: m, s = txt.split(":"); sec = int(m) * 60 + int(s)
            else: sec = float(txt) * 60
        except ValueError:
            messagebox.showerror("Boost", "Enter time as MM:SS or minutes."); return
        self.data["boosts"][name] = time.time() + sec; self.alerted.discard(name); save(self.data)

    def clear_boost(self, name):
        self.data["boosts"].pop(name, None); save(self.data)

    def refresh_boosts(self):
        now = time.time(); active = 0; min_left = None
        for name, _ in BOOSTS:
            t, _ = self.boost_rows[name]; end = self.data["boosts"].get(name)
            if end and end > now:
                left = end - now; active += 1
                t.config(text=fmt_mmss(left), fg=RED if left < 60 else TXT)
                min_left = left if min_left is None else min(min_left, left)
                if left < 60 and name not in self.alerted:
                    self.alerted.add(name); self.alert("BOOST EXPIRING", f"{name} runs out in under a minute")
            else:
                if end: self.data["boosts"].pop(name, None); self.alert("BOOST EXPIRED", f"{name} is gone – re-buy before lifting")
                t.config(text="--:--", fg=DIM)
        total = len(BOOSTS)
        if active == total:
            self.boost_status.config(text=f"ALL {total} BOOSTS ACTIVE – GOOD TO LIFT", fg=GREEN)
        elif active == 0:
            self.boost_status.config(text="NO BOOSTS – don't waste sets!", fg=RED)
        else:
            self.boost_status.config(text=f"{total - active} BOOST(S) MISSING – re-buy before lifting", fg=YEL)
        self.boost_bar.set((min_left or 0) / 1500)

    # ---------------- weight ----------------
    def cur_weight(self):
        try: return float(self.w_entry.get().replace(",", ""))
        except ValueError: return 0.0

    def step_weight(self, d):
        try: st = float(self.step.get().replace(",", ""))
        except ValueError: st = 1000
        v = max(0, self.cur_weight() + d * st); self.w_entry.delete(0, "end"); self.w_entry.insert(0, f"{v:,.0f}")
        self.refresh_weight()

    def log_max(self):
        try: mx = float(self.max_entry.get().replace(",", ""))
        except ValueError: return
        ex = self.ex.get().strip() or "Workout"
        self.data["weights"].setdefault(ex, []).append([time.time(), mx])
        self.ex["values"] = sorted(self.data["weights"].keys()); save(self.data); self.refresh_weight()

    def refresh_weight(self):
        ex = self.ex.get().strip(); hist = self.data["weights"].get(ex, [])
        info = ""
        if hist:
            last = hist[-1][1]; info = f"Last logged max: {last:,.1f} lb"
            if len(hist) >= 2:
                dt = hist[-1][0] - hist[0][0]; dv = hist[-1][1] - hist[0][1]
                if dt > 60:
                    rate = dv / dt * 3600; info += f"   |   growth ≈ {rate:,.0f} lb/hour"
            # suggestion: ~50 % of max tends to be the comfortable set weight; user can change
            info += f"\nSuggested weight to type in: {last * 0.5:,.0f} lb (50 % of max)"
            w = self.cur_weight()
            if last and w: info += f"   |   current entry = {w / last * 100:.0f} % of max"
        else:
            info = "Log your 'MAX +xxx LB' from the game to start tracking."
        self.w_info.config(text=info)
        # graph
        g = self.graph; g.delete("all"); W = g.winfo_width(); H = g.winfo_height()
        if len(hist) >= 2 and W > 10:
            xs = [h[0] for h in hist]; ys = [h[1] for h in hist]
            x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
            if x1 == x0: x1 += 1
            if y1 == y0: y1 += 1
            pts = []
            for x, y in zip(xs, ys):
                pts += [8 + (x - x0) / (x1 - x0) * (W - 16), H - 8 - (y - y0) / (y1 - y0) * (H - 16)]
            g.create_line(*pts, fill=ORANGE, width=2)
            for i in range(0, len(pts), 2): g.create_oval(pts[i] - 3, pts[i + 1] - 3, pts[i] + 3, pts[i + 1] + 3, fill=GREEN, outline="")
            g.create_text(W - 6, 6, text=f"{y1:,.0f}", fill=DIM, font=("Segoe UI", 8), anchor="ne")
            g.create_text(W - 6, H - 6, text=f"{y0:,.0f}", fill=DIM, font=("Segoe UI", 8), anchor="se")
        elif W > 10:
            g.create_text(W / 2, H / 2, text="max history graph", fill="#444", font=SMALL)

    # ---------------- session ----------------
    def refresh_session(self):
        s = self.data["session"]
        self.sess_lbl.config(text=f"Lifts this session: {s['lifts']}    Strength gained: +{s['strength']:,.2f}")

    def reset_session(self):
        self.data["session"] = {"lifts": 0, "strength": 0.0}; self.refresh_session()

    # ---------------- hold timer ----------------
    def hold_start(self, e=None):
        self.hold_t0 = time.time(); self.hold_btn.config(bg=ORANGE)

    def hold_stop(self, e=None):
        if self.hold_t0:
            held = time.time() - self.hold_t0
            self.hold_lbl.config(text=f"Held {held:.2f} s – {'OK, machine would open' if held >= 2 else 'too short (need 2.0 s)'}",
                                 fg=GREEN if held >= 2 else RED)
        self.hold_t0 = None; self.hold_btn.config(bg=CARD); self.hold_bar.set(0)

    # ---------------- hotkeys / alerts ----------------
    def setup_hotkeys(self):
        acts = {"F8": self.lift, "F9": lambda: self.resting.set(not self.resting.get()),
                "F10": lambda: self.set_stamina(100), "F7": self.restart_all_boosts}
        for k, fn in acts.items():
            self.bind_all(f"<{k}>", lambda e, fn=fn: fn())
            if keyboard:
                try: keyboard.add_hotkey(k.lower(), lambda fn=fn: self.after(0, fn))
                except Exception: pass

    def restart_all_boosts(self):
        for name, _ in BOOSTS: self.start_boost(name)

    def alert(self, title, msg):
        self.bell()
        if not self.alerts.get(): return
        w = tk.Toplevel(self); w.overrideredirect(True); w.attributes("-topmost", True); w.configure(bg=ORANGE)
        fr = tk.Frame(w, bg=PANEL, padx=16, pady=10); fr.pack(padx=2, pady=2)
        tk.Label(fr, text=title, bg=PANEL, fg=ORANGE, font=FONT).pack()
        tk.Label(fr, text=msg, bg=PANEL, fg=TXT, font=SMALL).pack()
        w.update_idletasks(); sw = w.winfo_screenwidth()
        w.geometry(f"+{sw - w.winfo_width() - 20}+40"); w.after(4000, w.destroy)

    # ---------------- loop ----------------
    def tick(self):
        now = time.time(); dt = now - self.last_tick; self.last_tick = now
        if self.resting.get() and self.stamina < 100:
            self.stamina = min(100, self.stamina + self.regen.get() * dt)
            if self.stamina >= 100: self.alert("STAMINA FULL", "Back to 100% – ready to lift")
        if self.hold_t0:
            h = time.time() - self.hold_t0; self.hold_bar.set(h / 2)
            self.hold_lbl.config(text=f"Holding… {h:.1f} / 2.0 s", fg=GREEN if h >= 2 else TXT)
        self.refresh_stamina(); self.refresh_boosts()
        self.after(100, self.tick)

    def close(self):
        self.data["regen"] = self.regen.get(); save(self.data); self.destroy()


if __name__ == "__main__":
    App().mainloop()
