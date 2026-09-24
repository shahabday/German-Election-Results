"""
Upgrade the nav already inserted into the 9 tool pages (by add_tool_nav.py) to
the mobile-friendly hamburger version, add an "About" link, and add a compact
one-line footer bar - reserving space for both above/below #app instead of
overlaying (avoids colliding with each tool's own corner panels).

Run from the repo root:
    python scripts/upgrade_tool_nav_footer.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    "map", "map-all-elections", "map-trends", "map-current-standing",
    "map-election-timeseries", "map-election-profile",
    "map-current-standing-trends", "map-demographics", "map-timeseries",
]

OLD_NAV_CSS = """  /* ---- top nav (shared across the site) ---- */
  .topnav {
    position: relative; z-index: 2000; height: 54px; flex-shrink: 0;
    background: rgba(15, 17, 21, 0.96); backdrop-filter: blur(6px); border-bottom: 1px solid var(--panel-border);
  }
  .topnav-inner {
    max-width: 1080px; margin: 0 auto; padding: 0 24px; height: 54px;
    display: flex; align-items: center; gap: 22px;
    overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none;
  }
  .topnav-inner::-webkit-scrollbar { display: none; }
  .topnav .brand { font-size: 14px; font-weight: 700; text-decoration: none; color: var(--text); white-space: nowrap; flex-shrink: 0; }
  .topnav .nav-links { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
  .topnav .nav-link { white-space: nowrap; font-size: 13px; color: var(--text-dim); text-decoration: none; padding: 8px 10px; border-radius: 6px; }
  .topnav .nav-link:hover { color: var(--text); background: #1e222b; }
  .dropdown { position: relative; }
  .dropdown-toggle {
    font: inherit; font-size: 13px; color: var(--text-dim); background: none; border: none; cursor: pointer;
    padding: 8px 10px; border-radius: 6px; display: flex; align-items: center; gap: 4px; white-space: nowrap;
  }
  .dropdown-toggle:hover, .dropdown:focus-within .dropdown-toggle { color: var(--text); background: #1e222b; }
  .dropdown-caret { font-size: 9px; transition: transform 0.15s; }
  .dropdown:hover .dropdown-caret, .dropdown:focus-within .dropdown-caret { transform: rotate(180deg); }
  .dropdown-menu {
    position: fixed; top: 0; left: 0; min-width: 170px;
    background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.5); padding: 6px; display: flex; flex-direction: column; gap: 2px;
    z-index: 2500; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s;
  }
  .dropdown:hover .dropdown-menu, .dropdown:focus-within .dropdown-menu { opacity: 1; visibility: visible; pointer-events: auto; }
  .dropdown-menu a { font-size: 12.5px; color: var(--text-dim); text-decoration: none; padding: 7px 9px; border-radius: 6px; }
  .dropdown-menu a:hover { color: var(--text); background: #20242e; }
</style>"""

NEW_NAV_CSS = """  /* ---- top nav (shared across the site) ---- */
  .topnav {
    position: relative; z-index: 2000; height: 54px; flex-shrink: 0;
    background: rgba(15, 17, 21, 0.96); backdrop-filter: blur(6px); border-bottom: 1px solid var(--panel-border);
  }
  .topnav-inner {
    max-width: 1080px; margin: 0 auto; padding: 0 24px; height: 54px;
    display: flex; align-items: center; gap: 22px;
  }
  .topnav .brand { font-size: 14px; font-weight: 700; text-decoration: none; color: var(--text); white-space: nowrap; flex-shrink: 0; }
  .topnav .nav-links { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
  .topnav .nav-link { white-space: nowrap; font-size: 13px; color: var(--text-dim); text-decoration: none; padding: 8px 10px; border-radius: 6px; }
  .topnav .nav-link:hover { color: var(--text); background: #1e222b; }
  .dropdown { position: relative; }
  .dropdown-toggle {
    font: inherit; font-size: 13px; color: var(--text-dim); background: none; border: none; cursor: pointer;
    padding: 8px 10px; border-radius: 6px; display: flex; align-items: center; gap: 4px; white-space: nowrap;
  }
  .dropdown-toggle:hover, .dropdown:focus-within .dropdown-toggle { color: var(--text); background: #1e222b; }
  .dropdown-caret { font-size: 9px; transition: transform 0.15s; }
  .dropdown:hover .dropdown-caret, .dropdown:focus-within .dropdown-caret { transform: rotate(180deg); }
  .dropdown-menu {
    position: fixed; top: 0; left: 0; min-width: 170px;
    background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.5); padding: 6px; display: flex; flex-direction: column; gap: 2px;
    z-index: 2500; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s;
  }
  .dropdown:hover .dropdown-menu, .dropdown:focus-within .dropdown-menu { opacity: 1; visibility: visible; pointer-events: auto; }
  .dropdown-menu a { font-size: 12.5px; color: var(--text-dim); text-decoration: none; padding: 7px 9px; border-radius: 6px; }
  .dropdown-menu a:hover { color: var(--text); background: #20242e; }

  .nav-toggle {
    display: none; flex-direction: column; justify-content: center; gap: 4px;
    width: 30px; height: 30px; background: none; border: none; cursor: pointer; padding: 0; margin-left: auto; flex-shrink: 0;
  }
  .nav-toggle span { display: block; width: 100%; height: 2px; background: var(--text-dim); border-radius: 2px; transition: transform 0.15s, opacity 0.15s; }
  .nav-toggle.open span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
  .nav-toggle.open span:nth-child(2) { opacity: 0; }
  .nav-toggle.open span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

  .mobile-menu {
    display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 2100;
    flex-direction: column; padding: 6px 16px 16px; background: var(--bg); border-bottom: 1px solid var(--panel-border);
    box-shadow: 0 12px 28px rgba(0,0,0,0.5); max-height: calc(100vh - 54px); overflow-y: auto;
  }
  .mobile-menu.open { display: flex; }
  .mobile-menu a { font-size: 14px; color: var(--text-dim); text-decoration: none; padding: 10px 6px; border-radius: 6px; }
  .mobile-menu a:hover { color: var(--text); background: #1e222b; }
  .mobile-menu .mobile-group-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-dim); opacity: 0.65; margin: 10px 6px 0; }

  @media (max-width: 760px) {
    .topnav .nav-links { display: none; }
    .nav-toggle { display: flex; }
  }

  #siteFooter {
    height: 30px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    background: rgba(15,17,21,0.96); border-top: 1px solid var(--panel-border);
    font-size: 10.5px; color: var(--text-dim); gap: 4px; padding: 0 12px; text-align: center;
  }
  #siteFooter a { color: var(--text-dim); text-decoration: none; }
  #siteFooter a:hover { color: var(--text); text-decoration: underline; }
</style>"""

NAV_HTML = """<nav class="topnav">
  <div class="topnav-inner">
    <a class="brand" href="../home.html">Germany in Maps</a>
    <div class="nav-links">
      <a class="nav-link" href="../index.html">Home</a>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Political <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="../index.html#political-map">Map visualizations</a>
          <a href="../index.html#political-trend">Trend visualizations</a>
        </div>
      </div>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Demographics &amp; Economy <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="../index.html#demo-map">Map visualization</a>
          <a href="../index.html#demo-trend">Trend visualization</a>
        </div>
      </div>
      <a class="nav-link" href="../about/project.html">About</a>
    </div>
    <button class="nav-toggle" type="button" aria-label="Toggle menu"><span></span><span></span><span></span></button>
  </div>
  <div class="mobile-menu">
    <a href="../index.html">Home</a>
    <div class="mobile-group-title">Political</div>
    <a href="../index.html#political-map">Map visualizations</a>
    <a href="../index.html#political-trend">Trend visualizations</a>
    <div class="mobile-group-title">Demographics &amp; Economy</div>
    <a href="../index.html#demo-map">Map visualization</a>
    <a href="../index.html#demo-trend">Trend visualization</a>
    <a href="../about/project.html">About</a>
  </div>
</nav>
"""

FOOTER_HTML = """<footer id="siteFooter">
  Made with ❤️ by @shahabday ·
  <a href="mailto:shahabdaiani@gmail.com">shahabdaiani@gmail.com</a> ·
  <a href="https://instagram.com/shahabday" target="_blank" rel="noopener">@shahabday</a> ·
  <a href="https://shahabwrites.com" target="_blank" rel="noopener">shahabwrites.com</a>
</footer>
"""

OLD_JS_TAIL = """  window.addEventListener("scroll", position, true);
});

// Leaflet (and some chart canvases) can compute their initial size before the
// nav bar above them has settled into layout - nudge them to remeasure once.
requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
</script>"""

NEW_JS_TAIL = """  window.addEventListener("scroll", position, true);
});

