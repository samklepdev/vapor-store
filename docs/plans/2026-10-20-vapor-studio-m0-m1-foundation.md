# vapor-studio — M0/M1 Foundation & Manual Proof Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Scope note:** This plan covers **M0 (Foundation)** and **M1 (Manual proof)** only. M2 (the OpenClaw automation skills) is deliberately deferred until a niche crosses "first sales + repeat interest," per the prove-before-automate principle in the spec. Tasks 1–4 are agent-executable code/setup. Tasks 5–8 are **owner-driven creative/market work** — no agent can do them; they are structured runbooks with concrete deliverables and checks.

**Goal:** Stand up the vapor-studio repo and a minimal, reproducible image-generation tool, then run a by-hand market test of two niches on Etsy to find what sells.

**Architecture:** A local Python CLI (`tools/producer`) turns prompt batches into images via a generator-agnostic provider interface (Flux on fal.ai first), writing raw output into dated pipeline folders. Everything else in M0/M1 is operational: a codified style bible, a provider account, and manual production + listing of test designs whose market signal decides what we automate next.

**Tech Stack:** Python 3.11+, `fal-client` (fal.ai Flux access), `pytest` for the producer's tested core, `ruff` for lint. Markdown for the style bible and briefs. Etsy (manual listing during M1).

## Global Constraints

- **Region/infra:** none — this is a local project on the owner's Mac; no AWS/cloud resources are provisioned in M0/M1.
- **Original-assets-only:** every generated piece must *evoke* the aesthetic, never reuse protected material. No brand logos, no anime stills/characters, no celebrity likenesses or identifiable real busts, no sampled ad imagery, no named band/artist references, no copyrighted typefaces in the art. (Copied from spec §4.1.)
- **Etsy AI disclosure:** every listing discloses "made with AI tools, designed and curated by Sam"; the human hand-finishes and publishes. (Spec §4.2.)
- **Human-in-the-loop on all outward actions:** no auto-publishing, no auto-messaging buyers, no bulk favorite/follow, no bot ordering. (Spec §4.3.)
- **One shop, steady cadence:** no multi-account, no overnight bulk dumps. (Spec §4.4.)
- **Generator-agnostic:** the producer hides the generator behind one interface so Flux/Ideogram/local can be swapped without touching callers. (Spec §5.)
- **Python style:** 3.11+, type hints on public functions, `ruff` clean, `pytest` for the tested core.

---

## File Structure

Created in M0:

```
vapor-studio/
  .gitignore
  README.md
  style-bible/
    README.md            # the style-bible format (what pre-QC will score against)
    vaporwave.md         # owner's codified taste: palettes, motifs, do/don't
    psychedelia.md
    ip-blocklist.md      # the original-assets-only rules, concrete
  niches/
    battlestation/briefs.md
    stream-packs/briefs.md
  tools/
    producer/
      __init__.py
      providers.py       # Provider protocol + FluxFalProvider
      generate.py        # dated-folder orchestration + CLI
      config.example.toml
      tests/
        __init__.py
        test_generate.py # TDD core: folder + filename + routing logic
      requirements.txt
      ruff.toml
  pipeline/
    01-briefs/{.gitkeep}
    02-raw/{.gitkeep}
    03-contact-sheets/{.gitkeep}
    04-approved/{.gitkeep}
    05-packaged/{.gitkeep}
  listings/{.gitkeep}
  reports/{.gitkeep}
  docs/
    specs/2026-10-20-vapor-studio-design.md   # already committed
    plans/2026-10-20-vapor-studio-m0-m1-foundation.md  # this file
```

---

### Task 1: Scaffold the repo

**Files:**
- Create: `.gitignore`, `README.md`, and the empty pipeline/listings/reports folders with `.gitkeep`.

