# Handoff — vapor-studio → OpenClaw continuation

**Date:** 2026-10-21 (updated)
**Repo:** `/Users/sam/Projects/ai/vapor-studio` → `github.com/samklepdev/vapor-store` (**public**)
**Default branch:** `main` (all work below is merged into it)
**Owner:** Sam
**For:** an OpenClaw-hosted agent (or next session) continuing after the M0/M1 core.

---

## TL;DR

The **M0/M1 core tooling is built, tested, reviewed, and merged to `main`.** The
producer can generate images two ways — **local ComfyUI/SDXL (free)** or
**fal.ai/Flux (paid)** — and the **style bible aesthetics are owner-approved.**
What remains is **entirely owner-driven**: your reference images, a live
generation smoke test, and the creative/market work (Tasks 5–8).

**Do not re-derive the project — read the committed artifacts:**
- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- M0/M1 plan: `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`
- Local-provider spec + plan: `docs/specs/2026-10-21-comfyui-local-provider-design.md`, `docs/plans/2026-10-21-comfyui-local-provider.md`
- SDD progress ledger (source of truth): `.superpowers/sdd/progress.md`

---

## What is DONE (merged to `main`)

| Area | Status |
|------|--------|
| Repo scaffold + `.gitignore` + `verify-task-1.sh` | ✅ merged |
| Producer core (`GenRequest`, `Provider` protocol, `run`/`save_batch`/`dated_output_dir`, CLI) | ✅ merged, TDD |
| `FluxFalProvider` — Flux via fal.ai (paid) | ✅ merged (+ FAL_KEY + response-shape fixes) |
| `ComfyUIProvider` — SDXL via local ComfyUI (free, resale-clean) | ✅ merged (PR #1), 14/14 tests, reviewed |
| Config-driven provider selection (`[provider].kind` + `--provider` flag) | ✅ merged (PR #1) |
| Style bible **format** + `ip-blocklist.md` | ✅ merged |
| Style bible **aesthetics** — `vaporwave.md`, `psychedelia.md` | ✅ owner-approved, merged (PR #2) |

Two PRs merged: **#1** (foundation + ComfyUI provider), **#2** (style-bible aesthetics).

**Producer public interface (stable — the future M2 `producer` skill wraps it):**
`GenRequest`, the `Provider` protocol, `FluxFalProvider`, `ComfyUIProvider`, and
`dated_output_dir` / `save_batch` / `run` in `tools/producer/`. Select the
backend via `config.toml` `[provider].kind` (`"comfyui"` | `"flux-fal"`) or
`--provider`. Invoke as a module from repo root:
`python -m tools.producer.generate --niche <slug> --prompt "..." --n 4`.

**Environment:** venv at `tools/producer/.venv` (Python 3.15; pytest 9.1.1,
ruff 0.17.1, fal-client installed). Run tests/lint from the repo root.

---

## What is BLOCKED on the owner (the real outstanding work)

### 1. Style bible **reference sets** — last piece of Task 2
The aesthetic sections of `vaporwave.md` / `psychedelia.md` are owner-approved.
Only the **Reference set** section of each is still `OWNER-TODO`: Sam must add
paths to 5–10 of his own A-grade exemplars (local files, not redistributed
assets) — private taste anchors the pre-QC step scores against.
→ *Agent action when paths arrive:* wire them into the two files, commit.

### 2. Live generation smoke test — pick a backend
Neither backend has completed a live run yet:
- **ComfyUI (free, preferred):** owner installs ComfyUI + an SDXL checkpoint,
  starts the server, sets `[comfyui].checkpoint` in `config.toml`, then runs the
  smoke test. This validates the live ComfyUI response shape — the one thing the
  mocked tests can't prove. (`docs/plans/2026-10-21-comfyui-local-provider.md`, Task 3.)
- **fal.ai (paid):** key is in `config.toml` (present, gitignored, not tracked).
  Smoke test currently **blocked on account balance** — fal returned
  `403 User is locked: Exhausted balance`. Top up at fal.ai/dashboard/billing to use it.

Smoke-test command (set `[provider].kind` first):
```
source tools/producer/.venv/bin/activate
python -m tools.producer.generate --niche battlestation \
  --prompt "retro-futurist chrome grid, sunset gradient, original art" --n 2
```
Expect 2 PNGs under `pipeline/02-raw/<today>/`.

### 3. Tasks 5–8 — owner-driven creative/market work
Produce/finish the battlestation batch (5), list on Etsy — human publishes per
ToS (6), run the small stream-packs test (7), weekly go/no-go ritual (8). No
agent can do these. See the M0/M1 plan for the runbooks.

---

## The hard stop: do NOT build M2 yet

M2 is the OpenClaw automation layer (brief-generator, pre-QC, producer skill,
packager, etc.). Per the spec's prove-before-automate principle and the plan's
**Task 8 gate**, M2 is **deliberately not built until a niche crosses "first
sales + repeat interest."** An OpenClaw agent "continuing" this project should
carry the owner-driven M1 tasks and hold — not start writing M2 skills — until
that gate is hit. When it is, that triggers a *new* M2 plan. The producer's
stable interface (above) is what that skill will wrap.

---

## Parked (non-blocking, spec §8)

Messaging channel (Telegram vs WhatsApp), exact Claude model IDs for M2 (pin via
the `claude-api` skill when M2 starts), and whether `~/Projects/ai/art-store`
relates to this project.

---

## Notes for whoever takes over

- **License guard (important for resale):** local generation must use a
  commercially-licensed checkpoint — **SDXL (OpenRAIL)** or **FLUX.1-schnell
  (Apache-2.0)**. **Never run FLUX.1-dev locally for resale** (non-commercial
  weights). Using fal.ai's hosted `flux/dev` is fine (their terms cover it).
  This is documented in `config.example.toml`.
- Earlier deferred fal findings are **resolved**: response-shape tolerance +
  fail-loud (`result["images"]` or `data.images`) are in; the ComfyUI path got a
  per-request timeout (no hang) and surfaces ComfyUI's HTTP error body.
- Repo is **public** — no secrets are committed; `tools/producer/config.toml`
  (holds the fal key) is gitignored and untracked. Keep it that way.

## Secrets

No secrets in the repo. `tools/producer/config.toml` holds the fal.ai key, is
gitignored and untracked. Never commit it.
