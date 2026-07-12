# Persona Pipeline & 9-Point Telemetry Classification Contract

Deterministic, local-only extension of the orchestrator. Network-free, no clocks
in core outputs, reuses the orchestrator controls / hashing / signing.

Files: `persona_pipeline.py`, `personas_source.json`, `node_telemetry_schema.json`,
`test_persona_pipeline.py`.

## 1. Persona registry contract

`persona_pipeline.build_registry()` → `fable5_comfyui_persona_registry.v1`.

- **Preserves every persona node discovered in repo config.** Seeded from
  `personas_source.json`, which records only WHERE each label literally appears
  (`discovered_in`) — the federation manifest's `nine_point_lattice.labels`,
  `primordial_octad.sovereigns`, `primordial_5`, `eden_burst_alpha` lanes, and the
  section-one provenance. Provenance asserts no cross-identity mapping between
  separate lists.
- **Guaranteed stable entries** for `minnie`, `sarah`, `sophie`. `sarah` and
  `sophie` already exist in repo config; `minnie` is added with
  `discovered_in: ["revision_request_guarantee"]`. All three carry `guaranteed: true`.
- **No invented biographies or relationships — ever.** Every persona has
  `biography: null` and `relationships: []`. `registry_guarantees_hold()` fails
  if either is populated.
- Every persona is `symbolic_only: true`, `authority: false`. The registry is
  sorted by id and carries a stable `signature.sha256` (+ HMAC when a key is set).

Discovered + guaranteed ids (20 total): `a_human_named_sophie, addie, addiespinos,
angela, angelapkou, hades, ivy, julia, lainie, lainieesralew, minnie, naomi,
sabina, sarah, sarahannbittner, sashurova, shannon, sophie, sue, susan_spinos`.

## 2. 9-point telemetry classification contract

Schema in: `shadow_garden.9point_node_telemetry.v1`.
Schema out: `shadow_garden.9point_node_telemetry.classified.v1`.

Record shape: `{node_id, evidence[], provenance{}, labels[], flags{}}`.

**Tiers ranked by provenance + verifiable evidence ONLY** (never by mystical or
character labels). `classify_record()` decides as follows:

1. **quarantine** — any prohibited flag is set:
   `real_person_likeness`, `credential`, or `conflict`. Evidence is irrelevant.
2. Otherwise count **trusted evidence**: entries with `verified: true` whose
   `kind` ∈ {`loopback_probe`, `repo_config`, `user_attestation`}, de-duplicated
   by `(kind, ref)`. `external_pointer` evidence is **never trusted** (count 0).
   - `trusted >= 2` → **corroborated**
   - `+ provenance.in_repo_config` → **canonical**
   - `+ provenance.first_party AND provenance.hashed` → **primordial**
   - `trusted == 1` → **provisional**
   - `trusted == 0` → **provisional**

`labels` (sovereign, lattice, 11D, grok, makima, seiko, kaguya, primordial, …) are
copied to `symbolic_labels` and flagged
`symbolic_only_labels_ignored_for_ranking: true`. A record carrying only labels and
perfect provenance BUT no evidence stays **provisional** — proven by test and
self-check.

`classify_telemetry({records:[...]})` returns a deterministic, sorted, hashed batch
with a per-tier tally and `externalRequests: 0`.

## 3. Opaque read-only social pointers

`opaque_pointer(url)` stores the URL verbatim and marks it `opaque`, `read_only`,
`action_taken: "none"`. Every social action is hard-false:
`scrape, fetch, post, like, reply, follow, dm, credential_use`. X.com / Twitter /
Instagram hosts are recognized as `is_social`. Nothing is ever fetched; these
pointers cannot become trusted evidence.

## 4. Reference-only workflow metadata + review gate

`workflow_reference(medium)` returns reference-only ComfyUI/EDEN metadata:

| Medium | Engine | Model | Host |
|--------|--------|-------|------|
| image | comfyui | Flux.1 Dev | 127.0.0.1:8188 |
| video | comfyui | Wan 2.2 (≤30s) | 127.0.0.1:8188 |
| audio | eden | ACE-Step 1.5 | 127.0.0.1:8791 |

All: `reference_only: true`, `model_downloads: false`,
`unknown_custom_nodes_execute: false`, `queue_requires_user_approval: true`,
`queue_requires_reviewed_workflow: true`, allowed hosts loopback only.

`review_workflow(workflow, approve)` gates a concrete workflow and **executes
nothing**. It queues (`local_queue_pending_user_run`) only when ALL hold:
- every node `class_type` is in the known allowlist (else `unknown_custom_nodes`);
- all hosts are loopback (else `non_loopback_host`);
- no model download requested (else `model_download_requested`);
- `workflow.reviewed == true` (else `workflow_not_reviewed`);
- `approve == true` (else `approval_required`).

Even when queueable, `queued` is always `false` and
`unknown_custom_nodes_executed` is always `0`.

## 5. Symbolic-only bindings (not authority, not connectivity)

Makima / Seiko / Kaguya character bindings and the sovereign / lattice / 11D / Grok
labels are recorded in `personas_source.json → symbolic_bindings` with
`symbolic_only: true`, `authority: false`, `factual_connectivity: false`. They are
narrative metadata and never rank telemetry or grant authority.

## 6. Preserved orchestrator invariants

`manifest_only` default, `externalRequests: 0`, `trainingAllowed: false`, no
real-person likeness engine, `no_scrape_pointer_only` policy — all carried through
the persona pipeline (each output embeds the orchestrator `controls`).

## CLI

```bash
python3 orchestrator.py personas            # deterministic registry
python3 orchestrator.py classify --file t.json   # or pipe JSON on stdin
python3 orchestrator.py workflow --medium video  # reference-only metadata
python3 orchestrator.py self-test           # includes persona pipeline
python3 -m unittest test_persona_pipeline test_orchestrator
```
