#!/bin/bash

# Event Extractor Installation Script
# Automates the setup process for macOS Event Extractor

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_MIN_VERSION="3.8"
VENV_DIR="$SCRIPT_DIR/venv"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
CONFIG_TEMPLATE="$SCRIPT_DIR/config.yaml.template"
SERVICE_DIR="$HOME/Library/Services"
WORKFLOW_NAME="Extract Events.workflow"

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}    Event Extractor for macOS - Installer${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This installer is for macOS only"
        exit 1
    fi
    print_success "Running on macOS"
}

check_python() {
    print_step "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        print_info "Please install Python 3.8+ from https://python.org or via Homebrew:"
        print_info "  brew install python3"
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python $PYTHON_VERSION is too old. Minimum required: $PYTHON_MIN_VERSION"
        exit 1
    fi
}

create_virtual_environment() {
    print_step "Creating Python virtual environment..."

    if [ -d "$VENV_DIR" ]; then
        print_info "Virtual environment already exists. Removing old one..."
        rm -rf "$VENV_DIR"
    fi

    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
}

install_dependencies() {
    print_step "Installing Python dependencies..."

    source "$VENV_DIR/bin/activate"

    # Upgrade pip first
    pip install --upgrade pip

    # Install requirements
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip install -r "$SCRIPT_DIR/requirements.txt"
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi

    deactivate
}

setup_configuration() {
    print_step "Setting up configuration..."

    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$CONFIG_TEMPLATE" ]; then
            cp "$CONFIG_TEMPLATE" "$CONFIG_FILE"
            print_success "Configuration file created from template"
            print_info "Please edit $CONFIG_FILE and add your API keys"
        else
            print_error "Configuration template not found"
            exit 1
        fi
    else
        print_info "Configuration file already exists"
    fi
}

install_service() {
    print_step "Installing macOS Service..."

    # Create Services directory if it doesn't exist
    mkdir -p "$SERVICE_DIR"

    # Copy workflow
    if [ -d "$SCRIPT_DIR/$WORKFLOW_NAME" ]; then
        cp -r "$SCRIPT_DIR/$WORKFLOW_NAME" "$SERVICE_DIR/"
        print_success "Service installed to ~/Library/Services/"
        print_info "The service will appear in the Services menu after restarting applications"
    else
        print_error "Workflow file not found: $WORKFLOW_NAME"
        exit 1
    fi
}

make_scripts_executable() {
    print_step "Making scripts executable..."

    chmod +x "$SCRIPT_DIR/main.py"
    chmod +x "$SCRIPT_DIR/extract_events_service.sh"

    print_success "Scripts made executable"
}

test_installation() {
    print_step "Testing installation..."

    # Test Python imports
    source "$VENV_DIR/bin/activate"

    if python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
try:
    from event_extractor import EventExtractor
    from calendar_manager import CalendarManager
    print('Python modules imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"; then
        print_success "Python modules test passed"
    else
        print_error "Python modules test failed"
        deactivate
        exit 1
    fi

    deactivate

    # Test basic CLI
    if "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py" --help > /dev/null 2>&1; then
        print_success "CLI test passed"
    else
        print_error "CLI test failed"
        exit 1
    fi
}

request_api_key() {
    echo
    print_info "To complete the setup, you'll need an API key from one of these providers:"
    echo "  1. OpenAI (Recommended): https://platform.openai.com/api-keys"
    echo "  2. Anthropic: https://console.anthropic.com/"
    echo "  3. Local LLM: Set up Ollama (https://ollama.ai/)"
    echo

    read -p "Do you want to configure an API key now? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_api_key
    else
        print_info "You can configure API keys later by editing: $CONFIG_FILE"
    fi
}

configure_api_key() {
    echo
    echo "Select your LLM provider:"
    echo "1) OpenAI (GPT-4/GPT-3.5)"
    echo "2) Anthropic (Claude)"
    echo "3) Local/Ollama"
    echo

    read -p "Choice (1-3): " -n 1 -r
    echo

    case $REPLY in
        1)
            configure_openai
            ;;
        2)
            configure_anthropic
            ;;
        3)
            configure_ollama
            ;;
        *)
            print_info "Skipping API configuration"
            ;;
    esac
}

configure_openai() {
    echo
    read -p "Enter your OpenAI API key: " api_key

    if [ -n "$api_key" ]; then
        # Update config file
        if command -v sed &> /dev/null; then
            sed -i '' "s/your-openai-api-key-here/$api_key/" "$CONFIG_FILE"
            sed -i '' 's/provider: "openai"/provider: "openai"/' "$CONFIG_FILE"
            print_success "OpenAI API key configured"
        else
            print_info "Please manually update the openai_api_key in $CONFIG_FILE"
        fi
    fi
}

configure_anthropic() {
    echo
    read -p "Enter your Anthropic API key: " api_key

    if [ -n "$api_key" ]; then
        if command -v sed &> /dev/null; then
            sed -i '' "s/your-anthropic-api-key-here/$api_key/" "$CONFIG_FILE"
            sed -i '' 's/provider: "openai"/provider: "anthropic"/' "$CONFIG_FILE"
            print_success "Anthropic API key configured"
        else
            print_info "Please manually update the anthropic_api_key in $CONFIG_FILE"
        fi
    fi
}

configure_ollama() {
    print_info "For local LLM setup with Ollama:"
    echo "  1. Install Ollama: https://ollama.ai/"
    echo "  2. Pull a model: ollama pull llama2"
    echo "  3. Start Ollama: ollama serve"

    if command -v sed &> /dev/null; then
        sed -i '' 's/provider: "openai"/provider: "ollama"/' "$CONFIG_FILE"
        print_success "Configuration updated for Ollama"
    fi
}

run_test() {
    print_step "Running functionality test..."

    # Test with sample text
    test_text="I have a meeting tomorrow at 2 PM with John to discuss the project."

    echo "Testing with sample text: '$test_text'"

    if "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py" --test-llm --test-text "$test_text"; then
        print_success "Test completed successfully"
    else
        print_error "Test failed - check your API configuration"
        print_info "You can run tests manually with: python3 main.py --test-llm"
    fi
}

print_final_instructions() {
    echo
    print_success "Installation completed successfully!"
    echo
    print_info "Next steps:"
    echo "  1. Edit configuration file if needed: $CONFIG_FILE"
    echo "  2. Test the installation:"
    echo "     cd $SCRIPT_DIR"
    echo "     ./venv/bin/python main.py --test-llm"
    echo "  3. Copy some text and run:"
    echo "     ./venv/bin/python main.py"
    echo "  4. Use the Service menu in any app (after restarting apps)"
    echo
    print_info "Troubleshooting:"
    echo "  - Grant calendar access when prompted"
    echo "  - Check logs in the project directory"
    echo "  - Run with -v flag for verbose output"
    echo
    print_info "Documentation: $SCRIPT_DIR/README.md"
}

# Main installation flow
main() {
    print_header

    check_macos
    check_python
    create_virtual_environment
    install_dependencies
    setup_configuration
    make_scripts_executable
    install_service
    test_installation

    request_api_key

    # Final test if API key was configured
    if grep -q "your-.*-api-key-here" "$CONFIG_FILE"; then
        print_info "Skipping functionality test (no API key configured)"
    else
        run_test
    fi

    print_final_instructions
}

# Handle script interruption
trap 'echo -e "\n${RED}Installation interrupted${NC}"; exit 1' INT

# Check if running as source or direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
