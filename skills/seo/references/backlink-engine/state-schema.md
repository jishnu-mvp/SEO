# State Schema

The programme has memory. Without it the system re-pitches the same publishers, loses track of promised links, cannot compute a funnel, and cannot tell whether a link decayed. State is what makes this a programme rather than a series of one-off efforts.

## Where state lives

In priority order, use the first that is available:

1. **A connected local folder**, if one is attached to the session. Fastest and simplest.
2. **Google Drive**, in a folder named `seo-backlink-engine/<domain>/`. Works across sessions and machines, and is the recommended default.
3. **The attached project**, if the session has one.

Whichever is used, record the location in the client profile so the next cycle finds it. Never scatter state across two stores.

## Files, one folder per domain

```
seo-backlink-engine/
  <domain>/
    profile.md            The client profile. Read first, every cycle.
    baseline.md           The verified starting position. Written once, amended never.
    link-ledger.md        Every confirmed link, and every decayed one.
    prospect-ledger.md    Every prospect ever sourced, with its disposition.
    outreach-log.md       Every send, follow-up and reply.
    citation-log.md       AI citation checks, one row per engine per prompt per cycle.
    cycles/
      2026-09.md          One file per cycle: target, result, funnel, decisions.
```

## profile.md

The universal per-website configuration. Everything that makes the system work for any site rather than one site.

```markdown
# Client profile: <domain>

## Identity
- Domain, and whether www or non-www is canonical
- Legal name and trading name
- Country and primary market, plus any secondary markets
- Physical locations, if any
- Founded
- Founder and key spokespeople, with roles and their public profiles

## Commercial
- What the business actually sells, in plain words
- ICP, in one paragraph
- The 3 to 5 real search competitors, with why each is included
- Target terms in three tiers:
  - Tier 1, branded and low competition, winnable in 4 to 8 weeks
  - Tier 2, medium commercial, 3 to 6 months
  - Tier 3, head terms, not a ranking play, pursue via third-party roundups
- Target questions in natural language, for AI citation testing

## Assets available for outreach
- Client results with real numbers that may be cited publicly
- Certifications and accreditations, with evidence
- Existing press coverage, verified, with URLs
- Proprietary data that could become a study
- Previous podcast or speaking appearances, as proof for pitches

## Voice and approval
- Brand voice notes, or the brand style guide to apply
- Signature block for outreach
- The named human who approves sends
- Relationship owners for any client or partner outreach
- Do-not-contact list

## Programme settings
- Monthly target, verified referring domains
- State location
- Which data sources are connected, and which are not
- Any tactic explicitly out of scope, with the reason
```

## link-ledger.md

One row per confirmed link. This is the number that gets reported, so nothing enters without a CONFIRMED verdict from the verifier.

| Field | Notes |
|-------|-------|
| Referring domain | |
| Linking page URL | |
| Target URL | |
| Anchor text | Exact |
| Anchor class | Branded, naked URL, generic, partial, exact-match commercial |
| Follow status | Followed or nofollow, from the literal `rel` |
| Literal rel | As read from the DOM |
| Placement | Body, bio, footer, sitewide, comment |
| Tactic | Which playbook won it |
| Date confirmed | |
| Last re-verified | |
| Status | Live, decayed, conditional |
| Verifier note | |

## prospect-ledger.md

Every prospect ever sourced, kept permanently. This is what prevents re-pitching and enables per-tactic conversion measurement.

| Field | Notes |
|-------|-------|
| Domain and target page | |
| Tactic class | |
| Tier | A, B, C or rejected |
| Qualification verdict | With the axis and evidence if rejected |
| Contact name, role, address | Plus route and confidence |
| First sourced | |
| Disposition | Not yet pitched, pitched, replied, won, declined, no response, rejected at gate |
| Cooldown until | Do not re-pitch before this date, default 6 months after a no-response |

## outreach-log.md

| Field | Notes |
|-------|-------|
| Prospect domain | |
| Contact | |
| Tactic | |
| Draft created | Date, and the draft identifier |
| Sent | Date the human actually sent, if known |
| Follow-up 1 and 2 | Dates |
| Reply | Date and summary |
| Outcome | Link promised, link live, declined, no response |

## citation-log.md

Only useful as a time series, so the prompt text is mandatory and must never change between cycles.

| Field | Notes |
|-------|-------|
| Cycle | |
| Prompt text | Verbatim. Changing it breaks the series. |
| Engine | ChatGPT, Gemini, Perplexity, Claude |
| Cited | Yes or no |
| URL cited | If any |
| Competitors named instead | |

## cycles/<YYYY-MM>.md

| Section | Contents |
|---------|----------|
| Target | Verified referring domains targeted |
| Result | Confirmed, against target |
| Funnel | Sourced, qualified, contacts resolved, drafts, sends, replies, promised, confirmed |
| Largest drop-off | The stage, and what it implies |
| Rejected | Prospects at the gate, and claimed links at verification, with reasons |
| Decisions | What was escalated, and what the human decided |
| Next cycle changes | What the funnel says to change |

## Hygiene rules

- Never delete a row. Change its status. Deleted history destroys the conversion measurement that tells the director what to do next.
- Never edit `baseline.md` after it is written. It is the fixed comparison point. Later findings go in the current cycle file.
- Write the cycle file at the end of every cycle even when the cycle failed. A missing cycle file reads as a cycle that never ran.
- Record data sources that were unavailable, so a later reader knows why a number is missing rather than assuming it was zero.
