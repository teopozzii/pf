# App Icon Integration Guide

**Project**: Conto - Personal Finance Dashboard  
**Objective**: App icon (logo_conto.png) integrated into Windows & macOS releases via PyInstaller  
**Status**: ✅ **COMPLETE & IN PRODUCTION** (v0.1.14+)

**Date Updated**: March 30, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Current State](#current-state)
3. [File Structure](#file-structure)
4. [How Icons Work](#how-icons-work)
5. [Updating Icons in the Future](#updating-icons-in-the-future)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The Conto application displays a professional app icon (based on `logo_conto.png`) in:
- **Windows**: Taskbar, File Explorer, Desktop, Start Menu
- **macOS**: Dock, Finder, Activity Monitor, Launchpad

This is achieved by embedding icon files into the PyInstaller executables during the CI/CD build process.

---

## Current State

### Implementation Status: ✅ PRODUCTION-READY

| Stage | Status | Details |
|-------|--------|---------|
| **Icon Files Generated** | ✅ Done | Windows `.ico`, macOS `.icns` |
| **Local Testing** | ✅ Done | Icon verified in Finder/Dock/Activity Monitor |
| **CI/CD Integrated** | ✅ Done | GitHub Actions builds include `--icon` flags |
| **Release Testing** | ✅ Done | v0.1.14 released with embedded icons |
| **Production** | ✅ Live | Users downloading releases see correct app icons |

### Icon Files in Repository

```
assets/
├── logo_conto.png              (Original source - 1024×1024)
├── logo_conto.ico              (Windows icon - 137.4 KB)
├── logo_conto.icns             (macOS icon - 2.1 MB)
└── logo_conto.iconset/         (macOS source - 9 PNG files)
    ├── icon_16x16.png
    ├── icon_32x32.png
    ├── icon_32x32@2x.png
    ├── icon_128x128.png
    ├── icon_128x128@2x.png
    ├── icon_256x256.png
    ├── icon_256x256@2x.png
    ├── icon_512x512.png
    └── icon_512x512@2x.png

scripts/
└── create_icons.py             (PNG → ICO/ICNS converter)

.github/workflows/
└── build.yml                   (Includes --icon flags in PyInstaller commands)
```

---

## File Structure

### Icon Files

| File | Purpose | Size | Platform | Details |
|------|---------|------|----------|---------|
| `logo_conto.png` | Source image | N/A | Both | 1024×1024 RGBA, original design |
| `logo_conto.ico` | Windows icon | 137.4 KB | Windows | 6 sizes: 16, 32, 48, 64, 128, 256 px |
| `logo_conto.icns` | macOS icon | 2.1 MB | macOS | 9 sizes: 16-1024 px (with @2x variants) |
| `logo_conto.iconset/` | macOS source | 1.8 MB | macOS | PNG files for future conversions |

### Build Integration

**Windows** (`.github/workflows/build.yml` line ~43):
```yaml
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --icon=assets/logo_conto.ico --add-data "assets;assets" ...
```

**macOS** (`.github/workflows/build.yml` line ~52):
```yaml
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --icon=assets/logo_conto.icns --add-data "assets:assets" ...
```

---

## How Icons Work

### Generation Pipeline

```
logo_conto.png (1024×1024)
    ↓
[Python script: scripts/create_icons.py]
    ↓
    ├─→ logo_conto.ico (Windows - 6 sizes)
    └─→ logo_conto.iconset/ (macOS source - 9 PNG files)
            ↓
        [macOS tool: iconutil -c icns]
            ↓
        logo_conto.icns (macOS - bundled sizes)
```

### Embed in Executable

**CI/CD Build Process**:
1. Checkout code
2. Install dependencies (includes PyInstaller)
3. Run PyInstaller with `--icon=assets/logo_conto.ico` (Windows) or `--icon=assets/logo_conto.icns` (macOS)
4. PyInstaller embeds icon into executable binary
5. Release artifact published with icon embedded

**Result**: Users downloading `BankStatementApp.exe` or `BankStatementApp` see the company logo in Finder/File Explorer/Dock.

---

## Updating Icons in the Future

### When to Update

- Logo design changes
- Icon needs different visual style
- Need different sizes or formats

### Update Process

**Step 1: Replace or Update Source Image**

```bash
cd /Users/matteopozzi/code/conto

# Option A: Replace with new logo_conto.png (1024×1024 minimum)
# cp /path/to/new/logo.png assets/logo_conto.png

# Option B: Edit existing logo in design tool
# Then save as PNG to assets/logo_conto.png
```

Requirements:
- Square image (1024×1024 or larger recommended)
- RGBA PNG format
- Transparent background (recommended for dock display)
- Professional quality (will be downscaled to small sizes)

**Step 2: Regenerate Icon Files**

```bash
# Generate Windows .ico and macOS .iconset (with PNG files)
python scripts/create_icons.py
```

Expected output:
```
✅ Created: assets/logo_conto.ico (137.4 KB)
✅ Created 9 PNG files in .iconset
```

**Step 3: Convert macOS Iconset to ICNS**

```bash
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns && echo "✅ ICNS creation successful"
```

**Step 4: Verify Generated Files**

```bash
# Check all icon files exist and are correct size
ls -lh assets/logo_conto.ico assets/logo_conto.icns

# Verify ICNS is valid macOS icon format
file assets/logo_conto.icns
# Expected: "Macintosh icon file"
```

**Step 5: Test Locally** (optional but recommended)

```bash
# Clean previous builds
rm -rf build dist *.spec

# Build with new icons
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --icon=assets/logo_conto.icns --add-data "assets:assets" \
  --add-data "pages:pages" --add-data "utils:utils" \
  --hidden-import dash_pages --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers

# Launch and verify icon in Dock/Finder
./dist/BankStatementApp
```

**Step 6: Commit and Release**

```bash
# Stage updated icon files
git add assets/logo_conto.ico assets/logo_conto.icns assets/logo_conto.iconset/

# Commit with descriptive message
git commit -m "refactor(icon): update app icon with new design

- Updated assets/logo_conto.png with new design
- Regenerated assets/logo_conto.ico for Windows
- Regenerated assets/logo_conto.icns for macOS
- New icon reflects updated branding"

# Tag new release (uses updated icons automatically)
git tag v0.2.0  # Update version appropriately
git push origin v0.2.0

# CI/CD will build with new icons automatically
```

---

## Troubleshooting

### Icon Not Appearing After Build

**Symptom**: App builds successfully but icon is generic in Finder/Dock

**Checklist**:
1. ✅ Icon files exist: `ls -lah assets/logo_conto.ico* assets/logo_conto.icns`
2. ✅ Files are not corrupted: `file assets/logo_conto.ico assets/logo_conto.icns`
3. ✅ PyInstaller command includes `--icon` flag
4. ✅ Path is relative (not absolute): `--icon=assets/logo_conto.icns` ✓
5. ✅ Clean rebuild: `rm -rf build dist *.spec` then rebuild

**If still not appearing**:
```bash
# Verify PyInstaller can read the icon file
pyinstaller launcher.py --one-file --icon=assets/logo_conto.icns --help | head -5

# If error, regenerate icon files
python scripts/create_icons.py
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns
```

### ICNS Conversion Fails

**Symptom**: `iconutil` command returns error

**Solution**:
```bash
# Verify .iconset folder structure
ls -lah assets/logo_conto.iconset/

# Should show 9 PNG files. If missing, regenerate:
python scripts/create_icons.py

# Then try iconutil again
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns
```

### Icon Appears Pixelated at Taskbar

**Symptom**: Icon looks blurry in Windows taskbar or macOS Dock

**Cause**: Source image too small or poor quality

**Solution**:
- Ensure source PNG is **1024×1024 minimum** (yours is 1024×1024 ✓)
- Verify PNG is high quality (no compression artifacts)
- For vector logos, export from design tool at high DPI

### CI/CD Build Fails with Icon Path Error

**Symptom**: GitHub Actions build fails: "icon file not found"

**Check**:
1. Icon files are committed: `git status` shows icon files tracked
2. Path is correct: `assets/logo_conto.ico` (Windows) and `assets/logo_conto.icns` (macOS)
3. Workflow syntax is correct: Check `.github/workflows/build.yml`

**If not in git**:
```bash
git add assets/logo_conto.ico assets/logo_conto.icns assets/logo_conto.iconset/
git commit -m "Add missing icon files"
git push
```

---

## Reference Guide

### Quick Commands Summary

**One-time setup** (already complete):
```bash
# Create icons from PNG
python scripts/create_icons.py

# Convert macOS source to ICNS
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns
```

**Update icons** (if logo changes):
```bash
# Replace logo_conto.png with new design
cp /path/to/new/logo.png assets/logo_conto.png

# Regenerate all icon files
python scripts/create_icons.py
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns && echo "✅ ICNS creation successful"

# Test locally
rm -rf build dist *.spec
pyinstaller launcher.py --onefile --windowed --name BankStatementApp \
  --icon=assets/logo_conto.icns --add-data "assets:assets" \
  --add-data "pages:pages" --add-data "utils:utils" \
  --hidden-import dash_pages --hidden-import dash_bootstrap_components \
  --hidden-import plotly.io._renderers
./dist/BankStatementApp
```

**Commit and release**:
```bash
git add assets/logo_conto.ico assets/logo_conto.icns assets/logo_conto.iconset/
git commit -m "refactor(icon): update app icon"
git tag vX.Y.Z
git push origin vX.Y.Z
```

---

## Implementation Details

### Technical Choices

| Decision | Rationale |
|----------|-----------|
| PIL/Pillow for .ico | Built-in, no external tools, cross-platform |
| macOS `iconutil` for .icns | Native OS tool, produces optimal format |
| Keep .iconset/ in repo | Allows future ICNS regeneration without source PNG |
| Embed in PyInstaller via `--icon` | Native PyInstaller feature, no post-processing needed |
| Commit icon files to git | Reproducible builds, available in CI/CD |

### Size Considerations

- **Total icon files**: ~2.3 MB (reasonable for git)
  - `logo_conto.ico`: 137.4 KB
  - `logo_conto.icns`: 2.1 MB
  - `logo_conto.iconset/`: 1.8 MB (source for future use)
- **No impact on app size**: Icon embedded in executable, doesn't increase download size significantly

---

## Success Criteria

✅ Icon visible in Windows File Explorer  
✅ Icon visible in macOS Finder  
✅ Icon visible in Windows Taskbar  
✅ Icon visible in macOS Dock  
✅ Icon visible in Activity Monitor (macOS) / Task Manager (Windows)  
✅ Icon matches logo design (financial dashboard)  
✅ Icon appears at all sizes (16×16 to 1024×1024)  

All criteria currently **satisfied** ✅

---

## Support

**For questions about icons**:
1. Check `scripts/create_icons.py` documentation (inline comments)
2. Run `python scripts/create_icons.py --help` (if added)
3. Refer to sections above: "Updating Icons" or "Troubleshooting"

**For GitHub Actions concerns**:
- Check `.github/workflows/build.yml` for `--icon` flags
- Review GitHub Actions logs if build fails
- Ensure icon files are committed to git

---

## Summary

The app icon integration is **complete and working** in production (v0.1.14+). To update icons in the future, run these commands:

```bash
# 1. Update or create new logo_conto.png (1024×1024)
# 2. Regenerate icons
python scripts/create_icons.py

# 3. Convert to ICNS
iconutil -c icns ./assets/logo_conto.iconset -o ./assets/logo_conto.icns && echo "✅ ICNS creation successful"

# 4. Test (optional)
# - Verify files: ls -lh assets/logo_conto.*
# - Build locally if desired
# 5. Commit and release
git add assets/logo_conto.ico assets/logo_conto.icns assets/logo_conto.iconset/
git commit -m "refactor(icon): update app icon"
git tag vX.Y.Z && git push origin vX.Y.Z
```

No further action needed—icons are already integrated into every build! 🎉
