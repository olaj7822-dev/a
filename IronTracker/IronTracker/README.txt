IRON PROJECT COMPANION TRACKER
==============================
A manual stat tracker you run next to Roblox. It does NOT read or control the game.

HOW TO GET THE .EXE (Windows)
1. Install Python from https://python.org (tick "Add Python to PATH" during install).
2. Double-click build_exe.bat
3. Your file is at dist\IronTracker.exe  -  copy it anywhere and run it.

(Or just double-click iron_tracker.py to run it without building.)

FEATURES
- Stamina: type your % from the game, press LIFT (-8) per lift, see lifts left
  and time until full. Tick "Resting" when you exit the machine to simulate regen
  (set the regen %/sec to match what you see in game).
- Boosts: enter the timer shown on your screen (e.g. 23:56) and press START for
  Protein powder / Creatine / Pre-workout / Electrolytes. Beeps + turns red at
  <1 minute, tells you when a boost is MISSING so you don't waste sets.
- Weight planner: -/+ buttons with custom step or type the number directly,
  LOG MAX saves your "MAX +xxx LB" value per exercise, shows growth per hour,
  suggested weight and a history graph.
- Session: counts lifts and strength gained (+5.45 per lift by default, editable).

Data is saved to iron_tracker_save.json in your user folder.

GET THE EXE WITHOUT INSTALLING PYTHON (GitHub builds it for you)
1. Create a free account at github.com and click "New repository" (any name, Public).
2. Click "uploading an existing file" and drag in EVERYTHING from this folder,
   including the hidden ".github" folder (or upload IronTracker.zip contents).
   Easiest: unzip, then drag the whole contents of the IronTracker folder.
3. Commit. Open the "Actions" tab -> "Build IronTracker.exe" -> wait ~2 min.
4. Click the finished run -> "Artifacts" -> download IronTracker-exe (zip with the .exe).

HOTKEYS: F8 = LIFT, F9 = Resting on/off, F10 = stamina 100%, F7 = restart all boost timers.
HOLD TIMER: press and hold the big E button for 2 s to practise the in-game hold (visual only).
ALERTS: pop-up in the top-right when stamina is full or a boost expires.
