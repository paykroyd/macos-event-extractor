#!/usr/bin/env python3
"""
Calendar Manager - macOS Calendar integration using EventKit
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import objc
from Foundation import NSDate, NSTimeZone, NSCalendar, NSDateComponents
from EventKit import (
    EKEventStore, EKEvent, EKAlarm, EKRecurrenceRule,
    EKEntityTypeEvent
)

# Try to import authorization status constants (may not exist in newer versions)
try:
    from EventKit import (
        EKAuthorizationStatusAuthorized, EKAuthorizationStatusDenied,
        EKAuthorizationStatusRestricted, EKAuthorizationStatusNotDetermined
    )
    HAS_OLD_AUTH_API = True
except ImportError:
    # For newer macOS versions, these constants may not be available
    HAS_OLD_AUTH_API = False
    EKAuthorizationStatusAuthorized = 3
    EKAuthorizationStatusDenied = 2
    EKAuthorizationStatusRestricted = 1
    EKAuthorizationStatusNotDetermined = 0


class CalendarManager:
    """Manage calendar events using macOS EventKit."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the calendar manager."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.event_store = EKEventStore.alloc().init()
        self._authorization_status = None

    def request_calendar_access(self) -> bool:
        """Request access to calendar and return authorization status."""
        try:
            # Check if we have the new API (macOS 14+)
            if hasattr(self.event_store, 'requestFullAccessToEventsWithCompletion_'):
                self.logger.info("Using new EventKit API for calendar access")
                return self._request_access_new_api()

            # Check if we have the old authorization status method
            elif hasattr(self.event_store, 'authorizationStatusForEntityType_'):
                self.logger.info("Using legacy EventKit API for calendar access")
                return self._request_access_old_api()

            else:
                # Try the newer requestAccessToEntityType method
                self.logger.info("Using intermediate EventKit API for calendar access")
                return self._request_access_sync()

        except Exception as e:
            self.logger.error(f"Error requesting calendar access: {e}")
            self._authorization_status = False
            return False

    def _request_access_new_api(self) -> bool:
        """Request access using the new API (macOS 14+)."""
        import threading
        import time

        result = [None]
        event = threading.Event()

        def completion_handler(granted, error):
            result[0] = granted and not error
            if error:
                self.logger.error(f"Calendar access request error: {error}")
            event.set()

        # Use the new full access API
        self.event_store.requestFullAccessToEventsWithCompletion_(completion_handler)

        # Wait for response (with timeout)
        if event.wait(timeout=15.0):
            success = result[0] or False
            self._authorization_status = success
            if success:
                self.logger.info("Calendar access granted")
            else:
                self.logger.error("Calendar access denied")
            return success
        else:
            self.logger.error("Calendar access request timed out")
            self._authorization_status = False
            return False

    def _request_access_old_api(self) -> bool:
        """Request access using the old API (macOS 13 and earlier)."""
        try:
            # Check current authorization status
            status = self.event_store.authorizationStatusForEntityType_(EKEntityTypeEvent)

            if status == EKAuthorizationStatusAuthorized:
                self.logger.info("Calendar access already authorized")
                self._authorization_status = True
                return True
            elif status == EKAuthorizationStatusDenied:
                self.logger.error("Calendar access denied by user")
                self._authorization_status = False
                return False
            elif status == EKAuthorizationStatusRestricted:
                self.logger.error("Calendar access restricted by system")
                self._authorization_status = False
                return False
            elif status == EKAuthorizationStatusNotDetermined:
                self.logger.info("Requesting calendar access...")
                # Request access synchronously
                success = self._request_access_sync()
                self._authorization_status = success
                return success

            return False

        except Exception as e:
            self.logger.error(f"Error with old calendar API: {e}")
            return self._request_access_sync()

    def _request_access_sync(self) -> bool:
        """Request calendar access synchronously using intermediate API."""
        import threading
        import time

        result = [None]  # Use list to make it mutable in closure
        event = threading.Event()

        def completion_handler(granted, error):
            result[0] = granted and not error
            if error:
                self.logger.error(f"Calendar access request error: {error}")
            event.set()

        try:
            # Try the requestAccessToEntityType method
            if hasattr(self.event_store, 'requestAccessToEntityType_completion_'):
                self.event_store.requestAccessToEntityType_completion_(
                    EKEntityTypeEvent, completion_handler
                )
            else:
                # Last resort: assume we have access and test it
                self.logger.warning("No recognized authorization method found, testing access directly")
                try:
                    # Try to access calendars to test permission
                    calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                    result[0] = calendars is not None and len(calendars) >= 0
                    event.set()
                except Exception as e:
                    self.logger.error(f"Direct calendar access test failed: {e}")
                    result[0] = False
                    event.set()

            # Wait for response (with timeout)
            if event.wait(timeout=15.0):
                success = result[0] or False
                self._authorization_status = success
                if success:
                    self.logger.info("Calendar access granted")
                else:
                    self.logger.error("Calendar access denied")
                return success
            else:
                self.logger.error("Calendar access request timed out")
                self._authorization_status = False
                return False

        except Exception as e:
            self.logger.error(f"Error in sync access request: {e}")
            self._authorization_status = False
            return False

    def get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of available calendars."""
        if not self._check_authorization():
            return []

        try:
            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            calendar_list = []

            for calendar in calendars:
                calendar_info = {
                    'title': str(calendar.title()),
                    'identifier': str(calendar.calendarIdentifier()),
                    'color': self._get_calendar_color(calendar),
                    'is_subscribed': calendar.isSubscribed(),
                    'allows_content_modifications': calendar.allowsContentModifications()
                }
                calendar_list.append(calendar_info)

            return calendar_list

        except Exception as e:
            self.logger.error(f"Error getting calendars: {e}")
            return []

    def _get_calendar_color(self, calendar) -> str:
        """Get calendar color as hex string."""
        try:
            if hasattr(calendar, 'color') and calendar.color():
                # Convert NSColor to hex
                color = calendar.color()
                if hasattr(color, 'redComponent'):
                    r = int(color.redComponent() * 255)
                    g = int(color.greenComponent() * 255)
                    b = int(color.blueComponent() * 255)
                    return f"#{r:02x}{g:02x}{b:02x}"
            return "#0066CC"  # Default blue
        except:
            return "#0066CC"

    def get_default_calendar(self):
        """Get the default calendar for new events."""
        if not self._check_authorization():
            return None

        try:
            # Try to get calendar by name from config
            calendar_name = self.config.get('calendar', {}).get('default_calendar')
            if calendar_name:
                calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
                for calendar in calendars:
                    if calendar.title() == calendar_name and calendar.allowsContentModifications():
                        return calendar

            # Fall back to default calendar
            return self.event_store.defaultCalendarForNewEvents()

        except Exception as e:
            self.logger.error(f"Error getting default calendar: {e}")
            return None

    def add_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add multiple events to calendar."""
        if not self._check_authorization():
            return []

        results = []
        for event_data in events:
            result = self.add_event(event_data)
            results.append(result)

        return results

    def add_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single event to calendar."""
        if not self._check_authorization():
            return {'success': False, 'error': 'Calendar access not authorized'}

        try:
            # Get the calendar to add to
            calendar = self.get_default_calendar()
            if not calendar:
                return {'success': False, 'error': 'No suitable calendar found'}

            # Create the event
            event = EKEvent.eventWithEventStore_(self.event_store)

            # Set basic properties
            event.setTitle_(event_data.get('title', 'Untitled Event'))

            description = event_data.get('description', '')
            if description:
                event.setNotes_(description)

            location = event_data.get('location')
            if location:
                event.setLocation_(location)

            # Set calendar
            event.setCalendar_(calendar)

            # Handle all-day events
            if event_data.get('all_day', False):
                event.setAllDay_(True)
                # For all-day events, use date components
                start_date = event_data['start_time']
                event.setStartDate_(self._datetime_to_nsdate(start_date))

                if event_data.get('end_time'):
                    end_date = event_data['end_time']
                    event.setEndDate_(self._datetime_to_nsdate(end_date))
                else:
                    # All-day event defaults to same day
                    event.setEndDate_(self._datetime_to_nsdate(start_date + timedelta(days=1)))
            else:
                # Regular timed event
                start_time = event_data['start_time']
                event.setStartDate_(self._datetime_to_nsdate(start_time))

                if event_data.get('end_time'):
                    end_time = event_data['end_time']
                    event.setEndDate_(self._datetime_to_nsdate(end_time))
                else:
                    # Default duration
                    duration = self.config.get('calendar', {}).get('default_duration', 60)
                    end_time = start_time + timedelta(minutes=duration)
                    event.setEndDate_(self._datetime_to_nsdate(end_time))

            # Add reminder if configured
            reminder_minutes = self.config.get('calendar', {}).get('default_reminder')
            if reminder_minutes:
                alarm = EKAlarm.alarmWithRelativeOffset_(-reminder_minutes * 60)  # negative for before
                event.addAlarm_(alarm)

            # Save the event
            error = objc.nil
            success = self.event_store.saveEvent_span_error_(event, 0, objc.nil)  # 0 = this event only

            if success:
                event_id = str(event.eventIdentifier())
                self.logger.info(f"Successfully added event: {event_data.get('title')} (ID: {event_id})")
                return {
                    'success': True,
                    'event_id': event_id,
                    'title': event_data.get('title'),
                    'calendar': str(calendar.title())
                }
            else:
                error_msg = str(error) if error else "Unknown error"
                self.logger.error(f"Failed to save event: {error_msg}")
                return {'success': False, 'error': f'Failed to save event: {error_msg}'}

        except Exception as e:
            error_msg = f"Error adding event: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def _datetime_to_nsdate(self, dt: datetime) -> NSDate:
        """Convert Python datetime to NSDate."""
        # Convert to timestamp and create NSDate
        timestamp = dt.timestamp()
        return NSDate.dateWithTimeIntervalSince1970_(timestamp)

    def _check_authorization(self) -> bool:
        """Check if calendar access is authorized."""
        if self._authorization_status is None:
            return self.request_calendar_access()
        return self._authorization_status

    def find_events(self, start_date: datetime, end_date: datetime, title_filter: str = None) -> List[Dict[str, Any]]:
        """Find events in the specified date range."""
        if not self._check_authorization():
            return []

        try:
            # Create date predicate
            start_ns = self._datetime_to_nsdate(start_date)
            end_ns = self._datetime_to_nsdate(end_date)

            calendars = self.event_store.calendarsForEntityType_(EKEntityTypeEvent)
            predicate = self.event_store.predicateForEventsWithStartDate_endDate_calendars_(
                start_ns, end_ns, calendars
            )

            # Fetch events
            events = self.event_store.eventsMatchingPredicate_(predicate)

            event_list = []
            for event in events:
                # Apply title filter if specified
                if title_filter and title_filter.lower() not in event.title().lower():
                    continue

                event_info = {
                    'event_id': str(event.eventIdentifier()),
                    'title': str(event.title()),
                    'start_date': self._nsdate_to_datetime(event.startDate()),
                    'end_date': self._nsdate_to_datetime(event.endDate()),
                    'all_day': event.isAllDay(),
                    'location': str(event.location()) if event.location() else None,
                    'notes': str(event.notes()) if event.notes() else None,
                    'calendar': str(event.calendar().title())
                }
                event_list.append(event_info)

            return event_list

        except Exception as e:
            self.logger.error(f"Error finding events: {e}")
            return []

    def _nsdate_to_datetime(self, nsdate: NSDate) -> datetime:
        """Convert NSDate to Python datetime."""
        timestamp = nsdate.timeIntervalSince1970()
        return datetime.fromtimestamp(timestamp)

    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        if not self._check_authorization():
            return False

        try:
            event = self.event_store.eventWithIdentifier_(event_id)
            if not event:
                self.logger.warning(f"Event with ID {event_id} not found")
                return False

            success = self.event_store.removeEvent_span_error_(event, 0, objc.nil)
            if success:
                self.logger.info(f"Successfully deleted event: {event_id}")
                return True
            else:
                self.logger.error(f"Failed to delete event: {event_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting event {event_id}: {e}")
            return False


if __name__ == "__main__":
    # Test the calendar manager
    import sys

    logging.basicConfig(level=logging.INFO)

    manager = CalendarManager()

    # Request access
    if not manager.request_calendar_access():
        print("Calendar access denied or failed")
        sys.exit(1)

    # List calendars
    calendars = manager.get_calendars()
    print(f"Found {len(calendars)} calendars:")
    for cal in calendars:
        print(f"  - {cal['title']} ({cal['identifier']})")

    # Test adding an event
    test_event = {
        'title': 'Test Event from Python',
        'description': 'This is a test event created by the calendar manager',
        'start_time': datetime.now() + timedelta(hours=1),
        'end_time': datetime.now() + timedelta(hours=2),
        'location': 'Test Location',
        'all_day': False
    }

    result = manager.add_event(test_event)
    print(f"Add event result: {result}")
