import { useState, useRef, useCallback } from 'react'
import { BEAT_W, BEAT_GAP, ROW_H, beatMap, freeRuns } from '../../utils/harmonyEngine'
import { getChordAccent, hexToRgba } from '../../utils/chordUtils'

function ChordEvent({ ev, section, onResize, onContextMenu }) {
  const accent  = getChordAccent(ev.label);
  const dragRef = useRef(null);
  const [dragging,    setDragging]    = useState(false);
  const [previewSpan, setPreviewSpan] = useState(ev.span);

  const map = beatMap(section);
  let maxSpan=1;
  for(let b=ev.beat+1;b<section.totalBeats;b++){
    if(map[b]!==null&&map[b]!==ev)break;
    maxSpan=b-ev.beat+1;
  }
  maxSpan=Math.min(maxSpan,section.totalBeats-ev.beat);

  const handleDragStart = e => {
    e.preventDefault(); e.stopPropagation();
    dragRef.current={startX:e.clientX,startSpan:ev.span};
    setDragging(true); setPreviewSpan(ev.span);
    const onMove=me=>{
      const dx=me.clientX-dragRef.current.startX;
      const delta=Math.round(dx/(BEAT_W+BEAT_GAP));
      setPreviewSpan(Math.max(1,Math.min(dragRef.current.startSpan+delta,maxSpan)));
    };
    const onUp=me=>{
      const dx=me.clientX-dragRef.current.startX;
      const delta=Math.round(dx/(BEAT_W+BEAT_GAP));
      setDragging(false);
      onResize(ev,Math.max(1,Math.min(dragRef.current.startSpan+delta,maxSpan)));
      window.removeEventListener("mousemove",onMove);
      window.removeEventListener("mouseup",onUp);
    };
    window.addEventListener("mousemove",onMove);
    window.addEventListener("mouseup",onUp);
  };

  const span  = dragging?previewSpan:ev.span;
  const width = span*BEAT_W+(span-1)*BEAT_GAP;

  return (
    <div onContextMenu={e=>onContextMenu(e,ev)} style={{
      position:"absolute", left:ev.beat*(BEAT_W+BEAT_GAP), top:0,
      width, height:ROW_H, borderRadius:5,
      border:`2px solid ${hexToRgba(accent,dragging?0.95:0.7)}`,
      background: dragging
        ? hexToRgba(accent,0.28)
        : `linear-gradient(160deg,${hexToRgba(accent,0.22)} 0%,${hexToRgba(accent,0.14)} 100%)`,
      boxShadow: dragging
        ? `0 0 22px ${hexToRgba(accent,0.5)}, inset 0 1px 0 ${hexToRgba(accent,0.3)}`
        : `0 2px 8px ${hexToRgba(accent,0.25)}, inset 0 1px 0 rgba(255,240,220,0.4)`,
      color:accent, display:"flex", alignItems:"center", paddingLeft:6,
      fontSize:10, fontFamily:"'DM Mono',monospace", fontWeight:700,
      userSelect:"none", overflow:"hidden",
      transition:dragging?"none":"width 0.12s,box-shadow 0.12s",
      cursor:"default", zIndex:dragging?10:1,
    }}>
      <span style={{flex:1,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis",
        letterSpacing:"-0.02em",
        textShadow:`0 0 8px ${hexToRgba(accent,0.4)}`}}>{ev.label}</span>
      <span style={{fontSize:7,opacity:0.55,marginRight:11,fontWeight:500}}>{span}b</span>
      <div onMouseDown={handleDragStart} style={{
        position:"absolute",right:0,top:0,width:10,height:ROW_H,
        cursor:"ew-resize",display:"flex",alignItems:"center",justifyContent:"center",
        borderRadius:"0 4px 4px 0",
      }}
        onMouseEnter={e=>e.currentTarget.style.background=hexToRgba(accent,0.3)}
        onMouseLeave={e=>{if(!dragging)e.currentTarget.style.background="transparent";}}>
        <svg width={4} height={12} viewBox="0 0 4 12" style={{opacity:0.55}}>
          <rect x={0.5} y={1} width={1} height={10} rx={0.5} fill={accent}/>
          <rect x={2.5} y={1} width={1} height={10} rx={0.5} fill={accent}/>
        </svg>
      </div>
    </div>
  );
}

// ─── Empty beat with + hint ──────────────────────────────────────────────────
function EmptyBeat({ beat, sectionId, onAddChord }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onContextMenu={e=>onAddChord(e,sectionId,beat)}
      onMouseEnter={()=>setHov(true)}
      onMouseLeave={()=>setHov(false)}
      title="Right-click to add chord"
      style={{
        position:"absolute", left:beat*(BEAT_W+BEAT_GAP),
        top:0, width:BEAT_W, height:ROW_H,
        cursor:"context-menu", borderRadius:3, zIndex:2,
        display:"flex", alignItems:"center", justifyContent:"center",
        background: hov ? "rgba(100,65,25,0.1)" : "transparent",
        transition:"background 0.1s",
      }}>
      {hov && (
        <span style={{
          fontSize:14, color:"rgba(100,65,25,0.45)",
          fontWeight:"300", lineHeight:1,
          pointerEvents:"none", userSelect:"none",
        }}>+</span>
      )}
    </div>
  );
}

