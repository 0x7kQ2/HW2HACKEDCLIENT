#!/bin/sh
# Match the game's native graphics DLLs when resolving the tool's imports.
set -eu
steam_root='$HOME/.local/share/Steam'
tool_dir="$steam_root/steamapps/common/Hood Warfare 2/HW2HACKEDCLIENT/Binaries/Win64"
export STEAM_COMPAT_DATA_PATH="$steam_root/steamapps/compatdata/5155360"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$steam_root"
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:+$WINEDLLOVERRIDES;}dxgi=n;d3d11=n;d3d12=n;d3d12core=n"
$HOME/HW2HACKEDCLIENT-tool-extension/start-worker.sh
cd "$tool_dir"
exec "$steam_root/steamapps/common/Proton - Experimental/proton" runinprefix ./HW2HACKEDCLIENT_loader.exe HW2HACKEDCLIENT_internal.dll --wait "$@"
