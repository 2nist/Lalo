/**
 * @lalo/core — local portable copy
 *
 * Canonical music-theory constants and pure functions used across all LALO
 * components. No UI dependencies — safe to import anywhere (components,
 * tests, Node scripts, Electron main process).
 *
 * Mirrors the public API of the original monorepo package so the import
 * alias `@lalo/core` can point here without changing any consumer code.
 */

// ── Root names ───────────────────────────────────────────────────────────────

export const ROOTS = ["C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B"];

/** Enharmonic / Unicode → canonical root. */
const ENHARMONIC_MAP = {
  "Db":"C♯","Eb":"D♯","Gb":"F♯","Ab":"G♯","Bb":"A♯",
  "C#":"C♯","D#":"D♯","F#":"F♯","G#":"G♯","A#":"A♯",
};

export function normalizeRoot(root) {
  if (!root) return null;
  const s = root.trim();
  if (ROOTS.includes(s)) return s;
  return ENHARMONIC_MAP[s] ?? null;
}

/** Semitone index 0–11. Falls back to 0 for unrecognised roots. */
export function getRootIdx(rootName) {
  const n = normalizeRoot(rootName);
  return n === null ? 0 : ROOTS.indexOf(n);
}

// ── Qualities ────────────────────────────────────────────────────────────────

export const QUALITIES = [
  { label:"maj",  symbol:"",    accent:"#5a3e1a" },
  { label:"min",  symbol:"m",   accent:"#3a6ea8" },
  { label:"dim",  symbol:"°",   accent:"#b54040" },
  { label:"°7",   symbol:"°7",  accent:"#8b2020" },
  { label:"ø",    symbol:"ø",   accent:"#c05050" },
  { label:"aug",  symbol:"+",   accent:"#c07030" },
  { label:"sus2", symbol:"sus2",accent:"#3a8a5a" },
  { label:"sus4", symbol:"sus4",accent:"#2a7a7a" },
  { label:"5",    symbol:"5",   accent:"#7a7a7a" },
];

// ── Extensions ───────────────────────────────────────────────────────────────

export const EXTENSIONS = [
  { label:"—",    symbol:""     },
  { label:"7",    symbol:"7"    },
  { label:"maj7", symbol:"maj7" },
  { label:"6",    symbol:"6"    },
  { label:"add9", symbol:"add9" },
  { label:"9",    symbol:"9"    },
  { label:"11",   symbol:"11"   },
  { label:"13",   symbol:"13"   },
];

// ── Inversions ───────────────────────────────────────────────────────────────

export const INVERSIONS = [
  { label:"root", symbol:""   },
  { label:"1st",  symbol:"/1" },
  { label:"2nd",  symbol:"/2" },
  { label:"3rd",  symbol:"/3" },
];

// ── Modal scale tables ────────────────────────────────────────────────────────

export const DIATONIC_SCALE = {
  major:      [0,2,4,5,7,9,11],
  minor:      [0,2,3,5,7,8,10],
  dorian:     [0,2,3,5,7,9,10],
  mixolydian: [0,2,4,5,7,9,10],
  phrygian:   [0,1,3,5,7,8,10],
  lydian:     [0,2,4,6,7,9,11],
  locrian:    [0,1,3,5,6,8,10],
  chromatic:  [0,1,2,3,4,5,6,7,8,9,10,11],
};

/** Scale-degree quality per mode: M = major, m = minor, d = diminished. */
export const DEGREE_QUALITY = {
  major:      ["M","m","m","M","M","m","d"],
  minor:      ["m","d","M","m","m","M","M"],
  dorian:     ["m","m","M","M","m","d","M"],
  mixolydian: ["M","m","d","M","m","m","M"],
  phrygian:   ["m","M","m","m","d","M","m"],
  lydian:     ["M","M","m","M","m","m","d"],
  locrian:    ["d","M","m","m","M","M","m"],
};

// ── Roman numeral helpers ─────────────────────────────────────────────────────

const ROMAN_NUMERALS = ["I","II","III","IV","V","VI","VII"];
const PARALLEL_MINOR = [0,2,3,5,7,8,10]; // for borrowed-chord detection in major

