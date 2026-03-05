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
  "Cb":"B","Db":"C♯","Eb":"D♯","Fb":"E","Gb":"F♯","Ab":"G♯","Bb":"A♯",
  "C♭":"B","D♭":"C♯","E♭":"D♯","F♭":"E","G♭":"F♯","A♭":"G♯","B♭":"A♯",
  "C#":"C♯","D#":"D♯","E#":"F","F#":"F♯","G#":"G♯","A#":"A♯","B#":"C",
  "C♯":"C♯","D♯":"D♯","E♯":"F","F♯":"F♯","G♯":"G♯","A♯":"A♯","B♯":"C",
};

export function normalizeRoot(root) {
  if (!root) return null;
  const s = String(root).trim();
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

// ── Named progression library ────────────────────────────────────────────────

export const NAMED_PROGRESSIONS = [
  {
    id: "axis",
    name: "Axis progression",
    numerals: ["I", "V", "vi", "IV"],
    aliases: ["I-V-vi-IV", "Pop progression", "Pachelbel progression"],
    notes: "Most common progression in Western pop. Endless rotation.",
    modes: ["major"],
  },
  {
    id: "axis-variant-vi",
    name: "Axis (vi start)",
    numerals: ["vi", "IV", "I", "V"],
    aliases: ["vi-IV-I-V"],
    notes: "Axis starting on relative minor - darker feel, same harmonic loop.",
    modes: ["major"],
  },
  {
    id: "doo-wop",
    name: "Doo-wop / 50s",
    numerals: ["I", "vi", "IV", "V"],
    aliases: ["I-vi-IV-V", "Heart and Soul"],
    notes: "Foundational to 50s/60s pop and doo-wop.",
    modes: ["major"],
  },
  {
    id: "12-bar-blues",
    name: "12-bar blues",
    numerals: ["I","I","I","I","IV","IV","I","I","V","IV","I","V"],
    aliases: ["blues"],
    notes: "Standard 12-bar blues. Each numeral = one bar.",
    modes: ["major"],
  },
  {
    id: "8-bar-blues",
    name: "8-bar blues",
    numerals: ["I","I","IV","IV","I","V","IV","I"],
    aliases: [],
    notes: "Compressed blues form.",
    modes: ["major"],
  },
  {
    id: "ii-V-I",
    name: "ii-V-I",
    numerals: ["ii", "V", "I"],
    aliases: ["2-5-1", "jazz cadence"],
    notes: "Fundamental jazz cadence. V7 implied.",
    modes: ["major"],
  },
  {
    id: "ii-V-I-minor",
    name: "ii°-V-i (minor)",
    numerals: ["ii°", "V", "i"],
    aliases: ["minor 2-5-1"],
    notes: "Minor key jazz cadence.",
    modes: ["minor"],
  },
  {
    id: "I-IV-V",
    name: "I-IV-V",
    numerals: ["I", "IV", "V"],
    aliases: ["three-chord", "rock and roll"],
    notes: "Three-chord foundation of rock, country, and folk.",
    modes: ["major"],
  },
  {
    id: "I-IV-V-I",
    name: "I-IV-V-I (full cadence)",
    numerals: ["I", "IV", "V", "I"],
    aliases: [],
    notes: "Complete tonic-subdominant-dominant-tonic loop.",
    modes: ["major"],
  },
  {
    id: "andalusian",
    name: "Andalusian cadence",
    numerals: ["i", "VII", "VI", "V"],
    aliases: ["i-VII-VI-V", "Spanish cadence"],
    notes: "Descending minor cadence. Flamenco, baroque, and rock.",
    modes: ["minor"],
  },
  {
    id: "royal-road",
    name: "Royal Road",
    numerals: ["I", "IV", "ii", "V"],
    aliases: ["Japanese pop progression", "Ohanashi"],
    notes: "Ubiquitous in J-pop. Strong resolution pull.",
    modes: ["major"],
  },
  {
    id: "circle",
    name: "Circle of fifths",
    numerals: ["I", "IV", "vii°", "iii", "vi", "ii", "V", "I"],
    aliases: ["diatonic circle"],
    notes: "All diatonic chords descending by fifth.",
    modes: ["major"],
  },
  {
    id: "pachelbel",
    name: "Pachelbel canon",
    numerals: ["I", "V", "vi", "iii", "IV", "I", "IV", "V"],
    aliases: ["Canon progression"],
    notes: "Baroque foundation. Endless pop derivatives.",
    modes: ["major"],
  },
  {
    id: "minor-i-VI-III-VII",
    name: "i-VI-III-VII",
    numerals: ["i", "VI", "III", "VII"],
    aliases: ["minor axis", "i-bVI-bIII-bVII"],
    notes: "Minor key equivalent of the axis. Very common in rock and metal.",
    modes: ["minor"],
  },
  {
    id: "I-V-ii-IV",
    name: "I-V-ii-IV",
    numerals: ["I", "V", "ii", "IV"],
    aliases: [],
    notes: "Variant of axis with supertonic instead of relative minor.",
    modes: ["major"],
  },
  {
    id: "ragtime",
    name: "Ragtime / classic turnaround",
    numerals: ["I", "I7", "IV", "iv", "I", "V7", "I"],
    aliases: ["turnaround"],
    notes: "Ragtime and jazz standard turnaround with chromatic subdominant.",
    modes: ["major"],
  },
  {
    id: "flamenco",
    name: "Flamenco / Phrygian",
    numerals: ["i", "bII", "i", "V"],
    aliases: ["Phrygian cadence"],
    notes: "Phrygian flavor. The bII is the Neapolitan.",
    modes: ["minor"],
  },
  {
    id: "bVI-bVII-I",
    name: "bVI-bVII-I",
    numerals: ["bVI", "bVII", "I"],
    aliases: ["flat-six flat-seven one", "rock cadence"],
    notes: "Borrowed from parallel minor. Ubiquitous in rock.",
    modes: ["major"],
  },
  {
    id: "IV-I",
    name: "Plagal cadence",
    numerals: ["IV", "I"],
    aliases: ["amen cadence"],
    notes: "Church music staple. Also common as a loop in folk.",
    modes: ["major"],
  },
  {
    id: "i-iv-v",
    name: "i-iv-v (minor)",
    numerals: ["i", "iv", "v"],
    aliases: [],
    notes: "All-minor three-chord. Natural minor feel.",
    modes: ["minor"],
  },
  {
    id: "I-iii-IV-V",
    name: "I-iii-IV-V",
    numerals: ["I", "iii", "IV", "V"],
    aliases: [],
    notes: "Adds mediant colour before the subdominant.",
    modes: ["major"],
  },
  {
    id: "deceptive",
    name: "Deceptive cadence loop",
    numerals: ["I", "IV", "vi", "V"],
    aliases: [],
    notes: "V resolves to vi instead of I - creates surprise.",
    modes: ["major"],
  },
  {
    id: "omnibus",
    name: "Neo-soul / omnibus",
    numerals: ["Imaj7", "iiim7", "IVmaj7", "V7"],
    aliases: [],
    notes: "Extended chord version of I-iii-IV-V. Neo-soul and smooth jazz.",
    modes: ["major"],
  },
];

const MAJOR_DIATONIC_SET = new Set(DIATONIC_SCALE.major);
const MINOR_DIATONIC_SET = new Set(DIATONIC_SCALE.minor);
const INTERVAL_DEGREE_MAP = {
  0: "I",
  1: "bII",
  2: "II",
  3: "III",
  4: "III",
  5: "IV",
  6: "bV",
  7: "V",
  8: "VI",
  9: "VI",
  10: "VII",
  11: "VII",
};

function baseDegreeForInterval(interval, mode) {
  const isMinorMode = mode === "minor";
  if (interval === 3) return isMinorMode ? "III" : "bIII";
  if (interval === 8) return isMinorMode ? "VI" : "bVI";
  if (interval === 10) return isMinorMode ? "VII" : "bVII";
  return INTERVAL_DEGREE_MAP[interval] ?? "I";
}

function applyNumeralCase(degreeBase, lowerCase) {
  if (!degreeBase) return degreeBase;
  const accidental = degreeBase.startsWith("b") ? "b" : "";
  const roman = accidental ? degreeBase.slice(1) : degreeBase;
  return `${accidental}${lowerCase ? roman.toLowerCase() : roman.toUpperCase()}`;
}

function qualityClass(quality) {
  const q = String(quality ?? "").toLowerCase();
  if (q === "maj" || q === "major") return "maj";
  if (q === "min" || q === "minor" || q === "m") return "min";
  if (q === "dim") return "dim";
  if (q === "°7" || q === "dim7") return "°7";
  if (q === "ø" || q === "halfdim" || q === "m7b5") return "ø";
  if (q === "aug" || q === "+") return "aug";
  if (q === "sus2") return "sus2";
  if (q === "sus4") return "sus4";
  if (q === "5" || q === "power") return "5";
  return "maj";
}

function mostFrequentValue(values) {
  if (!values.length) return null;
  const counts = new Map();
  for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])))[0]?.[0] ?? null;
}

