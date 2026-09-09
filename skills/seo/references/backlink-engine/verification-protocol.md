# Verification Protocol

The most common failure in link building is reporting links that are not real, not followed, or no longer live. This protocol is the defence. It applies to the baseline audit, to every claimed win, and to every re-verification.

## Why text extraction is not verification

Fetching a page as markdown or plain text destroys `rel` attributes and cannot distinguish a hyperlink from a plain-text URL. A tool that returns "no nofollow found" has told you nothing, because the attribute was never in the text it read.

**Verification requires reading the real DOM.** Use a browser and query the anchor elements directly. If the only available access is a text extraction, the `rel` status is UNVERIFIED and must be recorded that way.

Do not attempt to fetch web content with shell tools such as `curl` or `wget`. That path is blocked by policy in this environment, and a blocked fetch is not evidence of anything.

## The DOM query

Run this in the page context and record the full result verbatim:

```js
({
  url: location.href,
  title: document.title,
  links: [...document.querySelectorAll('a[href*="TARGET-DOMAIN"]')].map(a => ({
    href: a.getAttribute('href'),
    rel: a.getAttribute('rel') || 'NONE (followed)',
    anchor: a.innerText.trim().slice(0, 100),
    context: a.closest('article,main,footer,aside,nav,header')?.tagName || 'unknown'
  })),
  noindex: !!document.querySelector('meta[name="robots"][content*="noindex" i]'),
  canonical: document.querySelector('link[rel=canonical]')?.href || null
})
```

Replace `TARGET-DOMAIN` with the bare domain, no protocol, so both `http` and `https` and `www` and non-`www` variants match.

## Reading rel correctly

| `rel` value | Followed? |
|-------------|-----------|
| absent | Yes |
| `noopener`, `noreferrer`, or both | Yes. These are security and privacy hints, not ranking directives. |
| contains `nofollow` | No |
| contains `sponsored` | No |
| contains `ugc` | No |

A link tagged `sponsored` on a paid placement is correct publisher behaviour, not a defect. It just means the link passes no ranking value, so it should never have been bought as a ranking tactic.

## The seven checks

A link is CONFIRMED only when all seven pass.

1. **Existence** - an anchor element on the claimed page has an `href` resolving to the client's domain
2. **Follow status** - full `rel` read and recorded literally
3. **Direct target** - the `href` goes to the client's domain, not through a shortener or tracking redirect on the publisher's own domain
4. **Target resolves** - the destination URL returns real content, not a 404 or soft 404
5. **Anchor recorded** - exact text captured, and classified as branded, naked URL, generic, partial match or exact-match commercial
6. **Indexability** - the linking page is not `noindex`, not robots-blocked, not behind a login or paywall
7. **Placement** - body, author bio, footer, sitewide widget or comment. Body and bio carry value. Sitewide footer links are a spam signal.

## Verdicts

- **CONFIRMED** - all seven pass
- **CONDITIONAL** - link exists with a fixable defect. State the exact remedial ask: make it direct, remove the nofollow if followed was agreed, correct the target URL, or change the anchor.
- **REJECTED** - no link found, page gone, page not indexable, or claim unsubstantiated. State exactly what you looked for and did not find.
- **UNVERIFIABLE** - genuine access obstacle. Name the obstacle and the manual check a human can run. Never defaults to confirmed.
- **DECAYED** - previously confirmed, now absent. Record date last seen and date first found missing.

## Redirect-only links

A link routed through the publisher's own shortener, for example `l.publisher.com/clientname`, or a tracking redirect, is not a direct link. It passes little to nothing and search engines may not attribute it. Record as CONDITIONAL and treat it as an opportunity, because asking a publisher to make an existing link direct is one of the easiest requests in link building and it costs them nothing.

## Reporting arithmetic

Always state claimed against confirmed, explicitly, in this shape:

> 6 claimed, 3 confirmed, 2 conditional, 1 rejected.

Never present the claimed number as the result. Never soften the gap. The credibility of every future report depends on this number being the honest one.

## Re-verification cadence

- Before any report that repeats a historical total
- Every confirmed link at least quarterly
- All inbound links immediately after any site migration, relaunch or URL structure change
- Any link on a page that has been redesigned or restructured
