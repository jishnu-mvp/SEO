---
name: seo-backlink-audit
description: >
  This skill should be used when the user wants to know the verified current
  backlink position of a website, or says "audit our backlinks", "what
  backlinks do we have", "run a backlink audit", "is this link report real",
  "check our link profile", or asks whether claimed links actually exist. It
  runs discovery across every free source and DOM-verifies every link rather
  than trusting a report.
user-invocable: true
argument-hint: "<url>"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Audit a backlink profile

Produces the verified truth about what links into a site. Everything else in the programme trusts this output, so a wrong row is worse than a missing row.

Delegate to `seo-backlink-director`, which commissions `seo-backlink-baseline-auditor` and gates the result. For a profile-health question rather than a discovery question, commission `seo-backlink-portfolio-monitor` as well.

## Scope the request first

Three different questions get asked with the same words. Establish which one:

- **Discovery**: what links to us at all. Full `seo-backlink-baseline-auditor` run.
- **Claim checking**: an agency or vendor says we have N links, is that true. Run `seo-backlink-verifier` over their list, and report claimed against confirmed.
- **Health**: is anything wrong with the profile. Run `seo-backlink-portfolio-monitor` for decay, inbound 404s, anchor distribution, velocity and toxic inbound.

When unclear, run discovery and say what you scoped.

## Non-negotiables

Read `skills/seo/references/backlink-engine/verification-protocol.md` first.

- Every link is verified by reading the real DOM. Text and markdown extraction strips `rel` and cannot prove a link is a link.
- `rel` containing only `noopener` or `noreferrer` is followed. Any `nofollow`, `sponsored` or `ugc` token is not.
- A followed link into a 404 is a defect, not an asset.
- A link routed through the publisher's own shortener is redirect-only and passes little to nothing.
- Report referring domains, never total link count, as the headline.

## Deliver

A table of one row per referring domain with class, follow status, anchor, target and an honest verdict. Then:

- The single number: referring domains in the Asset class
- Unlinked mentions, listed separately, because they are the highest-conversion opportunity in the whole programme and usually the most valuable output of an audit
- Inbound links pointing at broken URLs, which are fixable with no third party involved
- Redirect-only links, which are fixable with one email
- Anchor text distribution
- Every source that could not be accessed, named, with the reason
- An explicit statement that discovery cannot enumerate a full crawler index when no paid index was used

Publish the audit as an artifact when the user will return to it or share it, applying the client profile's brand styling. A one-off spot check can stay in the conversation.

## Do not

- Lead with total link count
- Count owned social profiles, aggregator scrapes or press release syndication inside the asset number
- Report a follow status inferred from extracted text
- Present an estimate as a measurement
