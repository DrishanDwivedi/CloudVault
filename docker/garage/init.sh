#!/bin/sh
set -e

echo "[INFO] Waiting for Garage daemon to be responsive..."
until /garage status >/dev/null 2>&1; do
    sleep 1
done

echo "[INFO] Checking Garage cluster layout..."
NODE_ID=$(/garage status | grep -E "^[a-f0-9]{16,64}" | head -n 1 | awk '{print $1}')
if [ -n "$NODE_ID" ]; then
    echo "[INFO] Found Node ID: $NODE_ID"
    if /garage layout show | grep -q "NO ROLE ASSIGNED"; then
        echo "[INFO] Assigning role to node..."
        /garage layout assign -z dc1 -c 10G "$NODE_ID"
        /garage layout apply --version 1
    fi
fi

# Ensure deterministic API key exists
echo "[INFO] Configuring API key..."
/garage key import -n cloudvault-key --yes GK000000000000000000000001 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef || true

# Ensure archive bucket exists
echo "[INFO] Ensuring 'cloudvault-archive' bucket exists..."
/garage bucket create cloudvault-archive || true
/garage bucket allow --read --write --key cloudvault-key cloudvault-archive || true

echo "[PASS] Garage initialized successfully."
