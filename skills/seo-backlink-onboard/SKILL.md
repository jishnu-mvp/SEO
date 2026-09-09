---
name: seo-backlink-onboard
description: >-
  This skill should be used when setting up backlink and AEO work for a website
  for the first time, or when the user says "onboard this domain for
  backlinks", "set up link building for this site", "start SEO backlinks for a
  new client", or asks to begin a backlink programme on a site that has no
  profile yet. It builds the client profile, provisions the state store,
  confirms which data sources are connected, and commissions the baseline
  audit.
user-invocable: true
argument-hint: "<domain>"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Onboard a website into the backlink programme

Onboarding produces three things: a client profile, a state store, and a verified baseline. No outreach happens during onboarding. Skipping the profile is the most common cause of a programme producing generic, ignorable outreach.

Delegate to `seo-backlink-director` to own this. The director commissions `seo-backlink-baseline-auditor` and `seo-backlink-entity-authority-analyst`.

## Step 1, gather the profile

Read `skills/seo/references/backlink-engine/state-schema.md` for the full profile structure.

Fill everything derivable from the site itself before asking the user anything. Read the homepage, about, services, work, resources and contact pages, and any press or news section. Extract: what the business sells, its market, its locations, its people, its claimed coverage, its claimed certifications, and its existing client results.

Then ask the user only for what the site cannot tell you. Use AskUserQuestion, grouped, never more than a few at a time:

- The 3 to 5 real search competitors, and confirmation of any you inferred
- The target terms in three tiers, or agreement to a set you propose from the site's content
- Which client results and numbers may be cited publicly
- Brand voice, or which brand style guide to apply
- The signature block for outreach and the named human who approves sends
- Relationship owners for any client or partner outreach, and any do-not-contact names
- The monthly target for verified referring domains, defaulting to 3 to 4

## Step 2, verify every claim on the site

Critical, and routinely skipped. The site's own press and certification claims are the raw material for outreach, so a false one is a live credibility risk and an unusable pitch asset.

For each claimed press mention, certification or award: find the live source. Record it as verified with its URL, or flag it as unsubstantiated. Report unsubstantiated claims to the user as a finding in their own right, because an unverifiable claim on a live site damages trust with exactly the buyers the programme is trying to attract.

Watch specifically for a claimed publication whose only evidence is a PDF or screenshot hosted on the client's own domain. That is not coverage and there is no link to reclaim.

## Step 3, provision the state store

Per the state schema, in priority order: a connected local folder, then Google Drive at `seo-backlink-engine/<domain>/`, then the attached project. Create the folder and the empty ledger files. Record the chosen location in the profile so later cycles find it.

## Step 4, confirm the data sources

Read `skills/seo/references/backlink-engine/data-sources.md`. Establish what is actually connected rather than what the user believes is connected, by running a real query against each.

Then tell the user plainly which of the free stack is missing and what each unlocks. Do not proceed as though a source is available when it is not, and never substitute an estimate for a missing measurement.

## Step 5, commission the baseline

Run `seo-backlink-baseline-auditor` for the verified link position, and `seo-backlink-entity-authority-analyst` for entity consistency and a first citation measurement. The director gates both against the stage criteria before they are written to `baseline.md`.

Write `baseline.md` once. It is the fixed comparison point for the life of the programme and is never edited afterwards.

## Step 6, report and set expectations

Deliver: the verified baseline, the unsubstantiated claims found, the missing data sources, and the first cycle's plan.

Set expectations explicitly, in writing, because the expectation gap is what gets programmes cancelled before they work:

- Reclamation and directory work produce countable results inside the first month
- Links take weeks to be recrawled and months to compound, so the first cycle's links will not move rankings within that cycle
- First AI citations on a young domain typically appear 3 to 6 months in
- The month 1 win is a working process and a verified baseline, not traffic

## Do not

- Send any outreach during onboarding
- Write `baseline.md` before the director has approved the audit
- Accept a press or certification claim without finding the live source
- Set a monthly target above 4 verified referring domains for a site starting with a weak profile and no budget
