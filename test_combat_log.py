"""
Quick local test — run with:
    python test_combat_log.py "C:\path\to\WoW\_retail_\Screenshots"

Reads the last 3 seconds of your WoWCombatLog.txt and prints any deaths found.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "companion"))
import combat_log

folder = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Program Files (x86)\World of Warcraft\_retail_\Screenshots"

log_path = combat_log._log_path(folder)
print(f"Log path : {log_path}")
print(f"Exists   : {os.path.isfile(log_path)}")
print()

# Show the last 20 UNIT_DIED lines regardless of time window (for inspection)
if os.path.isfile(log_path):
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 32768))
        lines = f.read().splitlines()
    died_lines = [l for l in lines if "UNIT_DIED" in l]
    print(f"Last {len(died_lines)} UNIT_DIED events in tail:")
    for l in died_lines[-20:]:
        print(" ", l)
    print()

# Check with 2-minute window to find recent deaths
deaths = combat_log.check_for_deaths(folder, window_secs=120.0)
if deaths:
    for name, age in deaths:
        print(f"Death detected    : {name} ({age:.1f}s ago)")
else:
    print("Deaths in last 2min : (none)")

# Also show all Player- deaths in the tail (regardless of time)
if os.path.isfile(log_path):
    player_deaths = []
    for l in died_lines:
        if "UNIT_DIED" in l and "Player-" in l:
            try:
                fields = l.split("  ", 1)[1].split(",")
                if len(fields) > 6:
                    guid = fields[5]
                    name = fields[6].strip('"').split("-")[0]
                    if guid.startswith("Player-"):
                        player_deaths.append((name, l))
            except:
                pass
    if player_deaths:
        print(f"\nAll Player deaths in tail ({len(player_deaths)}):")
        for name, line in player_deaths[-10:]:
            print(f"  {name}: {line[:80]}...")

print(f"\nCaption           : {combat_log.death_caption(deaths) or '(none)'}")

