# X3 Desktop Simulator Test Guide

## CrossPoint 1.5.0 / CrossVi 1.1.2 — Windows, WSL2, macOS and Apple Silicon

**Project:** Z-Truyen X3  
**Purpose:** Build a repeatable desktop simulation environment for Xteink X3 firmware development and Z-Truyen application testing without flashing a physical X3.  
**Primary test targets:** CrossVi 1.1.2 and CrossPoint 1.5.0  
**Document status:** Engineering guide  
**Audience:** AI coding agent, developer, test owner  
**Physical-device policy:** No physical X3 flashing until all simulator/CI gates explicitly pass and the human owner approves.

---

## 1. Executive Summary

The Xteink X3 is an ESP32-C3 e-reader. CrossPoint and CrossVi provide a **native desktop simulator** that compiles firmware-side code for the host machine and renders the simulated e-ink framebuffer in an SDL2 window. This is the preferred pre-hardware test environment for the Z-Truyen project.

The upstream CrossPoint simulator explicitly supports:

- macOS Intel
- macOS Apple Silicon, including M4
- Linux
- Windows through WSL
- an X3-specific simulator target using the `SIMULATOR_DEVICE_X3` build flag
- a 792×528 X3 framebuffer
- simulated tilt input

The CrossVi repository currently exposes a direct X3 simulator launcher:

```bash
python3 scripts/run_simulator.py x3
```

and explicitly states that simulator testing covers build, boot, UI and basic application flows, while real hardware is still required for e-paper refresh/ghosting, SD timing, power use, physical buttons, and sleep/wake.

Sources:

- CrossVi: https://github.com/tvhdc/crossvi
- CrossPoint Reader: https://github.com/crosspoint-reader/crosspoint-reader
- CrossPoint Simulator: https://github.com/crosspoint-reader/crosspoint-simulator
- CrossVi SDK: https://github.com/tvhdc/crossvi-sdk

---

## 2. Critical Safety Rules

### 2.1 Simulator first

All firmware/UI/network/application changes MUST be tested in the simulator before physical hardware testing.

Required order:

```text
Source change
    ↓
Unit tests
    ↓
Integration tests
    ↓
Desktop simulator
    ↓
Stress / regression
    ↓
Firmware artifact
    ↓
Human approval
    ↓
Physical X3
```

### 2.2 No automatic flashing

The AI agent MUST NOT:

- flash a physical X3 automatically;
- erase physical flash;
- replace the bootloader;
- partition physical flash;
- perform unattended OTA on a physical device;
- switch a physical X3 to another firmware without explicit human approval.

The agent may build a `firmware.bin` artifact, calculate its SHA-256 checksum, and prepare instructions.

### 2.3 Simulator is not a full hardware emulator

The simulator is a **software simulation**, not a cycle-accurate X3 hardware emulator. CrossVi explicitly lists these behaviors as physical-only validation areas:

- e-paper refresh behavior
- ghosting
- SD-card timing
- power consumption
- physical buttons
- sleep/wake behavior

Therefore a simulator PASS means **software integration confidence**, not hardware certification.

---

## 3. What Is Being Simulated?

### 3.1 CrossPoint architecture

CrossPoint is the open-source firmware base for the Xteink X3/X4 and includes the reader engine, library, Wi-Fi, OPDS, KOReader Sync, storage, and related device logic.

Repository:

https://github.com/crosspoint-reader/crosspoint-reader

### 3.2 CrossVi architecture

CrossVi is a CrossPoint fork. It adds a richer library, statistics, configurable Home layouts and additional SD-storage safeguards. It currently provides an X3/X4 desktop simulator launcher.

Repository:

https://github.com/tvhdc/crossvi

### 3.3 CrossPoint Simulator architecture

The CrossPoint simulator compiles the firmware natively and renders its e-ink display in an SDL2 desktop window. It does not require a physical device.

For X3, the simulator uses:

```text
792 × 528 framebuffer
landscape X3 profile
tilt sensor simulation
```

Source: CrossPoint Simulator README.

---