// ─── ScrubField: drag up = increase, drag down = decrease ────────────────────
// PX_PER_STEP controls sensitivity — lower = more sensitive
const PX_PER_STEP = 10;

function ScrubField({ value, min, max, label, suffix, onChange }) {
  const [scrubbing, setScrubbing] = useState(false);
  const [preview,   setPreview]   = useState(value);
  const [hov,       setHov]       = useState(false);
  const ref = useRef(null);

  const handleMouseDown = useCallback(e => {
    e.preventDefault(); e.stopPropagation();
    const startY   = e.clientY;
    const startVal = value;
    setScrubbing(true);
    setPreview(value);

    // Lock cursor to n-resize globally while scrubbing
    const overlay = document.createElement("div");
    overlay.style.cssText = "position:fixed;inset:0;z-index:99999;cursor:ns-resize;";
    document.body.appendChild(overlay);

    const onMove = me => {
      const dy    = startY - me.clientY;           // up = positive
      const delta = Math.round(dy / PX_PER_STEP);
      const next  = Math.max(min, Math.min(max, startVal + delta));
      setPreview(next);
    };
    const onUp = me => {
      const dy    = startY - me.clientY;
      const delta = Math.round(dy / PX_PER_STEP);
      const next  = Math.max(min, Math.min(max, startVal + delta));
      setScrubbing(false);
      if (next !== value) onChange(next);
      document.body.removeChild(overlay);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup",   onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup",   onUp);
  }, [value, min, max, onChange]);

  const display = scrubbing ? preview : value;
  const pct     = (display - min) / (max - min); // 0–1 for fill bar

  return (
    <div ref={ref}
      onMouseDown={handleMouseDown}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      title={`${label}: drag up/down`}
      style={{
        position: "relative",
        display: "inline-flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        width: 28, height: 32,
        borderRadius: 4,
        border: `1px solid ${scrubbing ? "rgba(100,65,25,0.4)" : hov ? "rgba(100,65,25,0.25)" : "rgba(100,65,25,0.15)"}`,
        background: scrubbing ? "rgba(100,65,25,0.08)" : hov ? "rgba(100,65,25,0.04)" : "rgba(100,65,25,0.02)",
        cursor: "ns-resize",
        userSelect: "none",
        transition: "border 0.1s, background 0.1s",
        overflow: "hidden",
      }}>
      {/* Fill bar — grows from bottom */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        height: `${pct * 100}%`,
        background: scrubbing ? "rgba(100,65,25,0.1)" : "rgba(100,65,25,0.05)",
        transition: scrubbing ? "none" : "height 0.15s",
        pointerEvents: "none",
      }}/>
      {/* Value */}
      <span style={{
        position: "relative",
        fontSize: 10, fontWeight: scrubbing ? "600" : "500",
        color: scrubbing ? "#5a3010" : hov ? "#7a4e1a" : "#8a6030",
        fontFamily: "'DM Mono',monospace",
        lineHeight: 1,
        transition: "color 0.1s, font-weight 0.1s",
      }}>{display}</span>
      {/* Label */}
      <span style={{
        position: "relative",
        fontSize: 6.5, color: scrubbing ? "#7a4e1a" : "rgba(100,65,25,0.5)",
        fontFamily: "'DM Mono',monospace",
        letterSpacing: "0.04em", marginTop: 2,
        transition: "color 0.1s",
      }}>{suffix}</span>
      {/* Scrub arrows hint */}
      {(hov || scrubbing) && (
        <div style={{
          position: "absolute", right: -18, top: "50%",
          transform: "translateY(-50%)",
          display: "flex", flexDirection: "column", alignItems: "center", gap: 1,
          pointerEvents: "none",
        }}>
          <span style={{fontSize:7, color:"rgba(100,65,25,0.4)", lineHeight:1}}>▲</span>
          <span style={{fontSize:7, color:"rgba(100,65,25,0.4)", lineHeight:1}}>▼</span>
        </div>
      )}
    </div>
  );
}

