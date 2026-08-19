# Task 17 Report: Clone và Build CrossVi Simulator Documentation

**Date**: 2026-08-13
**Task**: Phase A-4 - CrossVi Simulator Setup Documentation

## Summary

Created complete documentation and scripts for setting up the Z-Truyen backend with CrossVi simulator on macOS (Mac mini M4). Since the simulator only runs on macOS and current environment is Windows, this task focused on creating clear documentation for the user.

## Deliverables

### 1. `docs/simulator-setup.md`
Complete setup guide including:
- Prerequisites (macOS, Python 3.12+, Git, SDL2)
- CrossVi/CrossPoint repository clone instructions
- Dependency installation (Homebrew packages, Python packages)
- Build instructions for Apple Silicon (M1-M4) and Intel Macs
- CrossVi simulator run commands
- OPDS server configuration steps
- Backend startup options (Direct Python, helper script, Docker)
- Troubleshooting section

### 2. `docs/crosvi-opds-spec.md`
OPDS specification documentation including:
- OPDS version support (1.0, 1.2; limited 2.0)
- Supported OPDS link relations (acquisition, navigation)
- Search implementation details
- EPUB download behavior and file naming convention
- Known limitations for CrossVi and CrossPoint Reader
- Validation checklist
- Testing commands (curl examples)

### 3. `scripts/run-dev.sh` (Updated)
Enhanced helper script with:
- Automatic local IP detection (en0/en1 fallback)
- Clear display of OPDS URL for X3 configuration
- Python virtual environment setup
- Automatic dependency installation
- Clean shutdown handling with trap

## OPDS Implementation Details

Based on project analysis:
- Backend implements OPDS 1.2 with Atom XML feeds
- Namespace: `http://opds-spec.org/2010/catalog`
- Supports: acquisition links, navigation, search
- EPUB files follow convention: `ztruyen_{source}_{slug}_v{vol}.epub`
- 50 chapters per volume for memory optimization

## Files Created/Modified

| File | Action |
|------|--------|
| `docs/simulator-setup.md` | Created |
| `docs/crosvi-opds-spec.md` | Created |
| `scripts/run-dev.sh` | Updated |

## Next Steps

User should:
1. Run `scripts/run-dev.sh` on Mac mini M4
2. Note the displayed OPDS URL
3. Configure CrossVi simulator with OPDS server URL
4. Test catalog browsing and EPUB download

## References

- CrossVi: https://github.com/tvhdc/crossvi
- CrossPoint Reader: https://github.com/crosspoint-reader/crosspoint-reader
- CrossPoint Simulator: https://github.com/uxjulia/crosspoint-simulator
- Existing docs: `docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md`
- OPDS Spec: https://opds-spec.org/specs/opds-catalog-1-2/
