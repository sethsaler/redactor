#!/bin/bash
# Redactor Installation Script
# Usage: curl -fsSL https://raw.githubusercontent.com/sethsaler/redactor/main/install.sh | bash

set -e

REPO_URL="https://github.com/sethsaler/redactor.git"
INSTALL_DIR="${HOME}/.local/share/redactor"
BIN_DIR="${HOME}/.local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "ubuntu"
        elif command -v yum &> /dev/null; then
            echo "rhel"
        elif command -v dnf &> /dev/null; then
            echo "fedora"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_status "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
            print_error "Python 3.8+ is required. Found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    local os=$1
    
    print_status "Installing system dependencies..."
    
    case $os in
        macos)
            if command -v brew &> /dev/null; then
                print_status "Installing Tesseract via Homebrew..."
                brew install tesseract
            else
                print_warning "Homebrew not found. Please install Tesseract manually:"
                print_warning "  brew install tesseract"
            fi
            ;;
        ubuntu)
            print_status "Installing Tesseract via apt..."
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr
            ;;
        rhel|fedora)
            print_status "Installing Tesseract via yum/dnf..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y tesseract
            else
                sudo yum install -y tesseract
            fi
            ;;
        windows)
            print_warning "Windows installation:"
            print_warning "  1. Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki"
            print_warning "  2. Add Tesseract to your PATH"
            ;;
        *)
            print_warning "Unknown OS. Please install Tesseract manually:"
            print_warning "  https://github.com/tesseract-ocr/tesseract"
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    VENV_DIR="${INSTALL_DIR}/venv"
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate and install
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    
    if [ -f "${INSTALL_DIR}/requirements.txt" ]; then
        pip install -r "${INSTALL_DIR}/requirements.txt"
    else
        pip install PyMuPDF Pillow pytesseract pdf2image openpyxl
    fi
    
    print_success "Python dependencies installed"
}

# Create wrapper script
create_wrapper() {
    print_status "Creating executable wrapper..."
    
    mkdir -p "$BIN_DIR"
    
    cat > "${BIN_DIR}/redact" << EOF
#!/bin/bash
# Redactor wrapper script
source "${INSTALL_DIR}/venv/bin/activate"
python "${INSTALL_DIR}/redact_ssns.py" "\$@"
EOF
    
    chmod +x "${BIN_DIR}/redact"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
        print_status "Adding ${BIN_DIR} to PATH..."
        
        SHELL_NAME=$(basename "$SHELL")
        case "$SHELL_NAME" in
            bash)
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "${HOME}/.bashrc"
                print_status "Added to ~/.bashrc. Run 'source ~/.bashrc' to apply."
                ;;
            zsh)
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "${HOME}/.zshrc"
                print_status "Added to ~/.zshrc. Run 'source ~/.zshrc' to apply."
                ;;
            *)
                print_warning "Please add ${BIN_DIR} to your PATH manually"
                ;;
        esac
    fi
}

# Clone repository
clone_repo() {
    print_status "Cloning redactor repository..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory ${INSTALL_DIR} already exists. Updating..."
        cd "$INSTALL_DIR"
        git pull origin main || true
    else
        mkdir -p "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    source "${INSTALL_DIR}/venv/bin/activate"
    
    # Check Python imports
    python3 -c "import fitz; print('PyMuPDF: OK')" 2>/dev/null || print_warning "PyMuPDF import failed"
    python3 -c "from PIL import Image; print('Pillow: OK')" 2>/dev/null || print_warning "Pillow import failed"
    python3 -c "import openpyxl; print('openpyxl: OK')" 2>/dev/null || print_warning "openpyxl import failed"
    
    # Check Tesseract
    if command -v tesseract &> /dev/null; then
        TESS_VERSION=$(tesseract --version 2>&1 | head -1)
        print_success "Tesseract: $TESS_VERSION"
    else
        print_warning "Tesseract not found in PATH. OCR support disabled."
    fi
    
    print_success "Installation complete!"
    echo ""
    echo "Usage:"
    echo "  redact document.pdf                    # SSN mode (default)"
    echo "  redact statement.pdf --mode bank       # Bank statement mode"
    echo "  redact data.csv --mode all -v          # Comprehensive mode, verbose"
    echo "  redact ./documents/ --recursive      # Batch process directory"
    echo ""
    echo "For help: redact --help"
}

# Main installation
main() {
    echo ""
    echo "=========================================="
    echo "  Redactor Installation Script"
    echo "=========================================="
    echo ""
    
    OS=$(detect_os)
    print_status "Detected OS: $OS"
    
    # Check prerequisites
    if ! command -v git &> /dev/null; then
        print_error "Git is required but not installed. Please install Git first."
        exit 1
    fi
    
    check_python
    
    # Install steps
    install_system_deps "$OS"
    clone_repo
    install_python_deps
    create_wrapper
    verify_installation
}

# Run main function
main
