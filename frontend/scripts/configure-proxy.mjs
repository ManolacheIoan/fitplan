// Fills the /api/* proxy rule in netlify.toml from Netlify environment variables.
// netlify.toml cannot read environment variables, but Netlify reads [[redirects]] only
// after the build command, so substituting placeholders here is supported
// (docs.netlify.com, "File-based configuration" > "Inject environment variable values").
//   BACKEND_URL   public https URL of the Render service
//   PROXY_SECRET  same value as PROXY_SECRET on Render (>= 32 characters); sent in the
//                 X-FitPlan-Proxy-Secret header so the backend can trust the visitor IP header
import { readFileSync, writeFileSync } from "node:fs";

if (process.env.NETLIFY !== "true") {
  console.warn("Not a Netlify build: leaving the proxy placeholders in netlify.toml.");
  process.exit(0);
}

const backend = process.env.BACKEND_URL?.replace(/\/+$/, "");
const secret = process.env.PROXY_SECRET ?? "";
if (!backend?.startsWith("https://")) {
  console.error("BACKEND_URL must be set to an https:// URL.");
  process.exit(1);
}
if (secret.length < 32 || /["\\\n]/.test(secret)) {
  console.error("PROXY_SECRET must be set: at least 32 characters, no quotes or backslashes.");
  process.exit(1);
}

const config = readFileSync("netlify.toml", "utf8");
const filled = config
  .replaceAll("BACKEND_URL_PLACEHOLDER", backend)
  .replaceAll("PROXY_SECRET_PLACEHOLDER", secret);
if (filled === config || filled.includes("_PLACEHOLDER")) {
  console.error("netlify.toml does not contain the expected proxy placeholders.");
  process.exit(1);
}
writeFileSync("netlify.toml", filled);
console.log(`Proxy: /api/* -> ${backend}/api/* (with proxy secret header)`);
