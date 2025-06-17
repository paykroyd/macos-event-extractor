#!/bin/bash

# Event Extractor Service - macOS Service Wrapper
# This script creates a macOS service that can be accessed via Services menu

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
SERVICE_NAME="Extract Events"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"
PYTHON_ENV="$SCRIPT_DIR/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON_ENV" ]; then
    # Fall back to system python3
    PYTHON_ENV="python3"
fi

# Function to show error dialog
show_error() {
    osascript -e "display alert \"Event Extractor Error\" message \"$1\" buttons {\"OK\"} default button \"OK\""
}

# Function to show notification
show_notification() {
    osascript -e "display notification \"$1\" with title \"Event Extractor\""
}

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$SCRIPT_DIR/service.log"
}

# Main function
main() {
    log_message "Service started"

    # Check if Python script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        show_error "Python script not found: $PYTHON_SCRIPT"
        log_message "ERROR: Python script not found"
        exit 1
    fi

    # Check if we have clipboard text
    CLIPBOARD_TEXT=$(pbpaste)
    if [ -z "$CLIPBOARD_TEXT" ]; then
        show_error "No text found in clipboard. Please copy some text first."
        log_message "ERROR: No clipboard text"
        exit 1
    fi

    log_message "Processing clipboard text (${#CLIPBOARD_TEXT} characters)"

    # Create a temporary file for the clipboard text
    TEMP_FILE=$(mktemp)
    echo "$CLIPBOARD_TEXT" > "$TEMP_FILE"

    # Run the Python script
    cd "$SCRIPT_DIR"

    # Capture output
    OUTPUT_FILE=$(mktemp)
    ERROR_FILE=$(mktemp)

    if "$PYTHON_ENV" "$PYTHON_SCRIPT" -f "$TEMP_FILE" > "$OUTPUT_FILE" 2> "$ERROR_FILE"; then
        # Success
        RESULT=$(cat "$OUTPUT_FILE")
        log_message "SUCCESS: $RESULT"

        # Show success notification
        if echo "$RESULT" | grep -q "Successfully added"; then
            COUNT=$(echo "$RESULT" | grep -o "Successfully added [0-9]*" | grep -o "[0-9]*")
            show_notification "Added $COUNT event(s) to calendar"
        else
            show_notification "No events found to add"
        fi
    else
        # Error occurred
        ERROR_MSG=$(cat "$ERROR_FILE")
        log_message "ERROR: $ERROR_MSG"

        # Show error dialog
        if echo "$ERROR_MSG" | grep -q "Calendar access"; then
            show_error "Calendar access required. Please grant permission in System Preferences > Security & Privacy > Privacy > Calendars"
        elif echo "$ERROR_MSG" | grep -q "API key"; then
            show_error "LLM API key not configured. Please check your config.yaml file."
        else
            show_error "Failed to extract events. Check the service log for details."
        fi
    fi

    # Cleanup
    rm -f "$TEMP_FILE" "$OUTPUT_FILE" "$ERROR_FILE"

    log_message "Service completed"
}

# Run main function
main "$@"
