"""
Upgrade the shared nav to a mobile-friendly version (hamburger + slide-down
menu instead of horizontal-scroll) and add a footer, across the about/*.html
pages and the about/project.html page (both document-style layouts sharing
identical nav/footer markup, unlike the 9 fullscreen tool pages which get a
separate compact treatment in add_tool_footer.py).

Run from the repo root:
    python scripts/upgrade_nav_footer.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD_NAV_CSS = """  .topnav {
    position: sticky; top: 0; z-index: 100; background: rgba(15, 17, 21, 0.96);
    backdrop-filter: blur(6px); border-bottom: 1px solid var(--panel-border);
  }
  .topnav-inner {
    max-width: 1080px; margin: 0 auto; padding: 0 24px; height: 54px;
    display: flex; align-items: center; gap: 22px;
    overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none;
  }
  .topnav-inner::-webkit-scrollbar { display: none; }
  .topnav .brand { font-size: 14px; font-weight: 700; text-decoration: none; color: var(--text); white-space: nowrap; flex-shrink: 0; }
  .topnav .nav-links { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
  .topnav .nav-link { white-space: nowrap; }
  .dropdown-toggle { white-space: nowrap; }
  .topnav .nav-link { font-size: 13px; color: var(--text-dim); text-decoration: none; padding: 8px 10px; border-radius: 6px; }
  .topnav .nav-link:hover { color: var(--text); background: #1e222b; }
  .dropdown { position: relative; }
  .dropdown-toggle {
    font: inherit; font-size: 13px; color: var(--text-dim); background: none; border: none; cursor: pointer;
    padding: 8px 10px; border-radius: 6px; display: flex; align-items: center; gap: 4px;
  }
  .dropdown-toggle:hover, .dropdown:focus-within .dropdown-toggle { color: var(--text); background: #1e222b; }
  .dropdown-caret { font-size: 9px; transition: transform 0.15s; }
  .dropdown:hover .dropdown-caret, .dropdown:focus-within .dropdown-caret { transform: rotate(180deg); }
  .dropdown-menu {
    position: fixed; top: 0; left: 0; min-width: 170px;
    background: var(--panel); border: 1px solid var(--panel-border); border-radius: 8px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.5); padding: 6px; display: flex; flex-direction: column; gap: 2px;
    z-index: 500; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s;
  }
  .dropdown:hover .dropdown-menu, .dropdown:focus-within .dropdown-menu { opacity: 1; visibility: visible; pointer-events: auto; }
  .dropdown-menu a { font-size: 12.5px; color: var(--text-dim); text-decoration: none; padding: 7px 9px; border-radius: 6px; }
  .dropdown-menu a:hover { color: var(--text); background: #20242e; }"""

NEW_NAV_CSS = """  .topnav {
    position: sticky; top: 0; z-index: 100; background: rgba(15, 17, 21, 0.96);
    backdrop-filter: blur(6px); border-bottom: 1px solid var(--panel-border);
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
    z-index: 500; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s;
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
    display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 90;
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

  footer.site-footer { margin-top: 56px; padding-top: 20px; border-top: 1px solid var(--panel-border); font-size: 11.5px; color: var(--text-dim); line-height: 1.7; }
  footer.site-footer a { color: var(--text-dim); }
  footer.site-footer a:hover { color: var(--text); }"""


def nav_html(site_prefix, about_href):
    return f"""<nav class="topnav">
  <div class="topnav-inner">
    <a class="brand" href="{site_prefix}index.html">Germany in Maps</a>
    <div class="nav-links">
      <a class="nav-link" href="{site_prefix}tools.html">Home</a>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Political <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="{site_prefix}tools.html#political-map">Map visualizations</a>
          <a href="{site_prefix}tools.html#political-trend">Trend visualizations</a>
        </div>
      </div>
      <div class="dropdown">
        <button class="dropdown-toggle" type="button">Demographics &amp; Economy <span class="dropdown-caret">▾</span></button>
        <div class="dropdown-menu">
          <a href="{site_prefix}tools.html#demo-map">Map visualization</a>
          <a href="{site_prefix}tools.html#demo-trend">Trend visualization</a>
        </div>
      </div>
      <a class="nav-link" href="{about_href}">About</a>
    </div>
    <button class="nav-toggle" type="button" aria-label="Toggle menu"><span></span><span></span><span></span></button>
  </div>
  <div class="mobile-menu">
    <a href="{site_prefix}tools.html">Home</a>
    <div class="mobile-group-title">Political</div>
    <a href="{site_prefix}tools.html#political-map">Map visualizations</a>
    <a href="{site_prefix}tools.html#political-trend">Trend visualizations</a>
    <div class="mobile-group-title">Demographics &amp; Economy</div>
    <a href="{site_prefix}tools.html#demo-map">Map visualization</a>
    <a href="{site_prefix}tools.html#demo-trend">Trend visualization</a>
    <a href="{about_href}">About</a>
  </div>
</nav>"""


FOOTER_HTML = """<footer class="site-footer">
  Made with ❤️ by @shahabday<br>
  Email: <a href="mailto:shahabdaiani@gmail.com">shahabdaiani@gmail.com</a> · Instagram: <a href="https://instagram.com/shahabday" target="_blank" rel="noopener">@shahabday</a> · Website: <a href="https://shahabwrites.com" target="_blank" rel="noopener">shahabwrites.com</a>
</footer>"""

MOBILE_TOGGLE_JS = """  document.querySelectorAll(".topnav").forEach((nav) => {
    const toggle = nav.querySelector(".nav-toggle");
    const menu = nav.querySelector(".mobile-menu");
    if (!toggle || !menu) return;
    toggle.addEventListener("click", () => {
      const open = menu.classList.toggle("open");
      toggle.classList.toggle("open", open);
    });
    menu.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
      menu.classList.remove("open");
      toggle.classList.remove("open");
    }));
  });"""


def upgrade_about_page(path, old_nav_html_block):
    html = path.read_text(encoding="utf-8")
    assert OLD_NAV_CSS in html, f"{path}: old nav css not found"
    html = html.replace(OLD_NAV_CSS, NEW_NAV_CSS, 1)

    assert old_nav_html_block in html, f"{path}: old nav html not found"
    html = html.replace(old_nav_html_block, nav_html("../", "project.html"), 1)

    marker = '<a class="back-home" href="../tools.html">← Back to all tools</a>\n</div>'
    assert marker in html, f"{path}: back-home/wrap-close marker not found"
    html = html.replace(marker, marker.replace("\n</div>", f"\n{FOOTER_HTML}\n</div>"), 1)

    old_js_tail = """  window.addEventListener("scroll", position, true);
});
</script>"""
    new_js_tail = """  window.addEventListener("scroll", position, true);
  });

""" + MOBILE_TOGGLE_JS + """
})();
</script>"""
    # about pages' existing script isn't wrapped in an IIFE - normalize it into one
    old_full_js = """<script>
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
</script>"""
    new_full_js = """<script>
(function () {
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

""" + MOBILE_TOGGLE_JS + """
})();
</script>"""
    assert old_full_js in html, f"{path}: js block not found"
    html = html.replace(old_full_js, new_full_js, 1)

    path.write_text(html, encoding="utf-8")
    print(f"  upgraded {path}")


def main():
    about_dir = ROOT / "about"
    for name in ["political-map.html", "political-trend.html", "demographics-map.html", "demographics-trend.html"]:
        path = about_dir / name
        html = path.read_text(encoding="utf-8")
        # extract the current nav html block to use as the exact replace target
        start = html.index('<nav class="topnav">')
        end = html.index("</nav>", start) + len("</nav>")
        old_block = html[start:end]
        upgrade_about_page(path, old_block)


if __name__ == "__main__":
    main()
