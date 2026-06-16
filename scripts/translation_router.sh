#!/bin/zsh
# Nuance-aware Grok translation router. Reads xAI credentials from local env only.
set -euo pipefail
SCRIPT_DIR="${0:A:h}"
source "$SCRIPT_DIR/env_guard.sh"
TARGET_LANG="${1:-es}"
INPUT_TEXT="${2:-}"
if [[ -z "$INPUT_TEXT" && ! -t 0 ]]; then
  INPUT_TEXT=$(cat)
fi
if [[ -z "${INPUT_TEXT//[[:space:]]/}" ]]; then
  echo "No input text provided." >&2
  exit 65
fi
MODEL="${GROK_TRANSLATION_MODEL:-grok-2}"
SYSTEM_PROMPT="You are a precision translator embedded in Fred's Mac system. Translate into ${TARGET_LANG} while preserving register, idioms, cultural nuance, and regional variants. For Spanish flag MX/ES/AR differences; Portuguese BR/PT; Chinese Simplified/Traditional plus pinyin where helpful; Japanese keigo level; Korean speech level; Thai politeness particles. If the user explicitly asks for NSFW/adult-content search phrasing, optimize for native legal adult consenting search keywords/tags only and refuse minors, coercion, incest, trafficking, hidden-camera, non-consensual, sexual violence, or exploitation. Return compact JSON with translated, source_lang, target_lang, nuance_notes, regional_variants, confidence, and when adult search mode is triggered include best_search_phrase, literal_translation, adult_context, search_variants, avoid_terms."
PAYLOAD=$(jq -n --arg model "$MODEL" --arg sys "$SYSTEM_PROMPT" --arg text "$INPUT_TEXT" '{
  model: $model,
  messages: [
    {role: "system", content: $sys},
    {role: "user", content: $text}
  ],
  response_format: {type: "json_object"}
}')
curl -fsS https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${XAI_API_KEY}" \
  -d "$PAYLOAD" | jq -r '.choices[0].message.content'
