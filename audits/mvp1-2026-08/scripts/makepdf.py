import asyncio, os
from playwright.async_api import async_playwright
SP=os.path.dirname(os.path.abspath(__file__))
frag=open(f"{SP}/mvp1-audit.html").read()
embedded=open(f"{SP}/fonts/embedded.css").read()
# strip the network font link; fonts are inlined for the PDF
import re as _re
frag=_re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>','',frag)
frag=_re.sub(r'<link[^>]*rel="preconnect"[^>]*>','',frag)
html=("<!doctype html><html><head><meta charset='utf-8'>"
 "<meta name='viewport' content='width=device-width,initial-scale=1'>"
 "<style>"+embedded+"</style>"
 "<style>:root{color-scheme:light}body{margin:0;font:14px system-ui;background:#fff}"
 "img{max-width:100%}[hidden]{display:none!important}</style></head><body>"+frag+"</body></html>")
open(f"{SP}/print.html","w").write(html)

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                                  args=["--no-sandbox"])
        ctx=await b.new_context(color_scheme="light")
        pg=await ctx.new_page()
        await pg.goto("file://"+SP+"/print.html", wait_until="load")
        # let webfonts resolve through the proxy
        try:
            await pg.wait_for_function("document.fonts.status==='loaded'", timeout=25000)
        except Exception as e:
            print("font wait:", str(e)[:60])
        fonts=await pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)")
        print("loaded font families:", sorted(set(fonts)) or "NONE (fallback stacks in use)")
        await pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
        await pg.emulate_media(media="print")
        await pg.wait_for_timeout(1200)
        await pg.pdf(path=f"{SP}/MVP1-Organic-Search-Audit-Aug2026.pdf",
                     format="A4", print_background=True,
                     margin={"top":"14mm","bottom":"14mm","left":"12mm","right":"12mm"},
                     display_header_footer=True,
                     header_template="<div></div>",
                     footer_template=("<div style=\"width:100%;font-size:7.5pt;color:#5E6C78;"
                       "font-family:Arial,sans-serif;padding:0 12mm;display:flex;justify-content:space-between\">"
                       "<span>MVP1 Ventures | mvp1.com.au</span>"
                       "<span>Organic Search Audit &middot; 31 August 2026</span>"
                       "<span class='pageNumber'></span>/<span class='totalPages'></span></div>"))
        await b.close()
asyncio.run(main())
