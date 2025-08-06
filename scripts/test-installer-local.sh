#!/bin/bash
# Local installer testing script - Test everything WITHOUT publishing to TestPyPI
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 CCNotify Local Installer Test Suite${NC}"
echo "========================================="

# Check dependencies
command -v uvx >/dev/null 2>&1 || { echo -e "${RED}uvx is required but not installed.${NC}" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}python3 is required but not installed.${NC}" >&2; exit 1; }

# Create temporary test directory
TEST_DIR=$(mktemp -d)
echo -e "${YELLOW}Test directory: $TEST_DIR${NC}"

# Save current directory
ORIGINAL_DIR=$(pwd)

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    # Kill any remaining Python servers
    pkill -f "python.*-m.*http.server.*8765" 2>/dev/null || true
    pkill -f "python.*-m.*pypiserver" 2>/dev/null || true
    # Remove test directory
    rm -rf "$TEST_DIR"
    cd "$ORIGINAL_DIR"
}
trap cleanup EXIT

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    echo -e "\n${YELLOW}▶ Test: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Test 1: Version consistency
test_version_consistency() {
    echo "Checking version consistency..."
    
    # Get version from pyproject.toml
    PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
    echo "  pyproject.toml: $PYPROJECT_VERSION"
    
    # Get version from __init__.py
    INIT_VERSION=$(grep '^__version__ = ' src/ccnotify/__init__.py | cut -d'"' -f2)
    echo "  __init__.py: $INIT_VERSION"
    
    if [ "$PYPROJECT_VERSION" != "$INIT_VERSION" ]; then
        echo -e "${RED}Version mismatch!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Versions match: $PYPROJECT_VERSION${NC}"
    return 0
}

# Test 2: Build package
test_build_package() {
    echo "Building package..."
    uvx hatch build > /dev/null 2>&1
    
    # Check if wheel was created
    WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n1)
    if [ -z "$WHEEL_FILE" ]; then
        echo -e "${RED}No wheel file created${NC}"
        return 1
    fi
    
    echo "  Built: $(basename $WHEEL_FILE)"
    return 0
}

# Test 3: Local server installation
test_local_installation() {
    echo "Setting up local package server..."
    
    # Create a simple index.html for PyPI-like serving
    mkdir -p "$TEST_DIR/simple/ccnotify"
    cd "$ORIGINAL_DIR"
    
    # Copy wheel to test directory
    WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n1)
    if [ -z "$WHEEL_FILE" ]; then
        echo "No wheel file found"
        return 1
    fi
    
    cp "$WHEEL_FILE" "$TEST_DIR/simple/ccnotify/"
    WHEEL_NAME=$(basename "$WHEEL_FILE")
    
    # Create index file
    cat > "$TEST_DIR/simple/ccnotify/index.html" << EOF
<!DOCTYPE html>
<html>
<body>
<a href="$WHEEL_NAME">$WHEEL_NAME</a>
</body>
</html>
EOF
    
    # Start server from test directory
    cd "$TEST_DIR"
    python3 -m http.server 8765 > /dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 2
    
    # Create a test environment
    TEST_HOME="$TEST_DIR/home"
    mkdir -p "$TEST_HOME/.claude"
    
    echo "Installing from local server..."
    
    # Try to install
    HOME="$TEST_HOME" uvx --index-url http://localhost:8765/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        ccnotify install --quiet 2>&1 | head -20
    
    # Kill the server
    kill $SERVER_PID 2>/dev/null || true
    
    # Check installation
    if [ -f "$TEST_HOME/.claude/ccnotify/ccnotify.py" ]; then
        echo -e "${GREEN}Script installed successfully${NC}"
        
        # Check version in installed script
        INSTALLED_VERSION=$(grep '__version__ = ' "$TEST_HOME/.claude/ccnotify/ccnotify.py" | cut -d'"' -f2)
        EXPECTED_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
        
        if [ "$INSTALLED_VERSION" = "$EXPECTED_VERSION" ]; then
            echo -e "${GREEN}Installed version correct: $INSTALLED_VERSION${NC}"
            return 0
        else
            echo -e "${RED}Version mismatch in installed script${NC}"
            echo "  Expected: $EXPECTED_VERSION"
            echo "  Got: $INSTALLED_VERSION"
            return 1
        fi
    else
        echo -e "${RED}Script not installed${NC}"
        return 1
    fi
}