**Interfaces:**
- Consumes: nothing (repo already `git init`'d with the spec committed).
- Produces: the directory skeleton all later tasks write into.

- [ ] **Step 1: Create the folder skeleton and .gitkeep files**

```bash
cd /Users/sam/Projects/ai/vapor-studio
mkdir -p style-bible niches/battlestation niches/stream-packs \
  tools/producer/tests \
  pipeline/01-briefs pipeline/02-raw pipeline/03-contact-sheets \
  pipeline/04-approved pipeline/05-packaged listings reports
for d in pipeline/01-briefs pipeline/02-raw pipeline/03-contact-sheets \
         pipeline/04-approved pipeline/05-packaged listings reports; do
  touch "$d/.gitkeep"
done
```

- [ ] **Step 2: Write `.gitignore`**

```gitignore
# secrets & config
tools/producer/config.toml
.env
*.key

# generated image output (keep folder structure via .gitkeep, ignore contents)
pipeline/02-raw/*
!pipeline/02-raw/.gitkeep
pipeline/05-packaged/*
!pipeline/05-packaged/.gitkeep

# python
__pycache__/
*.pyc
.venv/
.pytest_cache/
.ruff_cache/

# macOS
.DS_Store
```

- [ ] **Step 3: Write `README.md`**

```markdown
# vapor-studio

Human-in-the-loop digital-goods studio for vaporwave / psychedelia downloads.
OpenClaw runs the pipeline; the owner supplies taste at three approval gates.

- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- Current plan: `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`

## Status: M0/M1 — foundation + manual proof (no automation yet)

## Image generation (local tool)

    cd tools/producer
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp config.example.toml config.toml   # add your fal.ai key
    python generate.py --niche battlestation --prompt "..." --n 4
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: scaffold vapor-studio repo skeleton

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Codify the style bible (owner-driven, with template)

**Files:**
- Create: `style-bible/README.md`, `style-bible/vaporwave.md`, `style-bible/psychedelia.md`, `style-bible/ip-blocklist.md`

**Interfaces:**
- Consumes: the owner's taste (only the owner can fill the aesthetic content).
- Produces: the scoring fields that the future `pre-qc` skill (M2) and every brief will reference. This locks the format now so M2 doesn't have to reinvent it.

> **Nature of this task:** the *format* below is prescriptive; the *aesthetic content* must be written/approved by the owner — it is the core edge and cannot be ghost-filled. The agent may draft starting content from the owner's notes, but the owner approves it.

- [ ] **Step 1: Write `style-bible/README.md` (the format spec)**

```markdown
# Style Bible format

Each aesthetic file (`vaporwave.md`, `psychedelia.md`) uses these sections.
These sections ARE the fields pre-QC will score a draft against (0–3 each),
and briefs must reference them.

## Palette
Named colors + hex, and forbidden colors.

## Motifs — use
Concrete recurring elements that belong (e.g. chrome grids, sunset gradients).

## Motifs — avoid
Clichés that read as lazy/generic in this style.

## Composition
Layout rules: focal point, negative space, symmetry, grain/texture.

## Mood words
5–10 adjectives the piece must feel like.

## Reference set
Links/paths to 5–10 exemplars the owner considers "A-grade" (local files, not
redistributed assets).

## Pre-QC scoring rubric
For each of Palette / Motifs / Composition / Mood: 0 = off, 1 = weak,
2 = good, 3 = signature. A draft needs >= 2 on all four to reach the contact sheet.
```

- [ ] **Step 2: Draft `vaporwave.md` and `psychedelia.md` from the owner's notes**

Fill every section from Step 1 with the owner's actual taste. Keep the headings
exact (pre-QC parses them later). Do not invent reference exemplars — the owner
supplies them.

- [ ] **Step 3: Write `ip-blocklist.md` (concrete, enforceable)**

```markdown
# IP blocklist — original-assets-only

Hard "never generate / never ship" list. Applied by brief-generator (M2) and
checked by the owner at Gate 1.

- No brand logos or trade dress (Windows/Mac UI, Pepsi, Nike, Sega, etc.)
- No anime stills, frames, or recognizable characters
- No celebrity likenesses; no identifiable real sculptures/busts of real people
- No sampled advertising imagery or scanned magazine art
- No "[named band / album / living artist]" references in prompts or titles
- No copyrighted typefaces rendered into the art
- Greek/Roman statue motifs: only generic, non-identifiable, generated forms

When in doubt, it's out — regenerate rather than ship.
```

- [ ] **Step 4: Owner review gate**

The owner reads all three files and confirms they match their taste and intent.
This is a human checkpoint, not a command.

- [ ] **Step 5: Commit**

```bash
git add style-bible/
git commit -m "docs: add style bible format, aesthetics, and IP blocklist

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Set up generator access (fal.ai + Flux)

**Files:**
- Create: `tools/producer/config.example.toml`, `tools/producer/requirements.txt`, `tools/producer/ruff.toml`

**Interfaces:**
- Consumes: a fal.ai account + API key (owner creates the account; this is an external signup).
- Produces: the `[fal]` config shape and dependency pins the producer code (Task 4) reads.

> **Note:** fal.ai chosen as the default Flux host (simple API, pay-per-image). It is swappable per the generator-agnostic constraint — a Replicate provider can be added later without changing callers.

- [ ] **Step 1: Owner creates a fal.ai account and API key**

Sign up at fal.ai, create an API key, note it. (External action — not scriptable.)

- [ ] **Step 2: Write `requirements.txt`**

```
fal-client>=0.5
pytest>=8
ruff>=0.6
```

- [ ] **Step 3: Write `config.example.toml`**

```toml
[fal]
# Copy this file to config.toml and paste your key. config.toml is gitignored.
api_key = "PASTE_FAL_KEY_HERE"
model = "fal-ai/flux/dev"
```

- [ ] **Step 4: Write `ruff.toml`**

```toml
line-length = 100
target-version = "py311"
[lint]
select = ["E", "F", "I", "UP"]
```

- [ ] **Step 5: Create venv, install, verify**

```bash
cd /Users/sam/Projects/ai/vapor-studio/tools/producer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -c "import fal_client; print('fal-client ok')"
```
Expected: `fal-client ok`

- [ ] **Step 6: Commit**

```bash
git add tools/producer/requirements.txt tools/producer/config.example.toml tools/producer/ruff.toml
git commit -m "chore: add producer deps and fal.ai config template

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Build the producer (generator-agnostic image CLI)

**Files:**
- Create: `tools/producer/__init__.py`, `tools/producer/providers.py`, `tools/producer/generate.py`, `tools/producer/tests/__init__.py`, `tools/producer/tests/test_generate.py`

**Interfaces:**
- Consumes: `[fal]` config from Task 3.
- Produces:
  - `GenRequest(prompt: str, width: int = 1024, height: int = 1024, n: int = 1, slug: str = "img")`
  - `Provider` protocol with `generate(self, req: GenRequest) -> list[bytes]`
  - `FluxFalProvider(api_key: str, model: str)` implementing `Provider`
  - `dated_output_dir(base: Path, today: date | None = None) -> Path`
  - `save_batch(images: list[bytes], out_dir: Path, slug: str) -> list[Path]`
  - `run(provider: Provider, req: GenRequest, raw_base: Path, today=None) -> list[Path]`
  - These names/types are what the M2 `producer` skill will wrap — keep them stable.

- [ ] **Step 1: Write `providers.py` (protocol + real provider)**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class GenRequest:
    prompt: str
    width: int = 1024
    height: int = 1024
    n: int = 1
    slug: str = "img"


@runtime_checkable
class Provider(Protocol):
    name: str

    def generate(self, req: GenRequest) -> list[bytes]:
        """Return `req.n` images as raw PNG bytes."""
        ...


class FluxFalProvider:
    """Flux via fal.ai. The network call is isolated in `_submit`/`_download`
    so the orchestration in generate.py can be tested with a fake provider.

    NOTE: confirm the exact fal-client call and response shape against current
    fal.ai docs during execution (network code, not unit-tested here)."""

    name = "flux-fal"

    def __init__(self, api_key: str, model: str = "fal-ai/flux/dev") -> None:
        self._api_key = api_key
        self._model = model

    def generate(self, req: GenRequest) -> list[bytes]:
        urls = self._submit(req)
        return [self._download(u) for u in urls]

    def _submit(self, req: GenRequest) -> list[str]:
        import os

        import fal_client

        os.environ.setdefault("FAL_KEY", self._api_key)
        result = fal_client.subscribe(
            self._model,
            arguments={
                "prompt": req.prompt,
                "image_size": {"width": req.width, "height": req.height},
                "num_images": req.n,
            },
        )
        return [img["url"] for img in result["images"]]

    def _download(self, url: str) -> bytes:
        import urllib.request

        with urllib.request.urlopen(url) as resp:  # noqa: S310 (trusted fal URL)
            return resp.read()
```

- [ ] **Step 2: Write the failing test `tests/test_generate.py`**

```python
import datetime as dt
from pathlib import Path

from tools.producer.generate import dated_output_dir, run, save_batch
from tools.producer.providers import GenRequest, Provider


class FakeProvider:
    name = "fake"

    def __init__(self, blobs: list[bytes]) -> None:
        self._blobs = blobs
        self.seen: GenRequest | None = None

    def generate(self, req: GenRequest) -> list[bytes]:
        self.seen = req
        return self._blobs


def test_dated_output_dir_uses_iso_date(tmp_path: Path):
    d = dated_output_dir(tmp_path, today=dt.date(2026, 10, 20))
    assert d == tmp_path / "2026-10-20"


def test_save_batch_writes_padded_png_files(tmp_path: Path):
    paths = save_batch([b"a", b"b"], tmp_path, slug="battlestation")
    assert [p.name for p in paths] == ["battlestation-001.png", "battlestation-002.png"]
    assert (tmp_path / "battlestation-001.png").read_bytes() == b"a"


def test_run_calls_provider_and_writes_to_dated_dir(tmp_path: Path):
    prov: Provider = FakeProvider([b"x", b"y", b"z"])
    req = GenRequest(prompt="chrome grid sunset", n=3, slug="bs")
    paths = run(prov, req, raw_base=tmp_path, today=dt.date(2026, 10, 20))
    assert len(paths) == 3
    assert all(p.parent == tmp_path / "2026-10-20" for p in paths)
    assert prov.seen is req
```

- [ ] **Step 3: Run the test to verify it fails**

Run:
```bash
cd /Users/sam/Projects/ai/vapor-studio && source tools/producer/.venv/bin/activate
python -m pytest tools/producer/tests/test_generate.py -v
```
Expected: FAIL with `ModuleNotFoundError` / `ImportError: cannot import name 'run' from 'tools.producer.generate'`.

- [ ] **Step 4: Write `generate.py` (orchestration + CLI) and empty `__init__.py` files**

Create empty `tools/producer/__init__.py` and `tools/producer/tests/__init__.py`, then:

```python
from __future__ import annotations

import argparse
import datetime as dt
import tomllib
from pathlib import Path

from .providers import FluxFalProvider, GenRequest, Provider


def dated_output_dir(base: Path, today: dt.date | None = None) -> Path:
    return base / (today or dt.date.today()).isoformat()


def save_batch(images: list[bytes], out_dir: Path, slug: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, data in enumerate(images, start=1):
        p = out_dir / f"{slug}-{i:03d}.png"
        p.write_bytes(data)
        paths.append(p)
    return paths


def run(
    provider: Provider,
    req: GenRequest,
    raw_base: Path,
    today: dt.date | None = None,
) -> list[Path]:
    images = provider.generate(req)
    return save_batch(images, dated_output_dir(raw_base, today), req.slug)


def _load_fal(config_path: Path) -> FluxFalProvider:
    cfg = tomllib.loads(config_path.read_text())["fal"]
    return FluxFalProvider(api_key=cfg["api_key"], model=cfg.get("model", "fal-ai/flux/dev"))


def main() -> None:
    ap = argparse.ArgumentParser(description="vapor-studio image producer")
    ap.add_argument("--niche", required=True, help="slug, e.g. battlestation")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--config", default="tools/producer/config.toml")
    ap.add_argument("--raw-base", default="pipeline/02-raw")
    args = ap.parse_args()

    provider = _load_fal(Path(args.config))
    req = GenRequest(
        prompt=args.prompt, width=args.width, height=args.height, n=args.n, slug=args.niche
    )
    paths = run(provider, req, raw_base=Path(args.raw_base))
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass + lint**

Run:
```bash
cd /Users/sam/Projects/ai/vapor-studio && source tools/producer/.venv/bin/activate
python -m pytest tools/producer/tests/test_generate.py -v
ruff check tools/producer --config tools/producer/ruff.toml
```
Expected: 3 passed; ruff reports no errors.

- [ ] **Step 6: Smoke-test the real generator once (network)**

Only after `config.toml` has a real key. Confirm the fal call/response shape
against current fal.ai docs first (see note in `providers.py`), then:
```bash
python -m tools.producer.generate --niche battlestation \
  --prompt "retro-futurist chrome grid, sunset gradient, 1080x1080, original art" --n 2
```
Expected: two PNG paths printed under `pipeline/02-raw/<today>/`; open them to confirm they look right. If the response shape differs, fix `_submit` and re-run.

- [ ] **Step 7: Commit**

```bash
git add tools/producer/__init__.py tools/producer/providers.py tools/producer/generate.py \
  tools/producer/tests/
git commit -m "feat: add generator-agnostic image producer (Flux via fal.ai)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Produce the battlestation test batch (owner-driven)

> **Not agent-executable.** This is the owner's curation + finishing work — the core edge. Checklist, not code.

**Deliverable:** 10–15 finished, listing-ready battlestation wall-art designs.

- [ ] Write 10–15 prompt lines into `niches/battlestation/briefs.md`, each referencing style-bible sections and obeying `ip-blocklist.md`.
- [ ] Run the producer per prompt to fill `pipeline/02-raw/<date>/`.
- [ ] Manually curate: move keepers to `pipeline/04-approved/`. Apply the >= 2-on-all-four rubric from the style bible by eye.
- [ ] Hand-finish keepers in your own design tools (crop, color, upscale to print resolutions: 2:3, 3:4, 4:5, 11:14, ISO/A-series — a standard printable bundle).
- [ ] Export deliverables (high-res PNG/PDF bundle) into `pipeline/05-packaged/<listing-slug>/`.
- [ ] **Checkpoint:** every packaged design passes the IP blocklist on a human re-read.

---

### Task 6: List the battlestation batch on Etsy + instrument tracking (owner-driven)

> **Not agent-executable** (and must not be automated — Etsy ToS: human publishes). Checklist.

**Deliverable:** 10–15 live Etsy listings + a tracking sheet.

- [ ] Write title/description/13 tags per listing (SEO-minded). Include the AI-disclosure line from the Global Constraints.
- [ ] Generate mockups (in-situ framed-on-wall renders) for each.
- [ ] Publish each listing **manually**.
- [ ] Record each in `listings/battlestation.md`: slug, publish date, price, listing URL.
- [ ] Create `reports/tracking.md` with a row per listing to log weekly views / favorites / sales.

---

### Task 7: Run the stream-packs small test (owner-driven)

> **Not agent-executable.** Checklist. Kept small on purpose (higher production cost).

**Deliverable:** 2–3 stream-asset packs listed on Etsy.

- [ ] Write prompts into `niches/stream-packs/briefs.md` for overlay/panel/alert art (vaporwave/synthwave/psych). Add any text by hand in your design tools for this test (defer the Ideogram provider until a text-heavy product proves worth it — YAGNI).
- [ ] Produce, curate, finish, and assemble 2–3 packs (correct stream dimensions) into `pipeline/05-packaged/`.
- [ ] List manually; record in `listings/stream-packs.md` and add rows to `reports/tracking.md`.

---

### Task 8: Weekly review ritual + go/no-go gate (owner-driven)

> **Not agent-executable.** The decision that triggers (or cancels) the M2 automation plan.

**Deliverable:** a weekly decision logged in `reports/`, and after ~3 weeks a go/no-go.

- [ ] Each week, fill the view/favorite/sale numbers in `reports/tracking.md`.
- [ ] Apply the spec §6 signal table: flat views+favorites after 3 wks → deprioritize; favorites but no sales → fix price/mockups/bundle; **first sales + repeat views → winner.**
- [ ] After ~3 weeks, write a one-paragraph go/no-go in `reports/go-no-go.md` naming the winning niche (if any).
- [ ] **Gate:** only if a niche hits "first sales + repeat interest" do we commission the **M2 automation plan**, scoped to that niche. If nothing lands, iterate aesthetics/niches in M1 — do **not** build automation.

---

## Self-Review

**Spec coverage:**
- §2 pipeline folders → Task 1. §3 human/machine split → encoded as the owner-driven Tasks 5–8 + the fail-closed manual listing. §4 guardrails → Global Constraints + Task 2 (`ip-blocklist.md`) + Tasks 5–7 checkpoints. §5 generator-agnostic producer → Task 4 (`Provider` protocol); Ideogram explicitly deferred (YAGNI, Task 7). §6 validation plan → Tasks 5–8. §7 M0/M1 milestones → Tasks 1–8; **M2/M3 intentionally out of scope** (deferred until the Task 8 gate). §8 open items: generator host resolved (fal.ai, Task 3); messaging channel + Claude model IDs correctly NOT resolved (not needed until M2); `art-store` relation still open (does not block M0/M1).
- **Gap check:** no spec requirement for M0/M1 is unassigned. M2 skills are a deliberate deferral, not a gap.

**Placeholder scan:** The producer's tested core (Task 4 Steps 1–5) is fully specified with real code and real tests. The single network-dependent piece (`FluxFalProvider._submit` response shape) carries an explicit "confirm against fal.ai docs during execution" step rather than a fake unit test — honest, since the exact fal response shape should be verified live, not guessed. No "TBD"/"handle edge cases"/"similar to Task N" placeholders.

**Type consistency:** `GenRequest`, `Provider.generate -> list[bytes]`, `dated_output_dir`, `save_batch`, `run` names/signatures match between `providers.py`, `generate.py`, and `test_generate.py`. `run` takes `req.slug` for the filename (no separate slug arg) consistently.

---

## Execution Handoff

Tasks 1–4 are agent-executable (scaffold + the tested producer). Tasks 5–8 are **yours** — the creative/market work no agent can or should do.
