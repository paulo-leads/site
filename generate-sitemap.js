const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const BASE_URL = "https://pauloleads.com.br";

const IGNORE = [
  ".git",
  ".github",
  "assets",
  "node_modules",
  "css",
  "js",
  "images"
];

const urls = [];

function getLastModified(target) {
  try {
    const date = execSync(
      `git log -1 --format=%cI -- "${target}"`
    )
      .toString()
      .trim();

    return date.split("T")[0];
  } catch {
    return new Date().toISOString().split("T")[0];
  }
}

function getPriority(slug) {
  if (slug === "/") return "1.0";

  if (slug.startsWith("/analises-mercado"))
    return "0.9";

  if (slug.startsWith("/cases-publicos"))
    return "0.8";

  return "0.7";
}

function walk(dir, relative = "") {
  const entries = fs.readdirSync(dir, {
    withFileTypes: true,
  });

  for (const entry of entries) {
    if (entry.name.startsWith(".")) continue;

    const full = path.join(dir, entry.name);

    const rel = relative
      ? `${relative}/${entry.name}`
      : entry.name;

    if (entry.isDirectory()) {
      if (IGNORE.includes(entry.name))
        continue;

      urls.push({
        slug: "/" + rel + "/",
        lastmod: getLastModified(full),
      });

      walk(full, rel);
    }
  }
}

walk(process.cwd());

urls.unshift({
  slug: "/",
  lastmod: getLastModified("."),
});

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

${urls
  .map(
    u => `
<url>
  <loc>${BASE_URL}${u.slug}</loc>
  <lastmod>${u.lastmod}</lastmod>
  <changefreq>weekly</changefreq>
  <priority>${getPriority(u.slug)}</priority>
</url>`
  )
  .join("\n")}

</urlset>
`;

fs.writeFileSync("sitemap.xml", xml);

console.log(
  `✅ Sitemap gerado (${urls.length} URLs)`
);