# Test 4: Update scenario
test_update_scenario() {
    echo "Testing update scenario..."
    
    # Create a fake old installation
    TEST_HOME="$TEST_DIR/home_update"
    mkdir -p "$TEST_HOME/.claude/ccnotify"
    
    # Create old version script
    cat > "$TEST_HOME/.claude/ccnotify/ccnotify.py" << 'EOF'
#!/usr/bin/env python3
__version__ = "0.1.3"
print("old version")
EOF
    
    # Create config
    cat > "$TEST_HOME/.claude/ccnotify/config.json" << 'EOF'
{
    "tts_provider": "kokoro",
    "config_version": "1.0"
}
EOF
    
    # Reuse the simple index from previous test
    # Server should still be set up from test 3
    
    # Create index if not exists
    if [ ! -f "$TEST_DIR/simple/ccnotify/index.html" ]; then
        mkdir -p "$TEST_DIR/simple/ccnotify"
        WHEEL_FILE=$(ls "$ORIGINAL_DIR"/dist/*.whl 2>/dev/null | head -n1)
        if [ -z "$WHEEL_FILE" ]; then
            echo "No wheel file found"
            return 1
        fi
        cp "$WHEEL_FILE" "$TEST_DIR/simple/ccnotify/"
        WHEEL_NAME=$(basename "$WHEEL_FILE")
        
        cat > "$TEST_DIR/simple/ccnotify/index.html" << EOF
<!DOCTYPE html>
<html>
<body>
<a href="$WHEEL_NAME">$WHEEL_NAME</a>
</body>
</html>
EOF
    fi
    
    # Start server
    cd "$TEST_DIR"
    python3 -m http.server 8765 > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 2
    
    echo "Running update..."
    
    # Try to update
    HOME="$TEST_HOME" uvx --index-url http://localhost:8765/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        ccnotify install --quiet 2>&1 | head -20
    
    # Kill the server
    kill $SERVER_PID 2>/dev/null || true
    
    # Check if update worked
    if [ -f "$TEST_HOME/.claude/ccnotify/ccnotify.py" ]; then
        NEW_VERSION=$(grep '__version__ = ' "$TEST_HOME/.claude/ccnotify/ccnotify.py" | cut -d'"' -f2)
        cd "$ORIGINAL_DIR"  # Return to original directory to find pyproject.toml
        EXPECTED_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
        
        if [ "$NEW_VERSION" = "$EXPECTED_VERSION" ] && [ "$NEW_VERSION" != "0.1.3" ]; then
            echo -e "${GREEN}Update successful: 0.1.3 -> $NEW_VERSION${NC}"
            
            # Check config preserved
            if [ -f "$TEST_HOME/.claude/ccnotify/config.json" ]; then
                if grep -q "kokoro" "$TEST_HOME/.claude/ccnotify/config.json"; then
                    echo -e "${GREEN}Configuration preserved${NC}"
                    return 0
                else
                    echo -e "${RED}Configuration lost during update${NC}"
                    return 1
                fi
            fi
        else
            echo -e "${RED}Update failed${NC}"
            echo "  Expected: $EXPECTED_VERSION"
            echo "  Got: $NEW_VERSION"
            return 1
        fi
    else
        echo -e "${RED}Script missing after update${NC}"
        return 1
    fi
}

# Test 5: Import test
test_package_imports() {
    echo "Testing package imports..."
    
    # Create a clean virtual environment
    python3 -m venv "$TEST_DIR/venv"
    source "$TEST_DIR/venv/bin/activate"
    
    # Install the package
    cd "$ORIGINAL_DIR"
    pip install --quiet dist/*.whl
    
    # Try to import
    if python3 -c "import ccnotify; print(f'Version: {ccnotify.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}Package imports successfully${NC}"
        deactivate
        return 0
    else
        echo -e "${RED}Package import failed${NC}"
        deactivate
        return 1
    fi
}

# Run all tests
echo -e "\n${GREEN}Starting test suite...${NC}\n"

FAILED_TESTS=0

run_test "Version Consistency" test_version_consistency || ((FAILED_TESTS++))
run_test "Package Build" test_build_package || ((FAILED_TESTS++))
run_test "Local Installation" test_local_installation || ((FAILED_TESTS++))
run_test "Update Scenario" test_update_scenario || ((FAILED_TESTS++))
run_test "Package Imports" test_package_imports || ((FAILED_TESTS++))

# Summary
echo -e "\n========================================="
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo "Package is ready for TestPyPI publication."
    exit 0
else
    echo -e "${RED}❌ $FAILED_TESTS test(s) failed${NC}"
    echo "Please fix the issues before publishing."
    exit 1
fi