# 4. Recommended Host Strategy

## 4.1 Preferred host: macOS

If a Mac with Apple Silicon is available, use it as the primary simulator host.

The upstream CrossPoint Simulator explicitly states it has been tested on Apple Silicon, including M4.

Recommended stack:

```text
macOS
  ├── Homebrew
  ├── Git
  ├── Python 3
  ├── PlatformIO / pioarduino
  ├── SDL2
  ├── CrossVi
  ├── CrossPoint Simulator
  └── Z-Truyen backend
```

For the project owner, an Apple Silicon Mac is especially convenient because the existing Mac mini M4 can also become the always-on Z-Truyen development/server host. The simulator itself can be run on the same machine, provided test load remains reasonable.

## 4.2 Preferred Windows strategy: WSL2

Native Windows is **not supported by the upstream CrossPoint Simulator**. The supported path is WSL/Linux under Windows.

Recommended:

```text
Windows 11
   ↓
WSL2
   ↓
Ubuntu
   ↓
PlatformIO + SDL2 + OpenSSL
   ↓
CrossPoint/CrossVi simulator
```

Use WSL2 rather than VirtualBox/VMware for the simulator unless the user has a separate reason to require a full VM.

---

# 5. Windows PC — Recommended WSL2 Setup

## 5.1 Install WSL2

Open PowerShell as Administrator:

```powershell
wsl --install
```

Reboot if requested.

Then verify:

```powershell
wsl --status
wsl -l -v
```

The target should be WSL2.

Recommended distro:

```text
Ubuntu 24.04 LTS
```

If an existing Ubuntu WSL2 environment is already available, it may be reused after verifying the required packages.

## 5.2 Update Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
```

## 5.3 Install base packages

```bash
sudo apt install -y \
  git \
  curl \
  wget \
  unzip \
  zip \
  build-essential \
  python3 \
  python3-pip \
  python3-venv \
  pkg-config \
  libsdl2-dev \
  libssl-dev \
  ca-certificates
