# CCNotify Test Infrastructure Plan

## Problem Statement
We've had an unacceptable number of installer failures discovered only after publishing to TestPyPI:
- Version mismatches between `__init__.py` and `pyproject.toml`
- Script update not actually updating files
- Update flow skipping issue fixes when version is current
- Models installing in wrong directory
- Hardcoded paths to old directories
- Missing error propagation
- Dependencies not found when installing from TestPyPI

**Goal:** Zero failed publishes. Every version should be thoroughly tested locally before any publication.

## Testing Infrastructure Components

### 1. Local Package Server
```bash
tests/local-pypi/
├── server.py           # Simple PyPI server for testing
├── packages/           # Built wheels stored here
└── index/              # Package index
```

**Implementation:**
- Use `pypiserver` or simple HTTP server
- Build packages locally with `uvx hatch build`
- Upload to local server for testing
- Test installation: `uvx --index-url http://localhost:8080/simple/ ccnotify install`

### 2. Docker-Based Isolated Testing
```yaml
# tests/docker/Dockerfile.test
FROM python:3.10-slim
RUN apt-get update && apt-get install -y git curl
WORKDIR /test
```

**Test Scenarios:**
- Fresh Ubuntu/Debian environment
- Fresh macOS-like environment (using Darwin detection mocks)
- Different Python versions (3.10, 3.11, 3.12)
- Missing system dependencies

### 3. Test Harness Script
```bash
#!/bin/bash
# scripts/test-installer-local.sh

# Build package
echo "Building package..."
uvx hatch build

# Start local PyPI server
python -m http.server 8080 --directory dist/ &
SERVER_PID=$!

# Run test scenarios
python tests/test_scenarios.py

# Cleanup
kill $SERVER_PID
```

### 4. Comprehensive Test Scenarios

#### A. Installation States Testing
```python
# tests/test_installation_states.py
class TestInstallationStates:
    def test_fresh_install(self):
        """Test completely new installation"""
        
    def test_update_from_0_1_3(self):
        """Test updating from broken 0.1.3"""
        
    def test_missing_models(self):
        """Test recovery when models are missing"""
        
    def test_missing_hooks(self):
        """Test automatic hook configuration"""
        
    def test_corrupted_config(self):
        """Test recovery from corrupted config.json"""
        
    def test_partial_installation(self):
        """Test recovery from interrupted installation"""
```

#### B. Version Management Testing
```python
# tests/test_version_consistency.py
def test_version_consistency():
    """Ensure all version sources match"""
    pyproject_version = get_pyproject_version()
    init_version = get_init_version()
    cli_version = get_cli_version()
    
    assert pyproject_version == init_version == cli_version
    
def test_version_embedding():
    """Test version is correctly embedded in generated scripts"""
    template = get_notify_template()
    assert f'__version__ = "{current_version}"' in template
```

#### C. Update Flow Testing
```python
# tests/test_update_flow.py
class TestUpdateFlow:
    def test_update_with_issues_no_version_change(self):
        """Ensure issues are fixed even when version is current"""
        
    def test_update_preserves_config(self):
        """Ensure configuration is preserved during updates"""
        
    def test_update_script_actually_updates(self):
        """Ensure script file is actually modified"""
        
    def test_backup_and_restore(self):
        """Test backup creation and restoration on failure"""
```

### 5. Mock Claude Environment
```python
# tests/fixtures/claude_env.py
class MockClaudeEnvironment:
    def setup(self, state="fresh"):
        """Create mock ~/.claude directory structure"""
        self.claude_dir = Path(self.temp_dir) / ".claude"
        self.claude_dir.mkdir()
        
        if state == "configured":
            self.create_settings_json()
        elif state == "broken":
            self.create_broken_installation()
            
    def create_settings_json(self):
        settings = {
            "hooks": {
                "preToolUse": [],
                "postToolUse": []
            }
        }
        # ... create mock settings
```

