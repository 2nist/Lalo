import { useRef } from 'react'

export const DOCK_SIDES = ["bottom","top","left","right"];
export const DOCK_ICONS = { bottom:"▼", top:"▲", left:"◀", right:"▶" };
export const MIN_SIZE      = 80;
export const DEFAULT_SIZES = { bottom:260, top:260, left:340, right:340 };
// Max size is 80% of the relevant viewport axis — computed at drag time so it
// responds correctly after window resizes without needing an event listener.
const maxSize = (side) =>
  (side==="left"||side==="right") ? window.innerWidth * 0.8 : window.innerHeight * 0.8;

function Drawer({ side, size, onResize, open, onToggle, pos, onPosChange, children }) {
  const isHoriz   = side==="left"||side==="right";
  const resizeRef = useRef(null);

  // ── Edge drag = resize (only when docked) ───────────────────────────────────
  const handleResizeStart = e => {
    if (pos) return; // don't resize-drag when floating — could conflict with move
    e.preventDefault();
    resizeRef.current = { start: isHoriz?e.clientX:e.clientY, startSize:size };
    const onMove = me => {
      const delta = isHoriz?me.clientX-resizeRef.current.start:me.clientY-resizeRef.current.start;
      const dir   = (side==="right"||side==="bottom")?-1:1;
      onResize(Math.max(MIN_SIZE,Math.min(maxSize(side),resizeRef.current.startSize+delta*dir)));
    };
    const onUp = ()=>{
      window.removeEventListener("mousemove",onMove);
      window.removeEventListener("mouseup",onUp);
    };
    window.addEventListener("mousemove",onMove);
    window.addEventListener("mouseup",onUp);
  };

  // ── Title-bar drag = move entire drawer freely (max 80 % of viewport) ───────
  const handleMoveStart = e => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const vw = window.innerWidth, vh = window.innerHeight;
    // Seed initial floating position from current docked anchor when first lifted
    let sx = pos?.x, sy = pos?.y;
    if (sx == null) {
      sx = side==="right" ? vw - size : 0;
      sy = side==="bottom" ? vh - size : 0;
    }
    // Offset from pointer to top-left corner of drawer
    const ox = e.clientX - sx, oy = e.clientY - sy;
    onPosChange({ x: sx, y: sy }); // snap to floating immediately
    const onMove = me => {
      onPosChange({
        x: Math.max(0, Math.min(vw * 0.8, me.clientX - ox)),
        y: Math.max(0, Math.min(vh * 0.8, me.clientY - oy)),
      });
    };
    const onUp = ()=>{
      window.removeEventListener("mousemove",onMove);
      window.removeEventListener("mouseup",onUp);
    };
    window.addEventListener("mousemove",onMove);
    window.addEventListener("mouseup",onUp);
  };

  // ── Resize handle strip (edge of drawer, hidden when floating) ──────────────
  const handleStyle = {
    position:"absolute", zIndex:10, background:"transparent",
    ...(side==="bottom" ? {top:0,    left:0,right:0,height:6,cursor:"ns-resize"} : {}),
    ...(side==="top"    ? {bottom:0, left:0,right:0,height:6,cursor:"ns-resize"} : {}),
    ...(side==="left"   ? {right:0,  top:0,bottom:0,width:6, cursor:"ew-resize"} : {}),
    ...(side==="right"  ? {left:0,   top:0,bottom:0,width:6, cursor:"ew-resize"} : {}),
  };

  // ── Drawer style: floating vs docked ────────────────────────────────────────
  const drawerStyle = pos ? {
    // Floating panel — free position, rounded corners, elevated shadow
    position:"fixed", zIndex:210,
    left: pos.x, top: pos.y,
    width:  isHoriz ? (open ? size  : 36) : (open ? Math.max(size, 320) : 240),
    height: isHoriz ? (open ? Math.min(size, window.innerHeight * 0.8) : 200) : (open ? size : 36),
    borderRadius: 10,
    border: "1px solid rgba(120,80,30,0.35)",
    boxShadow: "0 12px 48px rgba(80,50,20,0.30), 0 2px 8px rgba(80,50,20,0.18)",
    overflow:"hidden",
  } : {
    // Docked to screen edge
    position:"fixed", zIndex:200,
    borderTop:   side==="bottom"?"1px solid rgba(120,80,30,0.2)":undefined,
    borderBottom:side==="top"   ?"1px solid rgba(120,80,30,0.2)":undefined,
    borderRight: side==="left"  ?"1px solid rgba(120,80,30,0.2)":undefined,
    borderLeft:  side==="right" ?"1px solid rgba(120,80,30,0.2)":undefined,
    boxShadow: side==="bottom"?"0 -4px 24px rgba(80,50,20,0.15)":
               side==="top"   ?"0  4px 24px rgba(80,50,20,0.15)":
               side==="left"  ?"4px 0  24px rgba(80,50,20,0.15)":
                                "-4px 0 24px rgba(80,50,20,0.15)",
    overflow:"hidden",
    transition:"width 0.22s cubic-bezier(0.4,0,0.2,1), height 0.22s cubic-bezier(0.4,0,0.2,1)",
    ...(side==="bottom" ? {bottom:0,left:0,right:0,height:open?size:36} : {}),
    ...(side==="top"    ? {top:0,   left:0,right:0,height:open?size:36} : {}),
    ...(side==="left"   ? {left:0,  top:0,bottom:0,width:open?size:36}  : {}),
    ...(side==="right"  ? {right:0, top:0,bottom:0,width:open?size:36}  : {}),
  };

  return (
    <div className="drawer-paper" style={drawerStyle}>
      {/* Resize strip — only when docked */}
      {open && !pos && <div style={handleStyle} onMouseDown={handleResizeStart}/>}

      {/* Title bar — drag to move, click toggle button to open/close */}
      <div
        onMouseDown={handleMoveStart}
        style={{
          display:"flex", alignItems:"center",
          padding: isHoriz?"8px 10px 8px 14px":"0 14px",
          height:36, flexShrink:0,
          cursor: "grab",
          userSelect: "none",
          borderBottom: (!isHoriz&&open)?"1px solid rgba(120,80,30,0.15)":undefined,
          borderRight:  (isHoriz&&open) ?"1px solid rgba(120,80,30,0.15)":undefined,
          ...(isHoriz?{flexDirection:"column",justifyContent:"space-between",height:"100%",width:36,
            float:"left",boxSizing:"border-box",padding:"10px 0"}:{}),
        }}>
        {!isHoriz&&(
          <span style={{fontSize:8,letterSpacing:"0.15em",color:"rgba(100,65,25,0.5)",fontFamily:"'DM Mono',monospace"}}>
            ⠿ SONG MAP
          </span>
        )}
        {isHoriz&&(
          <span style={{
            fontSize:7,letterSpacing:"0.15em",color:"rgba(100,65,25,0.5)",fontFamily:"'DM Mono',monospace",
            writingMode:"vertical-rl",textOrientation:"mixed",
            transform:side==="left"?"rotate(180deg)":"none",
          }}>⠿ SONG MAP</span>
        )}
        <div style={{display:"flex", gap:4, alignItems:"center"}}>
          {/* Snap-back button — only shown when floating */}
          {pos && (
            <button
              onMouseDown={e=>e.stopPropagation()}
              onClick={()=>onPosChange(null)}
              title="Snap back to edge"
              style={{
                background:"none", border:"1px solid rgba(120,80,30,0.2)", borderRadius:4,
                padding:"2px 6px", cursor:"pointer",
                fontSize:9, color:"rgba(100,65,25,0.55)", fontFamily:"'DM Mono',monospace",
                lineHeight:1,
              }}>⊞</button>
          )}
          <button
            onMouseDown={e=>e.stopPropagation()}
            onClick={onToggle}
            style={{
              background:"none",border:"1px solid rgba(120,80,30,0.2)",borderRadius:4,
              padding:"2px 6px",cursor:"pointer",
              fontSize:9,color:"rgba(100,65,25,0.55)",fontFamily:"'DM Mono',monospace",
              lineHeight:1,flexShrink:0,
            }}>{open?"✕":DOCK_ICONS[side]}</button>
        </div>
      </div>

      {/* Content */}
      {open&&(
        <div style={{
          position:"absolute",
          ...(isHoriz?{left:36,top:0,right:0,bottom:0}:{top:36,left:0,right:0,bottom:0}),
          overflow:"auto",
        }}>
          {children}
        </div>
      )}
    </div>
  );
}

export function DockPicker({ current, onChange }) {
  return (
    <div style={{
      position:"fixed",bottom:16,right:16,zIndex:300,
      display:"flex",gap:4,
      background:"rgba(220,185,140,0.92)",
      border:"1px solid rgba(120,80,30,0.2)",borderRadius:6,padding:4,
      boxShadow:"0 2px 12px rgba(80,50,20,0.12)",
    }}>
      {DOCK_SIDES.map(s=>(
        <button key={s} onClick={()=>onChange(s)} title={`Dock ${s}`} style={{
          width:24,height:24,border:"none",borderRadius:4,
          background:current===s?"rgba(100,65,25,0.75)":"transparent",
          color:current===s?"#f5e8d0":"rgba(100,65,25,0.55)",
          cursor:"pointer",fontSize:10,lineHeight:1,
          transition:"all 0.12s",
        }}>{DOCK_ICONS[s]}</button>
      ))}
    </div>
  );
}

export default Drawer;
