# Recovery Helper / 復旧ヘルパー

A bilingual, local-only troubleshooting helper for people affected by ChatGPT
conversation loading, 429, blank-screen, WebSocket, or recovery-related errors.

日本語 / English の両方に対応しています。

## Properties

- 100% client-side
- no automatic ChatGPT/OpenAI API calls
- no fetch / WebSocket / EventSource / sendBeacon
- no cookies
- no localStorage / sessionStorage
- no analytics / telemetry
- no external JavaScript, images, or fonts
- official OpenAI troubleshooting is clearly separated from research-derived
  suggestions
- support memo generation happens locally in the browser
- language selection is not persisted

## Privacy boundary

The helper may contain fields for a conversation URL/ID or request/Ray ID
because those can be useful when preparing a support request.

Those fields stay in page memory only.

The helper does not submit them anywhere.

Do not paste passwords, authentication tokens, cookies, or other secrets.

## Official sources

The UI links directly to:

- https://status.openai.com/
- https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages
- https://help.openai.com/en/articles/6614161-how-can-i-contact-support
- Japanese equivalents of the Help Center pages

Official guidance takes precedence over research-derived suggestions.

## Research-derived additions

The helper adds conservative guidance motivated by this repository:

- avoid unnecessary repeated retries;
- collapse duplicate same-conversation recovery attempts;
- record cross-client differences rather than assuming canonical data loss;
- treat a single temporary success as provisional recovery;
- keep public raw authenticated HAR files out of GitHub/social media.

These are labeled as research-derived, not OpenAI policy.

## GitHub Pages

The static site is ready to publish from the repository's `/docs` directory.

Expected Pages path after Pages is enabled:

```text
https://hopeless-t.github.io/chatgpt-recovery-dynamics/
```

The root `docs/index.html` forwards to:

```text
/recovery-helper/
```

If GitHub Pages has not yet been enabled for this repository, the one-time
repository setting is:

```text
Settings
  -> Pages
  -> Build and deployment
  -> Deploy from a branch
  -> main
  -> /docs
```

The repository connector used to author this project does not expose the Pages
enable/disable setting, so the static site is committed and deployment-ready
without pretending that the site is already live.

## CI safety contract

The main validation workflow fails if the Helper gains any of these:

- `fetch(...)`
- `XMLHttpRequest`
- `WebSocket`
- `EventSource`
- `sendBeacon`
- local/session storage
- cookie access
- external scripts
- images/iframes/forms
- non-OpenAI external HTTP links

This keeps the Helper aligned with the repository's provider-friendly and
privacy-preserving design.