### 6. End-to-End Test Suite
```python
# tests/test_e2e.py
def test_complete_installation_flow():
    """Test the complete installation from scratch"""
    with MockClaudeEnvironment() as env:
        # 1. Build package
        build_package()
        
        # 2. Install from local server
        result = install_from_local_server()
        assert result.success
        
        # 3. Verify installation
        assert script_exists()
        assert config_valid()
        assert models_downloaded()
        assert hooks_configured()
        
        # 4. Test notification
        assert test_notification_works()
        
def test_update_flow():
    """Test updating from old version"""
    with MockClaudeEnvironment(state="old_version") as env:
        # Install old version first
        install_old_version()
        
        # Update to new version
        result = update_to_new_version()
        assert result.success
        
        # Verify update
        assert version_updated()
        assert config_preserved()
        assert issues_fixed()
```

### 7. Automated Pre-Publish Checks
```yaml
# .github/workflows/pre-publish-tests.yml
name: Pre-Publish Tests
on:
  workflow_dispatch:
  
jobs:
  test-installer:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]
    
    steps:
      - name: Run installer tests
        run: |
          ./scripts/test-installer-complete.sh
          
      - name: Test version consistency
        run: |
          python tests/test_version_consistency.py
          
      - name: Test update scenarios
        run: |
          python tests/test_update_scenarios.py
```

### 8. Manual Testing Checklist
```markdown
# tests/MANUAL_TEST_CHECKLIST.md

## Before Publishing - Manual Tests

### Fresh Installation
- [ ] Build package: `uvx hatch build`
- [ ] Start local server: `python -m http.server 8080 --directory dist/`
- [ ] Install: `uvx --index-url http://localhost:8080/simple/ ccnotify install`
- [ ] Verify:
  - [ ] Script at ~/.claude/ccnotify/ccnotify.py
  - [ ] Config at ~/.claude/ccnotify/config.json
  - [ ] Models at ~/.claude/ccnotify/models/ (if Kokoro selected)
  - [ ] Hooks configured in ~/.claude/settings.json

### Update from Previous Version
- [ ] Install old version from TestPyPI
- [ ] Build new version locally
- [ ] Update using local server
- [ ] Verify:
  - [ ] Version updated in script
  - [ ] Config preserved
  - [ ] Issues fixed automatically

### Edge Cases
- [ ] Test with missing ~/.claude directory
- [ ] Test with corrupted config.json
- [ ] Test with missing models directory
- [ ] Test with unconfigured hooks
- [ ] Test non-interactive mode (--quiet)
```

### 9. Local Development Workflow
```bash
# Development cycle:
1. Make changes
2. Run quick tests: pytest tests/unit/
3. Build package: uvx hatch build
4. Test locally: ./scripts/test-installer-local.sh
5. Run full suite: pytest tests/
6. Manual test: Follow MANUAL_TEST_CHECKLIST.md
7. Only then: git commit and push
8. Wait for CI to pass
9. Publish to TestPyPI
```

### 10. Version Management Tool
```python
# scripts/bump-version.py
#!/usr/bin/env python3
"""Single source of truth for version bumping"""

def bump_version(bump_type="patch"):
    # Update pyproject.toml
    # Update src/ccnotify/__init__.py
    # Update any other version references
    # Verify consistency
    # Create git commit
```

## Implementation Priority

### Phase 1: Immediate (Today)
1. Create `scripts/test-installer-local.sh` for basic local testing
2. Add version consistency check
3. Create minimal test scenarios for current issues

### Phase 2: This Week
1. Set up Docker-based testing
2. Create comprehensive test suite
3. Add MockClaudeEnvironment

### Phase 3: Next Week
1. Integrate with GitHub Actions
2. Add automated pre-publish workflow
3. Create version management tool

## Success Metrics
- **Zero** failed TestPyPI publishes after implementation
- **100%** of installations work on first try
- **All** edge cases handled gracefully
- Test suite runs in **under 5 minutes**
- **Every** commit tested automatically

## Key Testing Principles
1. **Test locally first** - Never push untested code
2. **Test in isolation** - Use Docker/venv for clean environments
3. **Test all scenarios** - Fresh, update, broken, edge cases
4. **Automate everything** - Manual testing is error-prone
5. **Fail fast** - Catch issues before they reach TestPyPI

## Next Steps
1. Review and approve this plan
2. Start with Phase 1 implementation
3. Test the test infrastructure itself
4. Document any additional test cases discovered
5. Make testing mandatory before any publish