function numeralToIntervalAndLabel(numeral, mode = "major") {
  const raw = String(numeral ?? "").trim();
  if (!raw) return null;

  const accidental = raw.startsWith("b") ? -1 : 0;
  const body = accidental ? raw.slice(1) : raw;
  const romanMatch = body.match(/[ivIV]+/);
  if (!romanMatch) return null;
  const romanRaw = romanMatch[0];
  const romanUpper = romanRaw.toUpperCase();

  const baseMapMajor = { I:0, II:2, III:4, IV:5, V:7, VI:9, VII:11 };
  const baseMapMinor = { I:0, II:2, III:3, IV:5, V:7, VI:8, VII:10 };
  const base = (mode === "minor" ? baseMapMinor : baseMapMajor)[romanUpper];
  if (base === undefined) return null;

  const interval = (base + accidental + 12) % 12;
  const hasMaj7 = /maj7/i.test(body);
  const hasM7 = /m7/i.test(body) && !hasMaj7;
  const hasDim7 = /°7/.test(body);
  const hasDim = /°/.test(body);
  const hasHalfDim = /ø/.test(body);
  const hasAug = /\+/.test(body);
  const hasSeven = /7/.test(body);
  const isLower = romanRaw === romanRaw.toLowerCase();

  let chordSuffix = "";
  if (hasMaj7) chordSuffix = "maj7";
  else if (hasM7) chordSuffix = "m7";
  else if (hasDim7) chordSuffix = "dim7";
  else if (hasHalfDim) chordSuffix = "m7b5";
  else if (hasDim) chordSuffix = "dim";
  else if (hasAug) chordSuffix = "aug";
  else if (hasSeven && !isLower) chordSuffix = "7";
  else if (hasSeven && isLower) chordSuffix = "m7";
  else if (isLower) chordSuffix = "m";

  return { interval, chordSuffix };
}

