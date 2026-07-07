const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");
const https = require("https");

const DOMAIN = "https://pauloleads.com.br";

const IGNORE = [
  ".git",
  ".github",
  "assets",
  "node_modules"
];

const INDEXNOW_KEY =
  "9f8c2a1f4ab1442ba123456789abcdef";

const URLS = [];

function lastmod(target) {
  try {
    return execSync(
      `git log -1 --format=%cI "${target}"`
    )
      .toString()
      .trim()
      .split("T")[0];
  } catch {
    return new Date().toISOString().split("T")[0];
  }
}

function priority(slug) {
  if (slug === "/") return "1.0";
  if (slug.includes("analises-mercado")) return "0.9";
  return "0.8";
}

function scan(dir, rel = "") {
  const files = fs.readdirSync(dir, {
    withFileTypes: true,
  });

  for (const file of files) {
    if (file.name.startsWith(".")) continue;

    const full = path.join(dir, file.name);

    const relative = rel
      ? `${rel}/${file.name}`
      : file.name;

    if (file.isDirectory()) {
      if (IGNORE.includes(file.name)) continue;

      URLS.push({
        slug: "/" + relative + "/",
        lastmod: lastmod(full),
      });

      scan(full, relative);
    }
  }
}

scan(process.cwd());

URLS.unshift({
  slug: "/",
  lastmod: lastmod("."),
});

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${URLS.map(
  u => `
<url>
<loc>${DOMAIN}${u.slug}</loc>
<lastmod>${u.lastmod}</lastmod>
<changefreq>weekly</changefreq>
<priority>${priority(u.slug)}</priority>
</url>`
).join("")}
</urlset>`;

fs.writeFileSync("sitemap.xml", sitemap);

const robots = `
User-agent: *
Allow: /

Sitemap: ${DOMAIN}/sitemap.xml
`;

fs.writeFileSync(
  "robots.txt",
  robots.trim()
);

fs.writeFileSync(
  `${INDEXNOW_KEY}.txt`,
  INDEXNOW_KEY
);

console.log(
  `Sitemap: ${URLS.length} URLs`
);

const payload = JSON.stringify({
  host: "pauloleads.com.br",
  key: INDEXNOW_KEY,
  keyLocation:
    `${DOMAIN}/${INDEXNOW_KEY}.txt`,
  urlList: [
    `${DOMAIN}/sitemap.xml`
  ]
});

const req = https.request(
  "https://api.indexnow.org/indexnow",
  {
    method: "POST",
    headers: {
      "Content-Type":
        "application/json",
      "Content-Length":
        payload.length
    }
  }
);

req.write(payload);
req.end();

console.log("IndexNow enviado");
