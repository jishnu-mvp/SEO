# URL Redirect Map — mvp1.com.au (live) → new site (currently staged at mvp1-website.vercel.app)

Built by directly enumerating both sites' XML sitemaps in full (live: 51 URLs across 6 sitemaps; staging: 44 URLs in 1 sitemap) and matching by content/slug correlation. Use this as the spec for the 301 redirect rules before cutover.

## Confirmed 1:1 matches (build these as 301s)

| Old URL (mvp1.com.au) | New URL |
|---|---|
| `/` | `/` |
| `/aimaturity` | `/aimaturity.html` |
| `/about-us` | `/about-us.html` |
| `/contact` | `/contact.html` |
| `/ai-agents` | `/ai-agents.html` |
| `/solution-overview` | `/solution-overview.html` |
| `/overview` | `/overview.html` |
| `/accelerate-program` | `/accelerate-program.html` |
| `/what-we-build` | `/what-we-build.html` |
| `/our-work` | `/our-work.html` |
| `/funded-tech-startups-scale-ups-smbs` | `/funded-tech-startups-scale-ups-smbs.html` |
| `/platform-stabilisation` | `/platform-stabilisation.html` |
| `/podcasts` | `/podcasts.html` |
| `/resources` | `/resources.html` |
| `/news-media` | `/news-media.html` |
| `/casestudies` | `/our-work.html` *(confirm — closest equivalent, not an exact rename)* |
| `/casestudies/uber-for-kids` | `/case-studies/kago-child-transport-platform.html` |
| `/casestudies/tiny-home-marketplace` | `/case-studies/volstrukt-tiny-home-marketplace.html` |
| `/casestudies/security-marketplace` | `/case-studies/guardbay-security-marketplace.html` |
| `/ebook/why-platform-business` | `/resources/business-model-workbook.html` *(confirm — plausible match, different naming, not verified as the same asset)* |
| `/blog/ai-agents-vs-chatbots-what-business-leaders-need-to-understand-before-automating-workflows` | `/blog/ai-agents-vs-chatbots.html` |
| `/blog/custom-software-development-for-growing-businesses-when-to-build-buy-or-stabilise` | `/blog/build-buy-or-stabilise.html` |
| `/blog/stalled-product-roadmap-rescue-guide` | `/blog/stalled-product-roadmap.html` |
| `/blog/enterprise-ai-strategy-business-growth` | `/blog/enterprise-ai-strategy.html` |
| `/blog/inbound-ai-voice-agent-solution-guide` | `/blog/inbound-ai-voice-agents.html` |
| `/blog/the-rise-of-agentic-workflows-why-businesses-are-replacing-traditional-automation-in-2026` | `/blog/agentic-workflows.html` |
| `/blog/why-most-ai-agent-projects-fail-in-production-and-how-enterprise-teams-are-fixing-it` | `/blog/why-ai-agent-projects-fail.html` |
| `/blog/agentic-ai-30x-productivity-guide` | `/blog/agentic-ai-productivity.html` |
| `/blog/private-ai-infrastructure-control-data-sovereignty` | `/blog/private-ai-infrastructure.html` |
| `/blog/sovereign-ai-infrastructure-offshore-ai-legal-risks` | `/blog/sovereign-ai-offshore-risk.html` |
| `/blog/ai-agent-development-replace-traditional-hiring` | `/blog/ai-agents-and-hiring.html` |
| `/blog/7-core-principles-of-building-a-successful-platform-business` | `/blog/platform-business-principles.html` |
| `/blog/why-traditional-business-models-are-at-risk-of-disruption-by-ai-platforms` | `/blog/traditional-models-at-risk.html` |
| `/blog/the-untapped-valuation-potential-of-ai-driven-businesses` | `/blog/ai-business-valuation.html` |
| `/blog/how-data-fuels-the-ai-revolution-lessons-from-whatsapps-19-billion-valuation` | `/blog/data-fuels-ai.html` |
| `/podcast/every-industry-will-be-disrupted-jay-pandya` | `/podcast/every-industry-will-be-disrupted.html` |
| `/podcast/business-model-ai-platform-valuation-jay-pandya` | `/podcast/business-model-ai-platform-valuation.html` |
| `/podcast/human-first-technology-tech-strategy-jay-pandya` | `/podcast/human-first-technology.html` |
| `/podcast/scope-creep-the-silent-killer-of-product-market-fit-jay-pandya-on-startup-discipline` | `/podcast/scope-creep-and-product-market-fit.html` |
| `/podcast/ai-avatars-transforming-sales-and-customer-engagement` | `/podcast/ai-avatars-sales-and-engagement.html` |
| `/podcast/scaling-human-expertise-with-ai-jay-pandya-on-the-future-of-digital-solutions` | `/podcast/scaling-human-expertise-with-ai.html` |
| `/podcast/using-ai-to-share-knowledge-with-the-world-jay-pandya` | `/podcast/using-ai-to-share-knowledge.html` |

## No match found on staging — resolve before launch (Critical)

| Old URL | Status | Action needed |
|---|---|---|
| `/rates` | Missing | Confirm the Transparent Pricing page exists somewhere on the new site; if not published yet, either build it or redirect to the closest relevant page (e.g. `/contact.html`) until it exists — do not let it 404. |
| `/enterprise` | Missing | Confirm an Enterprise Solutions page exists on the new site under some URL; if genuinely dropped, decide a redirect target (e.g. `/overview.html` or `/what-we-build.html`). |
| `/blackvault-private-ai-infrastructure` | Missing | This is the BlackVault *product/solution* page, distinct from the existing blog post about private AI infrastructure (`/blog/private-ai-infrastructure.html`). Confirm whether the product page itself was migrated under a different path. |
| `/terms-conditions` | Missing | **Legal/compliance gap, not just SEO** — confirm this page exists on the new site before launch, regardless of redirect planning. |
| `/privacy-policy` | Missing | **Legal/compliance gap, not just SEO** — same as above. |
| `/careers` | Missing | Confirm whether this page still exists; if dropped, decide the redirect target. |

## Content likely dropped or rewritten beyond matching (verify)

| Old URL | Note |
|---|---|
| `/blog/software-development-agency-selection-guide` | No corresponding URL found on staging. Staging's blog list is otherwise a complete 1:1 set (15 of 16 matched); this is the one live post with no staging counterpart. Staging does have one blog URL with no live counterpart (`/blog/delivery-signals.html`) — possibly this post was rewritten/retitled beyond recognition, or it's genuinely new and the old one was retired. Confirm which, and if retired, decide a redirect target (e.g. to `/blog/delivery-signals.html` if it's a true replacement, or to `/resources.html` if not). |

## New pages on staging with no live equivalent (no redirect needed, informational only)

- `/smbs.html`
- `/vibe-coded-to-production.html`

## How this was built

Full sitemap enumeration on both sites on 2026-08-19: `sitemap_index.xml` + 6 child sitemaps on the live site (page/blog/casestudies/ebook/podcast/ai-tool), and the single `sitemap.xml` on staging (which already publishes final `mvp1.com.au` URLs). Matches made by content/slug correlation, not automated diffing — the "confirm" flags above mark matches that are plausible but not independently verified against actual page content.