export function chordToNumeral(root, quality, key, mode = "major") {
  const normalizedRoot = normalizeRoot(root);
  const normalizedKey = normalizeRoot(key);
  if (!normalizedRoot || !normalizedKey) {
    return { numeral: null, diatonic: false, borrowed: false };
  }
  if (normalizedRoot === "N" || normalizedRoot === "X") {
    return { numeral: null, diatonic: false, borrowed: false };
  }

  const rootIdx = getRootIdx(normalizedRoot);
  const keyIdx = getRootIdx(normalizedKey);
  const interval = (rootIdx - keyIdx + 12) % 12;

  const diatonicSet = mode === "minor" ? MINOR_DIATONIC_SET : MAJOR_DIATONIC_SET;
  const parallelSet = mode === "minor" ? MAJOR_DIATONIC_SET : MINOR_DIATONIC_SET;
  const diatonic = diatonicSet.has(interval);
  const borrowed = !diatonic && parallelSet.has(interval);

  const degreeBase = baseDegreeForInterval(interval, mode);
  const qClass = qualityClass(quality);
  const lowerCase = qClass === "min" || qClass === "dim" || qClass === "°7" || qClass === "ø";
  let numeral = applyNumeralCase(degreeBase, lowerCase);

  if (qClass === "dim") numeral += "°";
  else if (qClass === "°7") numeral += "°7";
  else if (qClass === "ø") numeral += "ø";

  return { numeral, diatonic, borrowed };
}

export function sequenceToNumerals(chordEvents = [], key = "C", mode = "major") {
  return (Array.isArray(chordEvents) ? chordEvents : []).map((ev = {}) => {
    const analyzed = chordToNumeral(ev.root, ev.quality, key, mode);
    return {
      numeral: analyzed.numeral,
      diatonic: analyzed.diatonic,
      borrowed: analyzed.borrowed,
      beat: ev.beat ?? 0,
      span: ev.span ?? 0,
      label: ev.label ?? "",
    };
  });
}

export function fingerprintProgression(numerals = []) {
  const seq = Array.isArray(numerals) ? numerals : [];
  const fingerprint = seq.join("-");
  if (!seq.length) return { fingerprint, rotationalFingerprint: fingerprint };

  const rotations = seq.map((_, i) => [...seq.slice(i), ...seq.slice(0, i)].join("-"));
  const rotationalFingerprint = rotations.sort((a, b) => a.localeCompare(b))[0];
  return { fingerprint, rotationalFingerprint };
}

export function matchNamedProgression(numerals = []) {
  const target = fingerprintProgression(numerals);

  for (const entry of NAMED_PROGRESSIONS) {
    const fp = fingerprintProgression(entry.numerals);
    if (fp.fingerprint === target.fingerprint) return entry;
  }
  for (const entry of NAMED_PROGRESSIONS) {
    const fp = fingerprintProgression(entry.numerals);
    if (fp.rotationalFingerprint === target.rotationalFingerprint) return entry;
  }
  return null;
}

