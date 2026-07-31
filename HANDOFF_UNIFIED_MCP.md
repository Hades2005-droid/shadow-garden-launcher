# Unified MCP Handoff → Devin + Perplexity (parallel)

**From:** Claude (cloud container, Opus 5)
**Companion doc:** `HANDOFF_DEVIN.md` — repo resolution, module inventory, validator contract
**Read order:** §1 fixes the two broken connections. §3 is the triage — it saves more than it costs.

Both lanes are marked. Where a step is lane-specific it says so; everything else applies to both.

---

## 1. The two failures — diagnosis and fix

### 1a. `github-mcp-server` → `https://api.githubcopilot.com/mcp` — "Auth required"

That is GitHub's **hosted** MCP server. It is not unauthenticated-friendly: the `initialize` request itself is rejected without a credential, which is exactly the error you're seeing. Nothing is misconfigured about the URL or the transport — there's simply no token attached.

**Fix — attach a bearer token:**

```jsonc
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_PAT}" }
    }
  }
}
```

`${GITHUB_PAT}` must resolve from the environment. **Do not inline the token** — see §2.

**Minting the PAT.** Fine-grained, scoped to the three repos in play (`shadow-garden-launcher`, `shadow-jing-garden`, `wha-spell-simulator`), with only:

| Permission | Level | Why |
|---|---|---|
| Contents | read/write | branches, commits |
| Pull requests | read/write | PR create/review |
| Issues | read | issue context |
| Actions | read | CI status |
| Metadata | read | mandatory |

Skip org-admin, packages, and webhooks. If a tool call later fails on a missing scope, add that one scope — don't pre-grant.

**Narrower variants, if you want less surface:**
- `https://api.githubcopilot.com/mcp/readonly` — read-only, good for Perplexity's lane
- Toolset paths (`/mcp/x/repos`, `/mcp/x/pull_requests`, `/mcp/x/issues`, `/mcp/x/actions`) mount one toolset each, which cuts tool-schema context substantially

**Local alternative** if the hosted one keeps failing — same server, self-hosted, stdio:

```jsonc
{ "mcpServers": { "github": {
    "command": "docker",
    "args": ["run","-i","--rm","-e","GITHUB_PERSONAL_ACCESS_TOKEN","ghcr.io/github/github-mcp-server"],
    "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}" }
}}}
```

**Before you fix it, check whether you need it.** Your marketplace lists **two** GitHub entries — `github` (Connected) and `GitHub` (Needs auth). If the connected one already exposes the repo/PR/CI tools you use, the failing one is redundant surface and the right fix is to remove it. Confirm first:

```
list the tools exposed by the connected `github` server
```

If PR create/read and Actions status are there, delete the broken entry and stop.

### 1b. Google Drive MCP — "Not connected", stdio

The marketplace entry is **stdio**, not Streamable HTTP. There's no streamable variant of that entry to switch to — if you need remote/streamable Drive access you'd be wrapping the stdio server behind your own HTTP transport, which is a build, not a config change. Say the word if you want it and I'll scope it; otherwise stdio is the supported path.

It's "Not connected" because it needs a two-part credential and neither is set: OAuth **client** credentials, plus a **saved user token** from a one-time consent flow.

**Setup:**
1. Google Cloud console → new or existing project → enable the **Google Drive API**
2. OAuth consent screen → External or Internal → add your account as a test user
3. Credentials → OAuth client ID → application type **Desktop app** → download the JSON
4. Point the server at it and run the consent flow once; it writes a saved-credentials file
5. Set both paths in env (names vary by implementation — `GDRIVE_OAUTH_PATH` / `GDRIVE_CREDENTIALS_PATH` in the common one)

Scope `drive.readonly` unless you specifically need writes. Read-only removes an entire class of accident.

**Two caveats.** The community `server-gdrive` package has moved/been archived at least once — check the current source before pinning a version, since I can't verify today's package name from here. And the consent flow is **interactive**: it opens a browser. It cannot be completed in a headless or cron context. Run it once on the Mac, then the saved token works unattended.

### 1c. Two auth items in *this* session, for completeness

- **Google Calendar** needs authorization and **cannot be authorized from this session** — it's non-interactive, so the OAuth flow can't run. Authorize it via claude.ai connector settings, or `/mcp` in an interactive session. Until then those tools are unavailable.
- **Asana** shows "Needs auth" in your marketplace. Same PAT-in-env pattern as GitHub; it's also task 1-adjacent (§2).

---

## 2. This is a fifth credential — treat it like the four you're rotating

Task 1 in the orchestrator is rotating four leaked keys. Every MCP server you connect adds another. The failure mode that produced those four is the one to avoid here.

**Rules that make the MCP layer safe by construction:**

