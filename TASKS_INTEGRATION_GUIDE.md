# Shadow Garden — 5 Pending Tasks Integration Guide

**Status:** All 4 modules enhanced to streamline the 5 pending human tasks.

## Quick Start

```bash
cd shadow-garden-launcher/helpers

# See overall status
python3 task_orchestrator.py status

# Get guidance for any specific task (1-5)
python3 task_orchestrator.py task 1
python3 task_orchestrator.py task 2 --quick

# Verify all tasks after completion
python3 task_orchestrator.py verify-all
```

---

## The 5 Pending Tasks

### 1. Rotate 4 Leaked API Keys (CRITICAL)
**Priority:** CRITICAL  
**Time:** ~20 min  
**Keys:** JWT, Stable Horde, ElevenLabs, Perplexity

**Why:** All 4 keys were exposed and must be rotated immediately.

**Guide:**
```bash
python3 key_rotation_helper.py checklist
# Follow the steps for each key
python3 key_rotation_helper.py verify
```

**What it does:**
- Lists rotation steps for each service
- Guides you to generate new keys
- Verifies that old keys have been cleared from your environment

---

### 2. Rekey HARPA (Fix 403 Error)
**Priority:** HIGH  
**Time:** ~5 min  
**Current Status:** ERROR (403 — invalid key)

**Guide:**
```bash
python3 connector_bridge_enhanced.py validate-harpa
# Follow the next_steps output
python3 connector_bridge_enhanced.py validate-harpa  # verify after rekey
```

**What it does:**
- Shows HARPA current status
- Provides step-by-step rekey instructions
- Verifies HARPA_API_KEY is set after rekey

---

### 3. Rebind Qdrant (Fix Transport Fail)
**Priority:** HIGH  
**Time:** ~10 min  
**Current Status:** ERROR (transport connection failed)

**Guide:**
```bash
python3 connector_bridge_enhanced.py validate-qdrant
# Follow the next_steps output
python3 connector_bridge_enhanced.py validate-qdrant  # verify after rebind
```

**What it does:**
- Shows Qdrant current configuration status
- Provides rebind instructions
- Verifies QDRANT_CLUSTER_URL and QDRANT_API_KEY are set

---

### 4. Launch ComfyUI + Re-run Bridge Probe
**Priority:** MEDIUM  
**Time:** ~5 min  
**Current Status:** DEGRADED (no listener on 127.0.0.1:8188)

**Guide:**
```bash
# 1. Launch ComfyUI app on your Mac
# 2. Then verify it's listening:
python3 connector_bridge_enhanced.py validate-comfyui
```

**What it does:**
- TCP-probes ComfyUI on 127.0.0.1:8188
- Shows "listening" when ComfyUI is running
- No restart needed; just open the app

---

### 5. Set Up Steamworks Partner Account
**Priority:** MEDIUM  
**Time:** ~30 min setup + 1-2 days for tax/banking

**Guide:**
```bash
python3 steamworks_integration.py checklist
# Follow the setup steps
python3 steamworks_integration.py readiness  # check progress
```

**What it does:**
- Shows 6-step Steamworks setup checklist
- Explains separate depot requirement (base + adult DLC)
- Provides configuration templates
- Tracks readiness status

---

## Integration Architecture

### Enhanced Modules (All in `helpers/`)

| Module | Purpose | Commands |
|---|---|---|
| `connector_bridge_enhanced.py` | Validates HARPA, Qdrant, ComfyUI status | `validate-harpa`, `validate-qdrant`, `validate-comfyui` |
| `key_rotation_helper.py` | Guides key rotation for 4 leaked keys | `checklist`, `verify` |
| `steamworks_integration.py` | Steamworks Partner account scaffolding | `checklist`, `config-template`, `readiness` |
| `task_orchestrator.py` | Master workflow for all 5 tasks | `status`, `task <N>`, `verify-all` |

### Original Modules (Still in `monitors/`)

- `connector_bridge.py` — Base credential-free bridge (unchanged)
- **NEW:** `connector_bridge_enhanced.py` — Adds task-specific validation

### Original Modules (Scratchpad — Copied to Repos)

- `fable5_universe.py` — Deterministic game engine
- `fable5_agent.py` — Seamless loopback client
- `shadow_garden_packet.py` — Unified manifest

---

## Workflow Example

**Day 1: Immediate Actions**