export function detectProgressions(song = [], defaultKey = "C", defaultMode = "major") {
  const windows = [2, 3, 4, 6, 8, 12];
  const grouped = new Map();
  const sectionKeys = [];
  const sectionModes = [];

  const sections = Array.isArray(song) ? song : [];
  sections.forEach((section = {}, sectionIndex) => {
    const events = Array.isArray(section.events) ? section.events : [];
    if (!events.length) return;

    const key = section.key ?? defaultKey;
    const mode = section.mode ?? defaultMode;
    sectionKeys.push(key);
    sectionModes.push(mode);

    const analyzed = sequenceToNumerals(events, key, mode);
    const numerals = analyzed.map(a => a.numeral);
    if (!numerals.some(Boolean)) return;

    for (const size of windows) {
      if (numerals.length < size) continue;
      for (let start = 0; start <= numerals.length - size; start += 1) {
        const slice = analyzed.slice(start, start + size);
        const sliceNumerals = slice.map(x => x.numeral);
        if (sliceNumerals.some(n => n == null)) continue;

        const { fingerprint, rotationalFingerprint } = fingerprintProgression(sliceNumerals);
        const firstEvent = events[start] ?? {};
        const lastEvent = events[start + size - 1] ?? {};
        const occurrence = {
          sectionId: typeof section.id === "number" ? section.id : sectionIndex,
          sectionName: section.name ?? `Section ${sectionIndex + 1}`,
          beatStart: firstEvent.beat ?? 0,
          beatEnd: (lastEvent.beat ?? 0) + (lastEvent.span ?? 0),
          key,
          mode,
          chordLabels: events.slice(start, start + size).map(ev => ev?.label ?? ""),
        };
        if (section.keyDetected === false) occurrence.keyConfidence = "low";

        if (!grouped.has(fingerprint)) {
          grouped.set(fingerprint, {
            id: fingerprint,
            fingerprint,
            rotationalFingerprint,
            numerals: sliceNumerals,
            namedMatch: null,
            occurrences: [],
            occurrenceCount: 0,
          });
        }
        grouped.get(fingerprint).occurrences.push(occurrence);
      }
    }
  });

  const progressions = [...grouped.values()]
    .map((item) => {
      const occurrenceCount = item.occurrences.length;
      return {
        ...item,
        namedMatch: matchNamedProgression(item.numerals),
        occurrenceCount,
      };
    })
    .filter(item => item.occurrenceCount >= 2)
    .sort((a, b) => b.occurrenceCount - a.occurrenceCount || a.fingerprint.localeCompare(b.fingerprint));

  const mostCommon = progressions[0] ?? null;
  const namedCount = progressions.filter(p => p.namedMatch !== null).length;

  return {
    progressions,
    summary: {
      totalProgressions: progressions.length,
      mostCommon,
      namedCount,
      keyEstimate: mostFrequentValue(sectionKeys),
      modeEstimate: mostFrequentValue(sectionModes),
    },
  };
}

export function transposeProgression(numerals = [], fromKey = "C", toKey = "C", mode = "major") {
  const toKeyIdx = getRootIdx(toKey);
  const seq = Array.isArray(numerals) ? numerals : [];
  return seq.map((numeral) => {
    const parsed = numeralToIntervalAndLabel(numeral, mode);
    if (!parsed) return "";
    const root = ROOTS[(toKeyIdx + parsed.interval) % 12];
    return `${root}${parsed.chordSuffix}`;
  });
}

// ── SELF-TEST (run with: node src/core/index.js) ──────────────────────────
// if (typeof process !== 'undefined' && process.argv[1] === fileURLToPath(import.meta.url)) {
//   const tests = [
//     { fn: () => chordToNumeral("G", "maj", "C", "major").numeral,     expect: "V"    },
//     { fn: () => chordToNumeral("F#", "min", "A", "major").numeral,    expect: "vi"   },
//     { fn: () => chordToNumeral("Bb", "maj", "C", "major").numeral,    expect: "bVII" },
//     { fn: () => chordToNumeral("E", "min", "G", "major").numeral,     expect: "vi"   },
//     { fn: () => chordToNumeral("D", "maj", "A", "major").numeral,     expect: "IV"   },
//     { fn: () => fingerprintProgression(["I","V","vi","IV"]).fingerprint, expect: "I-V-vi-IV" },
//     { fn: () => matchNamedProgression(["I","V","vi","IV"])?.id,        expect: "axis" },
//     { fn: () => matchNamedProgression(["vi","IV","I","V"])?.id,        expect: "axis-variant-vi" },
//     { fn: () => transposeProgression(["I","V","vi","IV"], "C", "G", "major").join(","), expect: "G,D,Em,C" },
//   ]
//   let pass = 0
//   tests.forEach(({ fn, expect }, i) => {
//     const result = fn()
//     const ok = String(result) === String(expect)
//     console.log(`${ok ? "✓" : "✗"} test ${i+1}: got "${result}" expected "${expect}"`)
//     if (ok) pass++
//   })
//   console.log(`\n${pass}/${tests.length} passed`)
// }

