# Publishing Guide

This document outlines the process for publishing CCNotify releases to PyPI and managing versions.

## Version Management

CCNotify follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Version Locations

Version must be updated in two places:
1. `pyproject.toml` - `project.version`
2. `src/ccnotify/__init__.py` - `__version__`

## Release Process

### 1. Prepare Release

```bash
# Update version in both files
# Test the package build
uvx hatch build --clean

# Verify package contents
uvx twine check dist/*
```

### 2. Update Changelog

Update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed  
- Changes in existing functionality

### Fixed
- Bug fixes

### Removed
- Removed features
```

### 3. Create Git Tag

```bash
# Commit version changes
git add pyproject.toml src/ccnotify/__init__.py CHANGELOG.md
git commit -m "chore: bump version to vX.Y.Z"

# Create annotated tag
git tag -a vX.Y.Z -m "Release vX.Y.Z: Brief description"

# Push changes and tag
git push origin main && git push origin vX.Y.Z
```

### 4. Create GitHub Release

```bash
# Create release with built artifacts
gh release create vX.Y.Z dist/* \
  --title "vX.Y.Z - Release Title" \
  --notes-file RELEASE_NOTES.md
```

## PyPI Publishing

### Automated Publishing (Recommended)

GitHub Actions automatically publishes to PyPI when a release is created:

1. **Automatic**: Publishing triggers on GitHub release creation
2. **Manual**: Use GitHub Actions workflow dispatch
   - Go to Actions → "Publish to PyPI" 
   - Choose environment (testpypi/pypi)
   - Run workflow

### Manual Publishing

#### Prerequisites

1. **PyPI Account**: Create account at https://pypi.org
2. **API Token**: Generate at https://pypi.org/manage/account/token/
3. **TestPyPI Account**: Create account at https://test.pypi.org (for testing)

#### Setup Credentials

```bash
# Create .pypirc file (one-time setup)
cat > ~/.pypirc << EOF
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
EOF

chmod 600 ~/.pypirc
```

#### Test Publishing

```bash
# Build package
uvx hatch build --clean

# Upload to TestPyPI first
uvx twine upload --repository testpypi dist/*

# Test installation from TestPyPI
uvx --index-url https://test.pypi.org/simple/ ccnotify install
```

#### Production Publishing

```bash
# Upload to PyPI
uvx twine upload dist/*

# Verify on PyPI
open https://pypi.org/project/ccnotify/
```

## GitHub Secrets Setup

For automated publishing, configure these repository secrets:

1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

## Version Bumping Helper Script

```bash
#!/bin/bash
# scripts/bump_version.sh

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.2.0"
    exit 1
fi

NEW_VERSION=$1

# Update pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Update __init__.py
sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/ccnotify/__init__.py

echo "Version bumped to $NEW_VERSION"
echo "Don't forget to update CHANGELOG.md!"
```

## Troubleshooting

### Common Issues

1. **Package name conflict**: Choose a different name if ccnotify is taken
2. **Version already exists**: Bump patch version
3. **Build fails**: Check dependencies and metadata in pyproject.toml
4. **Upload fails**: Verify API tokens and network connectivity

### Verification Steps

```bash
# Check package metadata
uvx twine check dist/*

# Verify installability
uvx --from dist/ccnotify-X.Y.Z-py3-none-any.whl ccnotify --version

# Test in clean environment
docker run --rm -it python:3.11 bash -c "pip install ccnotify && ccnotify --version"
```

## Best Practices

1. **Always test on TestPyPI first**
2. **Verify installation works** before publishing to production
3. **Keep CHANGELOG.md updated** with every release
4. **Use semantic versioning** consistently
5. **Tag releases** with descriptive messages
6. **Include built artifacts** in GitHub releases
7. **Test on multiple Python versions** when possible

## Resources

- [PyPI Publishing Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)