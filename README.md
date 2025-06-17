# Event Extractor for macOS

A Python-based macOS service that extracts calendar events from text using Large Language Models (LLMs) and automatically adds them to your macOS Calendar. Perfect for quickly capturing events from emails, messages, notes, or any text content.

## Features

- 🤖 **LLM-powered event extraction** - Uses OpenAI GPT, Anthropic Claude, or local models
- 📅 **Native macOS Calendar integration** - Adds events directly to your calendar
- 🚀 **Multiple input methods** - Clipboard, text files, or direct text input
- 📱 **macOS Service integration** - Access via right-click context menu
- ⚙️ **Highly configurable** - Customize LLM settings, calendar preferences, and more
- 🔔 **Smart notifications** - Get notified when events are added
- 🎯 **Intelligent parsing** - Handles relative dates, times, locations, and descriptions

## Requirements

- macOS 10.14 or later
- Python 3.8 or later
- An API key for your preferred LLM provider (OpenAI, Anthropic, or local setup)

## Quick Start

### 1. Clone or Download

```bash
# Option 1: Clone the repository
git clone <repository-url>
cd extract_event

# Option 2: Download and extract the files to a folder called extract_event
```

### 2. Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure API Keys

Copy the configuration template and add your API keys:

```bash
cp config.yaml.template config.yaml
# Edit config.yaml with your preferred text editor
nano config.yaml
```

Update the configuration with your API key:

```yaml
llm:
  provider: "openai"  # or "anthropic"
  openai_api_key: "your-actual-api-key-here"
  # ... other settings
```

### 4. Test the Setup

```bash
# Test LLM connection
python3 main.py --test-llm

# Test calendar access (will prompt for permission)
python3 main.py --list-calendars
```

### 5. Install as macOS Service

Copy the Automator workflow to your Services folder:

```bash
# Create Services directory if it doesn't exist
mkdir -p ~/Library/Services

# Copy the workflow
cp -r "Extract Events.workflow" ~/Library/Services/
```

## Usage

### Command Line Interface

```bash
# Process text from clipboard
python3 main.py

# Process specific text
python3 main.py -t "Meeting with John tomorrow at 2 PM"

# Process text from file
python3 main.py -f notes.txt

# List available calendars
python3 main.py --list-calendars

# Test LLM connection
python3 main.py --test-llm
```

### macOS Service (Right-click Menu)

Once installed, you can:

1. Copy any text containing event information
2. Right-click in any application
3. Select "Services" > "Extract Events"
4. Events will be automatically extracted and added to your calendar

### Supported Applications

The service works with any macOS application that supports text selection:

- Mail
- Safari
- TextEdit
- Notes
- Messages
- Slack
- Discord
- And many more!

## Configuration

### LLM Providers

#### OpenAI (Recommended)
```yaml
llm:
  provider: "openai"
  openai_api_key: "sk-your-key-here"
  openai_model: "gpt-4"  # or "gpt-3.5-turbo"
```

#### Anthropic Claude
```yaml
llm:
  provider: "anthropic"
  anthropic_api_key: "sk-ant-your-key-here"
  anthropic_model: "claude-3-sonnet-20240229"
```

#### Local Models (Advanced)
For local LLM setups using Ollama:
```yaml
llm:
  provider: "ollama"
  ollama_model: "llama2"
  ollama_url: "http://localhost:11434"
```

### Calendar Settings

```yaml
calendar:
  default_calendar: "Work"  # Specify calendar name or leave empty for default
  timezone: ""  # Leave empty to use system timezone
  default_duration: 60  # Default event duration in minutes
  default_reminder: 15  # Default reminder time in minutes
```

### Text Processing

```yaml
text:
  min_length: 10    # Minimum text length to process
  max_length: 5000  # Maximum text length to process
```

## Examples

### Sample Input Text

```
I have a dentist appointment tomorrow at 2:30 PM.
Team meeting on Friday at 10 AM in the conference room.
Birthday party on Saturday evening at 7 PM at John's house.
Conference call with client next Monday at 3 PM - discuss project proposal.
```

### Extracted Events

The system will create calendar events with:
| Title | Date | Location | Description |
|-------|------|----------|-------------|
| Dentist Appointment | Tomorrow at 2:30 PM | | Routine dental checkup |
| Team Meeting | Friday at 10 AM | Conference Room | Weekly team sync |
| Birthday Party | Saturday at 7 PM | John's House | Celebration event |
| Conference Call with Client | Next Monday at 3 PM | | Discuss project proposal |

## Troubleshooting

### Calendar Access Issues

If you get calendar access errors:

1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Calendars** from the left sidebar
3. Grant permission to Terminal, Python, or the specific application

### LLM API Issues

- **OpenAI**: Ensure your API key is valid and has sufficient credits
- **Anthropic**: Check your API key and rate limits
- **Local**: Ensure Ollama or your local LLM server is running

### Service Not Appearing

If the service doesn't appear in the Services menu:

1. Restart your Mac or log out and back in
2. Check that the workflow is in `~/Library/Services/`
3. Try opening the workflow in Automator and saving it again

### Python Environment Issues

```bash
# If you get import errors, ensure you're using the right Python
which python3
python3 --version

# Reinstall dependencies if needed
pip install --upgrade -r requirements.txt
```

## Advanced Usage

### Custom Prompts

You can modify the LLM prompt in `event_extractor.py` to customize how events are extracted:

```python
def _create_extraction_prompt(self, text: str) -> str:
    # Modify this method to customize the extraction prompt
```

### Adding New LLM Providers

To add support for additional LLM providers:

1. Update the `_setup_llm_client()` method in `event_extractor.py`
2. Add the corresponding API call method
3. Update the configuration schema

### Batch Processing

For processing multiple files:

```bash
# Process all text files in a directory
for file in *.txt; do
    python3 main.py -f "$file"
done
```

## API Reference

### EventExtractor Class

```python
from event_extractor import EventExtractor

extractor = EventExtractor('config.yaml')
events = extractor.extract_events(text)
```

### CalendarManager Class

```python
from calendar_manager import CalendarManager

manager = CalendarManager(config)
manager.request_calendar_access()
results = manager.add_events(events)
```

## Privacy and Security

- **API Keys**: Store securely in `config.yaml`, never commit to version control
- **Calendar Data**: Only creates new events, doesn't read existing calendar data
- **Text Processing**: Text is sent to your configured LLM provider for processing
- **Local Processing**: For maximum privacy, use local LLM models

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files in the project directory
3. Enable verbose logging with the `-v` flag
4. Create an issue with detailed error information

## Changelog

### Version 1.0.0
- Initial release
- Support for OpenAI and Anthropic LLMs
- macOS Calendar integration
- Service menu integration
- Configurable event processing

---

**Note**: This tool requires internet access for cloud-based LLM providers. For offline usage, consider setting up a local LLM with Ollama or similar tools.