// ── Vamp pattern library ────────────────────────────────────────────────────

export const VAMP_PATTERNS = [
  {
    id: "vamp-I",
    name: "Tonic vamp",
    numerals: ["I"],
    notes: "Single tonic chord. Groove-only sections, intros, outros.",
    modes: ["major", "minor"],
  },
  {
    id: "vamp-i",
    name: "Minor tonic vamp",
    numerals: ["i"],
    notes: "Single minor tonic. Dark grooves, hip-hop, doom.",
    modes: ["minor"],
  },
  {
    id: "vamp-I-IV",
    name: "I-IV vamp",
    numerals: ["I", "IV"],
    notes: "Tonic-subdominant alternation. Blues, gospel, soul, funk.",
    modes: ["major"],
  },
  {
    id: "vamp-IV-I",
    name: "IV-I vamp (plagal)",
    numerals: ["IV", "I"],
    notes: "Reversed plagal. Running On Empty, gospel turnarounds.",
    modes: ["major"],
  },
  {
    id: "vamp-I-V",
    name: "I-V vamp",
    numerals: ["I", "V"],
    notes: "Tonic-dominant alternation. Anthemic rock, country.",
    modes: ["major"],
  },
  {
    id: "vamp-i-VII",
    name: "i-VII vamp",
    numerals: ["i", "VII"],
    notes: "Minor tonic to subtonic. Rock, grunge, Dorian feel.",
    modes: ["minor"],
  },
  {
    id: "vamp-i-iv",
    name: "i-iv vamp",
    numerals: ["i", "iv"],
    notes: "Minor tonic-subdominant. Flamenco, dark soul.",
    modes: ["minor"],
  },
  {
    id: "vamp-I-bVII",
    name: "I-bVII vamp",
    numerals: ["I", "bVII"],
    notes: "Mixolydian alternation. Classic rock, Stones, Beatles.",
    modes: ["major"],
  },
  {
    id: "vamp-I-ii",
    name: "I-ii vamp",
    numerals: ["I", "ii"],
    notes: "Tonic-supertonic. Jazz vamps, bossa nova.",
    modes: ["major"],
  },
  {
    id: "vamp-i-bVI",
    name: "i-bVI vamp",
    numerals: ["i", "bVI"],
    notes: "Minor tonic to flat-six. Cinematic, Aeolian.",
    modes: ["minor"],
  },
  {
    id: "vamp-I-vi",
    name: "I-vi vamp",
    numerals: ["I", "vi"],
    notes: "Tonic-submediant. Romantic, introspective.",
    modes: ["major"],
  },
  {
    id: "vamp-V-IV",
    name: "V-IV vamp",
    numerals: ["V", "IV"],
    notes: "Dominant-subdominant alternation. Blues rock, ZZ Top.",
    modes: ["major"],
  },
  {
    id: "vamp-i-V",
    name: "i-V vamp (harmonic minor)",
    numerals: ["i", "V"],
    notes: "Minor with raised leading tone V. Spanish, classical.",
    modes: ["minor"],
  },
  {
    id: "vamp-IV-V",
    name: "IV-V vamp",
    numerals: ["IV", "V"],
    notes: "Subdominant-dominant. Build sections, pre-chorus energy.",
    modes: ["major"],
  },
  {
    id: "vamp-ii-V",
    name: "ii-V vamp",
    numerals: ["ii", "V"],
    notes: "Jazz two-five loop without resolution. Modal jazz, cool.",
    modes: ["major"],
  },
];

const VAMP_EMPTY_RESULT = { isVamp: false, density: 0, matchedVamp: null };
const COLOR_POOLS = {
  strong: ["#4a7c52", "#5a8f62", "#3d6644", "#6a9e72", "#2e5238"],
  modal: ["#5a6e82", "#4a7a8a", "#3d6070", "#6a8a9a", "#2e505e"],
  dominant: ["#c4822a", "#b06820", "#d4963a", "#a05818", "#c8a050"],
  minor: ["#b84830", "#a03828", "#c85840", "#8a2818", "#d06850"],
  vamp: ["#9a8040", "#8a7030", "#aa9050", "#7a6028", "#b4a060"],
  fallback: ["#7a6e8a", "#6e8a7a", "#8a7a6e", "#7a8a8a", "#8a6e7a", "#6e7a8a", "#8a8a6e", "#7a7a8a"],
};

function clampInt(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.round(n));
}