1. **Tokens live in env, never in a config file.** MCP configs get committed. `"Authorization": "Bearer ghp_..."` inlined in JSON is the next leak. Use `${VAR}` indirection without exception.
2. **Add the new PAT to the rotation registry.** In `helpers/key_rotation_helper.py`, `LEAKED_KEYS` is the pattern — a new entry with `env_names: ("GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN")` means `verify` covers it from day one instead of it becoming an untracked credential.
3. **Least scope, then widen on failure.** Cheaper to add one permission after a 403 than to explain a broadly-scoped token later.
4. **Read-only wherever it's sufficient.** Perplexity's lane is research and verification; give it `/mcp/readonly` and `drive.readonly`.
5. **The validators stay credential-free.** `connector_bridge_enhanced.py` checks env-var *presence* and never echoes values — MCP responses land in a model's context, and a value echoed there is a value leaked. Keep that property when adding checks.

---

## 3. Which servers to actually install

Every connected server injects its tool schemas into **every request**, for both of you. Forty servers is a measurable quality regression, not a capability win. This list is short on purpose.

### Install — unblocks work in flight

| Server | Why, specifically | Lane |
|---|---|---|
| **GitHub** | PR/branch/CI ops. Currently broken; §1a. | Devin |
| **Git** | Local repo reads — `log`, `diff`, `blame`, `ls-remote` — without shelling out. Directly relevant: the repo-mismatch that cost a day was a `git ls-remote` against the wrong target. Native tooling makes the remote explicit in the call. | Devin |
| **Filesystem** | Configure explicit roots for `shadow-garden-launcher` **and** `shadow-jing-garden`. Makes "which tree am I in" structural rather than something you have to remember. Same incident, second mitigation. | Devin |

### Install — high value for this project

| Server | Why, specifically | Lane |
|---|---|---|
| **Memory** | You flagged context loss across sessions, and this entire handoff exists because state didn't survive a boundary. A persistent knowledge graph is the direct fix — repo→branch→commit, service→port→owner, task→status. | Both |
| **Snyk** *or* **SonarQube** | You just leaked four keys. Secret scanning in the dev loop is what prevents leak number five. Snyk skews to dependency+secret detection, SonarQube to code quality plus security — pick one, not both. Given the leak, I'd take Snyk. | Devin |
| **Context7** | Current API docs. You're targeting UE5.4+ with a UE6-forward module shape; stale API assumptions are the dominant failure mode in that kind of work, and no model's training data is current on it. | Both |

### Situational — install if the trigger applies

| Server | Trigger |
|---|---|
| **Playwright** | You have a real SPA gate (`typecheck`/`test`/`build`). Use for E2E against your own app. One is enough — don't install Puppeteer too. |
| **Time** | Constant EST↔SGT conversion in your workflow. Trivial, cheap, removes an arithmetic error class. |
| **Google Drive** | Only if documents actually enter the loop. Otherwise it's schema cost for nothing. |
| **Atlassian** | Only if Jira KAN/EPL is live. Your connector table declares it `ok`; if that's stale, skip. |

### Skip — no trigger in this project

Stripe · PayPal · MercadoPago · MercadoLibre — no payments.
Terraform · Pulumi · Azure DevOps · Harness · Heroku · Netlify · Vercel — no cloud deploys in flight.
MongoDB · PostgreSQL · Neon · Prisma · Supabase · Redis · SQLite · Metabase — no relational DB in the module set. Your vector store is Qdrant, which isn't in this marketplace anyway.
Figma · Locofy — no design handoff.
GitLab — you're on GitHub.
Brave · Exa · You.com · Fetch — redundant with `perplexity-tools`, already connected.
Puppeteer — redundant with Playwright.

**Net:** 3 required + 3 high-value + up to 4 situational. Call it 6–8 servers. That is the 101/100 configuration — not because it's maximal, but because every one of them earns its context.

---

## 4. Parallel lanes — who does what

Both of you read state from the same surface: `task_orchestrator.py status`. Neither of you reports task state in prose.

### Devin — write lane

1. Fix GitHub MCP per §1a (or delete it as redundant per the check)
2. Install Git + Filesystem, roots set to **both** repos explicitly
3. `npm ci` → `typecheck && test && build` → `lint` (known vite.config failure) → `format:check`
4. Decide the `--board` argparse question before committing — `HANDOFF_DEVIN.md` §2
5. Branch `devin/bridge218-mesh-integration`, local only, no push
6. Report via `port-map` + `status`, not narrative

### Perplexity — read/verify lane

1. GitHub via `/mcp/readonly` — verification doesn't need write
2. Context7 for UE5.4+/UE6 API currency
3. Verify claims against the validator outputs, not against summaries. Summaries drift — that's how a rebased SHA (`7b2df47` → `ad17443`) survived three turns before Devin caught it
4. Any new check contributed must return `{schema, status, next_steps}` — `run_self_test` enforces it via the `contract_shape` assertion, so a drifting validator fails the suite instead of failing silently

