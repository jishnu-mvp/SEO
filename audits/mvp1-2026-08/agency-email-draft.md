**To:** [Agency account manager]
**Cc:** [Your account lead], [MVP1 finance]
**Subject:** mvp1.com.au: urgent credential exposure, and findings from our independent audit
**Attachment:** MVP1-Organic-Search-Audit-Aug2026.pdf

---

Hi [Name],

We have completed an independent audit of mvp1.com.au covering the full engagement to date, May through August 2026. We checked every deliverable in the shared Drive folder against live Google Search Console and GA4 data, crawled all 53 pages of the site, and verified the links and markup you reported.

The full report is attached. There is one item below that needs your attention today, ahead of everything else.

## 1. Urgent: account credentials are exposed in a public folder

The Drive folder you shared with us is set to "anyone with the link can view". At least four files inside it contain the plaintext password for mvpausqld@gmail.com, which is the Google account controlling our Google Business Profile. The same files also expose the recovery email address and recovery phone number. A second, different password for that same account appears in the Month 3 claim and verification report, and the same password has been reused for the Medium and Tumblr accounts created on our behalf.

We are rotating these credentials now. Please:

- Confirm today that link sharing on that folder has been disabled.
- Tell us every other location where our credentials have been stored or transmitted, including internal systems, spreadsheets, and any subcontractors.
- Confirm whether this folder structure has been shared with anyone outside your team.
- Explain how plaintext client passwords came to be stored in delivery documents at all, and what you are changing so it does not recur.

We also found a complete article about fire extinguisher services in Sydney, with live links to majesticfire.com.au, left inside our Month 3 workbook. That is another client's content in our file. Combined with the credential handling above, it raises a reasonable concern that our data has travelled the same way.

## 2. Performance over the engagement

Measured against April 2026, the last full month before work began:

| Metric | April | August | Change |
|---|---|---|---|
| Organic clicks | 202 | 103 | down 49% |
| Impressions | 4,832 | 1,945 | down 60% |
| Average position | 8.4 | 16.4 | down 8.0 places |
| GA4 organic sessions | 195 | 126 | down 35% |

We want to be fair about cause. Branded impressions fell at a similar rate while brand rankings held steady around position 5 to 6, which indicates falling brand search demand rather than lost rankings. That part is our problem to solve, not yours.

The part we hold you accountable for is non-branded organic traffic, which is what the retainer exists to grow. Non-branded clicks have been 0 to 1 per month every month since March and have not moved. Of the 17 commercial keywords across your four keyword mapping sheets, one has ever registered a single impression: "private ai infrastructure", with 9 impressions and no clicks in May.

## 3. Specific claims we need explained

Each of these is a claim in your reports that the live site or the raw data does not support.

**Press release distribution, Month 1.** Your report states 557 live links. We tested a random sample of 70 of the URLs listed in the deliverable. 30% are dead, returning 404 or 500. Of the 49 that load, every single one is tagged rel="nofollow", which means none passes any ranking value. Please confirm whether any dofollow links were delivered, and how this campaign was expected to influence rankings. We note your own April benchmark flagged 32 potentially spammy referring domains as a risk, before several hundred more of the same type were added in June.

**Schema implementation, Month 1, dated 17 June.** Your report lists eight schema types applied to 11 pages. On the live site, six of the ten pages we can check carry no structured data at all: /about-us, /contact, /overview, /solution-overview, /funded-tech-startups-scale-ups-smbs and /enterprise. Four of the eight claimed types, WebPage, WebSite, AboutPage and ContactPage, do not appear anywhere on the site.

**Benchmark figures, Month 1.** Your report gives 6,826 impressions and 278 clicks for 16 March to 14 April. Search Console returns 5,661 impressions and 269 clicks for that exact window, so impressions are overstated by 20.6%. We tested every 20 to 45 day window in 2026 and none matching the stated period produces your figure. Please send the Search Console export behind that number. If you were reading a domain property rather than the URL prefix property, say so and we will reconcile it. We should add that the GA4 half of the same report is exact to the user, which is why the gap stands out.

**Sitemap, Month 1, dated 13 June.** Your report states a new sitemap of 44 URLs was created and submitted at /sitemap_index.xml. That URL returns 404. The live sitemap is at /sitemap.xml and contains 53 URLs. The same report claims robots.txt was configured to block unwanted folders; the live file blocks nothing.

**Image ALT optimisation, Month 1.** Every image URL in that sheet points at /wp-content/uploads/, which are WordPress paths. The live site does not use them, so the work could not have been applied. Our homepage still has 20 of 42 images with no alt text.

**Month 4 deliverables.** The Local Business Listing Report is a one page PDF with no content in it at all. It is one of only three files delivered that month.

**Repeated deliverable.** "Recommended Case Study Structure" appears in the Month 1, Month 2 and Month 3 folders. All three files are byte for byte identical, 418,129 bytes with the same MD5 hash. Please confirm it was billed once.

**Citation remediation.** The NAP audit itself is genuine and useful, and identified 14 directories with incorrect details. However, across Months 2 and 3, all five prioritised sites still show status "Contacted Site Admin, Waiting For Response". Four months in, the directory data is still wrong.

## 4. What we do credit

We want the record to be balanced. Four things check out:

- Conversion goal tracking was set up correctly on 16 June and works. Key events went from zero before June to 30 in July. This is genuine value we did not have in April. Two goals point at /thank-you and /ebook/why-platform-business, neither of which resolves, so those need repointing.
- The GA4 figures in the benchmark report are accurate to the user.
- The guest post on altervision.org is live and carries three dofollow links. It is the only working backlink we found across four months.
- The Search Console noindex issues are genuinely resolved. All 53 pages return 200 with correct canonicals.

## 5. What we need, and by when

1. Confirmation that the Drive folder is locked down, plus your answers on credential handling. **Today.**
2. Written responses to each item in section 3, with supporting exports. **Within five business days.**
3. A meeting to walk through the attached report and agree what happens next. Please propose times this week.

We are pausing approval of the next invoice until we have those responses. To be clear about our intent: we would rather fix this engagement than end it, and a straight answer on each point is what gets us there.

Regards,

[Your name]
[Title]
MVP1 Ventures
mvp1.com.au
