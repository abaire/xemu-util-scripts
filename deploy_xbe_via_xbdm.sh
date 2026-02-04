#!/bin/bash

set -euo pipefail

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
    echo "[ERROR] Invalid arguments."
    echo "Usage: $0 <BuildDir> <TargetName> <XboxIP> [PathToBridge]"
    exit 1
fi

BUILD_DIR="$1"
TARGET_NAME="$2"
XBOX_IP="$3"
XBDM="${4:-xbdm_gdb_bridge}"

PREFERRED_PATH="$BUILD_DIR/xbe/$TARGET_NAME"
FALLBACK_PATH="$BUILD_DIR/xbe/xbe_file"
SOURCE_PATH=""

if [[ -d "$PREFERRED_PATH" && -d "$FALLBACK_PATH" ]]; then
    echo "[WARNING] Both deployment directories exist."
    echo "  Preferred: $PREFERRED_PATH"
    echo "  Fallback:  $FALLBACK_PATH"
    echo "-> Defaulting to preferred path: $PREFERRED_PATH"
    SOURCE_PATH="$PREFERRED_PATH"
elif [[ -d "$PREFERRED_PATH" ]]; then
    SOURCE_PATH="$PREFERRED_PATH"
elif [[ -d "$FALLBACK_PATH" ]]; then
    SOURCE_PATH="$FALLBACK_PATH"
else
    echo "[ERROR] No valid deployment directory found."
    echo "  Checked:"
    echo "    $PREFERRED_PATH"
    echo "    $FALLBACK_PATH"
    exit 1
fi

echo "Deploying to Xbox ($XBOX_IP)..."
echo "  Source: $SOURCE_PATH"
echo "  Dest:   e:\\$TARGET_NAME"

"$XBDM" "$XBOX_IP" -v3 -- "mkdir e:\\$TARGET_NAME"
"$XBDM" "$XBOX_IP" -v3 -- "%syncdir \"$SOURCE_PATH\" \"e:\\$TARGET_NAME\" -f"

