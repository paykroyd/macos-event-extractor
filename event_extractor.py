#!/usr/bin/env python3
"""
Event Extractor - Extract calendar events from text using LLM
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import dateparser
from dateutil import tz
import yaml
import logging

# LLM clients
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import requests
except ImportError:
    requests = None


class EventExtractor:
    """Extract calendar events from text using various LLM providers."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the event extractor with configuration."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_llm_client()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_path} not found. Using defaults.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'llm': {
                'provider': 'openai',
                'openai_model': 'gpt-4',
                'anthropic_model': 'claude-3-sonnet-20240229',
                'temperature': 0.1,
                'max_tokens': 1000
            },
            'calendar': {
                'default_duration': 60,
                'default_reminder': 15
            },
            'text': {
                'min_length': 10,
                'max_length': 5000
            },
            'logging': {
                'level': 'INFO'
            }
        }

    def _setup_logging(self):
        """Setup logging configuration."""
        level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _setup_llm_client(self):
        """Setup LLM client based on configuration."""
        provider = self.config.get('llm', {}).get('provider', 'openai')

        if provider == 'openai' and openai:
            api_key = self.config.get('llm', {}).get('openai_api_key')
            if api_key and api_key != 'your-openai-api-key-here':
                openai.api_key = api_key
                self.llm_client = openai
                self.logger.info("Initialized OpenAI client")
            else:
                self.logger.warning("OpenAI API key not configured")
                self.llm_client = None
        elif provider == 'anthropic' and anthropic:
            api_key = self.config.get('llm', {}).get('anthropic_api_key')
            if api_key and api_key != 'your-anthropic-api-key-here':
                self.llm_client = anthropic.Anthropic(api_key=api_key)
                self.logger.info("Initialized Anthropic client")
            else:
                self.logger.warning("Anthropic API key not configured")
                self.llm_client = None
        else:
            self.logger.warning(f"Unsupported LLM provider: {provider}")
            self.llm_client = None

    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """Extract events from text using LLM."""
        if not self._validate_text(text):
            return []

        if not self.llm_client:
            self.logger.error("No LLM client available")
            return []

        try:
            prompt = self._create_extraction_prompt(text)
            response = self._call_llm(prompt)
            events = self._parse_llm_response(response)
            return self._process_events(events)
        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return []

    def _validate_text(self, text: str) -> bool:
        """Validate input text."""
        if not text or not text.strip():
            self.logger.warning("Empty text provided")
            return False

        text_config = self.config.get('text', {})
        min_length = text_config.get('min_length', 10)
        max_length = text_config.get('max_length', 5000)

        if len(text) < min_length:
            self.logger.warning(f"Text too short: {len(text)} < {min_length}")
            return False

        if len(text) > max_length:
            self.logger.warning(f"Text too long: {len(text)} > {max_length}")
            return False

        return True

    def _create_extraction_prompt(self, text: str) -> str:
        """Create prompt for LLM to extract events."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

        prompt = f"""
Extract calendar events from the following text. Current date/time: {current_time}

Text to analyze:
{text}

Please extract any calendar events mentioned in the text and return them as a JSON array. For each event, include:
- title: Brief descriptive title
- description: Full description or context
- start_time: ISO format datetime (YYYY-MM-DDTHH:MM:SS)
- end_time: ISO format datetime (YYYY-MM-DDTHH:MM:SS) or null if not specified
- location: Location if mentioned, or null
- all_day: true if it's an all-day event, false otherwise

Rules:
1. If no year is mentioned, assume current year
2. If no time is mentioned but it's clearly an event, assume it's all-day
3. If start time is given but no end time, set end_time to null
4. Be conservative - only extract clear, actionable events
5. If relative dates are used (e.g., "tomorrow", "next Monday"), calculate the actual date
6. Return only valid JSON - no additional text or explanations

Example output format:
[
  {{
    "title": "Meeting with John",
    "description": "Discuss project proposal",
    "start_time": "2024-01-15T14:00:00",
    "end_time": "2024-01-15T15:00:00",
    "location": "Conference Room A",
    "all_day": false
  }}
]

If no events are found, return an empty array: []
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the prompt."""
        provider = self.config.get('llm', {}).get('provider', 'openai')

        if provider == 'openai':
            return self._call_openai(prompt)
        elif provider == 'anthropic':
            return self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        model = self.config.get('llm', {}).get('openai_model', 'gpt-4')
        temperature = self.config.get('llm', {}).get('temperature', 0.1)
        max_tokens = self.config.get('llm', {}).get('max_tokens', 1000)

        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        model = self.config.get('llm', {}).get('anthropic_model', 'claude-3-sonnet-20240229')
        max_tokens = self.config.get('llm', {}).get('max_tokens', 1000)

        response = self.llm_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract events."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                events = json.loads(json_str)
                if isinstance(events, list):
                    return events

            # If no JSON array found, try parsing the entire response
            events = json.loads(response)
            if isinstance(events, list):
                return events

            self.logger.warning("LLM response is not a valid JSON array")
            return []

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {e}")
            self.logger.debug(f"Response was: {response}")
            return []

    def _process_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate extracted events."""
        processed_events = []

        for event in events:
            try:
                processed_event = self._process_single_event(event)
                if processed_event:
                    processed_events.append(processed_event)
            except Exception as e:
                self.logger.error(f"Error processing event {event}: {e}")
                continue

        return processed_events

    def _process_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process and validate a single event."""
        # Required fields
        if 'title' not in event or not event['title']:
            self.logger.warning("Event missing required title field")
            return None

        # Parse start time
        start_time = self._parse_datetime(event.get('start_time'))
        if not start_time:
            self.logger.warning(f"Event '{event['title']}' has invalid start time")
            return None

        # Parse end time
        end_time = None
        if event.get('end_time'):
            end_time = self._parse_datetime(event['end_time'])

        # If no end time specified, use default duration
        if not end_time and not event.get('all_day', False):
            duration = self.config.get('calendar', {}).get('default_duration', 60)
            end_time = start_time + timedelta(minutes=duration)

        return {
            'title': event['title'].strip(),
            'description': event.get('description', '').strip(),
            'start_time': start_time,
            'end_time': end_time,
            'location': event.get('location', '').strip() if event.get('location') else None,
            'all_day': bool(event.get('all_day', False))
        }

    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse datetime string into datetime object."""
        if not dt_str:
            return None

        try:
            # Try ISO format first
            if 'T' in dt_str:
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))

            # Use dateparser for flexible parsing
            parsed = dateparser.parse(dt_str)
            if parsed:
                # If no timezone info, assume local timezone
                if parsed.tzinfo is None:
                    local_tz = tz.tzlocal()
                    parsed = parsed.replace(tzinfo=local_tz)
                return parsed

            return None

        except Exception as e:
            self.logger.error(f"Error parsing datetime '{dt_str}': {e}")
            return None


if __name__ == "__main__":
    # Test the event extractor
    extractor = EventExtractor()

    sample_text = """
    I have a meeting with Sarah tomorrow at 2 PM to discuss the project proposal.
    Don't forget about the team lunch on Friday at noon at the Italian restaurant.
    """

    events = extractor.extract_events(sample_text)
    print(f"Extracted {len(events)} events:")
    for event in events:
        print(f"- {event['title']} at {event['start_time']}")
