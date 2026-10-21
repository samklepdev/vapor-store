# vapor-studio — operating workflow & M1 manual runbook

**Purpose:** the end-to-end operating loop, what's built vs. deferred, the
**M1 manual runbook** to run it by hand now, and the **trigger** that starts the
OpenClaw (M2) automation handoff. Source of truth for stages/gates is the design
spec (`docs/specs/2026-10-20-vapor-studio-design.md` §2–§3, §6–§7).

---

## The daily operating loop (what OpenClaw will eventually run)

Each row is a pipeline stage. **🚪 = a human gate that fails closed** — no
approval → nothing publishes, nothing sends. OpenClaw never auto-publishes and
never auto-messages a buyer.

| # | Stage | Who | OpenClaw skill (M2, deferred) | Folder |
|---|-------|-----|------------------------------|--------|
| 1 | **Research** (nightly) — browse trends/competitors, Claude finds gaps → morning digest | machine | `niche-research` | `reports/` |
| 2 | **Brief** — owner picks a direction (or standing theme list); Claude expands to N prompts obeying the style bible + IP blocklist | machine | `brief-generator` | `pipeline/01-briefs/` |
| 3 | **Produce** — fire prompts at the generator, file raw drafts | machine | **`producer`** (built — see below) | `pipeline/02-raw/<date>/` |
| 4 | **Pre-QC** — Claude vision-scores drafts vs. the style bible, auto-kills failures, flags possible IP, builds a contact sheet | machine | `pre-qc` | `pipeline/03-contact-sheets/` |
| 5 | **🚪 Gate 1 — Curate & finish** — approve keepers; hand-finish in the owner's own design tools *(primary time investment; the edge lives here)* | **owner** | — | `pipeline/04-approved/` |
| 6 | **Package** — SEO title/desc/tags, deliverable files at correct dimensions, mockups | machine | `packager` | `pipeline/05-packaged/` |
| 7 | **🚪 Gate 2 — Publish** — OpenClaw preps the Etsy listing as a *draft*; owner reviews and submits (human publish = ToS-clean) | **owner** | `listing-drafter` | `listings/` |
| 8 | **Support** — buyer message → drafted reply | machine | `inbox-handler` | — |
| 9 | **🚪 Gate 3 — Approve/send** — revisions stay human | **owner** | — | — |
| 10 | **Report** (nightly) — views/favorites/sales per listing → feeds tomorrow's research | machine | `reporter` | `reports/` |

**Recurring owner calls:** *weekly* kill/double-down (read the report, fuel
winners, kill the flat); *ongoing* licensing + "is this actually good" judgment
the machine must never make alone. Target rhythm once automated: **~15–40
focused min/day at the gates.**

---

## What's built now vs. deferred

**Built (M0):**
- **`producer`** (stage 3) — `tools/producer/`, a generator-agnostic CLI.
  Backends: **local ComfyUI/SDXL** (free, resale-clean — proven working) and
  **fal.ai/Flux** (paid fallback). Selected via `config.toml` `[provider].kind`.
- **Style bible** (`style-bible/`) — the taste codified; the reference stages 2
  and 4 score against. Aesthetics approved; reference-set images still owner-TODO.
- **IP blocklist** (`style-bible/ip-blocklist.md`) and the **folder pipeline**.

**Deferred to M2 (do NOT build yet):** every OpenClaw skill in the table above,
the nightly loop, and the messaging channel. See the hard stop below.

---

## M1 manual runbook (run the loop by hand — now)

The goal of M1 is **market signal, not efficiency**: get ~10–15 battlestation
listings + 2–3 stream packs live and gather real view/favorite/sale data. Run
each loop by hand:

1. **Theme** — pick a battlestation direction (the proven-first niche).
2. **Prompts** — write N prompts from `style-bible/vaporwave.md` (palette, use
   motifs) respecting `ip-blocklist.md`. *(Claude can draft these on request.)*
3. **Produce** — ensure ComfyUI is running + `config.toml` → `kind = "comfyui"`, then:
   ```
   source tools/producer/.venv/bin/activate
   python -m tools.producer.generate --niche <slug> --prompt "..." --n 4
   ```
   Raw files land in `pipeline/02-raw/<date>/`. (Use a distinct `--niche` slug per
   prompt so files don't overwrite within a day.)
4. **Manual pre-QC (🚪 Gate 1)** — eyeball the raw output against the style bible;
   keep only ≥2-on-all-four; copy keepers to `pipeline/04-approved/`.
5. **Finish** — hand-finish keepers in your own design tools (this is the edge).
6. **Package** — export deliverables at correct dimensions + make mockups →
   `pipeline/05-packaged/`; write the SEO title/description/tags.
7. **Publish (🚪 Gate 2)** — create the Etsy listing yourself, with the honest AI
   disclosure ("made with AI tools, designed and curated by Sam"). Human publish.
8. **Record** — note the listing + status in `listings/`.
9. **Weekly** — read views/favorites/sales; kill the flat, fuel the winner.

Guardrails apply the whole time: original-assets-only, honest AI disclosure,
one shop built slowly, human on every outward action (`docs/specs/...` §4).

---

## The OpenClaw (M2) handoff — trigger, not a date

**Hard stop:** per prove-before-automate (spec §6) and the Task 8 gate, the
OpenClaw automation is **built only after a niche crosses "first sales + repeat
interest"** (typically 3–4+ weeks of M1). Building the nightly loop for a niche
nobody has bought from is the exact saturation/wasted-effort trap the plan avoids.

**When that signal hits, M2 is:**
1. Stand up self-hosted OpenClaw + one messaging channel (Telegram/WhatsApp — spec §8 open item).
2. Pin exact Claude model IDs/cost tiers (verify via the `claude-api` skill, not memory).
3. Build the deferred skills in the loop table **for that one proven niche** — each
   a focused unit with a clean input→output (spec §5).
4. The **`producer` skill wraps the existing tool interface** (`GenRequest` /
   `Provider` / `run` in `tools/producer/`) — kept stable for exactly this. The
   ComfyUI backend in use now carries straight over.

M2 is "done" when a day's listings go research → draft-ready with only gate time.
Then M3 adds more niches on the shared engine + the signature LoRA + owned store.

---

## References
- Design spec: `docs/specs/2026-10-20-vapor-studio-design.md`
- M0/M1 plan: `docs/plans/2026-10-20-vapor-studio-m0-m1-foundation.md`
- Local provider: `docs/specs/2026-10-21-comfyui-local-provider-design.md`
- OpenClaw continuation handoff: `docs/handoffs/2026-10-21-openclaw-continuation.md`
