#!/bin/bash
# Pre-publish checklist - Run this BEFORE publishing to TestPyPI
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    CCNotify Pre-Publish Checklist     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

FAILED=0

# 1. Check version consistency
echo -e "${YELLOW}1. Checking version consistency...${NC}"
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
INIT_VERSION=$(grep '^__version__ = ' src/ccnotify/__init__.py | cut -d'"' -f2)

if [ "$PYPROJECT_VERSION" = "$INIT_VERSION" ]; then
    echo -e "${GREEN}   ✅ Versions match: $PYPROJECT_VERSION${NC}"
else
    echo -e "${RED}   ❌ Version mismatch!${NC}"
    echo -e "${RED}      pyproject.toml: $PYPROJECT_VERSION${NC}"
    echo -e "${RED}      __init__.py: $INIT_VERSION${NC}"
    FAILED=1
fi

# 2. Run installer logic tests
echo -e "\n${YELLOW}2. Testing installer logic...${NC}"
if uvx --from . python scripts/test-installer-logic.py > /tmp/installer-test.log 2>&1; then
    echo -e "${GREEN}   ✅ All installer logic tests passed${NC}"
else
    echo -e "${RED}   ❌ Installer logic tests failed!${NC}"
    echo -e "${RED}      See /tmp/installer-test.log for details${NC}"
    FAILED=1
fi

# 3. Clean and build package
echo -e "\n${YELLOW}3. Building package...${NC}"
rm -rf dist/
if uvx hatch build > /dev/null 2>&1; then
    WHEEL=$(ls dist/*.whl 2>/dev/null | head -n1)
    if [ -n "$WHEEL" ]; then
        echo -e "${GREEN}   ✅ Package built: $(basename $WHEEL)${NC}"
    else
        echo -e "${RED}   ❌ No wheel file created${NC}"
        FAILED=1
    fi
else
    echo -e "${RED}   ❌ Build failed${NC}"
    FAILED=1
fi

# 4. Check for uncommitted changes
echo -e "\n${YELLOW}4. Checking git status...${NC}"
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}   ✅ No uncommitted changes${NC}"
else
    echo -e "${YELLOW}   ⚠️  Uncommitted changes detected:${NC}"
    git status --short
fi

# 5. Check for hardcoded paths or debug code
echo -e "\n${YELLOW}5. Checking for common issues...${NC}"
ISSUES_FOUND=0

# Check for hardcoded /Users paths
if grep -r "/Users/helmi" src/ --include="*.py" 2>/dev/null; then
    echo -e "${RED}   ❌ Hardcoded paths found!${NC}"
    ISSUES_FOUND=1
fi

# Check for print debugging
if grep -r "print(" src/ccnotify/installer/ --include="*.py" 2>/dev/null | grep -v "console.print"; then
    echo -e "${YELLOW}   ⚠️  Debug print statements found${NC}"
    ISSUES_FOUND=1
fi

# Check for TODO comments
TODO_COUNT=$(grep -r "TODO" src/ --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}   ⚠️  $TODO_COUNT TODO comments found${NC}"
fi

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}   ✅ No critical issues found${NC}"
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo -e "${GREEN}Ready to publish version $PYPROJECT_VERSION to TestPyPI${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Commit all changes: git add -A && git commit -m 'version $PYPROJECT_VERSION'"
    echo "2. Push to GitHub: git push"
    echo "3. Wait for GitHub Actions to publish to TestPyPI"
    echo "4. Test installation: uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ccnotify==$PYPROJECT_VERSION install"
else
    echo -e "${RED}❌ Pre-publish checks failed!${NC}"
    echo -e "${RED}Fix the issues above before publishing.${NC}"
    exit 1
fi