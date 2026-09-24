// Serves the static site (assets binding) under the /germany path prefix.
// Requests arrive as /germany/... because the Worker route on shahabwrites.com
// is scoped to that path, but the built assets are rooted at /, so the prefix
// has to be stripped before handing off to ASSETS, and any redirect the assets
// handler issues (e.g. /germany/map -> .../map/) needs the prefix added back.
const PREFIX = "/germany";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname !== PREFIX && !url.pathname.startsWith(PREFIX + "/")) {
      return new Response("Not found", { status: 404 });
    }

    // Bare "/germany" (no trailing slash) must redirect to "/germany/" first:
    // otherwise the browser treats "germany" as a file, and every relative
    // link on the page (e.g. href="map/") resolves against "/" instead of
    // "/germany/", sending visitors to the wrong URL.
    if (url.pathname === PREFIX) {
      url.pathname = PREFIX + "/";
      return Response.redirect(url.toString(), 301);
    }

    url.pathname = url.pathname.slice(PREFIX.length) || "/";

    // The asset binding runs with html_handling:"none" (exact-match only),
    // because its default "auto-trailing-slash" mode redirects /index.html
    // straight to "/" - which collided with wanting "/" to serve a *different*
    // file (home.html) and made the tool index unreachable. With that default
    // off, directory-index resolution has to happen here instead:
    //  - a bare directory path ("/map-all-elections", no trailing slash) is
    //    redirected to add the slash, same as the old default did;
    //  - a path ending in "/" gets its index document appended - home.html at
    //    the root, index.html (the actual per-folder file) everywhere else.
    if (!url.pathname.endsWith("/") && !/\.[a-zA-Z0-9]+$/.test(url.pathname)) {
      const redirectUrl = new URL(request.url);
      redirectUrl.pathname = PREFIX + url.pathname + "/";
      return Response.redirect(redirectUrl.toString(), 301);
    }
    if (url.pathname.endsWith("/")) {
      url.pathname += url.pathname === "/" ? "home.html" : "index.html";
    }

    const assetResponse = await env.ASSETS.fetch(new Request(url.toString(), request));

    const location = assetResponse.headers.get("Location");
    if (location) {
      const loc = new URL(location, url);
      if (!loc.pathname.startsWith(PREFIX)) {
        loc.pathname = PREFIX + loc.pathname;
        const headers = new Headers(assetResponse.headers);
        headers.set("Location", loc.toString());
        return new Response(assetResponse.body, { status: assetResponse.status, headers });
      }
    }

    return assetResponse;
  },
};
