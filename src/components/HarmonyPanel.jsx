/**
 * HarmonyPanel — Roman numeral analysis per section
 *
 * Architecture notes:
 *   - Zero imports from other LALO UI components — fully standalone
 *   - Accepts either props (current canvas wiring) or reads from
 *     useSongStore (future Zustand drop-in — just swap the top few lines)
 *   - Pure display: all analysis done in core/theory functions that
 *     already exist in MusicTheoryEngine.ts — no duplication
 *   - Ready to accept MIR import data (McGill, SALAMI, JAMS) as-is
 *
 * To wire to Zustand later:
 *   const { song } = useSongStore()   ← replace the `song` prop
 *
 * Compatible with: lalo-chord-schema.ts SongSection / ChordEvent shape
 */

import { useState, useMemo } from "react";
import {
  analyzeChord as coreAnalyzeChord,
  buildMotionSummary as coreMotionSummary,
} from "@lalo/core";
import { useSongStore, selectSongSummary } from "../store/useSongStore";

// ── UI colour tokens — maps HarmonicStrength → visual theme ─────────────────
// ROOTS, DIATONIC_SCALE, DEGREE_QUALITY are now centralised in @lalo/core.
const STRENGTH_COLORS = {
  strong:    { bg:"rgba(42,122,58,0.15)",  border:"rgba(42,122,58,0.5)",  text:"#1a5c28",  label:"strong"    },
  medium:    { bg:"rgba(176,120,32,0.12)", border:"rgba(176,120,32,0.4)", text:"#7a5010",  label:"medium"    },
  weak:      { bg:"rgba(122,96,80,0.10)",  border:"rgba(122,96,80,0.3)",  text:"#5a4030",  label:"weak"      },
  dissonant: { bg:"rgba(176,48,48,0.12)",  border:"rgba(176,48,48,0.4)",  text:"#8b1a1a",  label:"dissonant" },
  same:      { bg:"rgba(58,110,168,0.12)", border:"rgba(58,110,168,0.4)", text:"#1a3a6a",  label:"unison"    },
  borrowed:  { bg:"rgba(140,80,168,0.12)", border:"rgba(140,80,168,0.4)", text:"#5a1a7a",  label:"borrowed"  },
};

// ── Core analysis adapter ────────────────────────────────────────────────────
// Calls @lalo/core's pure analyzeChord, then enriches with UI colour data
// and extension superscripts (display concern only).
function analyzeChord(ev, sectionKey, sectionMode) {
  const core = coreAnalyzeChord(ev, sectionKey ?? "C", sectionMode ?? "major");

  // Append extension superscripts to roman numeral for display
  let roman = core.roman;
  if (roman) {
    const exts = ev.extensions ?? [];
    if (exts.includes("maj7"))      roman += "ᴹ⁷";
    else if (exts.includes("7"))    roman += "⁷";
    if (exts.includes("9"))         roman += "⁹";
  }

  return {
    ...core,
    roman,
    color: STRENGTH_COLORS[core.isBorrowed ? "borrowed" : core.strength]
        ?? STRENGTH_COLORS.weak,
  };
}