document.querySelectorAll(".topnav").forEach((nav) => {
  const toggle = nav.querySelector(".nav-toggle");
  const menu = nav.querySelector(".mobile-menu");
  if (!toggle || !menu) return;
  toggle.addEventListener("click", () => {
    const open = menu.classList.toggle("open");
    toggle.classList.toggle("open", open);
    window.dispatchEvent(new Event("resize"));
  });
  menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
    menu.classList.remove("open");
    toggle.classList.remove("open");
  }));
});

// Leaflet (and some chart canvases) can compute their initial size before the
// nav bar above them has settled into layout - nudge them to remeasure once.
requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
</script>"""


def process(tool):
    path = ROOT / tool / "index.html"
    html = path.read_text(encoding="utf-8")

    assert OLD_NAV_CSS in html, f"{tool}: old nav css not found"
    html = html.replace(OLD_NAV_CSS, NEW_NAV_CSS, 1)

    assert "height: calc(100vh - 54px); width: 100vw;" in html, f"{tool}: #app height rule not found"
    html = html.replace(
        "height: calc(100vh - 54px); width: 100vw;",
        "height: calc(100vh - 84px); width: 100vw;",
        1,
    )
    if "min-height: calc(100vh - 54px);" in html:
        html = html.replace(
            "min-height: calc(100vh - 54px);",
            "min-height: calc(100vh - 84px);",
            1,
        )

    old_nav_start = html.index('<nav class="topnav">')
    old_nav_end = html.index("</nav>", old_nav_start) + len("</nav>\n")
    html = html[:old_nav_start] + NAV_HTML + html[old_nav_end:]

    # insert footer right after #app's closing div (the only line that's exactly "</div>")
    html = re.sub(r"^</div>$", "</div>\n" + FOOTER_HTML.rstrip("\n"), html, count=1, flags=re.MULTILINE)

    assert OLD_JS_TAIL in html, f"{tool}: js tail not found"
    html = html.replace(OLD_JS_TAIL, NEW_JS_TAIL, 1)

    path.write_text(html, encoding="utf-8")
    print(f"  {tool}: nav + footer upgraded")


def main():
    for tool in TOOLS:
        process(tool)


if __name__ == "__main__":
    main()
