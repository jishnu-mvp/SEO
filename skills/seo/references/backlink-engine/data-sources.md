# Data Sources

What each source can and cannot tell you, how to reach it, and what it costs. The programme is designed to run at zero cost first and add paid tooling only when the free sources become the constraint.

## Free, and genuinely sufficient to start

### Google Search Console
The most complete free backlink source for a site you own, plus the only authoritative source for how the site is actually performing in search.

- **Links report** gives top linking sites, top linked pages, and top anchor text. Sampled, not exhaustive, and it does not tell you follow status, so every domain still needs DOM verification.
- **Performance report** gives impressions, clicks, CTR and average position per query and per page. This is the ranking measurement for the programme.
- **URL Inspection** gives per-URL index status and last crawl date, which is how you tell whether a new link's page has even been crawled yet.
- **Data lag** is 2 to 3 days. Never report a number from the last 3 days as final.
- **Access** via the Google Search Console connector where available, or the user exports from the UI.

### Bing Webmaster Tools
Free, an entirely independent index, and its backlink data routinely surfaces referring domains Search Console omits. Materially better for backlinks than most people expect, and there is no reason not to have it connected. Also carries its own keyword and crawl data.

### Google Analytics
Organic sessions, landing pages, conversions. This is where link work eventually connects to leads, with all the attribution caveats.

### Google Business Profile
For any business with a physical or service-area presence. Insights show discovery searches, direction requests and calls. Also the anchor for local citation consistency, and a common source of entity conflicts.

### Public search
Discovery of mentions, coverage, roundups, competitor links and prospect lists. Free and unlimited in practice. The `link:` operator has not worked for many years; do not use it. Use quoted brand and domain strings instead.

### A browser
The verification instrument. Reading the real DOM is the only way to establish follow status, and it is free.

### Hunter.io free tier
Around 50 email lookups a month, which covers the outreach volume of a 3 to 4 link a month programme.

### Journalist request platforms
Featured, Qwoted, SourceBottle and Source of Sources all have usable free tiers. SourceBottle is the most relevant for Australian and New Zealand clients.

---

## What free sources cannot do

Be honest about this in every report, **unless a paid index is connected**, in which case say which one and drop these caveats.

- **No full crawler index.** Neither Search Console nor Bing enumerates every referring domain, and neither can enumerate a competitor's profile at all. Competitor link mapping without a paid index is directional, not complete.
- **No authority metric.** There is no free equivalent of Domain Rating or Domain Authority. Judge prospects on relevance, reality and editorial quality instead, which is a better basis anyway.
- **No automated link gap.** The intersect must be assembled by hand from discovery.
- **No decay alerting.** Re-verification is a manual cadence.

## Ahrefs, when connected: the exact tool map

Call `mcp__Ahrefs__doc` before first use of any Ahrefs tool. Monetary values come back in USD cents, so divide by 100. When a response carries `render_with` in its metadata, call the named render tool rather than summarising raw rows.

| Job | Tool |
|-----|------|
| Every backlink to a domain | `site-explorer-all-backlinks` |
| Referring domains, the metric that matters | `site-explorer-referring-domains` |
| Referring domain count over time, for velocity | `site-explorer-refdomains-history` |
| Anchor text distribution | `site-explorer-anchors` |
| Links pointing at our 404s, live equity being lost | `site-explorer-broken-backlinks` |
| Domain Rating, and its history | `site-explorer-domain-rating`, `site-explorer-domain-rating-history` |
| Who actually ranks against us | `site-explorer-organic-competitors` |
| Screen many prospect domains at once | `batch-analysis` |
| Free DR lookup without burning quota | `public-domain-rating-free` |
| Search Console data | the `gsc-*` family, including `gsc-keywords`, `gsc-pages`, `gsc-performance-history` |
| Technical site issues | `site-audit-issues`, `site-audit-page-explorer` |
| Quota remaining | `subscription-info-limits-and-usage` |

**Brand Radar is the AEO and GEO measurement layer**, and it replaces most of the manual citation testing:

