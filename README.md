```
HW2HACKEDCLIENT - Installation & Usage Guide
============================================

FEATURES / WHAT IT CAN DO
-------------------------
  • Injects a full cheat menu ("HW2HACKEDCLIENT Menu") into the game's Config/Profile menu
  • Menu items: Aim assist, Aim (hold), aimKey, aimMaxDistM, Silent aim, ESP, espMaxDistM,
    No spread / nospread / Spread zeroes, menuKey, GlobalUnlock, Local unlocks,
    Visibility, Reset Visibility
  • Sets player/account level to 100
  • Maxes out all weapon challenge stats (kills, headshots, ADS, hipfire, etc.)
  • Patches the game DLL (HW2HACKEDCLIENT_internal.dll) with a menu hook
  • Runs a background unlock worker (systemd user service) that applies saves
  • Verifies unlocks were applied correctly (check_unlock.py)
  • Launches a local-only / offline session with network calls blocked
  • Backs up save files before applying any modifications

THE IN-GAME MENU
----------------
  patch_menu.py injects a full cheat menu into the game's Config/Profile menu
  (implemented via ImGui immediate-mode UI hooked into the game DLL):

    Menu title:  HW2HACKEDCLIENT Menu

  Menu items:

    • Local unlocks
        Applies local save-game unlocks (level 100, maxed weapon stats).
        Writes unlock.request for the background worker to process.

    • GlobalUnlock
        Global unlock flag for all content.

    • Aim assist
        Assists aim toward targets.

    • Aim (hold)
        Aim assist active only while the aim key is held down.

    • aimKey / Key (hold)
        Configures the hold key for aim assist.

    • aimMaxDistM
        Maximum distance (meters) for aim assist to engage.

    • Silent aim
        Hits register without visibly aiming at the target.

    • ESP
        Enemy ESP / wallhack visibility.

    • espMaxDistM
        Maximum distance (meters) for ESP rendering.

    • No spread / nospread / Spread zeroes
        Removes weapon spread so shots go exactly where aimed.

    • menuKey
        Key to toggle the menu open/closed.

    • Visibility
        Enemy visibility / line-of-sight checks.

    • Reset Visibility
        Resets visibility state.

  Clicking "Local unlocks" writes an unlock.request file that the background
  unlock worker picks up. The menu then shows one of these statuses:

    • Queued - restart HW2HACKEDCLIENT.
        The request has been queued; the worker will apply it once the game is closed.
    • Available after restarting HW2HACKEDCLIENT.
        The unlock has been applied; relaunch the game to see the changes.

  The worker writes unlock.status and unlock.request files in
  $HOME/HW2HACKEDCLIENT-tool-extension/ to coordinate between the in-game menu
  and the save-patching scripts.

1. WHAT THIS IS
---------------
HW2HACKEDCLIENT is a standalone client tool package. It contains:

  client/Win64/          - Native Windows binaries run under Proton/Wine
    HW2HACKEDCLIENT_loader.exe   - Main launcher executable
    HW2HACKEDCLIENT_internal.dll - Patched game DLL (menu hook)
    run-HW2HACKEDCLIENT-tool.sh  - Shell script to launch via Steam/Proton

  extension/             - Python tooling that patches the game DLL and runs unlocks
    patch_menu.py             - Injects an unlock button into the game menu
    unlock_worker.py          - Background worker that applies save unlocks
    unlock_HW2HACKEDCLIENT_weapons.original.py - Original weapon unlocker
    check_unlock.py           - Verifies unlocks were applied correctly
    start-worker.sh           - Starts the unlock worker as a systemd user service

  support/               - Offline/local launch support files
    HW2HACKEDCLIENT-offline       - Shell wrapper to run a local-only session
    unlock_HW2HACKEDCLIENT_weapons.py - Save-game unlocker (level + weapon stats)
    HW2HACKEDCLIENT_offline_net.c   - Offline network shim source
    libHW2HACKEDCLIENT-offline-net.so - Preload library for disconnected play

2. PREREQUISITES
----------------
  - Linux desktop (tested on SteamOS / Proton)
  - Steam installed with "Hood Warfare 2" (app ID 5155360) owned in your library
  - Proton - Experimental selected for the game in Steam compatibility settings
  - Python 3 (for the extension tooling)
  - systemd --user (for the background unlock worker)
  - `pefile` Python module (for patch_menu.py): pip install pefile

  All paths inside this client are dynamic ($HOME / os.path.expanduser('~')),
  so it works for any user on any machine without editing.

3. INSTALLATION
---------------
  Step A: Extract / place the folder
    Copy the entire HW2HACKEDCLIENT folder to a location of your choice, e.g.:

      cp -r HW2HACKEDCLIENT ~/HW2HACKEDCLIENT

    Or keep it on the Desktop:

      cp -r HW2HACKEDCLIENT ~/Desktop/HW2HACKEDCLIENT

  Step B: Make scripts executable
    chmod +x ~/HW2HACKEDCLIENT/client/Win64/run-HW2HACKEDCLIENT-tool.sh
    chmod +x ~/HW2HACKEDCLIENT/extension/start-worker.sh
    chmod +x ~/HW2HACKEDCLIENT/support/HW2HACKEDCLIENT-offline

  Step C: Install the Python dependency
    pip3 install pefile --user

  Step D: Verify Steam setup
    - Launch Steam
    - Right-click "Hood Warfare 2" -> Properties -> Compatibility
    - Enable "Force the use of a specific Steam Play compatibility tool"
    - Select "Proton - Experimental"
    - Launch the game once through Steam so the Proton prefix is created

4. HOW TO USE - METHOD 1: STEAM / PROTON (RECOMMENDED)
------------------------------------------------------
  This runs the patched DLL inside the actual game via Steam + Proton.

  Step 1: Patch the game DLL (run once)
    cd ~/HW2HACKEDCLIENT/extension
    python3 patch_menu.py

    This reads your game's HW2HACKEDCLIENT_internal.dll from your Steam
    library path (auto-detected via $HOME), backs it up, injects the unlock
    menu hook, and writes the patched DLL back. It also creates patch.json.

  Step 2: Set Steam launch options (so Steam runs the client when you click Play)
    - Open Steam
    - Right-click "Hood Warfare 2" -> Properties
    - In "Launch Options", paste the full path to the launcher script:

        $HOME/HW2HACKEDCLIENT/client/Win64/run-HW2HACKEDCLIENT-tool.sh %command%

    Example (replace USERNAME with your actual Linux username):

        /home/USERNAME/HW2HACKEDCLIENT/client/Win64/run-HW2HACKEDCLIENT-tool.sh %command%

    - Click "Play" on Hood Warfare 2
    - Steam runs the wrapper script, which starts the unlock worker, then launches
      the game through Proton with the patched DLL loaded
    - In the game's Config/Profile menu you will see a new "Local unlocks" button

  Step 3: Apply unlocks via the menu
    - Click the "Local unlocks" button in-game
    - This writes an unlock.request file for the background worker
    - If the unlock worker is running (see Method 2), it applies the save edits
    - Close and relaunch the game to see changes

5. HOW TO USE - METHOD 2: BACKGROUND UNLOCK WORKER
---------------------------------------------------
  The worker watches for unlock.request and applies progression/save edits.

  Step 1: Start the worker
    cd ~/HW2HACKEDCLIENT/extension
    ./start-worker.sh

    This registers a systemd user service named HW2HACKEDCLIENT-unlock-worker
    and runs unlock_worker.py in the background. Logs go to
    $HOME/HW2HACKEDCLIENT-tool-extension/worker.log

  Step 2: Check status
    systemctl --user status HW2HACKEDCLIENT-unlock-worker
    cat $HOME/HW2HACKEDCLIENT-tool-extension/worker.log

  Step 3: Request an unlock
    - Either click "Local unlocks" in-game (Method 1), or manually create the
      request file:
        touch $HOME/HW2HACKEDCLIENT-tool-extension/unlock.request
    - The worker detects the request, verifies the game is not running,
      applies level 100 + max weapon stats to your local saves, then removes
      the request and writes unlock.status

6. HOW TO USE - METHOD 3: OFFLINE / LOCAL-ONLY SESSION
-------------------------------------------------------
  Use this to play a local, disconnected session with unlocks pre-applied.

  cd ~/HW2HACKEDCLIENT/support
  ./HW2HACKEDCLIENT-offline <game-launch-command>

  This wrapper:
    - Runs unlock_HW2HACKEDCLIENT_weapons.py to set level 100 and max stats
    - Preloads libHW2HACKEDCLIENT-offline-net.so to block network calls
    - Then executes your game launch command in a private environment

  Example:
    ./HW2HACKEDCLIENT-offline steam steam://run/5155360

7. FILES & PATHS (ALL DYNAMIC)
------------------------------
  No paths are hardcoded to your username. Everything uses $HOME or
  os.path.expanduser('~'), so you can move this folder to any machine
  and it will resolve paths to that user's Steam library automatically.

  Key dynamic locations:
    - Steam library:        $HOME/.local/share/Steam
    - Game DLL target:      $HOME/.local/share/Steam/steamapps/common/Hood Warfare 2/HW2HACKEDCLIENT/Binaries/Win64/HW2HACKEDCLIENT_internal.dll
    - Save games:           $HOME/.local/share/Steam/steamapps/compatdata/5155360/pfx/drive_c/users/steamuser/AppData/Local/HW2HACKEDCLIENT/Saved
    - Tool extension dir:   $HOME/HW2HACKEDCLIENT-tool-extension/
    - Unlock request:       $HOME/HW2HACKEDCLIENT-tool-extension/unlock.request
    - Unlock status:        $HOME/HW2HACKEDCLIENT-tool-extension/unlock.status
    - Worker log:           $HOME/HW2HACKEDCLIENT-tool-extension/worker.log

8. TROUBLESHOTING
-----------------
  - "DLL not found": Make sure you ran patch_menu.py at least once and that
    Steam/Proton is installed. The DLL path is auto-detected from $HOME.
  - Worker not applying: Ensure the game is fully closed before creating
    unlock.request. The worker skips if it detects the game process running.
  - Changes revert on relaunch: Online profile sync may overwrite local saves.
    Use Method 3 (offline) for a disconnected session.
  - Permission denied: Run chmod +x on all .sh files (see Installation).

9. SAFETY / DISCLAIMER
----------------------
  This tool modifies your local save files and game DLL. Back up your saves
  before use. Online features may detect modified saves and restore or reset
  progress. Use the offline method (Method 3) if you want to avoid online
  sync overwriting your changes. Use at your own risk.

10. FOLDER CONTENTS
-------------------
  client/Win64/
    HW2HACKEDCLIENT_loader.exe
    HW2HACKEDCLIENT_internal.dll
    run-HW2HACKEDCLIENT-tool.sh

  extension/
    patch_menu.py
    unlock_worker.py
    unlock_HW2HACKEDCLIENT_weapons.original.py
    check_unlock.py
    start-worker.sh
    patch.json

  support/
    HW2HACKEDCLIENT-offline
    unlock_HW2HACKEDCLIENT_weapons.py
    HW2HACKEDCLIENT_offline_net.c
    libHW2HACKEDCLIENT-offline-net.so

  README.md (this file)

END OF GUIDE
```