function buildMotionSummary(analyses) {
  if (!analyses.length) return null;
  return coreMotionSummary(analyses);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ChordPill({ ev, analysis, isHovered, onHover }) {
  const c = analysis.color;
  const exts = (ev.extensions ?? []).filter(e => e !== "7" && e !== "maj7");

  return (
    <div
      onMouseEnter={() => onHover(ev.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        gap: 3, cursor: "default",
        opacity: isHovered === null || isHovered === ev.id ? 1 : 0.45,
        transition: "opacity 0.15s",
      }}>

      {/* Duration bar above */}
      <div style={{
        width: `${Math.min(100, (ev.durationBeats ?? ev.span ?? 1) * 18)}px`,
        height: 3, borderRadius: 2,
        background: c.border, opacity: 0.6,
        minWidth: 18,
      }}/>

      {/* Main pill */}
      <div style={{
        background: isHovered === ev.id ? c.border : c.bg,
        border: `1.5px solid ${c.border}`,
        borderRadius: 6, padding: "6px 10px",
        minWidth: 48, textAlign: "center",
        transition: "background 0.12s",
        boxShadow: isHovered === ev.id
          ? `0 2px 12px ${c.border}`
          : "0 1px 3px rgba(0,0,0,0.08)",
      }}>
        {/* Chord label */}
        <div style={{
          fontSize: 13, fontWeight: 700,
          color: isHovered === ev.id ? "white" : c.text,
          fontFamily: "'DM Mono',monospace",
          lineHeight: 1,
        }}>{ev.label ?? "?"}</div>

        {/* Roman numeral */}
        <div style={{
          fontSize: 10, fontWeight: 600,
          color: isHovered === ev.id ? "rgba(255,255,255,0.85)" : c.text,
          fontFamily: "'DM Mono',monospace",
          marginTop: 3, lineHeight: 1,
          opacity: 0.85,
        }}>{analysis.roman ?? "—"}</div>
      </div>

      {/* Beat label below */}
      <div style={{
        fontSize: 7, color: "rgba(80,50,20,0.45)",
        fontFamily: "'DM Mono',monospace",
        letterSpacing: "0.04em",
      }}>b{(ev.beat ?? 0) + 1}</div>
    </div>
  );
}

function SectionPanel({ section, isExpanded, onToggle }) {
  const [hovered, setHovered] = useState(null);

  // Build analyses keyed by event id — stable even when event order changes
  const analysesById = useMemo(() => {
    const m = {};
    for (const ev of section.events ?? []) {
      m[ev.id] = analyzeChord(ev, section.key, section.mode);
    }
    return m;
  }, [section.events, section.key, section.mode]);

  // Ordered array for summary / motion row (preserves section.events order)
  const analyses = useMemo(() =>
    (section.events ?? []).map(ev => analysesById[ev.id]).filter(Boolean),
    [section.events, analysesById]
  );

  const summary = useMemo(() => buildMotionSummary(analyses), [analyses]);

  const key    = section.key   ?? "C";
  const mode   = section.mode  ?? "major";
  const bpm    = section.bpm   ?? 120;
  const timeSig= section.timeSig ?? 4;
  const bars   = section.bars  ?? 2;

  const hoveredAnalysis = hovered ? (analysesById[hovered] ?? null) : null;
  const hoveredEv = hovered ? section.events.find(e => e.id === hovered) : null;

  return (
    <div style={{
      background: "rgba(232,212,184,0.6)",
      border: "1px solid rgba(100,65,25,0.2)",
      borderRadius: 8, overflow: "hidden",
      boxShadow: "0 1px 4px rgba(80,50,20,0.08)",
    }}>

      {/* Section header */}
      <div
        onClick={onToggle}
        style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "10px 14px", cursor: "pointer",
          background: isExpanded ? "rgba(100,65,25,0.08)" : "transparent",
          borderBottom: isExpanded ? "1px solid rgba(100,65,25,0.15)" : "none",
          transition: "background 0.12s",
          userSelect: "none",
        }}>

        {/* Expand arrow */}
        <span style={{
          fontSize: 9, color: "rgba(100,65,25,0.5)",
          transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
          transition: "transform 0.15s", display: "inline-block",
        }}>▶</span>

        {/* Section name */}
        <span style={{
          fontSize: 11, fontWeight: 700,
          color: "rgba(60,35,10,0.9)",
          fontFamily: "'DM Mono',monospace",
          letterSpacing: "0.06em", flex: 1,
        }}>{(section.name ?? "Section").toUpperCase()}</span>

        {/* Key/mode pill */}
        <span style={{
          fontSize: 8, fontWeight: 600,
          color: "rgba(80,50,20,0.7)",
          background: "rgba(100,65,25,0.12)",
          border: "1px solid rgba(100,65,25,0.2)",
          borderRadius: 4, padding: "2px 6px",
          fontFamily: "'DM Mono',monospace",
          letterSpacing: "0.04em",
        }}>{key} {mode.slice(0,3).toUpperCase()}</span>

        {/* Meta */}
        <span style={{
          fontSize: 8, color: "rgba(100,65,25,0.5)",
          fontFamily: "'DM Mono',monospace",
        }}>{bars}×{timeSig}  {bpm}bpm</span>

        {/* Summary badges */}
        {summary && (
          <div style={{ display:"flex", gap:4 }}>
            {summary.diatonic > 0 && (
              <span style={{
                fontSize:7, padding:"1px 5px", borderRadius:3,
                background: STRENGTH_COLORS.strong.bg,
                border: `1px solid ${STRENGTH_COLORS.strong.border}`,
                color: STRENGTH_COLORS.strong.text,
                fontFamily:"'DM Mono',monospace",fontWeight:600,
              }}>{summary.diatonic}d</span>
            )}
            {summary.borrowed > 0 && (
              <span style={{
                fontSize:7, padding:"1px 5px", borderRadius:3,
                background: STRENGTH_COLORS.borrowed.bg,
                border: `1px solid ${STRENGTH_COLORS.borrowed.border}`,
                color: STRENGTH_COLORS.borrowed.text,
                fontFamily:"'DM Mono',monospace",fontWeight:600,
              }}>{summary.borrowed}b</span>
            )}
            {summary.nonDiat > 0 && (
              <span style={{
                fontSize:7, padding:"1px 5px", borderRadius:3,
                background: STRENGTH_COLORS.weak.bg,
                border: `1px solid ${STRENGTH_COLORS.weak.border}`,
                color: STRENGTH_COLORS.weak.text,
                fontFamily:"'DM Mono',monospace",fontWeight:600,
              }}>{summary.nonDiat}✕</span>
            )}
          </div>
        )}
      </div>

      {/* Expanded body */}
      {isExpanded && (
        <div style={{ padding: "14px 16px", display:"flex", flexDirection:"column", gap:12 }}>

          {/* Chord pills row */}
          {section.events?.length > 0 ? (
            <div style={{
              display:"flex", flexWrap:"wrap", gap:10, alignItems:"flex-end",
            }}>
              {section.events.map(ev => (
                <ChordPill
                  key={ev.id}
                  ev={ev}
                  analysis={analysesById[ev.id]}
                  isHovered={hovered}
                  onHover={setHovered}
                />
              ))}
            </div>
          ) : (
            <div style={{
              fontSize:9, color:"rgba(100,65,25,0.4)",
              fontFamily:"'DM Mono',monospace",
              fontStyle:"italic", padding:"8px 0",
            }}>No chords in this section yet.</div>
          )}

          {/* Hover detail card */}
          {hoveredEv && hoveredAnalysis && (
            <div style={{
              background: hoveredAnalysis.color.bg,
              border: `1.5px solid ${hoveredAnalysis.color.border}`,
              borderRadius:6, padding:"10px 14px",
              display:"flex", gap:16, alignItems:"flex-start",
              transition:"all 0.15s",
            }}>
              <div>
                <div style={{
                  fontSize:18, fontWeight:700,
                  color: hoveredAnalysis.color.text,
                  fontFamily:"'DM Mono',monospace", lineHeight:1,
                }}>{hoveredEv.label}</div>
                <div style={{
                  fontSize:11, color: hoveredAnalysis.color.text,
                  fontFamily:"'DM Mono',monospace", marginTop:3, opacity:0.8,
                }}>{hoveredAnalysis.roman ?? "—"} &nbsp;·&nbsp; {hoveredAnalysis.relationName}</div>
              </div>
              <div style={{ flex:1 }}>
                {hoveredEv.bassNote && (
                  <div style={{ fontSize:8, color:hoveredAnalysis.color.text, fontFamily:"'DM Mono',monospace", opacity:0.8 }}>
                    bass: {hoveredEv.bassNote} (slash chord)
                  </div>
                )}
                {(hoveredEv.extensions ?? []).length > 0 && (
                  <div style={{ fontSize:8, color:hoveredAnalysis.color.text, fontFamily:"'DM Mono',monospace", opacity:0.8 }}>
                    extensions: {hoveredEv.extensions.join(", ")}
                  </div>
                )}
                <div style={{ fontSize:8, color:hoveredAnalysis.color.text, fontFamily:"'DM Mono',monospace", opacity:0.8 }}>
                  beat: {(hoveredEv.beatFloat ?? hoveredEv.beat ?? 0) + 1}
                  &nbsp;·&nbsp; duration: {hoveredEv.durationBeats ?? hoveredEv.span ?? 1} beats
                </div>
                <div style={{
                  marginTop:4,
                  fontSize:8, fontWeight:600,
                  color: hoveredAnalysis.color.text,
                  fontFamily:"'DM Mono',monospace",
                  textTransform:"uppercase", letterSpacing:"0.06em",
                  opacity:0.7,
                }}>{hoveredAnalysis.color.label}</div>
              </div>
            </div>
          )}

          {/* Summary bar */}
          {summary && section.events?.length > 1 && (
            <div style={{
              borderTop:"1px solid rgba(100,65,25,0.15)",
              paddingTop:10,
              display:"flex", flexDirection:"column", gap:6,
            }}>

              {/* Cadence detection */}
              {summary.cadence && (
                <div style={{
                  fontSize:9, fontWeight:600,
                  color:"rgba(60,35,10,0.75)",
                  fontFamily:"'DM Mono',monospace",
                  letterSpacing:"0.04em",
                }}>⟳ {summary.cadence}</div>
              )}

              {/* Roman numeral sequence */}
              <div style={{
                display:"flex", alignItems:"center", gap:6, flexWrap:"wrap",
              }}>
                <span style={{
                  fontSize:7, color:"rgba(100,65,25,0.5)",
                  fontFamily:"'DM Mono',monospace", letterSpacing:"0.08em",
                }}>MOTION</span>
                {analyses.map((a, i) => (
                  <span key={i} style={{
                    fontSize:9, fontWeight:700,
                    color: a.color.text,
                    fontFamily:"'DM Mono',monospace",
                  }}>
                    {a.roman ?? "?"}{i < analyses.length-1 ? " →" : ""}
                  </span>
                ))}
              </div>

              {/* Diatonic breakdown bar */}
              <div style={{ display:"flex", gap:3, alignItems:"center" }}>
                <span style={{
                  fontSize:7, color:"rgba(100,65,25,0.5)",
                  fontFamily:"'DM Mono',monospace", letterSpacing:"0.08em",
                  width:46,
                }}>COLOUR</span>
                <div style={{
                  flex:1, height:6, borderRadius:3,
                  background:"rgba(100,65,25,0.1)",
                  display:"flex", overflow:"hidden",
                }}>
                  {summary.diatonic > 0 && (
                    <div style={{
                      flex: summary.diatonic,
                      background: STRENGTH_COLORS.strong.border,
                      opacity:0.7,
                    }}/>
                  )}
                  {summary.borrowed > 0 && (
                    <div style={{
                      flex: summary.borrowed,
                      background: STRENGTH_COLORS.borrowed.border,
                      opacity:0.7,
                    }}/>
                  )}
                  {summary.nonDiat > 0 && (
                    <div style={{
                      flex: summary.nonDiat,
                      background: STRENGTH_COLORS.dissonant.border,
                      opacity:0.5,
                    }}/>
                  )}
                </div>
                <span style={{
                  fontSize:7, color:"rgba(100,65,25,0.45)",
                  fontFamily:"'DM Mono',monospace",
                }}>
                  {summary.diatonic}d {summary.borrowed}b {summary.nonDiat}✕
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

/**
 * HarmonyPanel
 *
 * Props:
 *   song       — array of SongSection (from canvas state or Zustand store)
 *   className  — optional CSS class for outer container
 *   style      — optional style override
 *
 * Future: replace `song` prop with `const { song } = useSongStore()`
 */
export default function HarmonyPanel({ song: songProp, style = {} }) {
  const storeSong = useSongStore(state => state.song);
  const summary = useSongStore(selectSongSummary);
  const song = songProp ?? storeSong;
  const [expanded, setExpanded] = useState(() =>
    Object.fromEntries(song.map(s => [s.id, true]))
  );

  const toggle = id =>
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  // Overall song stats
  const allEvents  = song.flatMap(s => s.events ?? []);
  const totalChords = allEvents.length;
  const uniqueLabels = new Set(allEvents.map(e => e.label)).size;

  return (
    <div style={{
      fontFamily: "'DM Mono',monospace",
      display: "flex", flexDirection: "column", gap: 0,
      ...style,
    }}>
      {/* Panel header */}
      <div style={{
        display:"flex", alignItems:"center", justifyContent:"space-between",
        padding:"10px 16px 8px",
        borderBottom:"1px solid rgba(100,65,25,0.15)",
      }}>
        <div style={{
          fontSize:8, letterSpacing:"0.18em",
          color:"rgba(100,65,25,0.55)", fontWeight:600,
        }}>HARMONY ANALYSIS</div>
        <div style={{
          display:"flex", gap:10, alignItems:"center",
        }}>
          {totalChords > 0 && (
            <>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {totalChords} chords
              </span>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {uniqueLabels} unique
              </span>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {summary.typeCount} types
              </span>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {summary.instanceCount} instances
              </span>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {summary.vampCount} vamps
              </span>
              <span style={{ fontSize:8, color:"rgba(100,65,25,0.4)" }}>
                {summary.namedCount} named
              </span>
            </>
          )}
          <div style={{ display:"flex", gap:8 }}>
            {[
              { label:"d", ...STRENGTH_COLORS.strong,  title:"diatonic"  },
              { label:"b", ...STRENGTH_COLORS.borrowed, title:"borrowed"  },
              { label:"✕", ...STRENGTH_COLORS.weak,    title:"chromatic" },
            ].map(({ label, bg, border, text, title }) => (
              <span key={label} title={title} style={{
                fontSize:7, padding:"1px 5px", borderRadius:3,
                background:bg, border:`1px solid ${border}`,
                color:text, fontWeight:600,
              }}>{label} = {title}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Sections */}
      <div style={{
        display:"flex", flexDirection:"column", gap:6,
        padding:"10px 12px 16px",
        overflowY:"auto",
      }}>
        {song.length === 0 ? (
          <div style={{
            fontSize:9, color:"rgba(100,65,25,0.4)",
            textAlign:"center", padding:"24px 0",
            fontStyle:"italic",
          }}>Add chords to the canvas to see analysis.</div>
        ) : (
          song.map(section => (
            <SectionPanel
              key={section.id}
              section={section}
              isExpanded={!!expanded[section.id]}
              onToggle={() => toggle(section.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