function collectSectionData(song = [], defaultKey = "C", defaultMode = "major") {
  const byId = new Map();
  const byIndex = new Map();
  const sections = Array.isArray(song) ? song : [];
  sections.forEach((section = {}, idx) => {
    const key = section.key ?? defaultKey;
    const mode = section.mode ?? defaultMode;
    const events = Array.isArray(section.events) ? section.events : [];
    const numerals = sequenceToNumerals(events, key, mode).map(x => x.numeral);
    const data = { section, idx, key, mode, events, numerals, sectionName: section.name ?? `Section ${idx + 1}` };
    if (typeof section.id === "number") byId.set(section.id, data);
    byIndex.set(idx, data);
  });
  return { byId, byIndex };
}

function getSectionContext(sectionInfo, sectionId) {
  if (sectionInfo.byId.has(sectionId)) return sectionInfo.byId.get(sectionId);
  if (sectionInfo.byIndex.has(sectionId)) return sectionInfo.byIndex.get(sectionId);
  return null;
}

function hashString(value) {
  let hash = 0;
  const s = String(value ?? "");
  for (let i = 0; i < s.length; i += 1) {
    hash = ((hash << 5) - hash + s.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function pickColorFromPool(pool, existingColors = []) {
  for (const color of pool) {
    if (!existingColors.includes(color)) return color;
  }
  return `${pool[0]}88`;
}

export function matchVampPattern(numerals = []) {
  const fp = fingerprintProgression(numerals).fingerprint;
  for (const vamp of VAMP_PATTERNS) {
    if (fingerprintProgression(vamp.numerals).fingerprint === fp) return vamp;
  }
  return null;
}

export function isVampPattern(numerals = [], sectionNumerals = []) {
  const pattern = Array.isArray(numerals) ? [...numerals] : [];
  const section = Array.isArray(sectionNumerals) ? [...sectionNumerals] : [];
  const len = pattern.length;
  if (!len || len > 2 || !section.length || len > section.length) return { ...VAMP_EMPTY_RESULT };

  const starts = [];
  let i = 0;
  while (i <= section.length - len) {
    const isMatch = pattern.every((n, pIdx) => section[i + pIdx] === n);
    if (isMatch) {
      starts.push(i);
      i += len;
    } else {
      i += 1;
    }
  }

  const matchCount = starts.length;
  const density = (matchCount * len) / section.length;
  let streak = 0;
  let maxStreak = 0;
  let prevStart = null;
  starts.forEach((start) => {
    if (prevStart === null || start - prevStart <= len + 1) streak += 1;
    else streak = 1;
    prevStart = start;
    if (streak > maxStreak) maxStreak = streak;
  });

  const matchedVamp = matchVampPattern(pattern);
  const isVamp = density >= 0.55 && maxStreak >= 3;
  return { isVamp, density, matchedVamp };
}

export function detectVampRun(numerals = [], sectionNumerals = []) {
  const pattern = Array.isArray(numerals) ? [...numerals] : [];
  const section = Array.isArray(sectionNumerals) ? [...sectionNumerals] : [];
  const len = pattern.length;
  if (!len || !section.length || len > section.length) {
    return { runLength: 0, runBars: 0, breakIndex: 0, breakNumeral: section[0] ?? null, preBreak: [] };
  }

  let best = { runLength: 0, breakIndex: 0 };
  for (let start = 0; start <= section.length - len; start += 1) {
    let runLength = 0;
    let ptr = start;
    while (ptr <= section.length - len) {
      const isMatch = pattern.every((n, pIdx) => section[ptr + pIdx] === n);
      if (!isMatch) break;
      runLength += 1;
      ptr += len;
    }
    if (runLength > best.runLength) best = { runLength, breakIndex: ptr };
  }

  const breakIndex = best.breakIndex;
  const breakNumeral = section[breakIndex] ?? null;
  const preBreak = section.slice(Math.max(0, breakIndex - 2), breakIndex);
  return {
    runLength: best.runLength,
    runBars: Math.ceil((best.runLength * len) / 4),
    breakIndex,
    breakNumeral,
    preBreak,
  };
}

export function assignProgressionColor(progressionType = {}, existingColors = []) {
  const named = progressionType.namedMatch ?? null;
  const isVamp = progressionType.isVamp === true;
  const id = named?.id ?? progressionType.id ?? fingerprintProgression(progressionType.numerals ?? []).fingerprint;

  if (isVamp) return pickColorFromPool(COLOR_POOLS.vamp, existingColors);

  if (named) {
    if (Array.isArray(named.modes) && named.modes.length === 1 && named.modes[0] === "minor") {
      return pickColorFromPool(COLOR_POOLS.minor, existingColors);
    }
    if (String(named.id).includes("blues")) {
      return pickColorFromPool(COLOR_POOLS.dominant, existingColors);
    }
    if (["ii-V-I", "circle", "pachelbel", "ragtime"].includes(named.id)) {
      return pickColorFromPool(COLOR_POOLS.modal, existingColors);
    }
    return pickColorFromPool(COLOR_POOLS.strong, existingColors);
  }

  const idx = hashString(id) % COLOR_POOLS.fallback.length;
  const preferred = COLOR_POOLS.fallback[idx];
  if (!existingColors.includes(preferred)) return preferred;
  return pickColorFromPool(COLOR_POOLS.fallback, existingColors);
}

/**
 * @typedef {Object} ProgressionType
 * A unique harmonic pattern - the abstract "what".
 * Lives in the session library. Referenced by ProgressionInstances.
 *
 * @property {string} id - Fingerprint string e.g. "I-V-vi-IV"
 * @property {string[]} numerals - Roman numeral sequence
 * @property {Object|null} namedMatch - Matched NAMED_PROGRESSIONS entry or null
 * @property {Object|null} vampMatch - Matched VAMP_PATTERNS entry or null
 * @property {boolean} isVamp - True if detected as ostinato
 * @property {number} vampDensity - 0.0-1.0 ratio of section covered (vamps only)
 * @property {string} color - Assigned display color (hex)
 * @property {number} occurrenceCount - Total instances across the song
 * @property {string} displayName - namedMatch.name ?? vampMatch.name ?? id
 */

/**
 * @typedef {Object} ProgressionInstance
 * A placed occurrence of a ProgressionType on the canvas timeline.
 * Lives in section.progressionInstances[].
 *
 * @property {number} id - Unique numeric ID (auto-increment from 2000)
 * @property {string} typeId - -> ProgressionType.id
 * @property {number} sectionId - -> SongSection.id
 * @property {number} beatStart - First beat of this instance
 * @property {number} beatEnd - Last beat (exclusive)
 * @property {string} key - Key at this instance e.g. "A"
 * @property {string} mode - "major" | "minor"
 * @property {string[]} chordLabels - Resolved chord labels e.g. ["A","E","F♯m","D"]
 * @property {boolean} keyConfidence - false if key was defaulted, not detected
 * @property {number|null} vampRunBars - Bars of continuous vamp before break (vamps only)
 * @property {number|null} vampBreakBeat - Beat where vamp pattern stops (vamps only)
 * @property {string} source - "detected" | "manual" | "imported"
 */

export function buildProgressionLibrary(detectionResult = {}, song = []) {
  const rawProgressions = Array.isArray(detectionResult.progressions) ? detectionResult.progressions : [];
  const sectionInfo = collectSectionData(song, detectionResult?.summary?.keyEstimate ?? "C", detectionResult?.summary?.modeEstimate ?? "major");
  const usedColors = [];
  const types = [];
  const instances = [];
  let nextId = 2000;

  rawProgressions.forEach((raw) => {
    const numerals = Array.isArray(raw.numerals) ? raw.numerals : [];
    const namedMatch = matchNamedProgression(numerals);
    const vampMatch = numerals.length <= 2 ? matchVampPattern(numerals) : null;

    let isVamp = false;
    let vampDensity = 0;
    (raw.occurrences ?? []).forEach((occ) => {
      const ctx = getSectionContext(sectionInfo, occ.sectionId);
      const sectionNumerals = ctx?.numerals ?? [];
      const vampCheck = isVampPattern(numerals, sectionNumerals);
      if (vampCheck.isVamp) isVamp = true;
      if (vampCheck.density > vampDensity) vampDensity = vampCheck.density;
    });

    const baseType = {
      id: raw.fingerprint,
      numerals,
      namedMatch,
      vampMatch,
      isVamp,
      vampDensity,
      occurrenceCount: raw.occurrenceCount ?? (raw.occurrences?.length ?? 0),
    };
    const color = assignProgressionColor(baseType, usedColors);
    usedColors.push(color);
    const displayName = namedMatch?.name ?? vampMatch?.name ?? baseType.id;

    /** @type {ProgressionType} */
    const progressionType = { ...baseType, color, displayName };
    types.push(progressionType);

    (raw.occurrences ?? []).forEach((occ) => {
      const ctx = getSectionContext(sectionInfo, occ.sectionId);
      const section = ctx?.section ?? {};
      const sectionNumerals = ctx?.numerals ?? [];
      const beatStart = clampInt(occ.beatStart);
      const beatEnd = clampInt(occ.beatEnd);
      const eventAtBreak = (section.events ?? [])[0];

      let vampRunBars = null;
      let vampBreakBeat = null;
      if (progressionType.isVamp) {
        const run = detectVampRun(numerals, sectionNumerals);
        vampRunBars = run.runBars;
        const breakEvent = (section.events ?? [])[run.breakIndex];
        const fallbackBeat = beatEnd;
        vampBreakBeat = clampInt(breakEvent?.beat ?? fallbackBeat ?? eventAtBreak?.beat ?? 0);
      }

      /** @type {ProgressionInstance} */
      const instance = {
        id: nextId,
        typeId: progressionType.id,
        sectionId: typeof occ.sectionId === "number" ? occ.sectionId : (ctx?.idx ?? -1),
        beatStart,
        beatEnd,
        key: occ.key ?? (ctx?.key ?? "C"),
        mode: occ.mode ?? (ctx?.mode ?? "major"),
        chordLabels: transposeProgression(numerals, null, occ.key ?? (ctx?.key ?? "C"), occ.mode ?? (ctx?.mode ?? "major")),
        keyConfidence: !(section.keyDetected === false),
        vampRunBars,
        vampBreakBeat,
        source: "detected",
      };
      instances.push(instance);
      nextId += 1;
    });
  });

  types.sort((a, b) => b.occurrenceCount - a.occurrenceCount || a.id.localeCompare(b.id));
  const vamps = types.filter(t => t.isVamp);
  const named = types.filter(t => t.namedMatch !== null);
  const dominantType = types[0] ?? null;
  const dominantVamp = [...vamps].sort((a, b) => b.vampDensity - a.vampDensity || b.occurrenceCount - a.occurrenceCount)[0] ?? null;

  const structuralSections = [];
  if (dominantType) {
    const names = [...new Set(instances
      .filter(ins => ins.typeId === dominantType.id)
      .map((ins) => getSectionContext(sectionInfo, ins.sectionId)?.sectionName ?? `Section ${ins.sectionId}`))];
    if (names.length > 1) structuralSections.push(...names);
  }

  return {
    types,
    instances,
    vamps,
    named,
    summary: {
      typeCount: types.length,
      instanceCount: instances.length,
      vampCount: vamps.length,
      namedCount: named.length,
      dominantType,
      dominantVamp,
      keyEstimate: detectionResult?.summary?.keyEstimate ?? "C",
      modeEstimate: detectionResult?.summary?.modeEstimate ?? "major",
      structuralSections,
    },
  };
}

export function mergeProgressionLibraries(existing = {}, incoming = {}) {
  const existingTypes = Array.isArray(existing.types) ? existing.types : [];
  const incomingTypes = Array.isArray(incoming.types) ? incoming.types : [];
  const existingInstances = Array.isArray(existing.instances) ? existing.instances : [];
  const incomingInstances = Array.isArray(incoming.instances) ? incoming.instances : [];

  const mergedTypeMap = new Map();
  existingTypes.forEach(t => mergedTypeMap.set(t.id, { ...t }));
  incomingTypes.forEach((t) => {
    if (!mergedTypeMap.has(t.id)) mergedTypeMap.set(t.id, { ...t });
  });

  const instanceKey = (i) => `${i.typeId}::${i.sectionId}::${i.beatStart}`;
  const mergedInstances = [...existingInstances];
  const seen = new Set(existingInstances.map(instanceKey));
  incomingInstances.forEach((ins) => {
    const key = instanceKey(ins);
    if (!seen.has(key)) {
      mergedInstances.push({ ...ins });
      seen.add(key);
    }
  });

  const occurrenceByType = new Map();
  mergedInstances.forEach((ins) => {
    occurrenceByType.set(ins.typeId, (occurrenceByType.get(ins.typeId) ?? 0) + 1);
  });

  const mergedTypes = [...mergedTypeMap.values()].map((type) => ({
    ...type,
    occurrenceCount: occurrenceByType.get(type.id) ?? 0,
  })).sort((a, b) => b.occurrenceCount - a.occurrenceCount || a.id.localeCompare(b.id));

  return { types: mergedTypes, instances: mergedInstances };
}

// Self-test additions for Task B
// Vamp detection tests
// { fn: () => isVampPattern(["IV","I"], ["IV","I","IV","I","IV","I","IV","I","IV","I","V","V"]).isVamp, expect: true },
// { fn: () => isVampPattern(["I","V","vi","IV"], ["I","V","vi","IV","I","V","vi","IV"]).isVamp, expect: false },
// { fn: () => matchVampPattern(["IV","I"])?.id, expect: "vamp-IV-I" },
// { fn: () => matchVampPattern(["I","IV"])?.id, expect: "vamp-I-IV" },
// { fn: () => matchVampPattern(["I","V","vi","IV"]), expect: null },
// { fn: () => detectVampRun(["IV","I"], ["IV","I","IV","I","IV","I","V","V"]).runLength, expect: 3 },
// { fn: () => detectVampRun(["IV","I"], ["IV","I","IV","I","IV","I","V","V"]).breakNumeral, expect: "V" },
