---
name: seo-backlink-report
description: >
  This skill should be used to produce the backlink and AEO performance report
  for a cycle, or when the user says "build the backlink report", "monthly SEO
  link report", "what did link building deliver this month", "report on our
  backlink programme", or needs a stakeholder update on link building results.
  It reports only independently verified links and shows the real outreach
  funnel including drop-off.
user-invocable: true
argument-hint: "[cycle]"
license: UNLICENSED
metadata:
  version: "2.2.4"
---

# Build the cycle report

The report is the only part of this programme most stakeholders will see, so its credibility is the programme's credibility. One inflated number destroys it.

Delegate to `seo-backlink-reporting-analyst`, gated by `seo-backlink-director`.

## Verify before reporting

Run `seo-backlink-verify` over every link the cycle claims, before writing anything. A link enters the report only with a CONFIRMED verdict. If 6 were claimed and 3 confirmed, the report says 3, states that 6 were claimed, and gives the reason each of the other 3 failed.

## Structure, in this order

1. **Verified new referring domains this cycle, against target.** One number, first line. If the target was missed, say so in the same line.
2. **What landed.** Per link: domain, page, follow status, anchor, target URL, tactic, date. This is the evidence.
3. **The funnel with real drop-off.** Prospects sourced, qualified, contacts resolved, drafts, sends, replies, promised, verified. Name the single largest drop-off and what it implies. This is the most useful section, because it says what to change.
4. **In flight.** What is mid-conversation, at what stage, expected when.
5. **Rejected and why.** Prospects rejected at the gate, and claimed links rejected at verification. Publishing your own rejections is what makes the confirmed number believable.
6. **Ranking movement.** Search Console impressions, clicks and average position for the tracked tiers, like period against like period, with the data lag stated.
7. **AI citation movement.** From the citation log, identical prompts to prior cycles, per engine. If a prompt changed, say the series is broken and why.
8. **Traffic and leads.** Analytics organic sessions and conversions, with attribution limits stated plainly.
9. **Portfolio health.** Decay, inbound 404s, anchor distribution, velocity, against thresholds with the actual numbers.
10. **Decisions needed.** The escalation list, each with a recommendation and the consequence of each option.

## Attribution honesty

State what changed in links, what changed in rankings, what changed in traffic and leads, and where a connection is plausible, call it plausible and name the confound. Never draw a causal line the data cannot support.

Repeat the timing expectation in every report, every time: links take weeks to be recrawled and months to compound, so this cycle's links will not appear in this cycle's rankings. The expectation gap is what gets programmes cancelled before they work.

## Delivery

Publish as an artifact so it has a durable URL and month-on-month reports form a series. Apply the client profile's brand palette and typography. Include the full verified link table inside the artifact, not just a summary, because the evidence is the point.

Write the cycle file to state, per the state schema, even when the cycle failed.

## Do not

- Report a claimed link as landed
- Put activity volume above the fold. Emails sent is not a result.
- Attribute a ranking or traffic change to this cycle's links
- Omit the rejected section, however unflattering
- Substitute an estimate for an unavailable measurement