function SectionRow({ section, onAddChord, onResizeChord, onEditChord, onChangeMeter }) {
  const { timeSig, bars, totalBeats } = section;
  const rowWidth = totalBeats*BEAT_W+(totalBeats-1)*BEAT_GAP;
  const runs = freeRuns(section);

  return (
    <div style={{display:"flex",alignItems:"flex-start",gap:10,paddingBottom:4}}>
      {/* Label + scrub meter */}
      <div style={{width:64,flexShrink:0,paddingTop:14,cursor:"default"}}>
        <div style={{fontSize:9,letterSpacing:"0.08em",color:"rgba(60,35,10,0.85)",textAlign:"right",marginBottom:6,fontWeight:"600"}}>
          {section.name.toUpperCase()}
        </div>
        {/* Two scrub fields side by side with a × separator */}
        <div style={{display:"flex",alignItems:"center",justifyContent:"flex-end",gap:5}}>
          <ScrubField value={timeSig} min={2} max={7} label="time sig" suffix="/ 4"
            onChange={v => onChangeMeter(section.id, v, bars)}/>
          <span style={{fontSize:8,color:"rgba(120,80,30,0.35)",fontFamily:"'DM Mono',monospace",
            lineHeight:1,flexShrink:0}}>×</span>
          <ScrubField value={bars} min={1} max={16} label="bars" suffix="bars"
            onChange={v => onChangeMeter(section.id, timeSig, v)}/>
        </div>
        {/* Key + mode tag */}
        <div style={{
          display:"flex", justifyContent:"flex-end", marginTop:5,
        }}>
          <span style={{
            fontSize:7, fontFamily:"'DM Mono',monospace", fontWeight:"600",
            color:"rgba(60,35,10,0.55)",
            background:"rgba(100,65,25,0.1)",
            border:"1px solid rgba(100,65,25,0.2)",
            borderRadius:3, padding:"1px 5px",
            letterSpacing:"0.04em", whiteSpace:"nowrap",
          }}>{section.key ?? "C"} {section.mode ? section.mode.slice(0,3).toUpperCase() : "MAJ"}</span>
        </div>
      </div>

      {/* Divider */}
      <div style={{width:1,height:ROW_H+16,background:"rgba(120,80,30,0.2)",flexShrink:0,marginTop:16}}/>

      {/* Timeline area */}
      <div style={{display:"flex",flexDirection:"column",gap:2,paddingTop:0}}>
        {/* Bar number row */}
        <div style={{display:"flex",marginTop:2,marginBottom:1}}>
          {Array.from({length:bars}).map((_,bar)=>(
            <div key={bar} style={{
              width:timeSig*BEAT_W+(timeSig-1)*BEAT_GAP,
              marginRight:bar<bars-1?BEAT_GAP:0,
              fontSize:9,color:"rgba(80,45,10,0.8)",fontFamily:"'DM Mono',monospace",
              fontWeight:"700",
              textAlign:"center",lineHeight:"14px",height:14,
              borderBottom:`2px solid rgba(100,60,15,0.45)`,
              letterSpacing:"0.04em",
            }}>{bar+1}</div>
          ))}
        </div>

        {/* Beat grid + chords */}
        <div style={{position:"relative",width:rowWidth,height:ROW_H,flexShrink:0}}>
          {Array.from({length:totalBeats}).map((_,i)=>{
            const isBar=i%timeSig===0;
            const beatNum=i%timeSig; // 0=bar start, 1,2,3...
            return (
              <div key={i} style={{
                position:"absolute",left:i*(BEAT_W+BEAT_GAP),top:0,
                width:BEAT_W,height:ROW_H,boxSizing:"border-box",
                border:`1px solid ${isBar?"rgba(100,65,25,0.45)":"rgba(100,65,25,0.18)"}`,
                borderLeft:isBar&&i>0?"2.5px solid rgba(100,65,25,0.55)":undefined,
                borderRadius:3,
                background: isBar
                  ? "rgba(100,65,25,0.07)"
                  : "rgba(100,65,25,0.02)",
              }}>
                {/* Beat number inside cell */}
                <span style={{
                  position:"absolute",bottom:3,right:4,
                  fontSize:6.5,fontFamily:"'DM Mono',monospace",fontWeight:"600",
                  color:`rgba(100,65,25,${isBar?0.5:0.25})`,
                  pointerEvents:"none",userSelect:"none",lineHeight:1,
                }}>{isBar?"1":beatNum+1}</span>
              </div>
            );
          })}

          {/* Empty beat targets */}
          {runs.map(run=>
            Array.from({length:run.span}).map((_,i)=>{
              const beat=run.beat+i;
              return (
                <EmptyBeat key={beat} beat={beat} sectionId={section.id} onAddChord={onAddChord}/>
              );
            })
          )}

          {/* Chord events */}
          {section.events.map(ev=>(
            <ChordEvent key={ev.id} ev={ev} section={section}
              onResize={onResizeChord}
              onContextMenu={(e,ev)=>onEditChord(e,section.id,ev)}/>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChordCanvas({ song, onAddChord, onResizeChord, onEditChord, onChangeMeter }) {
  return (
    <div style={{padding:"16px 16px 24px",overflowY:"auto",height:"100%",boxSizing:"border-box"}}>
      <div style={{fontSize:8,letterSpacing:"0.18em",color:"rgba(100,65,25,0.45)",marginBottom:14}}>
        CHORD CANVAS
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:10}}>
        {song.map(section=>(
          <SectionRow key={section.id} section={section}
            onAddChord={onAddChord} onResizeChord={onResizeChord}
            onEditChord={onEditChord} onChangeMeter={onChangeMeter}/>
        ))}
      </div>
      <div style={{marginTop:20,fontSize:8,color:"rgba(100,65,25,0.35)",letterSpacing:"0.06em",lineHeight:1.8}}>
        HOVER LABEL → SET BARS · RIGHT-CLICK BEAT → ADD CHORD · DRAG EDGE → RESIZE
      </div>
    </div>
  );
}
