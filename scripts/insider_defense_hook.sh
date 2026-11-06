#!/bin/bash
# /etc/profile.d/insider_defense_hook.sh
# Transparently captures SSH session keystroke dynamics for Insider Threat Defense

# Only activate for interactive SSH sessions with a TTY
if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    SENSOR_BIN="/opt/insider_defense/bin/keystroke_collector"
    
    # Fallback to user home directory if not installed in /opt
    if [ ! -f "$SENSOR_BIN" ]; then
        SENSOR_BIN="$HOME/Insider_Deneme/src/sensor/keystroke_collector"
    fi

    # Check if sensor binary and daemon socket exist
    if [ -x "$SENSOR_BIN" ] && [ -e "/var/run/insider_sensor.sock" ]; then
        # Ensure hook runs only once per SSH session
        if [ -z "$INSIDER_SENSOR_ACTIVE" ]; then
            export INSIDER_SENSOR_ACTIVE=1
            # Execute sensor in silent mode
            exec "$SENSOR_BIN" --silent
        fi
    fi
fi