```

The upstream simulator documentation specifically calls for `libsdl2-dev` and `libssl-dev` on Linux/WSL.

## 5.4 Verify toolchain

```bash
git --version
python3 --version
g++ --version
sdl2-config --version
openssl version
```

## 5.5 Install PlatformIO / pioarduino

The exact build frontend should follow the current CrossVi repository requirements. CrossVi currently lists `pioarduino`, Python 3.8+, Git and repository submodules as prerequisites.

Recommended approach:

```bash
python3 -m venv ~/.venvs/x3
source ~/.venvs/x3/bin/activate
python -m pip install --upgrade pip
python -m pip install platformio
```

If the repository pins a specific `pioarduino` release or environment, prefer the repository's pinned dependency rather than overriding it.

## 5.6 Clone CrossVi with submodules

```bash
git clone --recursive https://github.com/tvhdc/crossvi.git
cd crossvi
```

Verify submodules:

```bash
git submodule status
```

Do not use a shallow clone for the first development environment if build scripts depend on Git metadata.

---

# 6. macOS — Recommended Setup

## 6.1 Install Homebrew

If Homebrew is not installed, install it from:

https://brew.sh/

Then:

```bash
brew update
```

## 6.2 Install simulator dependencies

```bash
brew install git python sdl2
```

Verify:

```bash
git --version
python3 --version
sdl2-config --version
```

The CrossPoint Simulator README explicitly requires SDL2 and states that macOS and Linux/WSL use different native compiler/library flags.

## 6.3 Install PlatformIO

```bash
python3 -m venv ~/.venvs/x3
source ~/.venvs/x3/bin/activate
python -m pip install --upgrade pip
python -m pip install platformio
```

Then:

```bash
pio --version
```

## 6.4 Clone CrossVi

```bash
git clone --recursive https://github.com/tvhdc/crossvi.git
cd crossvi
```

---

# 7. Building CrossVi X3 Simulator

CrossVi currently documents the following direct simulator commands:

```bash
python3 scripts/run_simulator.py x3
```

and, for X4:

```bash
python3 scripts/run_simulator.py x4
```

For this project, only the X3 target should be treated as the primary simulator.

## 7.1 First baseline run

Run:

```bash
python3 scripts/run_simulator.py x3
```

Expected result:

- firmware compiles for native host execution;
- SDL2 simulator opens;
- X3-like framebuffer is displayed;
- Home/UI becomes interactive.

The exact simulator binary path may change between repository revisions. The launcher script is therefore preferred over hardcoding `.pio` paths.

## 7.2 Baseline evidence

Record:

```text
host OS
CPU architecture
Python version
PlatformIO version
CrossVi commit
Git submodule revisions
compiler version
simulator startup result
```

Create:

```text
docs/test-results/baseline-crossvi-x3.md
```

---

# 8. Building CrossPoint X3 Simulator

The CrossPoint Simulator repository provides device-specific build support through a simulator environment with:

```text
-DSIMULATOR_DEVICE_X3
```

This selects:

- X3 792×528 framebuffer;
- X3 board profile;
- simulated tilt input.

The upstream sample PlatformIO configuration exposes an environment named:

```text
simulator_x3
```

Reference:

https://github.com/crosspoint-reader/crosspoint-simulator

## 8.1 Clone CrossPoint

```bash
git clone --recursive https://github.com/crosspoint-reader/crosspoint-reader.git
cd crosspoint-reader
```

## 8.2 Install simulator dependency

The simulator can be used as the native library dependency. If the repository's current build configuration already references it, do not manually duplicate the dependency.

If using a dedicated simulator checkout, follow its README and sample PlatformIO configuration.

## 8.3 macOS configuration

The simulator repository provides a sample macOS PlatformIO configuration.

Important rule:

> On macOS, start from the repository's macOS sample configuration rather than copying Linux flags.

Run the project's documented simulator environment and verify that the X3-specific environment includes:

```text
-DSIMULATOR_DEVICE_X3
```

## 8.4 WSL configuration

Use the simulator's Linux/WSL sample configuration.

The sample build uses:

```text
-DSIMULATOR
-DSIMULATOR_DEVICE_X3
```

and native SDL2/OpenSSL compiler flags.

## 8.5 Do not use native Windows

The upstream simulator README explicitly says native Windows is not supported. Use WSL2.

---

# 9. Understanding the X3 Simulator SD Card

The simulator exposes a host-directory-backed filesystem for SD-card-like content.

This is extremely useful for Z-Truyen testing.

A simulator test directory can contain:

```text
sdcard/
  books/
  fonts/
  cache/
  screenshots/
  config/
```

A real X3 would see these as an SD card. The simulator can use the host directory instead.

Some CrossPoint-derived projects create `./sdcard/` automatically when starting the emulator. For a custom fork, inspect the current simulator launcher to determine the exact path.

## 9.1 Test EPUB injection

Example:

```bash
cp ~/Downloads/test-book.epub ./sdcard/
```

Then start the simulator.

Expected:

```text
Home / Library
    ↓
Book appears
    ↓
Open EPUB
    ↓
Reader renders content
```

## 9.2 Use deterministic test fixtures

Create:

```text
test-fixtures/
  epub/
    minimal.epub
    vietnamese.epub
    cjk.epub
    images.epub
    large.epub
    malformed.epub
```

Do not rely on random personal books for automated regression testing.

---

# 10. Z-Truyen Backend Test Environment

The backend should run separately from the firmware simulator.

Recommended layout:

```text
Z-Truyen-X3/
├── firmware/
│   ├── crossvi/
│   └── crosspoint/
├── simulator/
├── backend/
├── test-fixtures/
├── test-results/
├── docs/
└── scripts/
```

The simulator and server should communicate over HTTP just like a real X3.

Recommended local endpoints:

```text
http://127.0.0.1:8080/
http://127.0.0.1:8080/opds
http://127.0.0.1:8080/health
```

The simulator should not use hardcoded production URLs during development.

Use a configurable endpoint:

```text
ZTRUYEN_SERVER_URL
```

or firmware test configuration.

---

# 11. Recommended Local Network Topology

## 11.1 Single-host simulator

On macOS or Linux/WSL:

```text
+-------------------------------+
| Host PC / Mac                 |
|                               |
|  CrossVi simulator            |
|        │                      |
|        │ HTTP                 |
|        ▼                      |
|  Z-Truyen backend :8080       |
|        │                      |
|        ▼                      |
|  Mock/real source adapters    |
+-------------------------------+
```

This is the preferred development mode.

## 11.2 Mac mini development server

If the Z-Truyen backend is running on a dedicated Mac mini:

```text
Windows / Mac workstation
       │
       │ simulator
       │
       ▼
