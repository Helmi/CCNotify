# CCNotify Publishing & Release Workflow

This document outlines the comprehensive release process for CCNotify, from development to production deployment.

## Release Philosophy

Each release should be:
- **Thoroughly tested** before reaching PyPI
- **Incrementally versioned** following semantic versioning
- **Well documented** in CHANGELOG
- **User-verified** before being marked complete

## Complete Release Workflow

### Phase 1: Release Planning

#### 1.1 Version Agreement
```bash
# Discuss with user what changes warrant the release
# Agree on version number based on:
# - MAJOR: Breaking changes
# - MINOR: New features
# - PATCH: Bug fixes

# Example: "We fixed false notifications, that's a PATCH"
# Result: 0.1.13
```

#### 1.2 Review Pending Changes
```bash
# Check what's changed since last release
git log --oneline $(git describe --tags --abbrev=0)..HEAD

# Review uncommitted changes
git status

# Ensure all features/fixes are complete
```

### Phase 2: Pre-Release Preparation

#### 2.1 Create Pre-Release Branch
```bash
# Create a branch for the release candidate
git checkout -b release/v0.1.13-rc1

# This branch will be used for:
# - Final testing
# - Documentation updates
# - Version bumping
```

#### 2.2 Update Version Numbers
```bash
# Update version in both required locations:
# 1. pyproject.toml - project.version
# 2. src/ccnotify/__init__.py - __version__

# Use the helper script if available:
./scripts/bump_version.sh 0.1.13-rc1
```

#### 2.3 Update CHANGELOG
```markdown
## [0.1.13] - 2025-08-10

### Fixed
- NotebookEdit operations no longer trigger false error notifications
- Input needed alerts only appear for actual permission requests
- Empty error fields are now properly ignored

### Added
- Debug logging for notification triggers
- Keyword filtering for permission-related notifications

### Changed
- Error detection logic now checks for non-empty error values
```

### Phase 3: TestPyPI Validation

#### 3.1 Build Release Candidate
```bash
# Clean previous builds
rm -rf dist/

# Build the package
uvx hatch build

# Verify package contents
uvx twine check dist/*
```

#### 3.2 Upload to TestPyPI
```bash
# Push to TestPyPI for testing
uvx twine upload --repository testpypi dist/*

# The package will be available at:
# https://test.pypi.org/project/ccnotify/0.1.13rc1/
```

#### 3.3 Test Installation from TestPyPI
```bash
# Test in a clean environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    ccnotify==0.1.13rc1

# Run installer test
ccnotify install --non-interactive

# Test basic functionality
ccnotify --version
ccnotify setup --help
```

#### 3.4 Fix Issues & Iterate
```bash
# If issues found:
# 1. Fix the issues in the release branch
# 2. Bump to next RC: 0.1.13-rc2
# 3. Repeat from step 3.1

# Continue until no issues found
```

### Phase 4: Final Release Preparation

#### 4.1 Remove RC Suffix
```bash
# Once testing passes, update to final version
./scripts/bump_version.sh 0.1.13

# Update CHANGELOG date if needed
```

#### 4.2 Documentation Review
```bash
# Check and update if needed:
# - README.md for new features
# - Configuration examples
# - Installation instructions
# - Known issues

# Ensure all docs reflect the new version
```

#### 4.3 Create Release Commit
```bash
# Stage all release files
git add pyproject.toml src/ccnotify/__init__.py CHANGELOG.md docs/

# Commit with clear message
git commit -m "chore: release v0.1.13

- Fixed false error notifications for NotebookEdit
- Improved input needed detection logic
- Added debug logging for troubleshooting"

# Push release branch
git push -u origin release/v0.1.13-rc1
```

### Phase 5: Production Release

#### 5.1 Create Release PR
```bash
# Create PR from release branch to main
gh pr create --base main \
  --title "Release v0.1.13" \
  --body "## Release v0.1.13

### Changes
- Fixed false error notifications
- Improved notification filtering
  
### Testing
- Tested on TestPyPI
- Installer verified working
- All tests passing"
```

#### 5.2 Merge & Tag
```bash
# After PR approval, merge to main
gh pr merge --merge

# Checkout main and pull
git checkout main
git pull

# Create annotated tag
git tag -a v0.1.13 -m "Release v0.1.13: Fix false notifications"

# Push tag
git push origin v0.1.13
```

#### 5.3 Build Final Package
```bash
# Clean build directory
rm -rf dist/

# Build final package from tagged version
uvx hatch build

# Final verification
uvx twine check dist/*
```

#### 5.4 Publish to PyPI
```bash
# Upload to production PyPI
uvx twine upload dist/*

# Alternatively, use GitHub Actions:
# The release will auto-publish when tag is pushed
```

#### 5.5 Create GitHub Release
```bash
# Create release with artifacts
gh release create v0.1.13 \
  --title "v0.1.13 - False Notification Fixes" \
  --notes "### Fixed
- NotebookEdit false error notifications
- Spurious input needed alerts

### Installation
\`\`\`bash
uvx ccnotify install
\`\`\`

See CHANGELOG.md for full details." \
  dist/*
```

