/**
 * LALO music theory constants — shared across all components.
 * Data only, no logic, no JSX.
 */

export const ROOTS = ["C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B"];

// ── Qualities ──────────────────────────────────────────────────────────────
// dom removed (redundant: maj + 7 = C7, the dominant 7th)
// ø (half-dim) added: m7b5 — ii° in minor keys, very common
// °7 (full-dim) added: distinct from dim triad — all minor 3rds stacked
// Notes on extension compatibility per quality:
//   maj:  7→C7(dom7), maj7→Cmaj7, 9→C9, 11→C11, 13→C13, 6→C6, add9→Cadd9
//   min:  7→Cm7,      maj7→CmMaj7, 9→Cm9, 11→Cm11, 13→Cm13, 6→Cm6, add9→Cmadd9
//   dim:  triad only — 7/9/11/13/maj7 are invalid; use °7 quality for dim7
//   °7:   no extensions — the chord is already fully defined (4-note)
//   ø:    7 only → Cø7 (= Cm7b5); other extensions possible but uncommon
//   aug:  maj7→CaugMaj7 useful; 7→Caug7 valid; others unusual
//   sus2: 7→Csus2/7 occasionally; mostly triad
//   sus4: 7→C7sus4 very common; 9→C9sus4 common
//   5:    no extensions make sense (power chord)
export const QUALITIES = [
  { label:"maj",  symbol:"",    accent:"#5a3e1a" }, // neutral warm brown
  { label:"min",  symbol:"m",   accent:"#3a6ea8" }, // blue
  { label:"dim",  symbol:"°",   accent:"#b54040" }, // red
  { label:"°7",   symbol:"°7",  accent:"#8b2020" }, // deep red — full diminished
  { label:"ø",    symbol:"ø",   accent:"#c05050" }, // lighter red — half-dim
  { label:"aug",  symbol:"+",   accent:"#c07030" }, // orange
  { label:"sus2", symbol:"sus2",accent:"#3a8a5a" }, // green
  { label:"sus4", symbol:"sus4",accent:"#2a7a7a" }, // teal
  { label:"5",    symbol:"5",   accent:"#7a7a7a" }, // grey — power chord
];

// ── Extensions ────────────────────────────────────────────────────────────
// Ordered from simplest to richest.
// "—" = no extension (triad only)
// 7   = minor 7th on top of quality (dominant-style on maj, minor on min)
// maj7 = major 7th interval
// 6   = added 6th (no 7th)
// add9 = added 9th (no 7th)
// 9   = 7th + 9th
// 11  = 7th + 9th + 11th
// 13  = 7th + 9th + 11th + 13th
// °7 and 5 qualities ignore extensions — enforced in label builder below
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

// ── Inversions ────────────────────────────────────────────────────────────
// Positional — not hardcoded pitch names (those depend on root+quality).
// 3rd inversion only valid when a 7th-type extension is present.
export const INVERSIONS = [
  { label:"root", symbol:""    },
  { label:"1st",  symbol:"/1"  }, // bass = 3rd of chord
  { label:"2nd",  symbol:"/2"  }, // bass = 5th of chord
  { label:"3rd",  symbol:"/3"  }, // bass = 7th — only with 7th extensions
];
