# vapor-studio — Design Spec

**Date:** 2026-10-20
**Status:** Approved design, pre-implementation
**Owner:** Sam

---

## 1. Summary

`vapor-studio` is a **human-in-the-loop digital-goods studio**: a self-hosted
[OpenClaw](https://openclaw.ai/) assistant runs a continuous pipeline that
researches, generates, pre-filters, packages, and prepares listings for
**vaporwave / psychedelia digital downloads**, while the human owner supplies
taste at three approval gates. Claude (inside OpenClaw) is the reasoning/writing
brain; a hosted image generator supplies raw material; the owner curates,
finishes, and publishes.

The automation does everything that **scales**; the human does only what requires
**taste or a human's name on it**.

### Context & constraints

- **Product:** digital downloads (no shipping, no physical fulfillment).
- **Goal tier:** serious / replace-income ambition ($5k+/mo), several hrs/day
  available. Realistically many months out — the automation makes months 3–12
  tractable, not month one.
- **Owner's edge:** expert taste in **vaporwave and psychedelia**. Taste — not
  volume — is the moat in a saturated market.
- **Orchestrator:** OpenClaw (open-source, self-hosted, 29 messaging channels,
  persistent memory, browsing/email/shell, community skills system). Verified real.
- **Strategy arc:** start with **"Curated studio" (A)**, evolve the proven winner
  toward a **brand-led signature line (C)**. The high-volume semi-auto approach (B)
  is explicitly rejected as the saturation trap.

---

## 2. System architecture & pipeline

OpenClaw runs a continuous loop locally and reaches the owner through one
messaging channel (Telegram or WhatsApp — TBD at setup). The loop:

1. **Research (nightly)** — OpenClaw browses trends/competitors in the active
   niche; Claude summarizes gaps → a short morning digest to the owner's phone.
2. **Brief** — owner (or a standing theme list) picks a direction; Claude expands
   it into N structured prompts that obey the style bible and IP blocklist.
3. **Produce** — OpenClaw fires prompts at the generator; raw drafts land in a
   dated folder.
4. **Pre-QC** — Claude (vision) scores drafts against the style bible, auto-kills
   obvious failures, flags possible IP, assembles a contact sheet of survivors.
5. **🚪 Gate 1 — Curate & finish (human)** — approve keepers; hand-finish in the
   owner's own design tools.
6. **Package** — Claude writes SEO title/description/tags; OpenClaw builds
   deliverable files at correct dimensions + generates mockups from templates.
7. **🚪 Gate 2 — Publish (human)** — OpenClaw preps the Etsy listing as a *draft*;
   owner reviews and submits. Human publishes = ToS-clean.
8. **Support** — buyer message arrives → OpenClaw drafts a reply.
9. **🚪 Gate 3 — Approve/send (human)** — revisions stay human.
10. **Report (nightly)** — OpenClaw compiles views/favorites/sales per listing &
    niche → feeds tomorrow's research and the weekly kill/double-down call.

**Every gate fails closed:** no approval → nothing publishes, nothing sends.
OpenClaw never auto-publishes and never auto-messages a buyer. This is both the
taste filter and the ToS insurance.

### On-disk layout (all local, inside the project)

```
/Users/sam/Projects/ai/vapor-studio/
  style-bible/           # owner's taste codified: palettes, motifs, rules, refs
  niches/{battlestation, stream-packs, cover-kits}/
  pipeline/
    01-briefs/
    02-raw/<date>/       # generator output
    03-contact-sheets/
    04-approved/
    05-packaged/         # final deliverables + mockups
  listings/              # copy + status per listing
  reports/               # nightly digests, metrics
  skills/                # the OpenClaw skills we build
  docs/specs/            # this spec and future design docs
```

---

## 3. Who does what (human vs. machine)

### Machine (autonomous, no approval needed)
- Nightly niche/competitor research → morning digest
- Expanding themes into prompt batches (style-bible-aware, IP-blocklist applied)
- Firing prompts at the generator, filing raw output
- Pre-QC: vision-scoring, auto-killing failures, building contact sheets
- Writing SEO titles/descriptions/tags
- Packaging deliverable files + generating mockups
- Preparing Etsy listing *drafts*
- Drafting buyer replies
- Nightly metrics reports

### Human (owner) — three daily gates + two recurring calls
- **Gate 1 — Curate & finish:** approve contact-sheet keepers; hand-finish.
  *(Primary time investment — this is where the edge lives.)*
- **Gate 2 — Publish:** review prepared listing, submit.
- **Gate 3 — Buyer replies:** approve/send drafted messages; handle revisions.
- **Weekly — Kill/double-down:** read the report, decide which niche/designs get
  more fuel.
- **Ongoing — Licensing/taste calls:** the IP and "is this actually good"
  judgment the machine must never make alone.

**Target rhythm:** ~15–40 focused minutes/day at the gates, with larger creative
blocks going into finishing winners and steering the aesthetic.

---

## 4. Guardrails (ToS + copyright)

Baked into the pipeline as hard checks, not afterthoughts.

1. **Original-assets-only.** Every piece is generated from scratch to *evoke* the
   aesthetic — never built on protected material. The `brief-generator` and
   `pre-qc` skills enforce a blocklist: no recognizable brand logos, no anime
   stills/characters, no celebrity likenesses or identifiable real busts, no
   sampled ad imagery, no named band/artist references, no copyrighted typefaces
   in the art. Pre-QC flags anything IP-adjacent for Gate 1 review.
2. **Etsy AI-content compliance.** AI-assisted work is allowed if disclosed and
   genuinely the owner's (designed/curated/finished by a human). The
   `listing-drafter` adds the proper production-partner / "made with AI tools,
   designed and curated by Sam" disclosure; hand-finishing + human publish clears
   the "human maker" bar honestly.
3. **Human-in-the-loop on all outward actions.** No bot behavior: no
   auto-messaging buyers, no scripted listing spam, no bulk favorite/follow, no
   bot ordering. OpenClaw drafts; the human sends.
4. **One shop, built slowly.** No multi-account schemes, no overnight dumps of
   hundreds of listings. Steady, curated cadence. An owned storefront in the
   C-phase is additive, never an evasion tactic.

**Judgment call:** "evokes the aesthetic" vs. "too close to a specific work" is a
spectrum the machine will get wrong at the edges — hence the Gate 1 IP sniff and
deliberately over-flagging pre-QC. Better to waste 5 seconds than ship risk.

---

## 5. Tooling

### Image generator — Flux (hosted API) + Ideogram for text

- **Flux via a hosted API (fal.ai or Replicate)** is the primary generator:
  real API (automatable), top-tier quality for this aesthetic, cents per image,
  no local GPU required, and supports training a **custom LoRA on the owner's
  curated style** — the signature-look moat for the C-phase.
- **Midjourney is explicitly rejected** for automation: best vibe, but no
  legitimate API — automating it requires ToS-breaking unofficial bots.
- **Ideogram API** is the secondary generator, routed to for text-heavy products
  (stream-panel labels, quote art) where readable typography matters.
- The `producer` skill is **generator-agnostic** (one clean interface), so Flux /
  Ideogram / local ComfyUI can be swapped underneath without touching the rest of
  the pipeline. The generator choice is fully reversible.

### OpenClaw skills (each a focused unit: clear job, clean input→output)

| Skill | Does | In → Out |
|---|---|---|
| `niche-research` | nightly browse + gap analysis | niche config → morning digest |
| `brief-generator` | theme → prompt batch (style-bible-aware, IP-blocklist) | theme → prompts |
| `producer` | generator-agnostic image gen | prompts → raw files in `02-raw/<date>` |
| `pre-qc` | vision-score vs. style bible, kill failures, flag IP | raw files → contact sheet |
| `packager` | SEO copy + deliverable files + mockups | approved art → `05-packaged` |
| `listing-drafter` | Etsy draft + AI disclosure | packaged → listing draft |
| `inbox-handler` | draft buyer replies | buyer msg → draft reply |
| `reporter` | metrics digest, kill/double-down inputs | Etsy stats → nightly report |

### The brain

Claude inside OpenClaw does the reasoning/writing: a high-capability model for
taste-sensitive jobs (pre-QC vision scoring, listing copy), a cheaper/faster model
for routine drafting. **Exact model IDs and pricing to be pinned in the
implementation plan** (verified against current Claude API facts at that time,
not guessed now).

---

## 6. Validation plan (prove-before-automate)

The automation is **not** built first. A niche is proven by hand using a minimal
pipeline; only a proven niche gets automated.

### Niches (one shared aesthetic engine, staggered proof)

- **#2 Battlestation wall art** — printable art for aesthetic PC setups / home
  studios / dorms. Fastest, cheapest loop → fastest market signal. Proven first.
- **#1 Stream / gaming asset packs** — Twitch overlays/panels/alerts in
  vaporwave/synthwave/psych styles. Higher-ceiling "buyers actually pay" bet;
  heavier production, so tested small in parallel.
- **#3 Musician cover-art kits** — editable cover/canvas/thumbnail template packs.
  Held until #1 shows life (shared production); closest to the custom C-phase.

### Phases

- **Phase 0 — Setup (days):** style bible, messaging channel, Flux + Ideogram API
  keys. Folders + generator only, no automation.
- **Phase 1 — Manual proof (≈ weeks 1–3):** ~10–15 hand-finished battlestation
  listings + 2–3 stream packs live on Etsy; gates run manually. Purpose is market
  feel, not efficiency.

### Signals & how to read them

| Signal | Timeframe | Means |
|---|---|---|
| Listing views / impressions | ~1–3 wks (Etsy indexes new listings slowly) | Is anyone finding it? Low → SEO/demand problem |
| Favorites but no sales | 2–3 wks | Appealing but friction — price, mockups, or bundle wrong |
| First sales + repeat views on a theme | 3–4+ wks | Winner — double down |
| Flat views *and* favorites | 3 wks | Deprioritize; wrong niche or aesthetic-market fit |

Weekly: read the report → kill the flat, fuel the winner. Only once a niche
crosses **first sales + repeat interest** do we build its full OpenClaw automation.

**Expectation-setting:** first sales commonly take 2–6 weeks; the $5k/mo goal is
realistically many months out, via compounding (proven niche × automated volume ×
brand/owned-store C-phase), not month one.

---

## 7. Phasing, success criteria & risks

### Milestones

- **M0 — Foundation:** style bible written, generator wired, folders + channel
  live. *Done when one piece can go end-to-end by hand.*
- **M1 — Manual proof:** ~10–15 battlestation listings + 2–3 stream packs live,
  run by hand. *Done when real view/favorite/sale data exists.*
- **M2 — Automate the winner:** build the OpenClaw skills for the niche that
  crossed first-sales + repeat-interest; loop runs nightly, owner works the three
  gates. *Done when a day's listings go research → draft-ready with only gate time.*
- **M3 — Scale + evolve to C:** add second/third niche on the shared engine; begin
  the signature LoRA + owned storefront alongside Etsy. *Done when revenue
  compounds across more than one proven line.*

### Success criteria (in order)

1. Pre-QC's keep/kill pile matches the owner's eye in seconds (taste-aligned).
2. First sales on a proven niche.
3. Gate time stays ~15–40 min/day while output volume rises (real leverage).
4. At least one niche compounding month-over-month → the $5k path is real.

### Top risks

- **Saturation / taste-dilution** — mitigated by curation + LoRA signature, not volume.
- **IP edge-cases slipping through** — mitigated by Gate 1 sniff + over-flagging pre-QC.
- **Etsy account risk** — mitigated by fail-closed gates, honest AI disclosure,
  steady cadence, one shop.
- **Pre-QC taste drift** — re-tune scoring periodically against recent keep/kill decisions.
- **Generator ToS/pricing shifts** — mitigated by the generator-agnostic `producer` interface.

---

## 8. Open items for implementation plan

- Choose messaging channel (Telegram vs. WhatsApp).
- Choose hosted generator host (fal.ai vs. Replicate) and confirm Flux + Ideogram access.
- Pin exact Claude model IDs + cost tiering (verify against current Claude API facts).
- Confirm whether the existing `art-store` project is related or fully separate.
- Define the style-bible format (what fields pre-QC scores against).
- Decide Etsy API vs. manual listing for the draft-prep step during Phase 1.