Z-Truyen API on Mac mini
       │
       ▼
Internet/source websites
```

The simulator can therefore test the same backend that later serves a real X3.

---

# 12. Why the Simulator Is Better Than a Traditional VM for This Project

A VirtualBox/VMware machine does **not** itself emulate the X3.

The useful emulator is the CrossPoint/CrossVi desktop simulator.

A VM is only an optional host environment:

```text
Windows
  ↓
VirtualBox
  ↓
Ubuntu
  ↓
CrossPoint simulator
```

This adds another compatibility layer and is usually unnecessary.

Preferred Windows architecture:

```text
Windows
  ↓
WSL2 Ubuntu
  ↓
CrossVi/CrossPoint simulator
```

Preferred macOS architecture:

```text
macOS
  ↓
CrossVi/CrossPoint simulator
```

---

# 13. Simulator Limitations

## 13.1 It can validate

High confidence:

- C/C++ application logic
- navigation
- screen layout
- button event handling where simulated
- menu state
- library logic
- OPDS parsing
- HTTP request flow
- JSON/XML parsing
- file handling
- EPUB opening
- error states
- cache logic
- KOSync logic at protocol/application level
- memory instrumentation visible in host tests
- deterministic UI tests

## 13.2 It cannot certify

Physical hardware only:

- true E-Ink waveform quality
- exact ghosting
- panel controller timing
- physical SD electrical timing
- true power consumption
- battery gauge behavior
- sleep-current behavior
- physical button feel/debounce
- USB behavior
- hardware-specific failures on new X3 revisions

CrossVi explicitly calls out these limitations.

---

# 14. CrossVi Hardware-Revision Gate

Before any physical flash, the agent must verify the physical X3 revision.

CrossVi currently warns that newer X3 production units may use the UC8279 display controller and that support still needs validation on the new hardware.

Therefore:

```text
SIMULATOR PASS
      ≠
PHYSICAL HARDWARE COMPATIBLE
```

A physical X3 hardware record should include:

```text
device model
current stock firmware
hardware revision if available
display controller if determinable
purchase/source channel
USB lock state if known
SD backup status
```

---

# 15. CrossPoint Simulator-Specific Notes

The upstream simulator documentation states:

- it compiles firmware natively;
- it renders the e-ink display in an SDL2 window;
- macOS and Linux/WSL use different native compiler/library flags;
- native Windows is not supported;
- Apple Silicon M4 has been tested;
- X3 requires `SIMULATOR_DEVICE_X3`;
- device-specific environments include a ready-to-use `simulator_x3` target.

When a CrossPoint-derived fork adds a custom renderer, it may need to notify the simulator of orientation changes using the simulator hook described by the simulator README.

Agent task:

If the UI is rotated incorrectly in the simulator, inspect renderer orientation handling before changing application layout code.

---

# 16. CrossVi Simulator-Specific Notes

CrossVi currently provides:

```bash
python3 scripts/run_simulator.py x3
```

This should be the default X3 simulation command for the project.

CrossVi also requires its repository submodules.

Never manually replace the SDK submodule with an unrelated revision unless the task explicitly requires it.

CrossVi uses its own pinned SDK fork:

https://github.com/tvhdc/crossvi-sdk

This helps maintain reproducible builds.

---

# 17. Simulator Test Modes

The project should define at least four modes.

## MODE A — UI only

```text
No network
Mock local data
```

Purpose:

- fastest feedback
- deterministic UI testing

## MODE B — Mock backend

```text
Simulator
   ↓
