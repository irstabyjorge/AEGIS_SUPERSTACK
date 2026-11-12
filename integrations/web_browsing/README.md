# AEGIS Web Browsing Connector

**Status:** proposed reference adapter; not installed, executed, or runtime-verified.

## Purpose

Provide an explicit, auditable web-research capability for AEGIS/PETS using the OpenAI Responses API hosted `web_search` tool. The hosted tool can search current public sources, open pages when supported by the selected model, and return source/citation metadata.

This connector is separate from PETS presentation and the AEGIS core. It does not grant access to private accounts, authenticated pages, local devices, or files.

## Capability boundary

- Search public web content and return answer text plus source metadata.
- Accept an optional domain allowlist (up to 100 domains).
- Allow live access to be disabled for cache-only operation.
- Preserve source URLs and titles for downstream citation rendering.
- No automatic form submission, account login, purchases, messaging, file upload, downloads, or browser automation.
- No automatic transmission of local files, private records, credentials, or personal identifiers.
- Treat all page content as untrusted input. Page instructions never override AEGIS policy or the user's request.

## Configuration

Set `OPENAI_API_KEY` in the runtime's secret manager or process environment. Never commit the key to Git, logs, reports, or client-side bundles.

Optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `AEGIS_WEB_MODEL` | `gpt-6-astra` | Responses API model supporting hosted web search |
| `AEGIS_WEB_SEARCH_CONTEXT` | `medium` | `low`, `medium`, or `high` |
| `AEGIS_WEB_EXTERNAL_ACCESS` | `true` | `false` disables live external access |

## Minimal Node.js adapter

Requires Node.js 18+ for built-in `fetch`. It intentionally has no third-party package dependency.

```js
// integrations/web_browsing/web_search.mjs
const API_URL = "https://api.openai.com/v1/responses";

function readBoolean(value, fallback) {
  if (value == null || value === "") return fallback;
  return value.toLowerCase() === "true";
}

export async function searchWeb({
  query,
  allowedDomains = [],
  externalWebAccess = readBoolean(
    process.env.AEGIS_WEB_EXTERNAL_ACCESS,
    true
  ),
  contextSize = process.env.AEGIS_WEB_SEARCH_CONTEXT || "medium",
} = {}) {
  if (typeof query !== "string" || !query.trim()) {
    throw new TypeError("query must be a non-empty string");
  }
  if (query.length > 8000) {
    throw new RangeError("query exceeds the 8000-character limit");
  }
  if (!Array.isArray(allowedDomains) || allowedDomains.length > 100) {
    throw new TypeError("allowedDomains must be an array of at most 100 domains");
  }
  for (const domain of allowedDomains) {
    if (
      typeof domain !== "string" ||
      !/^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i.test(domain)
    ) {
      throw new TypeError(`invalid allowlisted domain: ${String(domain)}`);
    }
  }
  if (!["low", "medium", "high"].includes(contextSize)) {
    throw new TypeError("contextSize must be low, medium, or high");
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY is not configured");

  const webTool = {
    type: "web_search",
    external_web_access: Boolean(externalWebAccess),
    search_context_size: contextSize,
  };
  if (allowedDomains.length) {
    webTool.filters = { allowed_domains: [...new Set(allowedDomains)] };
  }

  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: process.env.AEGIS_WEB_MODEL || "gpt-6-astra",
      tools: [webTool],
      tool_choice: "auto",
      include: ["web_search_call.action.sources"],
      input: query.trim(),
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.error?.message || `Responses API request failed: ${response.status}`;
    throw new Error(message);
  }

  const sources = [];
  for (const item of payload.output || []) {
    if (item.type !== "web_search_call") continue;
    for (const source of item.action?.sources || []) {
      if (source.url) {
        sources.push({
          title: source.title || "",
          url: source.url,
          domain: source.domain || "",
        });
      }
    }
  }

  return {
    text: payload.output_text || "",
    sources: [...new Map(sources.map((s) => [s.url, s])).values()],
    responseId: payload.id || null,
    status: payload.status || "unknown",
  };
}
```

## PETS / AEGIS integration contract

Suggested call flow:

1. User explicitly requests a web search or asks to open a public URL.
2. PETS passes only the user's query and any user-selected domain restrictions.
3. The connector returns answer text and source metadata.
4. AEGIS validates and normalizes URLs before rendering links; source text remains untrusted.
5. PETS displays citations and a retrieval timestamp where available.
6. Store only the minimum research record needed: query, source URLs/titles, retrieval time, response ID, and integrity hash. Do not store API keys or unrelated browsing history.

## URL-opening policy

The hosted web-search tool may open pages as part of a search workflow when supported by the selected model. If a separate direct-URL fetcher is added later, it must reject non-HTTP(S) schemes, loopback/private/link-local IP destinations, localhost aliases, embedded credentials, and redirect chains into private address space. Apply response-size and timeout limits. Do not fetch arbitrary local-network or device endpoints.

## Validation gates before production

- Add unit tests for input validation, allowlist handling, API error handling, source deduplication, and missing credentials.
- Add mocked-response tests; no live API call is needed for unit tests.
- Verify citations render as clickable source links in the PETS UI.
- Verify live access can be disabled.
- Verify secrets never appear in logs, browser bundles, or repository history.
- Run a security review for prompt injection, SSRF, redirect handling, data minimization, and retention.
- Only then mark the adapter `tested` or `verified`. Until then its status remains `proposed`.

## Official references

- OpenAI web search guide: https://developers.openai.com/api/docs/guides/tools-web-search
- Responses API create reference: https://developers.openai.com/api/reference/resources/responses/methods/create


## Cross-browser ChatGPT conversation launcher

Browser-specific WebExtensions are in:
- `extension/chromium/` — Chrome and Microsoft Edge (Manifest V3).
- `extension/firefox/` — Firefox (Manifest V3).

### Conversation behavior

- Paste a full `https://chatgpt.com/c/<conversation-id>` URL into the toolbar popup and choose **Open in this browser**.
- When the active tab is already a ChatGPT conversation, the popup pre-fills its URL.
- Right-click a ChatGPT conversation link and choose **Open ChatGPT conversation**.
- The extension opens the exact conversation URL in a new tab. It does not export, copy, scrape, or transfer conversation content.
- To see the same history, sign into the same ChatGPT account in each browser. Each browser keeps its own login session; this extension does not copy cookies or credentials between profiles.

### Install for local testing

**Chrome**
1. Clone/download this repository and extract it.
2. Visit `chrome://extensions`.
3. Enable **Developer mode**.
4. Select **Load unpacked** and choose the `integrations/web_browsing/extension/chromium/` folder.

**Microsoft Edge**
1. Visit `edge://extensions`.
2. Enable **Developer mode**.
3. Select **Load unpacked** and choose the same `extension/chromium/` folder.

**Firefox**
1. Visit `about:debugging#/runtime/this-firefox`.
2. Select **This Firefox** → **Load Temporary Add-on**.
3. Choose `integrations/web_browsing/extension/firefox/manifest.json`.
4. Firefox temporary add-ons may need to be loaded again after a browser restart. Signed distribution is required for ordinary persistent installation.

### Security and status

The extension requests only active-tab and context-menu permissions. It does not request access to all websites, cookies, browsing history, or page contents. It has not been installed or tested in the user's browser profiles; the repository source is a local-test build, not a deployed browser extension. No browser can be remotely modified by this repository integration.
