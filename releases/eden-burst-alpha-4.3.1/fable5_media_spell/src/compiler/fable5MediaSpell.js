/**
 * Fable5 Media Spell compiler — local, approval-gated, identifier-free.
 *
 * Invariants:
 * - Default executionMode is manifest_only (no render until user approval)
 * - externalRequests always 0 at compile time
 * - trainingAllowed always false
 * - No device-identifying fields accepted by diagnoseIPhoneBridge
 * - Deterministic: identical input → identical manifest
 * - symbolic_only metadata for moonGate / catalyst numbers
 */

const SUPPORTED_MEDIA = new Set(['image', 'video', 'audio']);

const IMAGE_DEFAULTS = Object.freeze({
  rendererClass: 'comfyui_local',
  width: 1024,
  height: 1024,
});

const VIDEO_BOUNDS = Object.freeze({
  maxDurationSeconds: 30,
  maxFrameRate: 60,
  maxWidth: 1920,
  maxHeight: 1080,
});

const AUDIO_DEFAULTS = Object.freeze({
  rendererClass: 'local_audio_generator',
  sampleRate: 48000,
  channels: 2,
  durationSeconds: 10,
});

const MAX_PARTY = 5;

const IDENTIFYING_KEYS = new Set([
  'deviceId',
  'device_id',
  'udid',
  'serial',
  'imei',
  'macAddress',
  'mac_address',
  'advertisingId',
  'idfa',
  'idfv',
]);

function deepFreeze(obj) {
  if (obj && typeof obj === 'object' && !Object.isFrozen(obj)) {
    Object.freeze(obj);
    for (const k of Object.keys(obj)) deepFreeze(obj[k]);
  }
  return obj;
}

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function assertValidSpell(spellIR) {
  if (!spellIR || spellIR.valid !== true) {
    throw new Error('compileFable5MediaSpell requires a valid compiled spell');
  }
}

function assertMedium(medium) {
  if (!SUPPORTED_MEDIA.has(medium)) {
    throw new Error(`unsupported medium: ${medium}`);
  }
}

function assertParty(party) {
  if (party == null) return;
  if (!Array.isArray(party)) throw new Error('party must be an array');
  if (party.length > MAX_PARTY) {
    throw new Error(`party must have at most ${MAX_PARTY} members`);
  }
}

function spellReady(spellIR) {
  if (spellIR.active !== true) return false;
  const q = Number(spellIR.quality ?? 0);
  const s = Number(spellIR.stability ?? 0);
  const n = Number(spellIR.neatness ?? 0);
  const f = Number(spellIR.focus ?? 0);
  // All four axes must clear 0.5 for the moon gate to open.
  return q >= 0.5 && s >= 0.5 && n >= 0.5 && f >= 0.5;
}

function boundVideoMedia(media = {}) {
  const width = media.width ?? 1280;
  const height = media.height ?? 720;
  const frameRate = media.frameRate ?? 30;
  const durationSeconds = media.durationSeconds ?? 5;

  if (durationSeconds > VIDEO_BOUNDS.maxDurationSeconds) {
    throw new Error(
      `durationSeconds ${durationSeconds} exceeds max ${VIDEO_BOUNDS.maxDurationSeconds}`,
    );
  }
  if (frameRate > VIDEO_BOUNDS.maxFrameRate) {
    throw new Error(`frameRate ${frameRate} exceeds max ${VIDEO_BOUNDS.maxFrameRate}`);
  }
  if (width > VIDEO_BOUNDS.maxWidth || height > VIDEO_BOUNDS.maxHeight) {
    throw new Error('video resolution exceeds bound');
  }

  return {
    rendererClass: 'comfyui_local',
    width,
    height,
    frameRate,
    durationSeconds,
  };
}

function boundAudioMedia(media = {}) {
  return {
    rendererClass: AUDIO_DEFAULTS.rendererClass,
    sampleRate: media.sampleRate ?? AUDIO_DEFAULTS.sampleRate,
    channels: media.channels ?? AUDIO_DEFAULTS.channels,
    durationSeconds: media.durationSeconds ?? AUDIO_DEFAULTS.durationSeconds,
  };
}

function buildMedia(medium, media) {
  if (medium === 'image') {
    return {
      rendererClass: IMAGE_DEFAULTS.rendererClass,
      width: media?.width ?? IMAGE_DEFAULTS.width,
      height: media?.height ?? IMAGE_DEFAULTS.height,
    };
  }
  if (medium === 'video') return boundVideoMedia(media);
  if (medium === 'audio') return boundAudioMedia(media);
  throw new Error(`unsupported medium: ${medium}`);
}

/**
 * Compile a deterministic approval-gated media spell manifest.
 * Never executes renderers. Never makes external requests.
 */
export function compileFable5MediaSpell(input = {}) {
  const {
    spellIR,
    medium,
    intent = '',
    party = [],
    assetDigests = [],
    media = {},
  } = input;

  assertValidSpell(spellIR);
  assertMedium(medium);
  assertParty(party);

  const ready = spellReady(spellIR);
  const status = ready ? 'ready_for_user_approval' : 'needs_spell_refinement';

  const manifest = {
    status,
    intent: String(intent),
    medium,
    media: buildMedia(medium, media),
    party: clone(party),
    assetDigests: clone(assetDigests),
    controls: {
      approved: false,
      executionMode: 'manifest_only',
      externalRequests: 0,
      trainingAllowed: false,
    },
    fable5: {
      catalyst: 5,
      moonGate: {
        direct: 18,
        reduced: 9,
        open: ready,
        symbolic_only: true,
      },
      signature: spellIR.signature ?? null,
      element: spellIR.element ?? null,
      primaryManifestation: spellIR.primaryManifestation ?? null,
      quality: spellIR.quality ?? null,
      stability: spellIR.stability ?? null,
      neatness: spellIR.neatness ?? null,
      focus: spellIR.focus ?? null,
    },
    provenance: {
      compiler: 'fable5MediaSpell@1.0.0',
      carrier: 'love_and_harmony_6',
      symbolic_only: true,
    },
  };

  return deepFreeze(clone(manifest));
}

/**
 * Local-only iPhone bridge diagnostics.
 * Prohibits device-identifying fields. Never probes hardware.
 */
export function diagnoseIPhoneBridge(caps = {}) {
  for (const key of Object.keys(caps)) {
    if (IDENTIFYING_KEYS.has(key)) {
      throw new Error(
        'device-identifying fields are prohibited in diagnoseIPhoneBridge',
      );
    }
  }

  const failures = [];
  if (caps.secureContext !== true) failures.push('secureContext');
  if (!(Number(caps.touchPoints) >= 1)) failures.push('touchPoints');
  if (caps.webAudio !== true) failures.push('webAudio');
  if (caps.webGL2 !== true) failures.push('webGL2');

  const status = failures.length === 0 ? 'ready' : 'degraded';

  return deepFreeze({
    status,
    localOnly: true,
    externalRequests: 0,
    identifiersCollected: [],
    diagnosticsOnly: true,
    failures,
    viewport: caps.viewport
      ? { width: caps.viewport.width, height: caps.viewport.height }
      : null,
  });
}

export default {
  compileFable5MediaSpell,
  diagnoseIPhoneBridge,
};
