import { useState, useEffect, useRef, useCallback } from 'react';
import { ROOTS, QUALITIES, EXTENSIONS, INVERSIONS } from '../../constants/music';
import { polar, arcPath, hexToRgba, buildChordLabel, suggestedLabel } from '../../utils/chordUtils';
import { analyzeInterval } from '../../utils/harmonyEngine';

const DEFAULT_CHORD = { root:null, quality:0, extension:0, inversion:0 };

// ═══════════════════════════════════════════════════════════════════════════════
// RADIAL MENU — Ring (bubble slices with glow)
// ═══════════════════════════════════════════════════════════════════════════════

function Ring({ cx,cy,r1,r2,items,selected,hovered,onSelect,onHover,getAccent,getLabel,visible,animDelay=0,startAngle=0,span=360 }) {
  const count   = items.length;
  const degStep = span/count;
  const [mounted, setMounted] = useState(false);
  useEffect(()=>{
    if(visible){
      const t = setTimeout(()=>setMounted(true), animDelay*1000+16);
      return ()=>clearTimeout(t);
    } else {
      setMounted(false);
    }
  },[visible, animDelay]);

  const show = visible && mounted;

  return (
    <g style={{
      opacity: show ? 1 : 0,
      transition: "opacity 0.28s ease",
      pointerEvents: visible ? "auto" : "none",
    }}>
      {items.map((item,i) => {
        const s=startAngle+i*degStep, e=s+degStep, mid=s+degStep/2;
        const midPt   = polar(cx,cy,(r1+r2)/2,mid);
        const isSel   = selected===i;
        const isHov   = hovered===i && !isSel;
        const accent  = getAccent ? getAccent(item,i) : "#7a5c3a";
        const label   = getLabel  ? getLabel(item)    : String(item);
        const thickness = r2 - r1;
        const fs      = thickness > 36 ? 13 : thickness > 24 ? 11 : 9;
        const fillA   = isSel ? 0.32 : isHov ? 0.22 : 0.13;
        const strokeA = isSel ? 1.0  : isHov ? 0.7  : 0.38;
        const strokeW = isSel ? 2    : isHov ? 1.2  : 0.8;

        return (
          <g key={i}
            onClick={()=>onSelect(i)}
            onMouseEnter={()=>onHover(i)}
            onMouseLeave={()=>onHover(null)}
            style={{cursor:"pointer"}}>
            <path
              d={arcPath(cx,cy,r1,r2,s,e,1.8)}
              fill={hexToRgba(accent,fillA)}
              stroke={hexToRgba(accent,strokeA)}
              strokeWidth={strokeW}
              style={{
                transition:"fill 0.15s, stroke 0.15s",
                filter: isSel
                  ? `drop-shadow(0 0 7px ${hexToRgba(accent,0.85)}) drop-shadow(0 0 18px ${hexToRgba(accent,0.5)})`
                  : isHov
                  ? `drop-shadow(0 0 5px ${hexToRgba(accent,0.55)})`
                  : "none",
              }}
            />
            <text
              x={midPt.x} y={midPt.y}
              textAnchor="middle" dominantBaseline="central"
              fontSize={fs}
              fontFamily="'DM Mono',monospace"
              fontWeight="700"
              fill={isSel ? "#fff" : isHov ? hexToRgba(accent,1) : "rgba(30,15,0,0.85)"}
              style={{
                pointerEvents:"none", userSelect:"none",
                transition:"fill 0.12s",
                filter: isSel ? `drop-shadow(0 0 4px ${hexToRgba(accent,0.9)})` : "none",
              }}
            >{label}</text>
          </g>
        );
      })}
    </g>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// RADIAL MENU — Center (with harmonic context)
// ═══════════════════════════════════════════════════════════════════════════════

function Center({ cx,cy,chord,hover,step,prevChord,sectionKey="C",sectionMode="major",onConfirm,onClear,onCommitSuggestion,lockedRoot=null }) {
  const hasRoot  = chord.root!==null;
  const qObj     = QUALITIES[chord.quality??0];

  // What root is the user currently hovering / has selected?
  // lockedRoot preserves the last-hovered root ring slot so the suggestion
  // stays visible while the cursor travels from the ring to the center.
  const activeRoot = hasRoot ? chord.root : (hover.root ?? lockedRoot);

  // Harmonic analysis vs previous chord
  const harmonic = (prevChord && activeRoot !== null)
    ? analyzeInterval(prevChord.rootIdx, prevChord.qualityIdx, activeRoot, sectionKey, sectionMode)
    : null;

  // Suggested label from harmonic analysis (when hovering root ring, step=0)
  const sugLabel = (harmonic && !hasRoot && harmonic.sugQ !== null)
    ? suggestedLabel(activeRoot, harmonic.sugQ, harmonic.sugExt)
    : null;

  // Accent: harmonic color when hovering root, quality color once root picked
  const accent = hasRoot
    ? qObj.accent
    : (harmonic ? harmonic.color : "rgba(80,50,20,0.4)");

  // Main label to show
  const displayLabel = hasRoot
    ? buildChordLabel(chord.root, chord.quality, chord.extension, chord.inversion)
    : null;
  const previewRoot = hover.root ?? lockedRoot ?? chord.root;
  const previewLabel = !hasRoot && previewRoot !== null
    ? buildChordLabel(previewRoot, hover.quality ?? (harmonic?.sugQ ?? 0),
                      hover.extension ?? (harmonic?.sugExt ?? 0), hover.inversion ?? 0)
    : null;

  const shownLabel = displayLabel ?? previewLabel;
  const isPreview  = !displayLabel && !!previewLabel;
  const hQObj      = QUALITIES[hover.quality ?? chord.quality ?? 0];
  const RING_LABELS = ["ROOT","QUAL","EXT","INV"];

  // Previous chord display label
  const prevLabel = prevChord
    ? buildChordLabel(prevChord.rootIdx, prevChord.qualityIdx, prevChord.extensionIdx ?? 0, 0)
    : null;

  return (
    <g>
      {/* Previous chord — shown as small pill above the menu circle */}
      {prevLabel && (
        <g>
          {/* Pill background — to the left of the flat edge, visible via overflow */}
          <rect x={cx-72} y={cy-10} width={60} height={20} rx={10}
            fill="rgba(80,50,20,0.1)" stroke="rgba(80,50,20,0.25)" strokeWidth={1}/>
          <text x={cx-42} y={cy} textAnchor="middle" dominantBaseline="central"
            fill="rgba(80,50,20,0.7)" fontSize={9} fontFamily="'DM Mono',monospace" fontWeight="700"
            style={{userSelect:"none"}}>{prevLabel}</text>
          {/* Connector dot trail — horizontal, leading to the flat edge */}
          {[0,1,2].map(i=>(
            <circle key={i} cx={cx-10+i*4} cy={cy} r={1.5}
              fill="rgba(80,50,20,0.18)"/>
          ))}
        </g>
      )}

      {/* Center bubble — tinted by harmonic strength, non-interactive */}
      <circle cx={cx} cy={cy} r={46}
        fill={hexToRgba(accent, hasRoot ? 0.55 : harmonic ? 0.42 : 0.25)}
        stroke={hexToRgba(accent, hasRoot ? 0.95 : harmonic ? 0.85 : 0.55)}
        strokeWidth={hasRoot ? 2 : harmonic ? 1.8 : 1.2}
        style={{
          pointerEvents:"none",
          transition:"fill 0.18s,stroke 0.18s",
          filter: (hasRoot || harmonic)
            ? `drop-shadow(0 0 8px ${hexToRgba(accent,0.65)}) drop-shadow(0 0 20px ${hexToRgba(accent,0.3)})`
            : "none",
        }}
      />

      {/* Step dots */}
      {[0,1,2,3].map(i=>(
        <circle key={i} cx={cx-10.5+i*7} cy={cy+36} r={2.5}
          fill={i<step ? hexToRgba(accent,0.8) : "rgba(80,50,20,0.15)"}
          style={{pointerEvents:"none", transition:"fill 0.2s"}}/>
      ))}

      {/* Harmonic suggestion — clickable to commit directly */}
      {harmonic && !hasRoot && activeRoot !== null && (
        <>
          {/* Relationship name — non-interactive */}
          <text x={cx} y={cy - 20} textAnchor="middle" dominantBaseline="central"
            fill="rgba(20,10,0,0.75)" fontSize={7.5} fontFamily="'DM Mono',monospace" fontWeight="700"
            style={{userSelect:"none", letterSpacing:"0.05em", pointerEvents:"none"}}>
            {harmonic.name}
          </text>

          {sugLabel && (
            <g onClick={()=>onCommitSuggestion(activeRoot, harmonic.sugQ, harmonic.sugExt)}
              style={{cursor:"pointer", pointerEvents:"all"}}>

              {/* Hit area — fill:none + pointerEvents:all captures clicks without any visual flash */}
              <circle cx={cx} cy={cy} r={46} fill="none" stroke="none" style={{pointerEvents:"all"}}/>

              {/* Dashed orbit ring */}
              <circle cx={cx} cy={cy} r={43}
                fill="none"
                stroke={hexToRgba(harmonic.color, 0.4)}
                strokeWidth={1.5}
                strokeDasharray="3,4"
                style={{pointerEvents:"none",
                  animation:"rcm-spin 12s linear infinite",
                  transformOrigin:`${cx}px ${cy}px`}}
              />

              {/* Chord label */}
              <text x={cx} y={cy - 3} textAnchor="middle" dominantBaseline="central"
                fill={harmonic.color} fontSize={18} fontFamily="'DM Mono',monospace" fontWeight="700"
                style={{userSelect:"none",
                  filter:`drop-shadow(0 0 6px ${hexToRgba(harmonic.color,0.7)})`}}>
                {sugLabel}
              </text>

              {/* "tap to use" hint */}
              <text x={cx} y={cy+15} textAnchor="middle" dominantBaseline="central"
                fill="rgba(20,10,0,0.45)" fontSize={6.5}
                fontFamily="'DM Mono',monospace" fontWeight="600"
                style={{pointerEvents:"none", userSelect:"none", letterSpacing:"0.07em"}}>
                TAP TO USE
              </text>
            </g>
          )}

          {/* Description text — SVG only, no foreignObject */}
          <text x={cx} y={cy+28} textAnchor="middle" dominantBaseline="central"
            fill="rgba(20,10,0,0.55)" fontSize={6.5}
            fontFamily="'DM Mono',monospace"
            style={{pointerEvents:"none", userSelect:"none"}}>
            {harmonic.desc.length > 32
              ? harmonic.desc.slice(0,32) + "…"
              : harmonic.desc}
          </text>
        </>
      )}

      {/* Regular chord label (after root selected or no prev context) */}
      {shownLabel && (!harmonic || hasRoot) && (
        <>
          <text x={cx} y={cy-6} textAnchor="middle" dominantBaseline="central"
            fill={isPreview?"rgba(80,50,20,0.4)":"#1a0a00"}
            fontSize={20} fontFamily="'DM Mono',monospace" fontWeight="700"
            style={{userSelect:"none",transition:"fill 0.15s",
              filter:!isPreview?`drop-shadow(0 0 4px ${hexToRgba(accent,0.6)})`:"none"}}
          >{shownLabel}</text>
          <text x={cx} y={cy+13} textAnchor="middle" dominantBaseline="central"
            fill={hexToRgba(accent,0.65)} fontSize={8} fontFamily="'DM Mono',monospace" fontWeight="600"
            style={{userSelect:"none"}}>{isPreview?"preview":hQObj.label.toUpperCase()}</text>
        </>
      )}

      {/* Idle state — no prev, no hover */}
      {!shownLabel && !harmonic && (
        <text x={cx} y={cy+2} textAnchor="middle" dominantBaseline="central"
          fill="rgba(80,50,20,0.3)" fontSize={9} fontFamily="'DM Mono',monospace" fontWeight="500"
          style={{userSelect:"none"}}>{RING_LABELS[step]??""}</text>
      )}

      {/* Confirm + clear buttons */}
      {hasRoot&&(
        <>
          <g onClick={onConfirm} style={{cursor:"pointer"}}>
            <circle cx={cx} cy={cy+30} r={10}
              fill={hexToRgba(accent,0.15)} stroke={hexToRgba(accent,0.5)} strokeWidth={1}
              onMouseEnter={e=>e.currentTarget.setAttribute("fill",hexToRgba(accent,0.3))}
              onMouseLeave={e=>e.currentTarget.setAttribute("fill",hexToRgba(accent,0.15))}
              style={{transition:"fill 0.12s"}}/>
            <text x={cx} y={cy+30} textAnchor="middle" dominantBaseline="central"
              fill={hexToRgba(accent,0.9)} fontSize={13} fontFamily="'DM Mono',monospace"
              style={{pointerEvents:"none",userSelect:"none"}}>✓</text>
          </g>
          <g onClick={onClear} style={{cursor:"pointer"}}>
            <circle cx={cx} cy={cy-30} r={9}
              fill="rgba(80,50,20,0.06)" stroke="rgba(80,50,20,0.2)" strokeWidth={0.8}
              onMouseEnter={e=>e.currentTarget.setAttribute("fill","rgba(80,50,20,0.14)")}
              onMouseLeave={e=>e.currentTarget.setAttribute("fill","rgba(80,50,20,0.06)")}
              style={{transition:"fill 0.12s"}}/>
            <text x={cx} y={cy-30} textAnchor="middle" dominantBaseline="central"
              fill="rgba(80,50,20,0.45)" fontSize={11} fontFamily="'DM Mono',monospace"
              style={{pointerEvents:"none",userSelect:"none"}}>↺</text>
          </g>
        </>
      )}
    </g>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// RADIAL MENU — Main component (sequential ring reveal)
// ═══════════════════════════════════════════════════════════════════════════════

// Right-facing semicircle: flat edge on left, arcs open rightward (0°→180°)
const MENU_W = 214, MENU_H = 420;
const MCX = 10, MCY = MENU_H / 2;

export default function RadialChordMenu({ position, onCommit, onClose, prevChord=null, sectionKey="C", sectionMode="major" }) {
  const [chord, setChord] = useState({...DEFAULT_CHORD});
  const [hover, setHover] = useState({root:null,quality:null,extension:null,inversion:null});
  const [lockedRoot, setLockedRoot] = useState(null); // last non-null hover.root — keeps suggestion alive during mouse travel
  // step: 0=only root visible, 1=quality unlocked, 2=ext unlocked, 3=inv unlocked
  const [step, setStep]   = useState(0);
  const ref = useRef(null);
  const chordRef = useRef(chord);
  chordRef.current = chord;

  useEffect(()=>{
    const down=e=>{if(ref.current&&!ref.current.contains(e.target))onClose();};
    const key =e=>{if(e.key==="Escape")onClose();};
    document.addEventListener("mousedown",down);
    document.addEventListener("keydown",key);
    return()=>{document.removeEventListener("mousedown",down);document.removeEventListener("keydown",key);};
  },[onClose]);

  const pick = useCallback((key,idx)=>{
    setChord(prev=>({...prev,[key]:idx}));
    // Unlock next ring
    if(key==="root")     { setStep(s=>Math.max(s,1)); setLockedRoot(null); }
    if(key==="quality")  setStep(s=>Math.max(s,2));
    if(key==="extension")setStep(s=>Math.max(s,3));
    if(key==="inversion"){
      // auto-commit on inversion pick
      setChord(prev=>{
        const next={...prev,[key]:idx};
        const label=buildChordLabel(next.root,next.quality,next.extension,idx);
        const r=ROOTS[next.root], q=QUALITIES[next.quality??0];
        const ext=EXTENSIONS[next.extension??0], inv=INVERSIONS[idx];
        setTimeout(()=>onCommit({root:r,quality:q,extension:ext,inversion:inv,label}),0);
        return next;
      });
    }
  },[onCommit]);

  const hov = useCallback((key,idx)=>{
    setHover(prev=>({...prev,[key]:idx}));
    if (key === "root" && idx !== null) setLockedRoot(idx);
  },[]);

  const commit = useCallback(()=>{
    const c=chordRef.current;
    if(c.root===null)return;
    const label = buildChordLabel(c.root, c.quality, c.extension, c.inversion);
    const r=ROOTS[c.root], q=QUALITIES[c.quality??0];
    const ext=EXTENSIONS[c.extension??0], inv=INVERSIONS[c.inversion??0];
    onCommit({root:r,quality:q,extension:ext,inversion:inv,label});
  },[onCommit]);

  // Commit the harmonically suggested chord directly from center click
  const commitSuggestion = useCallback((rootIdx, sugQ, sugExt)=>{
    const rIdx = rootIdx ?? 0;
    const qIdx = sugQ   ?? 0;
    const eIdx = sugExt ?? 0;
    const label = buildChordLabel(rIdx, qIdx, eIdx, 0);
    onCommit({
      root:      ROOTS[rIdx],
      quality:   QUALITIES[qIdx],
      extension: EXTENSIONS[eIdx],
      inversion: INVERSIONS[0],
      label,
    });
  },[onCommit]);

  const clear = useCallback(()=>{setChord({...DEFAULT_CHORD});setStep(0);},[]);

  const vw=typeof window!=="undefined"?window.innerWidth:800;
  const vh=typeof window!=="undefined"?window.innerHeight:600;
  // Smart flip: when near right edge, open leftward so arcs don't leave viewport
  const flipLeft = position.x > vw * 0.65;
  // Anchor so the ring pivot (MCX) sits exactly on the click point
  const left = flipLeft
    ? Math.max(8, position.x - (MENU_W - MCX))  // mirrored: visual center = L + (MENU_W - MCX)
    : Math.min(position.x - MCX, vw - MENU_W - 8);
  const top = Math.max(8, Math.min(position.y - MCY, vh - MENU_H - 8));

  const qAccent = chord.quality!==null?QUALITIES[chord.quality].accent:"#888";
  // When flipped, mirror the whole container so arcs open leftward
  const flipStyle = flipLeft ? {transform:`scaleX(-1)`,transformOrigin:`${MENU_W/2}px 50%`} : {};

  return (
    <div ref={ref} style={{
      position:"fixed",left,top,width:MENU_W,height:MENU_H,
      borderRadius:"0 24px 24px 0",background:"transparent",
      overflow:"visible",
      zIndex:9999,animation:"rcm-pop 0.2s cubic-bezier(0.34,1.56,0.64,1)",...flipStyle,
    }}>
      <svg width={MENU_W} height={MENU_H} style={{display:"block",overflow:"visible"}}>

        {/* Root ring — always visible, tinted by harmonic strength when prev exists */}
        <Ring cx={MCX} cy={MCY} r1={52} r2={96} items={ROOTS}
          selected={chord.root} hovered={hover.root}
          onSelect={i=>pick("root",i)} onHover={i=>hov("root",i)}
          getAccent={(_,i)=>{
            if(!prevChord||chord.root!==null) return "#7a5c3a";
            const rel = analyzeInterval(prevChord.rootIdx, prevChord.qualityIdx, i, sectionKey, sectionMode);
            return rel ? rel.color : "#7a5c3a";
          }}
          getLabel={r=>r}
          visible={true} animDelay={0} startAngle={0} span={180}/>

        {/* Quality ring */}
        <Ring cx={MCX} cy={MCY} r1={100} r2={144} items={QUALITIES}
          selected={chord.quality} hovered={hover.quality}
          onSelect={i=>pick("quality",i)} onHover={i=>hov("quality",i)}
          getAccent={q=>q.accent} getLabel={q=>q.label}
          visible={step>=1} animDelay={0.04} startAngle={0} span={180}/>

        {/* Extension ring */}
        <Ring cx={MCX} cy={MCY} r1={148} r2={176} items={EXTENSIONS}
          selected={chord.extension} hovered={hover.extension}
          onSelect={i=>pick("extension",i)} onHover={i=>hov("extension",i)}
          getAccent={()=>qAccent} getLabel={e=>e.label}
          visible={step>=2} animDelay={0.06} startAngle={0} span={180}/>

        {/* Inversion ring */}
        <Ring cx={MCX} cy={MCY} r1={180} r2={198} items={INVERSIONS}
          selected={chord.inversion} hovered={hover.inversion}
          onSelect={i=>pick("inversion",i)} onHover={i=>hov("inversion",i)}
          getAccent={()=>qAccent} getLabel={v=>v.label}
          visible={step>=3} animDelay={0.08} startAngle={0} span={180}/>

        {/* Ring label tags */}
        {[
          {r:74,  label:"ROOT",  v:true    },
          {r:122, label:"QUAL",  v:step>=1 },
          {r:162, label:"EXT",   v:step>=2 },
          {r:189, label:"INV",   v:step>=3 },
        ].map(({r,label,v})=>{
          const pt=polar(MCX,MCY,r,4);
          return v&&(
            <text key={label} x={pt.x} y={pt.y}
              textAnchor="middle" dominantBaseline="central"
              fill="rgba(80,50,20,0.2)" fontSize={6}
              fontFamily="'DM Mono',monospace" fontWeight="600" letterSpacing="0.1em"
              style={{pointerEvents:"none",userSelect:"none"}}
            >{label}</text>
          );
        })}

        {/* Center */}
        <Center cx={MCX} cy={MCY} chord={chord} hover={hover} step={step}
          prevChord={prevChord} sectionKey={sectionKey} sectionMode={sectionMode}
          onConfirm={commit} onClear={clear}
          onCommitSuggestion={commitSuggestion} lockedRoot={lockedRoot}/>

        {/* ESC hint */}
        <text x={MCX+MENU_W/2} y={MENU_H-6} textAnchor="middle"
          fill="rgba(80,50,20,0.2)" fontSize={7} fontFamily="'DM Mono',monospace" fontWeight="500"
          style={{pointerEvents:"none",userSelect:"none"}}>ESC to cancel</text>
      </svg>
    </div>
  );
}