| Job | Tool |
|-----|------|
| Brand mention volume and trend | `brand-radar-mentions-overview`, `brand-radar-mentions-history` |
| AI citations of us | `brand-radar-citations-overview-entities`, `brand-radar-citations-history-entities` |
| Which pages and domains AI cites for our queries | `brand-radar-cited-pages`, `brand-radar-cited-domains` |
| The actual AI answers | `brand-radar-ai-responses` |
| Share of voice against competitors | `brand-radar-sov-overview`, `brand-radar-sov-history` |
| Manage the tracked prompt set | `management-brand-radar-prompts` |
| AI response count for a site | `site-explorer-ai-responses-count` |

`brand-radar-cited-pages` deserves special attention. It answers the single most valuable question in this whole programme: which third-party pages do AI engines cite for our target queries. Those pages are the priority link and listing targets, and this tool produces that list directly instead of by manual observation.

Check `subscription-info-limits-and-usage` before a large pull, and prefer `batch-analysis` and `public-domain-rating-free` for bulk prospect screening so quota goes on the analysis that needs it.

Two things Ahrefs does **not** replace. It does not report unlinked mentions, so reclamation prospecting still runs on public search. And it does not establish follow status reliably enough to report: DOM verification stays mandatory on every link that will be counted.

## Check what is already connected before assuming free-only

Run a connector listing at the start of a programme rather than assuming the free stack is all that is available. Two connectors change the picture materially and are commonly already present but toggled off for the chat:

**A backlink index, such as Ahrefs.** If present, it removes the single biggest limitation in this system. It gives real competitor referring-domain enumeration, an authority metric, a genuine link intersect, anchor profiles at scale, and decay detection. The specialists run on restricted tool grants, so the director pulls this data and hands it down. **DOM verification remains mandatory regardless**, because an index tells you a link probably exists while only the live markup tells you whether it is followed, direct and on an indexable page.

**A people-data provider, such as Apollo.** If present, contact resolution stops depending on pattern guessing. A provider-returned address counts as Verified. Look up only the specific person needed for a single outreach, never bulk-enrich a prospect list, and surface any credit consumption so the cost per resolved contact is visible.

If either is installed but not enabled for the chat, say so and ask for it to be enabled. It is a toggle, not a purchase.

## Paid, in the order worth buying

Only after the free process has run for a full cycle and held.

| Tool | Cost | What it unlocks | Buy when |
|------|------|-----------------|----------|
| Semrush SEO, annual | ~$117/mo | Rank tracking, competitor backlink gap, site audit, AI visibility tracking bundled | The weekly habit has held for a month and competitor gap analysis has become the constraint |
| Ahrefs Lite | ~$129/mo | The best backlink index available | Backlink data specifically is the constraint and AI visibility tracking is not needed |
| BuzzStream Starter | ~$29/mo | Outreach CRM, sequencing, reply tracking | More than roughly 10 concurrent outreach conversations. A spreadsheet is genuinely fine below that. |
| Respona | ~$160/placement | Pay-per-placement link acquisition | Only when free and earned tactics have plateaued. Buys volume, not authority. |

**Do not buy an AI visibility tracker separately** if buying Semrush, which bundles prompt tracking. Otterly Lite at roughly $25 a month is the cheapest honest standalone if the bundled coverage proves thin.

**Do not buy press release distribution as a backlink tactic.** Syndicated copies are near-duplicates and heavily discounted. It generates brand mentions, which have real AEO value, so judge it as a brand-mention buy and never as a link buy.

## Connector notes

Where a Google connector is available in the session, prefer it over asking the user to export. Confirm which properties and accounts are actually connected before running a query, because a query against the wrong property produces confidently wrong numbers. Report the property or account name alongside every metric so the reader can confirm it is the right one.

Where a source is unavailable, the value is "unavailable" with the reason named. Never substitute an estimate for a measurement.

## Setting up the free stack, in order

1. Google Search Console, verified on the domain property, sitemap submitted
2. Bing Webmaster Tools, which can import directly from Search Console
3. Google Analytics, with conversions defined so leads are countable
4. Google Business Profile, claimed and verified, hours and categories correct
5. Hunter.io free account
6. Free accounts on the journalist request platforms relevant to the client's market
7. A state folder for the programme ledgers, per the state schema
