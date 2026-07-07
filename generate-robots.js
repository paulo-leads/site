const fs = require("fs");

const robots = `
User-agent: *
Allow: /

Sitemap: https://pauloleads.com.br/sitemap.xml
`;

fs.writeFileSync("robots.txt", robots.trim());

console.log("✅ robots.txt criado");
