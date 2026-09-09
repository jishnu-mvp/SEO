---
name: seo-backlink-verify
description: >
  This skill should be used to independently confirm whether claimed backlinks
  are real, or when the user says "verify these links", "did the link go live",
  "check if this link is dofollow", "the publisher says it's live", "confirm
  our links before the report", or asks whether an agency's or vendor's link
  claims are true. It reads the live page markup and returns claimed against
  confirmed.
user-invocable: true
argument-hint: "<url> [links]"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Verify claimed backlinks

The most common failure in link building is reporting links that are not real, not followed, or no longer live. This is the check that catches it.

Delegate to `seo-backlink-verifier`. It is adversarial by design and assumes every claim is wrong until the markup says otherwise.

Read `skills/seo/references/backlink-engine/verification-protocol.md` first.

## Run all seven checks

A link is CONFIRMED only when all seven pass:

1. An anchor element on the claimed page has an `href` resolving to the client's domain
2. The complete `rel` is read from the real DOM and recorded literally
3. The `href` points directly at the client, not through a shortener or tracker on the publisher's own domain
4. The target URL returns real content, not a 404 or soft 404
5. The exact anchor text is captured and classified
6. The linking page is indexable: not `noindex`, not robots-blocked, not behind a login or paywall
7. Placement is recorded: body, author bio, footer, sitewide or comment

## Reading rel correctly

Absent, or containing only `noopener` and `noreferrer`, means followed. Any `nofollow`, `sponsored` or `ugc` token means not followed. A markdown or text extraction cannot tell you this, because the conversion strips the attribute. If the DOM is genuinely unreachable, the verdict is UNVERIFIABLE with the obstacle named, never CONFIRMED.

Do not attempt to fetch pages with shell tools. Use a browser.

## Verdicts

- **CONFIRMED** - all seven pass
- **CONDITIONAL** - exists with a fixable defect. State the exact remedial ask so it can be requested.
- **REJECTED** - not found, page gone, not indexable, or unsubstantiated. State what you looked for.
- **UNVERIFIABLE** - access blocked. Name the obstacle and the manual check a human can run.
- **DECAYED** - previously confirmed, now absent. Record dates last seen and first missing.

## Report the arithmetic honestly

Always state it in this shape, and never soften the gap:

> 6 claimed, 3 confirmed, 2 conditional, 1 rejected.

The claimed number never becomes the result. The credibility of every future report depends on this.

## Then update state

Write confirmed links to the link ledger. Hand conditional links back to outreach with the remedial ask. Hand decayed links to `seo-backlink-portfolio-monitor`.

## Do not

- Accept a publisher's email as evidence
- Infer follow status from text lacking the word nofollow
- Round conditional up to confirmed
- Let a 404 target pass because the link exists