Local mock server
```

Purpose:

- API contract testing
- download flow
- failure simulation

## MODE C — Local real backend

```text
Simulator
   ↓
Real Z-Truyen backend
   ↓
Real source websites
```

Purpose:

- full integration

## MODE D — Cloud staging

```text
Simulator
   ↓
HTTPS
   ↓
Cloud staging backend
```

Purpose:

- TLS
- auth
- CDN/cache
- production-like behavior

---

# 18. Unit-Test Layer

The AI agent must create tests for backend components independently.

Minimum:

### Source adapter

```text
search()
book()
chapters()
chapter()
```

### EPUB

```text
metadata
encoding
chapter generation
cover
ZIP validity
OPF validity
```

### Cache

```text
miss
hit
stale
invalidate
concurrency
```

### API

```text
200
400
401
404
429
500
```

---

# 19. Integration-Test Layer

Test:

```text
search
  ↓
book
  ↓
chapter
  ↓
download
  ↓
save
  ↓
open EPUB
```

Must run against:

1. mock source
2. real source adapter
3. staging deployment

---

# 20. Simulator Acceptance Tests

## TEST-X3-001 — Boot

Expected:

- simulator opens
- Home screen appears
- no crash

## TEST-X3-002 — Library

Expected:

- test EPUB is visible
- metadata is readable

## TEST-X3-003 — EPUB

Expected:

- Vietnamese text renders
- page navigation works

## TEST-X3-004 — OPDS

Expected:

- server connection succeeds
- catalog appears

## TEST-X3-005 — Search

Expected:

- search request reaches backend
- results render

## TEST-X3-006 — Chapter list

Expected:

- chapters displayed
- pagination works

## TEST-X3-007 — Download

Expected:

- EPUB downloads
- file appears in simulated SD

## TEST-X3-008 — Open downloaded EPUB

Expected:

- EPUB opens
- content is readable

## TEST-X3-009 — Offline

Procedure:

1. download EPUB
2. stop server
3. restart simulator
4. open book

Expected:

- book opens offline

## TEST-X3-010 — Network error

Expected:

- timeout does not crash firmware
- readable error shown

## TEST-X3-011 — Invalid EPUB

Expected:

- reader rejects it gracefully
- existing library remains intact

## TEST-X3-012 — Large EPUB

Expected:

- no crash
- acceptable responsiveness

---

# 21. KOSync Simulator Tests

The simulator can test application-level KOSync behavior, but not real Wi-Fi timing or every possible device-specific reader behavior.

Minimum test matrix:

| Scenario | Device A | Device B | Expected |
|---|---|---|---|
| same EPUB | CrossVi sim | KOReader | progress transfers |
| same filename | CrossVi sim | KOReader | match |
| different filenames | CrossVi sim | KOReader | verify configured matching mode |
| regenerated EPUB | CrossVi sim | KOReader | document identity behavior documented |
| different font | X3 sim | KOReader | location remains as accurate as mapping allows |
| remote ahead | CrossVi sim | KOReader | correct smart-sync behavior |
| local ahead | CrossVi sim | KOReader | correct smart-sync behavior |

The agent must not describe KOSync as file synchronization. It is primarily reading-position synchronization.

---

# 22. Memory and Stress Tests

Because the target hardware is an ESP32-C3, memory behavior is critical.

Test repeated operations:

```text
open → close EPUB × 100
search × 100
OPDS browse × 100
Wi-Fi reconnect × 50
Download × 50
```

Watch for:

- progressive heap decline
- crashes after repeated navigation
- allocator fragmentation
- stale handles
- file descriptor leaks
- network resource leaks

Host simulator memory trends do not directly equal ESP32 RAM behavior, but they can still reveal application-level leaks.

---

# 23. Performance Tests

Measure:

```text
simulator start time
OPDS root response time
search latency
book list rendering
chapter list rendering
EPUB download time
EPUB open time
large-document indexing time
```

Record a baseline before optimization.

Never accept a performance regression based only on visual impression.

---

# 24. CI Pipeline

Recommended GitHub Actions stages:

```text
lint
  ↓
