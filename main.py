#!/usr/bin/env python3
"""
Event Extractor - Main CLI application
Extract calendar events from text using LLM and add them to macOS Calendar
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import subprocess

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_extractor import EventExtractor
from calendar_manager import CalendarManager


class EventExtractorApp:
    """Main application class for event extraction and calendar integration."""

    def __init__(self, config_path: str = None):
        """Initialize the application."""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

        self.extractor = EventExtractor(config_path)
        self.calendar_manager = CalendarManager(self.extractor.config)
        self.logger = logging.getLogger(__name__)

    def run_from_clipboard(self) -> int:
        """Extract events from clipboard text and add to calendar."""
        try:
            # Get text from clipboard
            text = self._get_clipboard_text()
            if not text:
                print("No text found in clipboard")
                return 1

            print(f"Processing text from clipboard ({len(text)} characters)...")
            return self._process_text(text)

        except Exception as e:
            self.logger.error(f"Error processing clipboard: {e}")
            print(f"Error: {e}")
            return 1

    def run_from_text(self, text: str) -> int:
        """Extract events from provided text and add to calendar."""
        try:
            print(f"Processing provided text ({len(text)} characters)...")
            return self._process_text(text)

        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            print(f"Error: {e}")
            return 1

    def run_from_file(self, file_path: str) -> int:
        """Extract events from file and add to calendar."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            print(f"Processing text from file: {file_path} ({len(text)} characters)...")
            return self._process_text(text)

        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
            return 1
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            print(f"Error: {e}")
            return 1

    def _process_text(self, text: str) -> int:
        """Process text and extract events."""
        # Check calendar access first
        if not self.calendar_manager.request_calendar_access():
            print("Error: Calendar access is required but not granted.")
            print("Please grant calendar access in System Preferences > Security & Privacy > Privacy > Calendars")
            return 1

        # Extract events using LLM
        print("Extracting events using LLM...")
        events = self.extractor.extract_events(text)

        if not events:
            print("No events found in the text.")
            return 0

        print(f"Found {len(events)} event(s):")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['title']}")
            if event.get('start_time'):
                start_str = event['start_time'].strftime("%Y-%m-%d %H:%M")
                print(f"   Start: {start_str}")
            if event.get('end_time'):
                end_str = event['end_time'].strftime("%Y-%m-%d %H:%M")
                print(f"   End: {end_str}")
            if event.get('location'):
                print(f"   Location: {event['location']}")
            print()

        # Confirm before adding to calendar
        if self.extractor.config.get('service', {}).get('confirm_before_adding', True):
            response = input("Add these events to calendar? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Cancelled.")
                return 0

        # Add events to calendar
        print("Adding events to calendar...")
        results = self.calendar_manager.add_events(events)

        success_count = 0
        for i, result in enumerate(results):
            event_title = events[i]['title']
            if result['success']:
                success_count += 1
                print(f"✓ Added: {event_title}")
            else:
                print(f"✗ Failed to add: {event_title} - {result.get('error', 'Unknown error')}")

        print(f"\nSuccessfully added {success_count} of {len(events)} events to calendar.")

        # Show notification if configured
        if (success_count > 0 and
            self.extractor.config.get('service', {}).get('show_notifications', True)):
            self._show_notification(f"Added {success_count} event(s) to calendar")

        return 0 if success_count > 0 else 1

    def _get_clipboard_text(self) -> str:
        """Get text from macOS clipboard."""
        try:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error getting clipboard text: {e}")
            return ""

    def _show_notification(self, message: str, title: str = "Event Extractor"):
        """Show macOS notification."""
        try:
            # Escape quotes in message and title
            safe_message = message.replace('"', '\\"')
            safe_title = title.replace('"', '\\"')

            script = f'tell application "System Events" to display notification "{safe_message}" with title "{safe_title}"'
            subprocess.run(['osascript', '-e', script], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error showing notification: {e}")

    def list_calendars(self) -> int:
        """List available calendars."""
        if not self.calendar_manager.request_calendar_access():
            print("Error: Calendar access required")
            return 1

        calendars = self.calendar_manager.get_calendars()
        if not calendars:
            print("No calendars found")
            return 1

        print(f"Found {len(calendars)} calendar(s):")
        for cal in calendars:
            status = "✓" if cal['allows_content_modifications'] else "✗"
            print(f"{status} {cal['title']} ({cal['color']})")
            if cal['is_subscribed']:
                print("   (subscribed)")

        return 0

    def test_llm(self, test_text: str = None) -> int:
        """Test LLM connection and event extraction."""
        if test_text is None:
            test_text = """
            I have a dentist appointment tomorrow at 2:30 PM.
            Team meeting on Friday at 10 AM in the conference room.
            Birthday party on Saturday evening at 7 PM at John's house.
            """

        print("Testing LLM connection and event extraction...")
        print(f"Test text: {test_text.strip()}")
        print()

        events = self.extractor.extract_events(test_text)

        if not events:
            print("No events extracted. Check your LLM configuration.")
            return 1

        print(f"Successfully extracted {len(events)} event(s):")
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['title']}")
            if event.get('start_time'):
                print(f"   Start: {event['start_time']}")
            if event.get('end_time'):
                print(f"   End: {event['end_time']}")
            if event.get('location'):
                print(f"   Location: {event['location']}")
            if event.get('description'):
                print(f"   Description: {event['description']}")
            print()

        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract calendar events from text using LLM and add them to macOS Calendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process text from clipboard
  %(prog)s -t "Meeting tomorrow 2pm" # Process provided text
  %(prog)s -f notes.txt             # Process text from file
  %(prog)s --list-calendars         # List available calendars
  %(prog)s --test-llm               # Test LLM connection
        """
    )

    parser.add_argument(
        '-t', '--text',
        help='Text to process for event extraction'
    )

    parser.add_argument(
        '-f', '--file',
        help='File containing text to process'
    )

    parser.add_argument(
        '-c', '--config',
        help='Configuration file path (default: config.yaml)'
    )

    parser.add_argument(
        '--list-calendars',
        action='store_true',
        help='List available calendars and exit'
    )

    parser.add_argument(
        '--test-llm',
        action='store_true',
        help='Test LLM connection with sample text'
    )

    parser.add_argument(
        '--test-text',
        help='Custom text for LLM testing'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Check if running on macOS
    if sys.platform != 'darwin':
        print("Error: This application requires macOS")
        return 1

    try:
        app = EventExtractorApp(args.config)

        # Handle different modes
        if args.list_calendars:
            return app.list_calendars()
        elif args.test_llm:
            return app.test_llm(args.test_text)
        elif args.text:
            return app.run_from_text(args.text)
        elif args.file:
            return app.run_from_file(args.file)
        else:
            # Default: process clipboard
            return app.run_from_clipboard()

    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
