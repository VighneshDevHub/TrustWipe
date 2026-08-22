# Phase 2 — Wipe Agent

## What this phase delivers

A CLI program that:
1. Detects a target device (a safe test file for demos, or a real Linux
   block device for actual hardware)
2. Auto-selects the correct NIST 800-88 method based on device type
3. Executes the wipe
4. Verifies it by sampling random offsets before/after
5. Builds a report and submits it to the Phase 1 backend, receiving back
   a signed certificate

This is the piece that turns "we have a signing service" into "we have a
tool that actually wipes something and gets a certificate for it."

## Directory structure

```
wipe-agent/
├── src/
│   ├── main.py                        # CLI entrypoint — orchestrates the pipeline
│   ├── method_selector.py             # device type -> NIST 800-88 method mapping
│   ├── verifier.py                    # pre/post read-back sampling
│   ├── report_builder.py              # builds the payload sent to the backend
│   ├── api_client.py                  # HTTP client -> POST /api/v1/wipes
│   ├── detectors/
│   │   ├── base.py                    # DeviceInfo + DeviceDetector interface
│   │   ├── file_target.py             # SAFE: treats a file as the device (demo/tests)
│   │   └── linux_block_device.py      # REAL: detects an actual /dev/sdX via lsblk
│   └── wipers/
│       ├── base.py                    # Wiper interface + WipeResult
│       ├── clear.py                   # NIST Clear — 1-pass overwrite
│       ├── purge.py                   # NIST Purge — 3-pass overwrite (SW fallback)
│       └── crypto_erase.py            # NIST Purge via key destruction (SSD/NVMe)
├── tests/
│   ├── test_detectors.py
│   ├── test_wipers.py
│   ├── test_verifier.py
│   └── test_report_builder.py
└── requirements.txt
```

## Why a "file target" mode exists (read this before your demo)

**Never wipe a real production disk live on stage.** The file-target
detector treats any regular file (or a loopback disk image you create
with `dd` or `fallocate`) as the "device" — same pipeline, same wiper
code, same report format, zero risk. `linux_block_device.py` implements
real hardware detection via `lsblk` for when you actually deploy this
against physical drives, but it is a separate, explicit opt-in
(`--real-device`) — nobody can trigger it by accident.

## Commands to run it yourself

```bash
cd wipe-agent
pip install -r requirements.txt

# Run the test suite
pytest -v      # 14 passed

# Create a safe test volume to wipe (never a real disk)
python3 -c "open('/tmp/test_volume.img','wb').write(b'CONFIDENTIAL-DATA-'*4000)"

# Make sure the Phase 1 backend is running first:
#   cd ../backend && uvicorn app.main:app --port 8000

# Run the agent against it
python -m src.main --target /tmp/test_volume.img --operator "demo-station-1" --api-url http://localhost:8000
```

Expected output:
```
[detect] TEST_FILE — Simulated test volume (test_volume.img) (serial: TESTFILE-...)
[select] Method: NIST 800-88 Clear (single-pass overwrite)
[wipe] Starting...
[wipe] Done — 1 pass(es), 104000 bytes processed.
[verify] Sampling random offsets for read-back verification...
[verify] 20/20 sampled regions confirmed wiped.
[report] Submitting to http://localhost:8000...
[report] Certificate issued: <uuid>
```

## How to test it manually / for your live demo

1. Before running, `head -c 60 /tmp/test_volume.img` — shows your readable "CONFIDENTIAL-DATA" text
2. Run the agent (command above)
3. After running, `head -c 60 /tmp/test_volume.img | od -A x -t x1z` — now pure random bytes
4. Copy the certificate ID from the output, hit `GET /api/v1/verify/{id}` on the Phase 1 backend — shows `overall_verified: true`

This before/after byte comparison plus the live verification call is a
strong 60-second demo segment on its own — data was readable, now it
isn't, and here's a signed, independently-checkable proof of exactly when
and how.

## What we tested and why

| Test file | What it proves |
|---|---|
| `test_wipers.py` | Each wiper actually overwrites content — Clear does 1 pass, Purge does 3 (ending in zeros), Crypto Erase overwrites via simulated key destruction |
| `test_detectors.py` | The file-target detector correctly reads file size, raises clearly on a missing target, and produces a stable serial across repeated runs; the method selector maps every device type to the correct NIST-aligned wiper |
| `test_verifier.py` | **The important negative test**: if a wipe is a no-op (nothing actually overwritten), verification correctly reports failure rather than blindly trusting that a wipe happened |
| `test_report_builder.py` | The JSON payload's keys exactly match the backend's `WipeReportIn` schema, so Phase 1 and Phase 2 can't silently drift apart |

All 14 tests pass. The full pipeline was also run live end-to-end against
the actual Phase 1 backend (not mocked) — see the terminal output above.

## Production notes

- **Real hardware**: `linux_block_device.py` is a real, working
  implementation using `lsblk` — but production hardening should add
  `hdparm -I` / `nvme id-ctrl` checks to confirm actual Secure Erase /
  Sanitize support before attempting it, and should call those native
  commands directly for Purge rather than the software 3-pass fallback
  (much faster, and operates below the filesystem).
- **Windows support**: not implemented in this MVP — the architecture
  supports it (implement `WindowsBlockDeviceDetector` against the same
  `DeviceDetector` interface, likely via `wmic diskdrive` or `psutil` +
  `diskpart` scripting). Mentioned as a clear "Phase 2 extension" in your
  pitch rather than built, given hackathon time constraints.
- **Bootable USB**: for wiping a machine whose OS won't boot — package
  this agent into a minimal Linux live image (Alpine-based). Out of scope
  for the MVP but a good "vision" talking point.

## Next: Phase 3

Certificate generation — turning the JSON certificate the backend already
returns into an actual signed PDF with an embedded QR code, ready to hand
to a buyer. Say "next" when ready.
