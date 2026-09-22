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