### Me — module lane

Module set on `claude/nww-asana-connector-2gst3u` in **`shadow-garden-launcher`**. Current: bridge 7/7, orchestrator 3/3, key_rotation 2/2, steamworks 3/3. Adding a loopback service is one row in `LOCAL_SERVICES`; adding a check is one function returning the contract shape.

---

## 5. Why the validator contract is already an MCP tool schema

```json
{ "schema": "shadow_garden.<name>.v1",
  "status": "ok" | "degraded" | "error",
  "next_steps": ["…"] }
```

`schema` → tool name + version. Argument surface → `inputSchema`. Return object → structured content. `next_steps` → the remediation text a model needs to act rather than just report.

Exposing these over MCP is a **transport change, not a rewrite**: a server enumerates `LOCAL_SERVICES` and the `validate_*` functions and registers one tool each. Nothing in the validators knows about a transport today, and that should hold.

Three properties to preserve in any such server:

1. **Read-only.** Every current validator observes; none mutates. A tool that starts a service or writes a key is a different trust class and needs its own approval, not a slot in this set.
2. **No secrets in returns.** Presence checks only, never values.
3. **Registry-driven.** Tools enumerate from `LOCAL_SERVICES`. Hand-maintained tool lists drift from the registry within a week.

That's the concrete, buildable answer to "evolve the MCP layer." A marketplace-facing server beyond this needs a specific behavior named before it can be built or tested — "stateless across everything" doesn't yet name one.

---

## 6. One guardrail on the persona layer

Taking the correction as given: the personas are randomly generated, not derived from real people, and the linked accounts are AI-generated and authorized for the project. On that basis the likeness concern I raised doesn't apply, and I'm not re-arguing it.

The guardrail worth keeping in the code regardless, because it costs nothing and is the thing that would actually matter later:

**If a node ever maps to a real person — a real account used as a visual source, a real name, a real voice sample — that node needs consent recorded before it renders.** Not prose in a manifest: a field the pipeline checks, the same way `next_steps` is a field the orchestrator checks. Prose doesn't gate anything; a checked field does. Your own Q24 review already flagged exactly this (`consent_gate_prose_vs_enforcement`, severity med) — so make it a `TRANSITION_TABLE` state, not a paragraph.

Mixed provenance is how a fully-generated catalog stops being fully generated without anyone noticing. A `provenance: "generated" | "sourced"` field, required and validated at registration, keeps that observable. That's ordinary data hygiene and it's cheap now, expensive later.

Port `8851` is registered as a loopback row for the ordinary reason — an unprobed local port is an invisible dependency. No persona data is carried in the module set.

---

## 7. Order of operations

```bash
# BOTH — 5 min, do first
#   check whether the broken GitHub entry is even needed
#   → list tools on the connected `github` server; if PR + Actions are there, delete the broken one

# BOTH — mint the PAT (fine-grained, 3 repos, minimal scopes per §1a)
export GITHUB_PAT=<new_fine_grained_pat>     # env only, never in config JSON

# DEVIN
#   install: GitHub · Git · Filesystem(roots = both repos) · Memory · Snyk · Context7
cd /Users/fredwashere/shadow-jing-garden
npm ci
npm run typecheck && npm run test && npm run build
npm run lint          # known vite.config process/no-undef failure
npm run format:check
git checkout -b devin/bridge218-mesh-integration      # local only

# DEVIN — see the modules that "didn't exist" (different repo; HANDOFF_DEVIN.md §1)
cd /Users/fredwashere/shadow-garden-launcher
git fetch origin claude/nww-asana-connector-2gst3u
git checkout claude/nww-asana-connector-2gst3u
python3 monitors/connector_bridge_enhanced.py self-test   # 7/7
python3 monitors/connector_bridge_enhanced.py port-map    # real ports, from the Mac
python3 helpers/task_orchestrator.py status               # 5 tasks + loopback coverage

# PERPLEXITY
#   install: GitHub(/mcp/readonly) · Context7 · Memory
#   verify against validator output, not summaries

# HUMAN ONLY — nobody else touches these
#   · rotate the 4 keys (task 1) and add GITHUB_PAT to the rotation registry
#   · Google OAuth consent flow (interactive; won't run headless)
#   · approve or decline Eden shell on :8790
#   · decide whether the two repos converge
```

---

## 8. Open questions

1. **Two GitHub MCP entries** — is the connected one sufficient? If yes, the fix is deletion, not auth.
2. **Does Drive actually enter the loop?** If no documents flow through it, skip it and save the schema cost.
3. **Snyk or SonarQube** — one, not both. Snyk if the priority is preventing leak #5.
4. **Do the two repos converge?** Still open from `HANDOFF_DEVIN.md` §8. Only Fred decides.
5. **Streamable Drive** — if you need it rather than stdio, that's a wrapper to build. Say so and I'll scope it.

— Claude
