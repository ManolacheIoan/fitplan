// Writes out/_redirects so Netlify proxies /api/* to the backend (same-origin cookies).
// netlify.toml cannot read environment variables in redirect rules, hence this script.
import { writeFileSync } from "node:fs";

const backend = process.env.BACKEND_URL?.replace(/\/+$/, "");
if (!backend) {
  console.warn("BACKEND_URL is not set: skipping out/_redirects (local build).");
  process.exit(0);
}
if (!backend.startsWith("https://")) {
  console.error("BACKEND_URL must be an https:// URL.");
  process.exit(1);
}
writeFileSync("out/_redirects", `/api/*  ${backend}/api/:splat  200!\n`);
console.log(`Proxy: /api/* -> ${backend}/api/*`);
