# Process Gaps and How This System Closes Them

Most link building programmes fail in predictable ways. This file lists the failure modes, the agent or rule that closes each, and what to watch for if it starts happening anyway. Review this list whenever a cycle misses its target, because the cause is almost always on it.

## 1. No verified baseline

**Failure.** Nobody knows the starting position, so improvement cannot be demonstrated and existing assets go unnoticed. Sites routinely already hold real links nobody counted.

**Closed by.** `baseline-auditor` at onboarding, DOM-verifying every claim. `baseline.md` is written once and never edited, giving a fixed comparison point.

## 2. Reporting links that are not real

**Failure.** The single most damaging failure in the industry. A publisher says the link is live, it goes in the report, and it is nofollow, or on a `noindex` page, or was never added, or points at a 404. Client trust collapses when someone eventually checks.

**Closed by.** `link-verifier`, adversarial by design, plus the hard rule that the director reports only CONFIRMED links and always states claimed against confirmed. The verifier reads the real DOM because text extraction strips `rel` entirely.

## 3. Ignoring existing unlinked mentions

**Failure.** Programmes start cold-pitching strangers while publishers who already featured the client sit unasked. Reclamation converts around three times better than cold outreach.

**Closed by.** Reclamation is tactic 1 in the playbooks and the prospector works it first. The audit reports unlinked mentions as a separate headline output.

## 4. Losing equity to broken inbound links

**Failure.** After a migration or relaunch, existing links point at URLs that no longer resolve. The equity is live and being discarded, and it needs no third party to recover.

**Closed by.** `portfolio-monitor` check 2, run every cycle and mandatory after any migration. It is prioritised first in its output because it is the only link fix that requires nobody's permission.

## 5. Redirect-only links counted as real

**Failure.** A publisher links through their own shortener or tracker. It looks like a link in every report and passes little to nothing.

**Closed by.** A distinct classification in both the auditor and the verifier, and tactic 2 in the playbooks, since asking for a direct link converts around one in two.

## 6. No follow-up

**Failure.** One email goes out, nothing comes back, the prospect is written off. Most links come from the second touch, so this leaves roughly half the available links unclaimed.

**Closed by.** `outreach-writer` drafts the full sequence up front with labelled send dates, and the sprint has a dedicated follow-up stage that is explicitly not optional.

## 7. No memory, so prospects get re-pitched

**Failure.** The same publisher is pitched twice, or a site that already links to the client is pitched, which burns goodwill and looks amateur.

**Closed by.** The prospect ledger persists every prospect ever sourced with its disposition and a cooldown date. `prospect-qualifier` axis 4 is a mandatory dedupe against both the ledger and existing referring domains.

## 8. Pipeline monoculture

**Failure.** The pipeline becomes all directories, or all guest posts. It produces few followed links and collapses entirely when that one channel is exhausted.

**Closed by.** The coverage rule: at least four tactic classes per cycle, no class above half the pipeline. Enforced at the director's stage 4 gate.

## 9. Optimistic arithmetic

**Failure.** Tiers get inflated so the target looks reachable, and the cycle misses with no early warning.

**Closed by.** Fixed conversion expectations per tier in the risk policy, a required pipeline arithmetic line in the qualifier's output, and an explicit instruction to declare a short pipeline rather than re-tier to fix it.

## 10. Penalty risk from volume pressure

**Failure.** A target must be hit, so a paid or low-quality placement gets approved. Site reputation abuse enforcement has made this materially riskier than it used to be.

**Closed by.** `prospect-qualifier` axis 1 with an automatic rejection list, the director's rule that volume never justifies risk, and mandatory escalation for any paid placement.

## 11. Anchor over-optimisation

**Failure.** Manual link building drifts toward exact-match commercial anchors, which is exactly the footprint algorithmic scrutiny looks for.

**Closed by.** An anchor policy of branded or naked URL by default, anchor classification recorded on every verified link, and a monitored threshold at roughly 10% exact-match commercial.

## 12. Unnatural velocity

**Failure.** A burst of links to a young domain reads as manufactured.

**Closed by.** `portfolio-monitor` check 4 against a trailing average, with planned PR pushes annotated as explained rather than flagged as suspicious.

