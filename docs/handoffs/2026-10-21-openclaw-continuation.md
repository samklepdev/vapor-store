# Handoff — vapor-studio → OpenClaw continuation

**Date:** 2026-10-21
**Repo:** `/Users/sam/Projects/ai/vapor-studio`
**Branch:** `m0-foundation` (base `b4c1c7b` on `main`)
**Owner:** Sam
**For:** an OpenClaw-hosted agent (or next session) continuing after the M0/M1 core.

---

## TL;DR

The **M0/M1 core tooling is built, tested, and committed.** What remains is
**entirely owner-driven** — your taste (style bible), your fal.ai account, and
your creative/market execution (Tasks 5–8). No agent can produce these; this
handoff tells the next agent exactly what to do *once you supply the inputs*,
and where the hard stop is.

**Do not re-derive the project — read the committed artifacts:**
- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- Implementation plan (M0/M1): `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`
- SDD progress ledger (source of truth): `.superpowers/sdd/progress.md`

---

## What is DONE (committed on `m0-foundation`)

| Commit | What |
|--------|------|
| `ad5c51a` | Task 1 — repo scaffold (pipeline/listings/reports skeleton, `.gitignore`, README). Reviewed clean. |
| `23a1d45` | Task 3 (non-secret) — `requirements.txt`, `config.example.toml`, `ruff.toml`. Reviewed clean. |
| `0ac8124` | Task 4 — generator-agnostic image producer (`tools/producer/`). TDD, 3/3 tests, ruff clean. Reviewed Approved. |
| `795c188` | Task 4 fix — `FAL_KEY` config override (resolves the one Important review finding). |
| `b6c53fa` | Task 2 (partial) — style-bible **format** + IP blocklist. Aesthetic files are OWNER-TODO skeletons. |
| `f328faf` | `verify-task-1.sh` — re-runnable scaffold check (out-of-plan helper, 15/15 pass). |

**The producer's public interface (stable — the future M2 `producer` skill wraps it):**
`GenRequest`, `Provider` protocol, `FluxFalProvider`, and `dated_output_dir` /
`save_batch` / `run` in `tools/producer/`. Invoke the CLI as a module:
`python -m tools.producer.generate --niche <slug> --prompt "..." --n 4`.

**Environment:** venv at `tools/producer/.venv` (Python 3.15; pytest 9.1.1,
ruff 0.17.1, fal-client installed). Run tests/lint from the repo root.

---

## What is BLOCKED on the owner (the real "outstanding" work)

### 1. Style bible aesthetic content — Task 2
`style-bible/vaporwave.md` and `psychedelia.md` are committed as skeletons with
the section headings locked (pre-QC parses them) and `OWNER-TODO` placeholders.
Sam must fill, for each: Palette (named colors + hex), Motifs use/avoid,
Composition, Mood words, and a Reference set (paths to 5–10 of Sam's A-grade
exemplars — **not** redistributed assets). Then the **owner approval gate**
(plan Task 2 Step 4). This is the studio's core edge and must not be
ghost-written.
→ *Agent action when notes arrive:* fill the two files to the locked format,
present for approval, commit. Then Task 2 is complete.

### 2. fal.ai account + API key — Task 3 Step 1 / Task 4 Step 6
External signup (Sam's credentials/payment). Put the key in
`tools/producer/config.toml` (copy `config.example.toml`). **config.toml is
gitignored — never commit it.**
→ *Agent action when key exists:* run the Step 6 network smoke test
(`python -m tools.producer.generate --niche battlestation --prompt "..." --n 2`),
confirm 2 PNGs land under `pipeline/02-raw/<today>/`, and **verify the fal.ai
call/response shape against current fal.ai docs first** (see deferred findings).

### 3. Tasks 5–8 — owner-driven creative/market work
Produce/finish the battlestation batch (5), list on Etsy — human publishes per
ToS (6), run the small stream-packs test (7), weekly go/no-go ritual (8). No
agent can do these. See the plan for the runbooks.

---

## Deferred findings to clear before/at the Step 6 smoke test

Carried from the Task 4 review (network code is not unit-tested by design):
- **(Minor)** `FluxFalProvider._submit` assumes `result["images"][i]["url"]`
  and arg keys `image_size` / `num_images`. Confirm against live fal.ai docs
  before the first real run — a mismatch surfaces as a `KeyError`.
- **(Minor)** No `try/except` around the network calls in `_submit`/`_download`;
  errors propagate as a raw traceback through `main()`. Tighten once the real
  response shape is confirmed.

---

## The hard stop: do NOT build M2 yet

M2 is the OpenClaw automation layer (brief-generator, pre-QC, producer skill,
packager, etc.). Per the spec's prove-before-automate principle and the plan's
**Task 8 gate**, M2 is **deliberately not built until a niche crosses "first
sales + repeat interest."** An OpenClaw agent "continuing" this project should
carry the owner-driven M1 tasks and hold — not start writing M2 skills — until
that gate is actually hit. When it is, that triggers a *new* M2 plan.

---

## Parked (non-blocking, spec §8)

Messaging channel (Telegram vs WhatsApp), exact Claude model IDs for M2 (pin via
the `claude-api` skill when M2 starts), and whether `~/Projects/ai/art-store`
relates to this project.

---

## Working-tree notes for whoever takes over

- Uncommitted, **not agent-authored** (owner's IDE / manual edits, left
  untouched): `.gitignore` (adds `.idea/`), `README.md` (`python` → `python3`).
  Decide whether to keep/commit these.
- `README.md` still shows `python generate.py …`; the tool actually needs
  `python -m tools.producer.generate …` (relative imports). Worth correcting.
- Final whole-branch review + `finishing-a-development-branch` were
  intentionally **deferred** until Task 2's aesthetic content is committed and
  the Step 6 smoke test passes — i.e. until the branch is genuinely complete.

## Secrets

No secrets in the repo. `tools/producer/config.toml` (holds the fal.ai key) is
gitignored and not yet created. Never commit it.
