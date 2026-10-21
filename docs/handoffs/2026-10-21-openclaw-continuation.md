# Handoff — vapor-studio → OpenClaw continuation

**Date:** 2026-10-21 (updated)
**Repo:** `/Users/sam/Projects/ai/vapor-studio` → `github.com/samklepdev/vapor-store` (**public**)
**Default branch:** `main`
**Owner:** Sam
**For:** an OpenClaw-hosted agent (or next session) continuing after the M0/M1 core.

---

## TL;DR

The **M0/M1 core tooling is built, tested, reviewed, and merged.** Local
**ComfyUI/SDXL generation is proven live** (real images produced), the
**style-bible aesthetics are owner-approved**, and a **print-resolution upscale
pass** (Real-ESRGAN x4) is built. Work has moved into **M1 proper**: the owner
has approved 6 battlestation keepers and the first Etsy listings are in prep.
What remains is **owner-driven**: reference images, finishing/listing on Etsy,
and the market-signal wait (Tasks 5–8).

**Do not re-derive the project — read the committed artifacts:**
- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- M0/M1 plan: `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`
- Local-provider spec + plan: `docs/specs/2026-10-21-comfyui-local-provider-*.md`
- Upscale spec + plan: `docs/specs/2026-10-21-producer-upscale-design.md`, `docs/plans/2026-10-21-producer-upscale.md`
- **Operating workflow + M1 runbook + M2 trigger: `docs/workflow.md`**
- SDD progress ledger (source of truth): `.superpowers/sdd/progress.md`

---

## What is DONE

| Area | Status |
|------|--------|
| Repo scaffold + `.gitignore` + `verify-task-1.sh` | ✅ merged |
| Producer core (`GenRequest`, `Provider`, `run`/`save_batch`/`dated_output_dir`, CLI) | ✅ merged, TDD |
| `FluxFalProvider` — Flux via fal.ai (paid) | ✅ merged (FAL_KEY + response-shape fixes) |
| `ComfyUIProvider` — SDXL via local ComfyUI (free, resale-clean) | ✅ merged, reviewed |
| Config-driven provider selection (`[provider].kind` + `--provider`) | ✅ merged |
| **ComfyUI generation proven live** | ✅ real 1024² PNGs generated (smoke + a 12-image battlestation batch) |
| Style bible **format** + `ip-blocklist.md` | ✅ merged |
| Style bible **aesthetics** (`vaporwave.md`, `psychedelia.md`) | ✅ owner-approved, merged |
| Private **reference-anchors area** (`style-bible/refs/`, gitignored) | ✅ merged |
| **Upscale pass** (Real-ESRGAN x4, print-res) | ✅ built + reviewed Approved; live smoke + merge is the immediate next step (branch `producer-upscale`) |

**Producer public interface (stable — the future M2 `producer` skill wraps it):**
`GenRequest`, `Provider`, `FluxFalProvider`, `ComfyUIProvider` (incl. `upscale()`),
and `run`/`save_batch`/`dated_output_dir` in `tools/producer/`. Select backend via
`config.toml` `[provider].kind` (`comfyui` | `flux-fal`) or `--provider`. Generate:
`python -m tools.producer.generate --niche <slug> --prompt "..." --n 4`; upscale:
`python -m tools.producer.upscale pipeline/04-approved/<file>.png`.

**Environment:** venv at `tools/producer/.venv` (Python 3.15). Run tests/lint from repo root.

---

## Live-ops notes (learned running it)

- **ComfyUI = Comfy Desktop at `127.0.0.1:8188`.** Checkpoints live in
  `/Users/sam/ComfyUI-Shared/models/checkpoints/` (SDXL base installed),
  upscale models in `.../models/upscale_models/` (`RealESRGAN_x4plus.pth` installed).
- **The bash sandbox blocks loopback** — any command hitting ComfyUI must run
  with the sandbox override, or it gets "connection refused" to localhost.
- **ComfyUI can crash under sustained load** — it dropped mid-batch once (2 of a
  12-image run failed). The producer surfaces this cleanly (`RuntimeError: ComfyUI
  unreachable or unresponsive`), it recovers on its own, and failed prompts just
  re-run. Watch for it on long batches (likely Mac memory pressure).
- **Drafts are 1024² — not print-ready.** That's why the upscale pass exists:
  1024² → 4096² (~27″ at 150 DPI). Wall-art listings use the upscaled masters.

---

## What's left for the owner

### 1. Finish the first battlestation Etsy listings (M1, in progress)
6 keepers are approved in `pipeline/04-approved/` (`bs-night-neon-001`,
`bs-chrome-statue-002`, `bs-pure-grid-001/002`, `bs-miami-dusk-001`,
`bs-sunset-grid-001`). Plan: upscale each → print master → draft title/tags/
description (+ AI disclosure) + mockup → **owner reviews, creates the Etsy
listing, and publishes** (human-publish = ToS-clean). 6 separate listings.

### 2. Style-bible reference sets
Aesthetics approved; only the **Reference set** section of each file is
`OWNER-TODO`. The gitignored `style-bible/refs/{vaporwave,psychedelia}/` folders
are ready — owner drops 5–10 A-grade anchors per aesthetic (kept private; paths
committed, images not). Agent wires the paths.

### 3. Tasks 5–8 — creative/market
Produce/finish the battlestation batch, list on Etsy, stream-packs test, weekly
go/no-go. Watch signals; first sale + repeat interest is the M2 trigger.

*(Secondary, non-blocking: regenerate the 2 psychedelia concepts — `ps-botanical`,
`ps-cosmic` — that failed during the ComfyUI crash.)*

---

## The hard stop: do NOT build M2 yet

M2 (the OpenClaw skills: brief-generator, pre-QC, producer skill, packager, etc.)
is **not built until a niche crosses "first sales + repeat interest"** (spec
prove-before-automate / Task 8 gate). Zero listings are live yet, so the trigger
is nowhere near. Carry the owner-driven M1 tasks and hold. When the gate hits,
that's a new M2 plan; the producer's stable interface (above) is what the skill wraps.

---

## Parked (non-blocking, spec §8)

Messaging channel (Telegram vs WhatsApp), exact Claude model IDs for M2 (pin via
the `claude-api` skill when M2 starts), whether `~/Projects/ai/art-store` relates.

---

## Notes / guardrails

- **License guard (resale):** local generation must use a commercially-licensed
  model — **SDXL (OpenRAIL)**, **FLUX.1-schnell (Apache-2.0)**, or Real-ESRGAN x4
  (BSD-3). **Never FLUX.1-dev locally for resale.** fal.ai's hosted `flux/dev` is fine.
- **Repo is public** — no secrets committed; `tools/producer/config.toml` (fal key)
  is gitignored and untracked. Keep it that way. Draft art in `pipeline/` stays local.

## Secrets

No secrets in the repo. `tools/producer/config.toml` holds the fal.ai key, is
gitignored and untracked. Never commit it.