## 13. Silent link decay

**Failure.** Historical totals get repeated in reports long after links have been removed.

**Closed by.** Quarterly re-verification of every confirmed link, a DECAYED status in the ledger, and the rule that any report repeating a historical total triggers re-verification first.

## 14. Outreach that reads like a template

**Failure.** Generic emails get ignored, and at volume they damage the sender's domain reputation.

**Closed by.** A hard requirement for one verifiable specific per draft, personalisation hooks passed from `contact-resolver` to `outreach-writer`, and an explicit rejection rule: if two drafts differ only by name, personalisation has failed.

## 15. Emails sent without human review

**Failure.** An agent sends something wrong to a real person, irreversibly.

**Closed by.** Drafts only, everywhere. `outreach-writer` has no send tool and is instructed to refuse. The director treats this as a safety property rather than a preference.

## 16. Fabricated claims in outreach

**Failure.** An agent asserts a client result, certification or press mention that cannot be substantiated. Sent to a journalist, this is a serious reputational risk.

**Closed by.** Onboarding step 2 verifies every claim on the client's own site and flags the unsubstantiated ones, and `outreach-writer` may only assert what the profile substantiates.

## 17. No linkable assets, so the pipeline has a ceiling

**Failure.** Outreach exhausts the finite set of pages that could plausibly link to the client, and the programme stalls with nothing to escalate to.

**Closed by.** `linkable-asset-strategist`, triggered automatically when the qualified pipeline cannot reach the target, and quarterly regardless.

## 18. AEO and GEO treated as a separate project

**Failure.** Link building and AI visibility run as unrelated workstreams, so mention-generating activity gets dropped for producing no links, and the roundup pages AI actually cites never become link targets.

**Closed by.** `entity-authority-analyst` runs inside the same cycle, and its workstream 4 feeds the pages AI cites directly back to the prospector as priority targets. The playbook states explicitly that an unlinked mention is close to a full AEO win.

## 19. Entity ambiguity

**Failure.** Conflicting company facts across sources make AI assistants hedge or omit the business, and no amount of link building fixes it.

**Closed by.** `entity-authority-analyst` workstream 1, with conflicts reported as exact differing values and source URLs.

## 20. Citation measurement that cannot be compared

**Failure.** AI citation checks are run with different wording each time, so the series is meaningless.

**Closed by.** The citation log stores verbatim prompt text and the analyst is required to re-run identical prompts, declaring a broken series if a prompt changes.

## 21. Activity reported as achievement

**Failure.** Reports lead with emails sent and prospects contacted, which tells a stakeholder nothing and hides a failing programme.

**Closed by.** The report structure puts verified referring domains first and activity volume below the fold, and the director is instructed never to pad a miss with activity metrics.

## 22. Expectation gap kills the programme early

**Failure.** Links land in month 1, rankings do not move, and the programme is cancelled in month 3 just before it would have compounded.

**Closed by.** A mandatory timing statement in onboarding and in every single report: links take weeks to recrawl and months to compound, first AI citations typically 3 to 6 months, and the month 1 win is a process and a baseline rather than traffic.

## 23. No named owner, so the weekly habit dies

**Failure.** The most common real-world cause of failure. The work stops and nobody notices for a quarter.

**Closed by.** A named human approver required in the profile before a cycle can start, and a cycle file written every month even when the cycle failed, so a gap is visible rather than silent.

## Known limits, stated honestly

These are not solved, and pretending otherwise would be its own failure mode.

- **No paid index means no complete competitor link profile.** Gap analysis is directional. Semrush or Ahrefs is the fix, and the system is designed to prove value first and buy second. **Check first whether an index connector is already installed and simply toggled off for the chat**, because this limit is frequently self-inflicted. Where one is available the director supplies its data to the specialists and the caveat is dropped, but DOM verification stays mandatory.
- **No free authority metric exists.** The system judges relevance, reality and editorial quality instead, which is arguably better but is not a number a stakeholder can benchmark. Lifted when a paid index is connected.
- **AI citation testing is manual.** It cannot be automated reliably at zero cost, so its value depends entirely on method consistency.
- **Attribution from a link to a lead is genuinely weak.** The system reports the chain and names the confounds rather than claiming causation.
