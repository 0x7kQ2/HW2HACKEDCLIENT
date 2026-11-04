#!/bin/sh
set -eu
if systemctl --user --quiet is-active HW2HACKEDCLIENT-unlock-worker.service; then
    exit 0
fi
exec systemd-run --user --quiet --collect --unit=HW2HACKEDCLIENT-unlock-worker \
    --property=StandardOutput=append:$HOME/HW2HACKEDCLIENT-tool-extension/worker.log \
    --property=StandardError=append:$HOME/HW2HACKEDCLIENT-tool-extension/worker.log \
    /usr/bin/python3 -u $HOME/HW2HACKEDCLIENT-tool-extension/unlock_worker.py
