const https = require("https");

const payload = JSON.stringify({
  host: "pauloleads.com.br",
  key: "9f8c2a1f4ab1442ba123456789abcdef",
  keyLocation:
    "https://pauloleads.com.br/9f8c2a1f4ab1442ba123456789abcdef.txt",
  urlList: [
    "https://pauloleads.com.br/sitemap.xml"
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
  },
  res => {
    console.log(
      "IndexNow:",
      res.statusCode
    );
  }
);

req.write(payload);
req.end();
