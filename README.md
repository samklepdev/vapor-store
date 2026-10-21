# vapor-studio

Human-in-the-loop digital-goods studio for vaporwave / psychedelia downloads.
OpenClaw runs the pipeline; the owner supplies taste at three approval gates.

- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- Current plan: `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`

## Status: M0/M1 — foundation + manual proof (no automation yet)

## Image generation (local tool)

    cd tools/producer
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp config.example.toml config.toml   # add your fal.ai key
    python3 generate.py --niche battlestation --prompt "..." --n 4
