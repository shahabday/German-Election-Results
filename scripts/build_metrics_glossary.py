"""Builds about/metrics.html: a full glossary of every metric in map-demographics and
map-society, read straight from each tool's own metrics_manifest.json (single source of
truth - this script never hand-duplicates a description, it only formats what the two
build scripts already wrote).

Each tool's panel shows the SHORT description ("description") inline, with a "Learn
more" link to this page's anchor for that metric (id="m-<tool>-<key>"), where the FULL
description ("description_full"), unit, category, years covered, and source citation
all live.

Run from the repo root:
    python scripts/build_metrics_glossary.py
(re-run map-demographics/build_demographics_data.py and map-society/build_society_data.py
first if you've changed a description - this script only reads their output.)
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "about" / "metrics.html"

TOOLS = [
    {
        "id": "demographics",
        "name": "Demographics & Economy Map",
        "tool_href": "../map-demographics/",
        "manifest": ROOT / "map-demographics" / "data" / "prepared" / "metrics_manifest.json",
        "resolutions": [
            ("municipality", "Municipality (Zensus 2022, one snapshot)"),
            ("county", "County (multi-year, 1995–2022 depending on metric)"),
        ],
    },
    {
        "id": "society",
        "name": "Society & Culture Map",
        "tool_href": "../map-society/",
        "manifest": ROOT / "map-society" / "data" / "prepared" / "metrics_manifest.json",
        "resolutions": [
            ("county", "County / state (see each metric - some are broadcast from state-level sources)"),
        ],
    },
]


def esc(s):
    return html.escape(str(s), quote=True)


def metric_card(tool_id, res_key, m):
    anchor = f"m-{tool_id}-{m['key']}"
    years = m.get("years")
    years_line = ""
    if years:
        if len(years) > 1:
            years_line = f"<div class=\"m-meta\"><b>Years covered:</b> {esc(years[0])}–{esc(years[-1])} ({len(years)} years with data)</div>"
        else:
            years_line = f"<div class=\"m-meta\"><b>Years covered:</b> {esc(years[0])} only</div>"
    elif "year" in m:
        years_line = f"<div class=\"m-meta\"><b>Snapshot year:</b> {esc(m['year'])}</div>"
    source = m.get("source")
    source_line = f"<div class=\"m-meta\"><b>Source:</b> {esc(source)}</div>" if source else ""
    return f"""
      <div class="metric-card" id="{anchor}">
        <div class="m-head">
          <h3>{esc(m['label'])}</h3>
          <span class="m-unit">{esc(m['unit'])}</span>
        </div>
        <div class="m-meta"><b>Category:</b> {esc(m['category'])}</div>
        {years_line}
        {source_line}
        <p class="m-full">{esc(m['description_full'])}</p>
        <a class="m-anchor-link" href="#{anchor}">#{anchor}</a>
      </div>"""


def build_tool_section(tool):
    with open(tool["manifest"], encoding="utf-8") as f:
        manifest = json.load(f)

    sections = []
    for res_key, res_label in tool["resolutions"]:
        res = manifest.get(res_key)
        if not res:
            continue
        by_category = {}
        for m in res["metrics"]:
            by_category.setdefault(m["category"], []).append(m)

        cat_blocks = []
        for category in sorted(by_category):
            cards = "\n".join(metric_card(tool["id"], res_key, m) for m in by_category[category])
            cat_blocks.append(f"""
      <h4 class="category-title">{esc(category)}</h4>
      <div class="metric-grid">{cards}
      </div>""")

        sections.append(f"""
    <div class="resolution-block">
      <h3 class="resolution-title">{esc(res_label)}</h3>
      {"".join(cat_blocks)}
    </div>""")

    return f"""
  <section class="tool-block" id="{tool['id']}">
    <div class="tool-block-head">
      <h2>{esc(tool['name'])}</h2>
      <a class="open-btn" href="{esc(tool['tool_href'])}">Open tool →</a>
    </div>
    {"".join(sections)}
  </section>"""


def build_toc(tool):
    with open(tool["manifest"], encoding="utf-8") as f:
        manifest = json.load(f)
    total = sum(len(manifest[rk]["metrics"]) for rk, _ in tool["resolutions"] if rk in manifest)
    return f'<a href="#{tool["id"]}">{esc(tool["name"])}</a> <span class="toc-count">({total} metrics)</span>'


def main():
    tool_sections = "\n".join(build_tool_section(t) for t in TOOLS)
    toc_items = "".join(f"<li>{build_toc(t)}</li>" for t in TOOLS)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Metrics Glossary — Germany in Maps</title>
<style>
  :root {{
    --bg: #0f1115; --panel: #171a21; --panel-border: #2a2e38;
    --text: #e8eaed; --text-dim: #9aa0ab; --accent: #4a90e2;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
  body {{ padding-bottom: 80px; }}
  a {{ color: inherit; }}
  .wrap {{ max-width: 900px; margin: 0 auto; padding: 0 24px; }}

  .topnav {{
    position: sticky; top: 0; z-index: 100; background: rgba(15, 17, 21, 0.96);
    backdrop-filter: blur(6px); border-bottom: 1px solid var(--panel-border);
  }}
  .topnav-inner {{
    max-width: 1080px; margin: 0 auto; padding: 0 24px; height: 54px;
    display: flex; align-items: center; gap: 22px;
  }}
  .topnav .brand {{ font-size: 14px; font-weight: 700; text-decoration: none; color: var(--text); white-space: nowrap; flex-shrink: 0; }}
  .topnav .nav-links {{ display: flex; align-items: center; gap: 4px; flex-shrink: 0; }}
  .topnav .nav-link {{ white-space: nowrap; font-size: 13px; color: var(--text-dim); text-decoration: none; padding: 8px 10px; border-radius: 6px; }}
  .topnav .nav-link:hover {{ color: var(--text); background: #1e222b; }}
  .dropdown {{ position: relative; }}
  .dropdown-toggle {{
    font: inherit; font-size: 13px; color: var(--text-dim); background: none; border: none; cursor: pointer;
    padding: 8px 10px; border-radius: 6px; display: flex; align-items: center; gap: 4px; white-space: nowrap;
  }}
  .dropdown-toggle:hover, .dropdown:focus-within .dropdown-toggle {{ color: var(--text); background: #1e222b; }}
  .dropdown-caret {{ font-size: 9px; transition: transform 0.15s; }}
  .dropdown:hover .dropdown-caret, .dropdown:focus-within .dropdown-caret {{ transform: rotate(180deg); }}
  .dropdown-menu {{
    position: fixed; top: 0; left: 0; min-width: 170px;
    background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.5); padding: 6px; display: flex; flex-direction: column; gap: 2px;
    z-index: 500; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s;
  }}
  .dropdown:hover .dropdown-menu, .dropdown:focus-within .dropdown-menu {{ opacity: 1; visibility: visible; pointer-events: auto; }}
  .dropdown-menu a {{ font-size: 12.5px; color: var(--text-dim); text-decoration: none; padding: 7px 9px; border-radius: 6px; }}
  .dropdown-menu a:hover {{ color: var(--text); background: #20242e; }}

  .nav-toggle {{
    display: none; flex-direction: column; justify-content: center; gap: 4px;
    width: 30px; height: 30px; background: none; border: none; cursor: pointer; padding: 0; margin-left: auto; flex-shrink: 0;
  }}
  .nav-toggle span {{ display: block; width: 100%; height: 2px; background: var(--text-dim); border-radius: 2px; transition: transform 0.15s, opacity 0.15s; }}
  .nav-toggle.open span:nth-child(1) {{ transform: translateY(6px) rotate(45deg); }}
  .nav-toggle.open span:nth-child(2) {{ opacity: 0; }}
  .nav-toggle.open span:nth-child(3) {{ transform: translateY(-6px) rotate(-45deg); }}

  .mobile-menu {{
    display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 90;
    flex-direction: column; padding: 6px 16px 16px; background: var(--bg); border-bottom: 1px solid var(--panel-border);
    box-shadow: 0 12px 28px rgba(0,0,0,0.5); max-height: calc(100vh - 54px); overflow-y: auto;
  }}
  .mobile-menu.open {{ display: flex; }}
  .mobile-menu a {{ font-size: 14px; color: var(--text-dim); text-decoration: none; padding: 10px 6px; border-radius: 6px; }}
  .mobile-menu a:hover {{ color: var(--text); background: #1e222b; }}
  .mobile-menu .mobile-group-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-dim); opacity: 0.65; margin: 10px 6px 0; }}

  @media (max-width: 760px) {{
    .topnav .nav-links {{ display: none; }}
    .nav-toggle {{ display: flex; }}
  }}

  footer.site-footer {{ margin-top: 56px; padding-top: 20px; border-top: 1px solid var(--panel-border); font-size: 11.5px; color: var(--text-dim); line-height: 1.7; }}
  footer.site-footer a {{ color: var(--text-dim); }}
  footer.site-footer a:hover {{ color: var(--text); }}

  .breadcrumb {{ font-size: 12px; color: var(--text-dim); margin: 28px 0 18px; }}
  .breadcrumb a:hover {{ text-decoration: underline; }}
  h1 {{ font-size: 25px; margin: 0 0 14px; font-weight: 700; }}
  p.lead {{ font-size: 14.5px; color: var(--text-dim); line-height: 1.65; margin: 0 0 20px; max-width: 680px; }}

  .toc {{ background: var(--panel); border: 1px solid var(--panel-border); border-radius: 10px; padding: 16px 20px; margin-bottom: 36px; }}
  .toc-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-dim); margin-bottom: 8px; }}
  .toc ul {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }}
  .toc a {{ font-size: 14px; text-decoration: none; color: var(--accent); }}
  .toc a:hover {{ text-decoration: underline; }}
  .toc-count {{ font-size: 12px; color: var(--text-dim); }}

  .tool-block {{ padding: 30px 0; border-top: 1px solid var(--panel-border); scroll-margin-top: 66px; }}
  .tool-block:first-of-type {{ border-top: none; }}
  .tool-block-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }}
  .tool-block h2 {{ font-size: 20px; margin: 0; font-weight: 700; }}
  .open-btn {{
    display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600;
    color: #fff; background: var(--accent); text-decoration: none; padding: 7px 13px; border-radius: 6px; flex-shrink: 0;
  }}
  .open-btn:hover {{ filter: brightness(1.1); }}

  .resolution-block {{ margin-top: 18px; }}
  .resolution-title {{ font-size: 14px; font-weight: 700; color: var(--text-dim); margin: 22px 0 4px; text-transform: uppercase; letter-spacing: 0.03em; }}
  .category-title {{ font-size: 15px; font-weight: 700; margin: 20px 0 10px; color: var(--text); }}

  .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }}
  .metric-card {{
    background: var(--panel); border: 1px solid var(--panel-border); border-radius: 10px;
    padding: 14px 16px; scroll-margin-top: 66px; position: relative;
  }}
  .metric-card:target {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
  .m-head {{ display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-bottom: 6px; }}
  .m-head h3 {{ font-size: 14.5px; margin: 0; font-weight: 700; }}
  .m-unit {{ font-size: 10.5px; color: var(--text-dim); white-space: nowrap; flex-shrink: 0; }}
  .m-meta {{ font-size: 11px; color: var(--text-dim); margin-bottom: 4px; line-height: 1.5; }}
  .m-meta b {{ color: var(--text); font-weight: 600; }}
  .m-full {{ font-size: 12.5px; color: var(--text-dim); line-height: 1.6; margin: 8px 0 0; }}
  .m-anchor-link {{ position: absolute; top: 14px; right: 16px; font-size: 10px; color: var(--text-dim); text-decoration: none; opacity: 0; transition: opacity 0.1s; }}
  .metric-card:hover .m-anchor-link {{ opacity: 0.5; }}
  .m-anchor-link:hover {{ opacity: 1 !important; text-decoration: underline; }}

  .back-home {{ display: inline-block; margin-top: 30px; font-size: 12.5px; color: var(--text-dim); text-decoration: none; }}
  .back-home:hover {{ color: var(--text); text-decoration: underline; }}
</style>
</head>
<body>

<nav class="topnav">
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
      <a class="nav-link" href="../index.html#stories">Stories</a>
      <a class="nav-link" href="project.html">About</a>
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
    <a href="../index.html#stories">Stories</a>
    <a href="project.html">About</a>
  </div>
</nav>

<div class="wrap">
  <div class="breadcrumb"><a href="../index.html">Home</a> / Metrics Glossary</div>
  <h1>Metrics Glossary</h1>
  <p class="lead">Every metric across the Demographics &amp; Economy and Society &amp; Culture maps, with its exact source, what years it covers, and a fuller explanation than fits in the tool's own panel. Each tool links here directly from its metric description - click "Learn more" next to any metric to land on its card below.</p>

  <div class="toc">
    <div class="toc-title">Jump to</div>
    <ul>{toc_items}</ul>
  </div>

  {tool_sections}

  <a class="back-home" href="../index.html">← Back to all tools</a>
<footer class="site-footer">
  Made with ❤️ by @shahabday<br>
  Email: <a href="mailto:shahabdaiani@gmail.com">shahabdaiani@gmail.com</a> · Instagram: <a href="https://instagram.com/shahabday" target="_blank" rel="noopener">@shahabday</a> · Website: <a href="https://shahabwrites.com" target="_blank" rel="noopener">shahabwrites.com</a>
</footer>
</div>

<script>
(function () {{
  document.querySelectorAll(".dropdown").forEach((dd) => {{
    const toggle = dd.querySelector(".dropdown-toggle");
    const menu = dd.querySelector(".dropdown-menu");
    if (!toggle || !menu) return;
    const position = () => {{
      const r = toggle.getBoundingClientRect();
      menu.style.left = Math.round(r.left) + "px";
      menu.style.top = Math.round(r.bottom + 4) + "px";
    }};
    dd.addEventListener("mouseenter", position);
    toggle.addEventListener("focus", position);
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, true);
  }});

  document.querySelectorAll(".topnav").forEach((nav) => {{
    const toggle = nav.querySelector(".nav-toggle");
    const menu = nav.querySelector(".mobile-menu");
    if (!toggle || !menu) return;
    toggle.addEventListener("click", () => {{
      const open = menu.classList.toggle("open");
      toggle.classList.toggle("open", open);
    }});
    menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {{
      menu.classList.remove("open");
      toggle.classList.remove("open");
    }}));
  }});
}})();
</script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({len(page)} bytes)")


if __name__ == "__main__":
    main()