unit tests
  ↓
backend integration
  ↓
firmware compile
  ↓
simulator compile
  ↓
simulator smoke tests
  ↓
artifact generation
```

Physical X3 is intentionally outside automated CI.

CI artifacts should include:

```text
firmware.bin
SHA256SUMS
simulator binary/log
JUnit test report
build metadata
```

---

# 25. AI Agent Automation

The AI agent should be able to execute:

```bash
./scripts/bootstrap.sh
./scripts/test-unit.sh
./scripts/test-backend.sh
./scripts/build-simulator-x3.sh
./scripts/test-simulator-x3.sh
./scripts/build-firmware.sh
```

Recommended future repository structure:

```text
scripts/
  bootstrap.sh
  build-simulator-x3.sh
  test-simulator-x3.sh
  build-firmware.sh
  run-backend.sh
  validate-epub.sh
  collect-test-report.sh
```

The exact scripts may be implemented incrementally.

---

# 26. Screenshot / Visual Regression

The simulator renders into an SDL window, so deterministic UI screenshot testing is feasible.

Recommended:

```text
screenshots/
  baseline/
  current/
```

Compare:

- Home
- Search
- Book details
- Chapter list
- Download state
- Error state
- Reader

Use a tolerance for rendering differences only where necessary.

Do not weaken visual regression thresholds just to make tests pass.

---

# 27. Test Data Rules

Use synthetic books first.

Recommended fixtures:

```text
minimal_en.epub
vietnamese_basic.epub
vietnamese_diacritics.epub
cjk.epub
rtl.epub
image_heavy.epub
large.epub
malformed.epub
```

For real website testing, keep the test corpus small and respect source-site terms, rate limits and applicable copyright rules.

---

# 28. Production-Like Staging

After local simulator PASS:

```text
Simulator
    ↓
HTTPS
    ↓
Cloud staging
    ↓
EPUB cache
```

Validate:

- TLS certificate
- redirects
- authentication
- timeouts
- rate limiting
- compressed responses
- large downloads
- disconnect/retry

Do not point an automated stress test at production source websites.

---

# 29. Physical X3 Release Gate

The AI agent must stop before this stage.

The human owner must verify:

- current stock firmware recorded
- X3 hardware revision recorded
- SD card backed up
- correct target image
- SHA-256 verified
- recovery path available
- exact firmware provenance recorded

Only then may the owner manually flash.

---

# 30. Physical Validation Matrix

Simulator PASS is prerequisite.

Physical tests:

```text
PHYS-001 Boot
PHYS-002 Wi-Fi
PHYS-003 OPDS
PHYS-004 Search
PHYS-005 Download
PHYS-006 EPUB open
PHYS-007 Page turn
PHYS-008 Sleep
PHYS-009 Wake
PHYS-010 Ghosting
PHYS-011 Battery
PHYS-012 SD stress
PHYS-013 KOSync
PHYS-014 Recovery
```

Anything related to display quality, power or SD electrical behavior must be considered physical-only evidence.

---

# 31. Rollback Strategy

Never test a custom firmware without a known rollback procedure.

Maintain:

```text
artifacts/
  stock/
  crosspoint/
  crossvi/
  experimental/
```

Each artifact must have:

```text
filename
version
git commit
build timestamp
SHA256
```

Never mix X3 and X4 firmware images.

---

# 32. Recommended Development Sequence

```text
Stage 0
Host setup
    ↓
Stage 1
CrossVi simulator baseline
    ↓
Stage 2
CrossPoint simulator baseline
    ↓
Stage 3
Z-Truyen mock backend
    ↓
Stage 4
OPDS integration
    ↓
Stage 5
EPUB integration
    ↓
Stage 6
Real source adapter
    ↓
Stage 7
Cache + authentication
    ↓
Stage 8
CrossVi simulator integration
    ↓
Stage 9
KOSync tests
    ↓
