#!/bin/bash

SRC="/mnt/c/Users/MP2F3/Documents/Arduino/pico_hardware_control/"
DST="$HOME/scout-survey-rover/firmware/pico_hardware_control/"

mkdir -p "$DST"
rsync -av --delete \
  --exclude ".pio/" \
  --exclude ".vscode/" \
  --exclude ".git/" \
  "$SRC" "$DST"

echo "Synced firmware from Windows Arduino folder."