function formatRoman(romanRaw, degQuality, chordQuality) {
  const isMin = ["min","ø","dim","°7"].includes(chordQuality);
  const isDim = ["dim","°7"].includes(chordQuality);
  const isAug = chordQuality === "aug";
  let r = isMin ? romanRaw.toLowerCase() : romanRaw;
  if (isDim) r += "°";
  else if (isAug) r += "+";
  return r;
}

// ── analyzeChord ──────────────────────────────────────────────────────────────

/**
 * Analyse one chord event relative to a section key/mode.
 * Returns semantic strength + roman numeral data (no UI colours).
 *
 * @param {object} ev         - ChordEvent: { root, quality, extension, inversion }
 * @param {string} sectionKey - Root name of the section key (e.g. "C")
 * @param {string} sectionMode- Modal name (e.g. "major", "minor")
 * @returns {object} ChordAnalysis
 */
export function analyzeChord(ev, sectionKey = "C", sectionMode = "major") {
  const mode     = sectionMode ?? "major";
  const scale    = DIATONIC_SCALE[mode] ?? DIATONIC_SCALE.major;
  const degQ     = DEGREE_QUALITY[mode] ?? DEGREE_QUALITY.major;

  const keyIdx   = getRootIdx(sectionKey ?? "C");
  const rootIdx  = getRootIdx(ev.root     ?? "C");
  const interval = ((rootIdx - keyIdx) + 12) % 12;

  const degreePos  = scale.indexOf(interval);
  const isDiatonic = degreePos >= 0;

  let romanRaw = null;
  let roman    = null;

  if (isDiatonic) {
    romanRaw = ROMAN_NUMERALS[degreePos] ?? null;
    const dQ = degQ[degreePos] ?? "M";
    roman    = romanRaw ? formatRoman(romanRaw, dQ, ev.quality ?? "maj") : null;
  }

  const isBorrowed = !isDiatonic && mode === "major" && PARALLEL_MINOR.includes(interval);

  let strength     = "weak";
  let relationName = "non-diatonic";

  if (isDiatonic) {
    switch (degreePos) {
      case 0: relationName = "tonic";       strength = "strong"; break;
      case 4: relationName = "dominant";    strength = "strong"; break;
      case 3: relationName = "subdominant"; strength = "medium"; break;
      case 5: relationName = "submediant";  strength = "medium"; break;
      default: relationName = "diatonic";   strength = "weak";
    }
  } else if (isBorrowed) {
    relationName = "borrowed";
    strength     = "borrowed";
  } else {
    if      (interval === 6)                       { relationName = "tritone sub";    strength = "dissonant"; }
    else if (interval === 1 || interval === 11)    { relationName = "semitone shift"; strength = "dissonant"; }
    else if (interval === 7)                       { relationName = "parallel 5th";   strength = "medium"; }
  }

  return { isDiatonic, isBorrowed, roman, romanRaw, relationName, strength, interval,
           degreePos: isDiatonic ? degreePos : null };
}

// ── buildMotionSummary ────────────────────────────────────────────────────────

/**
 * Summarise an array of ChordAnalysis results for one section.
 * Detects common cadence patterns from the plain roman sequence.
 *
 * @param {object[]} analyses - Array of ChordAnalysis objects from analyzeChord()
 * @returns {object} MotionSummary
 */
export function buildMotionSummary(analyses) {
  if (!analyses || !analyses.length) {
    return { total:0, diatonic:0, borrowed:0, nonDiat:0, cadence:null };
  }

  const total    = analyses.length;
  const diatonic = analyses.filter(a => a.isDiatonic).length;
  const borrowed = analyses.filter(a => a.isBorrowed).length;
  const nonDiat  = total - diatonic - borrowed;

  const seq = analyses.map(a => a.romanRaw ?? "?").join(" ");

  let cadence = null;
  if      (/V\s+I\b/.test(seq))            cadence = "authentic (V→I)";
  else if (/IV\s+I\b/.test(seq))           cadence = "plagal (IV→I)";
  else if (/II\s+V\b/.test(seq))           cadence = "ii–V";
  else if (/I\s+V\s+VI\s+IV/.test(seq))   cadence = "I–V–vi–IV";
  else if (/VI\s+IV\s+I\s+V/.test(seq))   cadence = "vi–IV–I–V";
  else if (/I\s+IV\s+V/.test(seq))        cadence = "I–IV–V";

  return { total, diatonic, borrowed, nonDiat, cadence };
}