Stage 10
Stress / failure tests
    ↓
Stage 11
Cloud staging
    ↓
Stage 12
Native CrossVi feature, if still justified
    ↓
Stage 13
Human-approved physical X3 test
    ↓
Stage 14
Release
```

---

# 33. Definition of Done for Simulator Phase

The simulator phase is DONE only if:

- CrossVi X3 simulator builds
- CrossPoint X3 simulator builds
- both launch reliably
- test EPUBs render
- OPDS works
- Z-Truyen search works
- chapter listing works
- EPUB download works
- offline reading works
- errors are handled
- no reproducible crash remains in the defined smoke suite
- logs are captured
- artifacts are reproducible
- the exact tested Git commits are recorded

---

# 34. Recommended First Task for the AI Agent

The first automated task must be **environment reconnaissance only**.

Prompt to agent:

```text
Read this document completely.
Do not modify production firmware.
Do not flash any physical X3.
Do not attempt OTA on a physical device.

Task:
1. Detect host OS and CPU architecture.
2. Verify Git, Python, PlatformIO/pioarduino and SDL2.
3. Clone CrossVi recursively.
4. Clone CrossPoint recursively.
5. Inspect the CrossVi X3 simulator launcher.
6. Inspect the CrossPoint X3 simulator environment.
7. Build the unmodified CrossVi X3 simulator.
8. Build the unmodified CrossPoint X3 simulator.
9. Launch both simulators.
10. Create docs/PHASE_0_REPORT.md.

The report must contain:
- environment
- versions
- repository commits
- build commands
- simulator commands
- screenshots/log evidence
- failures and fixes
- exact next step

Do not start Z-Truyen implementation yet.
```

---

# 35. Known Upstream References

## CrossVi

https://github.com/tvhdc/crossvi

Current repository documentation states:

- X3/X4 firmware
- build requirements include pioarduino, Python 3.8+, Git and submodules
- X3 simulator command:
  `python3 scripts/run_simulator.py x3`
- simulator is suitable for build, boot, UI and basic application flows
- hardware-specific behaviors still require a physical device
- newer X3 revisions may use UC8279 and require additional validation

## CrossVi SDK

https://github.com/tvhdc/crossvi-sdk

## CrossPoint Reader

https://github.com/crosspoint-reader/crosspoint-reader

## CrossPoint Simulator

https://github.com/crosspoint-reader/crosspoint-simulator

The simulator README states:

- desktop SDL2 simulation
- macOS / Linux / WSL support
- native Windows unsupported
- Apple Silicon M4 tested
- `SIMULATOR_DEVICE_X3`
- 792×528 X3 framebuffer
- simulator_x3 PlatformIO environment

## Z-Truyenviet plugin

https://github.com/magicxlll/Z-Truyenviet.koplugin

This is the source/reference for the later Z-Truyen backend extraction. Its KOReader plugin nature must not be confused with an X3 firmware plugin runtime.

---

# 36. Final Architectural Decision

The safest project architecture is:

```text
                  Z-Truyen Cloud/Local Server
                  ┌──────────────────────────┐
                  │ Search                   │
                  │ Source adapters          │
                  │ Scraping                 │
                  │ EPUB generation          │
                  │ Cache                    │
                  │ Authentication           │
                  └────────────┬─────────────┘
                               │
                              OPDS
                               │
                  ┌────────────▼────────────┐
                  │ CrossVi / CrossPoint X3 │
                  │                         │
                  │ OPDS client             │
                  │ Downloader               │
                  │ Local storage            │
                  │ EPUB reader              │
                  │ KOSync                   │
                  └─────────────────────────┘
```

The X3 should remain a thin client whenever possible.

The simulator should be the default engineering test target.

The physical X3 is the final hardware validation target, not the primary development environment.

---

# 37. Source Verification Date

This guide was prepared using current public repository documentation checked on **2026-08-18**.

Because the simulator and firmware repositories are active, the AI agent MUST re-check the current repository README, build scripts and tags at the start of every development session rather than assuming these commands remain unchanged forever.