```bash
# 1. Check overall status
cd shadow-garden-launcher/helpers
python3 task_orchestrator.py status

# Output:
# {
#   "tasks": [
#     { "id": 1, "title": "Rotate 4 Leaked API Keys", "status": "PENDING" },
#     { "id": 2, "title": "Rekey HARPA (Fix 403 Error)", "status": "PENDING" },
#     ...
#   ],
#   "summary": { "total_tasks": 5, "completed": 0, "pending": 5, "progress_pct": 0 }
# }

# 2. Start with Task 1 (CRITICAL)
python3 task_orchestrator.py task 1

# 3. Follow the checklist, generate new keys for each service
# 4. Export to environment: export JWT_TOKEN=<new_key>, etc.

# 5. Verify rotation
python3 key_rotation_helper.py verify

# Output shows all 4 keys cleared from environment ✓
```

**Day 2: HARPA & Qdrant**

```bash
# Task 2: HARPA
python3 task_orchestrator.py task 2
# → Shows HARPA_API_KEY not set
# → Follow steps to regenerate in HARPA AUTOMATE tab
# → Export: export HARPA_API_KEY=<new_key>
python3 connector_bridge_enhanced.py validate-harpa
# ✓ HARPA_API_KEY set in environment

# Task 3: Qdrant
python3 task_orchestrator.py task 3
# → Shows QDRANT_CLUSTER_URL and QDRANT_API_KEY not set
# → Follow steps to get new cluster config from Qdrant Cloud
# → Export: export QDRANT_CLUSTER_URL=<url> QDRANT_API_KEY=<key>
python3 connector_bridge_enhanced.py validate-qdrant
# ✓ Qdrant cluster configured
```

**Day 3: ComfyUI & Steamworks**

```bash
# Task 4: ComfyUI
python3 task_orchestrator.py task 4
# → Shows ComfyUI not listening on 127.0.0.1:8188
# → Open ComfyUI app on your Mac
python3 connector_bridge_enhanced.py validate-comfyui
# ✓ ComfyUI is listening on 127.0.0.1:8188

# Task 5: Steamworks
python3 task_orchestrator.py task 5
# → Shows Steamworks prerequisites not met
# → Follow checklist to create Partner account
# → Set up tax/banking info
# → Pay $100 deposit
python3 steamworks_integration.py readiness
# ✓ Shows progress toward readiness
```

**Final Verification:**

```bash
python3 task_orchestrator.py verify-all
# {
#   "all_tasks_ok": true,
#   "verifications": {
#     "1_key_rotation": { "all_keys_rotated": true },
#     "2_harpa": { "status": "ok" },
#     "3_qdrant": { "status": "ok" },
#     "4_comfyui": { "status": "ok" },
#     "5_steamworks": { "overall_ready": true }
#   }
# }
```

---

## Key Features

✅ **Non-blocking:** Each task is independent; do them in any order  
✅ **Guided:** Step-by-step instructions built into each helper  
✅ **Verifiable:** Each task has a verification command  
✅ **No credentials stored:** Only validates env vars; no secrets in code  
✅ **Deterministic:** Same output for same inputs (timestamps injected)  
✅ **Content-neutral:** Scaffolding only; no adult content in code  

---

## Environment Variables to Set

As you complete each task, export these to your shell:

```bash
# Task 1: Rotated keys
export JWT_TOKEN=<new_key>
export STABLE_HORDE_API_KEY=<new_key>
export ELEVENLABS_API_KEY=<new_key>
export PERPLEXITY_API_KEY=<new_key>

# Task 2: HARPA
export HARPA_API_KEY=<new_key>

# Task 3: Qdrant
export QDRANT_CLUSTER_URL=<cluster_url>
export QDRANT_API_KEY=<new_key>

# Task 5: Steamworks
export STEAMWORKS_PARTNER_ID=<partner_id>
export STEAMWORKS_APP_ID=<app_id>
export STEAMWORKS_BASE_BUILD_PATH=<path>
export STEAMWORKS_ADULT_BUILD_PATH=<path>
```

---

## Next Steps After Tasks Complete

Once all 5 tasks are complete:

1. **Update shadow_garden_packet.py** to reflect new status
2. **Run full connector_bridge.py** to verify all services
3. **Update master_sync.sh** to use new keys
4. **Begin Steamworks submission** (base game → adult DLC after approval)

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'connector_bridge_enhanced'"**
→ Make sure you're in the `shadow-garden-launcher/helpers/` directory when running `task_orchestrator.py`

**"HARPA_API_KEY not set in environment"**
→ You haven't exported the key yet. Complete the HARPA rekey steps and run:
```bash
export HARPA_API_KEY=<new_key>
```

**"ComfyUI not listening"**
→ Open the ComfyUI app on your Mac. It must be actively running on port 8188.

---

## Summary

All 4 modules are now enhanced with:
- ✅ Credential-free validation
- ✅ Step-by-step guidance for each task
- ✅ Verification hooks to test completion
- ✅ Unified orchestrator for progress tracking

You can now execute all 5 pending tasks in a streamlined, guided workflow.
