# AEO and GEO Playbook

Answer Engine Optimisation and Generative Engine Optimisation are not a separate discipline from SEO. They are SEO fundamentals plus entity work plus a measurement loop. This file holds the evidence base and the method.

**Re-verify the evidence quarterly.** This field moves faster than any other part of search, and every number below is a snapshot from research current to late 2026.

## The evidence base

Reason from these, and cite them when challenged.

**Brand mentions beat backlinks for AI citation.** Measured correlation with AI visibility is roughly **0.66 for brand web mentions** against roughly **0.22 for backlinks**, so mentions matter around three times more. The top quartile of brands by mention volume averaged around **169 AI Overview citations** against about **14** for the next tier, a roughly tenfold gap.

**The practical consequence is large.** An unlinked brand mention, which classic link building treats as a partial failure to be reclaimed, is close to a full win for AI visibility. So reclamation outreach should ask for the link while understanding the mention already did most of the AEO work. Never skip a mention-generating activity because it will not produce a link.

**Classic ranking still gates citation.** Top-10 organic placement is among the strongest citation factors measured, alongside basic crawlability. Roughly nine in ten AI citations come from pages already ranking on page one. AEO does not replace SEO; it compounds on top of it.

**The highest-evidence citation factors**, in order:

1. URL accessibility. The page must be crawlable and not blocked.
2. Search rank. Top-10 organic placement.
3. Fan-out rank. Ranking across the related sub-queries an engine decomposes a question into.
4. Preview control. `nosnippet` and similar directives suppress the snippet an engine would quote, and therefore suppress citation.
5. Query-to-answer match. Directly answering the specific phrasing asked.
6. AI-ready structure. Clear headings and passages that can be extracted whole.
7. Self-contained passages. Sections that stand alone as a complete answer.

**Editorial content carries the majority of citations**, around 53% in one large analysis. Brochure and service pages are cited far less than articles that answer questions.

**Freshness matters.** Recently updated pages are cited disproportionately, so a content refresh cadence is an AEO activity, not just an SEO one.

## The five workstreams

### 1. Entity consistency

AI systems cross-check a business's facts across sources. Conflicts make them hedge or omit the business entirely.

Collect and compare across the site, its schema, LinkedIn, Crunchbase, Google Business Profile, YouTube, Wikidata, industry directories and review platforms:

- Legal name and trading name
- Founding date
- Headquarters and any other locations
- Employee count band
- Founder and leadership names, with roles
- Service categories
- Phone, email, address

Report every conflict with the exact differing values and each source URL. Fix at the source, starting with the client's own site and schema, then the profiles they control.

**Wikidata** deserves specific attention. An entry, where the business genuinely meets notability, is disproportionately useful for machine entity recognition. It is free and rarely pursued.

### 2. Structured data and answer structure

Required schema:

- `Organization`, one canonical entity referenced by a stable identifier across every page. Competing or duplicated organisation graphs are actively harmful, and are a common side effect of an SEO plugin auto-generating one alongside a hand-authored one.
- `Person` for the founder and key spokespeople, linked to the Organization via `founder` or `employee`
- `Service` for each service line
- `FAQPage` on a real, visible, crawlable FAQ
- `LocalBusiness` where there is a genuine physical presence
- `Article` with a named `author` on editorial content

Then answer structure. Each key page should open with a **self-contained answer of roughly 130 to 170 words** that a machine can lift whole and that makes sense with no surrounding context. Most sites already have the content and need restructuring rather than writing.

**Author signals.** Attribute articles to a named human with a visible byline and a real bio, not to the organisation. Thin author signals suppress both classic E-E-A-T assessment and AI citation.

### 3. Live citation testing

This is a manual measurement discipline whose entire value is as a time series, so method consistency beats cleverness.

Method:
1. Take the client's target questions in **natural language**, as a buyer would ask them, not as keywords.
2. Ask each of ChatGPT, Gemini, Perplexity and Claude.
3. Record per engine per question: cited or not, which URL if any, and which competitors were named instead.
4. **Log the exact prompt text.** A changed prompt breaks the series and the comparison is void.
5. Re-run the identical prompts every cycle.

Expect nothing for the first few months on a young domain. First citations typically appear 3 to 6 months in, and consistency across engines takes 6 to 12 months.

### 4. Citation source mining

This is the workstream that connects AEO back to link building, and it is the most underused idea in the whole programme.

For every target question where the client is **not** cited, record which pages the engines **did** cite. Those pages are the highest-value link and listing targets available, because they are demonstrably what the engines already trust for that query. A directory or roundup that AI quotes for "best X in Y" is worth more than a higher-authority page nobody quotes.

Hand these to the prospector as priority targets every cycle.

### 5. llms.txt, judged not assumed

Google states plainly that llms.txt is **not used** for AI Overviews, AI Mode or any of its generative features, and has compared it to the keywords meta tag. Anthropic references it for documentation contexts, OpenAI maintains files for some of its own products, and Perplexity has been observed surfacing llms.txt content.

**Recommend it only when** the site has developer documentation or an API reference, or AI assistant referral traffic is already material, and the site is small enough that maintenance is realistic. Say plainly that it is not a Google visibility lever. Never present it as a ranking tactic.

## What actually moves AI visibility, ranked

1. Rank in the top 10 organically for the target query. Nothing else substitutes.
2. Generate brand mentions everywhere, linked or not. Podcasts, communities, press, directories, roundups.
3. Get listed in the third-party roundups the engines already cite for the category.
4. Restructure key pages into self-contained extractable answers.
5. Make the entity unambiguous and consistent everywhere.
6. Attribute content to named humans with real bios.
7. Keep content fresh, with a real refresh cadence.
8. Do not block crawlers or suppress snippets.

## What does not work

- llms.txt as a Google play
- Keyword stuffing an FAQ
- Schema on content that does not exist on the page
- Buying syndicated press release distribution and calling it AEO. It does generate mentions, so it is not worthless, but the near-duplicate copies are heavily discounted and it is a poor use of budget compared to one real editorial mention.
- Any expectation of results inside 90 days on a young domain
