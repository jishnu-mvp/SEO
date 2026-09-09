---
name: seo-backlink-sprint
description: >
  This skill should be used to run a full monthly backlink acquisition cycle
  for a website, or when the user says "run the backlink sprint", "run this
  month's link building", "start the monthly backlink cycle", "get me this
  month's backlinks", or asks to execute the link building programme end to
  end. It orchestrates every specialist agent in sequence through the director,
  with a verification gate between stages, and ends with drafts in the user's
  mail client and a verified result.
user-invocable: true
argument-hint: "[url]"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Run a backlink acquisition cycle

One cycle, one month, one number that matters: verified new referring domains.

Delegate the whole cycle to `seo-backlink-director`. It sequences the specialists, gates each output, and escalates decisions. Do not invoke specialists directly from here; the gate is the point of the system.

## Preconditions

Refuse to start and route to `seo-backlink-onboard` if any of these is missing:

- A client profile exists and has been read
- A baseline exists, or this cycle includes commissioning one
- A monthly target is set
- A named human approver is recorded
- The state store location is known

## Sequence

The director runs these gates. Stages 4 to 7 iterate per prospect batch rather than waiting for the full pipeline, so drafts start reaching the user early in the cycle.

1. **Refresh state.** Read the profile, link ledger, prospect ledger and outreach log. Identify prospects in cooldown, promised links awaiting verification, and follow-ups now due.
2. **Baseline delta.** `seo-backlink-baseline-auditor` on changes since last cycle only, not a full re-audit. Catch decay and new inbound links nobody earned.
3. **Gap refresh.** `seo-backlink-gap-analyst`, quarterly or when the pipeline is thin. Skip in a month where the pipeline is already full.
4. **Entity and citation check.** `seo-backlink-entity-authority-analyst`. Re-run the identical citation prompts from the log. Mine the cited sources for new priority link targets.
5. **Prospect.** `seo-backlink-prospector`. Target 8 to 12 prospects per targeted link. Coverage rule applies: at least four tactic classes, no class above half.
6. **Qualify.** `seo-backlink-prospect-qualifier`. Expect heavy rejection. If the approved pipeline cannot support the target, say so now rather than at the end of the cycle.
7. **Resolve contacts.** `seo-backlink-contact-resolver`. Label inferred addresses as inferred.
8. **Draft.** `seo-backlink-outreach-writer`. Drafts into the mail client, unsent, plus the labelled follow-up sequence. Hand the user a working list.
9. **Follow up.** Draft the follow-ups due this cycle from the outreach log. Most links come from the second touch, so this stage is not optional.
10. **Verify.** `seo-backlink-verifier` on every claimed and promised link. Only CONFIRMED counts.
11. **Portfolio health.** `seo-backlink-portfolio-monitor`. Fix inbound 404s first; they need no third party.
12. **Report.** `seo-backlink-reporting-analyst`. Verified numbers only.

Run `seo-backlink-asset-strategist` when the qualified pipeline cannot reach the target, or once a quarter regardless. It removes the ceiling instead of pushing harder against it.

## Human touchpoints

Three, and only three, in a normal cycle:

1. **Approvals**, early: any spend, any live-site change, any client or partner outreach, any prospect that is attractive but risk-flagged.
2. **Sending**, mid-cycle: the user reviews and sends drafts. Nothing sends itself.
3. **Report**, at the end.

Batch approvals into one numbered decision list with a recommendation per item. Do not interrupt repeatedly.

## Write state as you go

Update the ledgers at each stage rather than at the end, so an interrupted cycle is resumable. Never delete a row; change its status.

## Close the cycle

Write `cycles/<YYYY-MM>.md` even when the cycle failed. Include the funnel with real drop-off, the largest constraint stage, and what changes next cycle.

## Do not

- Report a claimed link as won
- Send an email
- Let a single tactic exceed half the pipeline
- Inflate a prospect tier to make the target arithmetic work
- Skip the follow-up stage
- Present activity volume as a result
