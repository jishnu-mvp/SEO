---
name: seo-backlink-outreach
description: >
  This skill should be used to produce link building outreach for specific
  prospects, or when the user says "draft the outreach emails", "email these
  sites about links", "write the reclamation emails", "draft follow-ups for the
  link outreach", or asks to contact publishers about a link. It qualifies and
  resolves contacts first, then drafts personalised emails into the user's mail
  client, unsent, with the follow-up sequence.
user-invocable: true
argument-hint: "[prospects]"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Draft link building outreach

Every email lands as a draft for a human to review and send. Nothing sends itself. This is a safety property of the system, not a preference.

Delegate through `seo-backlink-director`, which runs `seo-backlink-prospect-qualifier`, then `seo-backlink-contact-resolver`, then `seo-backlink-outreach-writer`, gating each.

## Never skip the gates

A request to "just email these sites" still runs qualification and contact resolution first. Skipping them is how a programme emails a link farm, or emails a stranger at a guessed address, or pitches a publisher who already links to the client.

1. **Qualify.** `seo-backlink-prospect-qualifier` screens for spam and penalty risk, relevance, reality, dedupe against existing referring domains and the outreach log, and reachability. Rejections are reported with the failing axis and the evidence.
2. **Resolve.** `seo-backlink-contact-resolver` works the ladder from byline to author page to team page to submission form to verified pattern to generic inbox. Inferred addresses are labelled inferred, and the director decides whether to use them.
3. **Draft.** `seo-backlink-outreach-writer` writes per prospect, in the client's brand voice, using the tactic's playbook.

## What makes a draft acceptable

Read `skills/seo/references/backlink-engine/outreach-library.md` for the per-tactic templates. Every draft must have all of:

- One verifiable specific about the target page, proving a human read it
- An ask of one sentence, and a small one
- A reason that serves their reader, never our rankings
- Under 150 words for reclamation and repairs, under 200 for a credibility pitch
- The real signature from the client profile
- Their stated submission process followed, where they publish one

If two prospects would receive the same body with the name swapped, personalisation has failed and the drafts are rejected.

## Draft the follow-ups at the same time

Most links come from the second touch, so a programme without follow-up leaves roughly half its links unclaimed. Draft the full sequence up front with labelled send dates: first follow-up 5 working days after the initial, adding new information rather than repeating the ask; final follow-up 10 working days later, closing politely. Never a third. Never guilt.

## Where there is no email route

Produce paste-ready copy for the contact form or submission process, and say clearly that no draft was created because no email route exists.

## Anchor text

Ask for a branded anchor or a naked URL. Never request an exact-match commercial phrase. If a publisher offers to use any anchor, ask for the brand name.

## Deliver

A table of every draft created with recipient, subject, tactic and send date, so the user can work through their drafts in order. Then a list of prospects not drafted for, with reasons. Then log every draft in the outreach ledger.

## Do not

- Send anything
- Draft to a prospect the qualifier rejected
- Claim anything about the client not substantiated in the profile
- Contact a client, partner or supplier without routing through the relationship owner
- Continue past a site's stated no-unsolicited-contact policy
- Use em dashes