### Phase 6: Post-Release Verification

#### 6.1 User Testing
```bash
# User must test the production release:
uvx --refresh ccnotify install

# Verify:
# - Installation completes successfully
# - Version shows correctly
# - Core functionality works
# - Fixed issues are resolved
```

#### 6.2 Monitor for Issues
```bash
# Check for immediate issues:
# - PyPI page renders correctly
# - Downloads work
# - No installation errors reported

# Keep release branch for hotfixes if needed
```

#### 6.3 Cleanup
```bash
# After successful verification:
# 1. Delete local release branch
git branch -d release/v0.1.13-rc1

# 2. Delete remote release branch (if not auto-deleted)
git push origin --delete release/v0.1.13-rc1

# 3. Update main for next development
git checkout main
echo "## [Unreleased]" >> CHANGELOG.md
```

## Branch Strategy

### Development Flow
```
main
  ├── feature/new-feature
  ├── bugfix/fix-issue
  └── release/v0.1.13-rc1
       ├── (test on TestPyPI)
       ├── (fix issues)
       └── release/v0.1.13 → main (merge)
           └── tag: v0.1.13
```

### Branch Types

- **main**: Stable development branch
- **feature/***: New features
- **bugfix/***: Bug fixes  
- **release/***: Release candidates and final releases
- **hotfix/***: Emergency fixes to production

### Release Branch Rules

1. Create from main when ready to release
2. Only bug fixes and docs updates allowed
3. No new features during release phase
4. Test thoroughly before merging back
5. Tag only after merge to main

## TestPyPI Integration

### Configuration
```bash
# Add to ~/.pypirc if not exists
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN
```

### Testing Checklist
- [ ] Package builds without errors
- [ ] Metadata displays correctly
- [ ] Dependencies resolve properly
- [ ] Installation completes
- [ ] CLI commands work
- [ ] Core features function
- [ ] No import errors

### Common TestPyPI Issues

1. **Dependency conflicts**: TestPyPI may not have all dependencies
   - Solution: Use `--extra-index-url https://pypi.org/simple/`

2. **Version already exists**: Can't overwrite versions
   - Solution: Bump RC number (rc1 → rc2)

3. **Slow propagation**: Package may take time to appear
   - Solution: Wait 1-2 minutes, check URL directly

## Automation with GitHub Actions

### Workflow Triggers

The publish workflow triggers on:
1. Manual dispatch (workflow_dispatch)
2. Git tag push (v*)
3. GitHub release creation

### Environment Configuration

Two environments configured:
- **testpypi**: For release candidates
- **pypi**: For production releases

### Required Secrets
- `TEST_PYPI_API_TOKEN`: TestPyPI authentication
- `PYPI_API_TOKEN`: PyPI authentication

## Emergency Hotfix Process

When critical issues need immediate fixing:

```bash
# 1. Create hotfix from latest tag
git checkout -b hotfix/v0.1.14 v0.1.13

# 2. Make minimal fix
# 3. Test thoroughly
# 4. Bump patch version
# 5. Fast-track through TestPyPI
# 6. Release immediately
# 7. Merge back to main
```

## Version Management Best Practices

1. **Never reuse versions** - Even for TestPyPI
2. **RC versions for testing** - Use -rc1, -rc2 suffixes
3. **Semantic versioning strict** - MAJOR.MINOR.PATCH
4. **Document everything** - Every change in CHANGELOG
5. **Tag after merge** - Not before
6. **Test before tagging** - No rushing

## Release Communication

### Internal (Development Team)
- PR description with full changelist
- Tag message with summary
- CHANGELOG with categorized changes

### External (Users)
- GitHub Release with highlights
- PyPI description update if needed
- README updates for new features

## Rollback Procedure

If a release has critical issues:

```bash
# 1. Yank from PyPI (marks as broken)
curl -X POST https://pypi.org/project/ccnotify/0.1.13/yank/

# 2. Create hotfix from previous tag
git checkout -b hotfix/rollback v0.1.12

# 3. Bump to new patch version (0.1.14)
# 4. Release with fix or revert
```

## Quality Gates

Before any release reaches production:

- [ ] All tests passing
- [ ] Code formatted (black)
- [ ] No linting errors
- [ ] CHANGELOG updated
- [ ] Version bumped correctly
- [ ] TestPyPI installation works
- [ ] User has tested RC
- [ ] Documentation current
- [ ] PR reviewed
- [ ] Tag created after merge

## Useful Commands Reference

```bash
# Check current version
python -c "import ccnotify; print(ccnotify.__version__)"

# List all tags
git tag -l --sort=-v:refname

# Show tag details
git show v0.1.13

# Compare versions
git diff v0.1.12..v0.1.13

# Test package locally
pip install -e .

# Build and test wheel
uvx --from dist/ccnotify-*.whl ccnotify --version

# Check PyPI package
curl -s https://pypi.org/pypi/ccnotify/json | jq .info.version
```