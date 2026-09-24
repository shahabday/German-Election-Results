"""
Inject the shared top nav (with working dropdowns) into every self-contained
tool page, so navigation isn't only reachable from the hub. Each tool page
keeps its own layout; we just reserve 54px of vertical space above #app.

Run from the repo root:
    python scripts/add_tool_nav.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    "map", "map-all-elections", "map-trends", "map-current-standing",
    "map-election-timeseries", "map-election-profile",
    "map-current-standing-trends", "map-demographics", "map-timeseries",
]

NAV_CSS = """
  /* ---- top nav (shared across the site) ---- */
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

NAV_HTML = """<nav class="topnav">
  <div class="topnav-inner">
    <a class="brand" href="../index.html">Germany in Maps</a>
    <div class="nav-links">
      <a class="nav-link" href="../tools.html">Home</a>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Political <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="../tools.html#political-map">Map visualizations</a>
          <a href="../tools.html#political-trend">Trend visualizations</a>
        </div>
      </div>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Demographics &amp; Economy <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="../tools.html#demo-map">Map visualization</a>
          <a href="../tools.html#demo-trend">Trend visualization</a>
        </div>
      </div>
    </div>
  </div>
</nav>
"""

NAV_JS = """
<script>
document.querySelectorAll(".dropdown").forEach((dd) => {
  const toggle = dd.querySelector(".dropdown-toggle");
  const menu = dd.querySelector(".dropdown-menu");
  if (!toggle || !menu) return;
  const position = () => {
    const r = toggle.getBoundingClientRect();
    menu.style.left = Math.round(r.left) + "px";
    menu.style.top = Math.round(r.bottom + 4) + "px";
  };
  dd.addEventListener("mouseenter", position);
  toggle.addEventListener("focus", position);
  window.addEventListener("resize", position);
  window.addEventListener("scroll", position, true);
});
</script>
</body>"""


def process(tool):
    path = ROOT / tool / "index.html"
    html = path.read_text(encoding="utf-8")

    assert "<nav class=\"topnav\">" not in html, f"{tool}: nav already present"

    html = html.replace("</style>", NAV_CSS, 1)

    html = html.replace(
        "height: 100vh; width: 100vw;",
        "height: calc(100vh - 54px); width: 100vw;",
        1,
    )
    html = html.replace(
        "min-height: 100vh;",
        "min-height: calc(100vh - 54px);",
        1,
    )

    html = re.sub(r"(<body>\s*)", r"\1" + NAV_HTML, html, count=1)

    assert "</body>" in html
    html = html.replace("</body>", NAV_JS, 1)

    path.write_text(html, encoding="utf-8")
    print(f"  {tool}: nav inserted")


def main():
    for tool in TOOLS:
        process(tool)


if __name__ == "__main__":
    main()
