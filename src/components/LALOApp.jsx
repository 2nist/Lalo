import { useState, useRef, useCallback, useEffect } from 'react';
import { parseLabelToContext } from '../utils/chordUtils';
import { INITIAL_SONG, beatMap } from '../utils/harmonyEngine';
import { importMcGillJson } from '../utils/mirImport';
import Drawer, { DockPicker, DEFAULT_SIZES } from '../components/Drawer';
import ChordCanvas from '../components/Canvas';
import RadialChordMenu from '../components/RadialMenu';
import HarmonyPanel from './HarmonyPanel';

// ═══════════════════════════════════════════════════════════════════════════════
// CHORD CANVAS — data model
// ═══════════════════════════════════════════════════════════════════════════════

let evId = 1;



// ═══════════════════════════════════════════════════════════════════════════════
// CANVAS AREA — the main "song" content behind the drawer
// ═══════════════════════════════════════════════════════════════════════════════

function MockCanvas({ importMeta, dragActive }) {
  return (
    <div style={{
      width:"100%", height:"100%",
      backgroundImage:`
        linear-gradient(rgba(101,74,40,0.1) 1px, transparent 1px),
        linear-gradient(90deg,rgba(101,74,40,0.1) 1px, transparent 1px)
      `,
      backgroundSize:"32px 32px",
      display:"flex", alignItems:"center", justifyContent:"center",
      flexDirection:"column", gap:8, position:"relative",
      border:"1px solid rgba(90,60,30,0.2)",
      boxShadow: dragActive
        ? "inset 0 0 0 1px rgba(190,130,55,0.7), 0 0 22px rgba(190,130,55,0.35)"
        : "inset 0 0 0 1px rgba(90,60,30,0.12)",
      transition:"box-shadow 120ms ease, border-color 120ms ease",
    }}>
      {importMeta ? (
        <div style={{
          position:"absolute", top:12, left:14,
          fontSize:10, letterSpacing:"0.06em",
          color:"rgba(52,30,10,0.82)",
          background:"rgba(232,212,184,0.7)",
          border:"1px solid rgba(100,65,25,0.2)",
          borderRadius:4, padding:"6px 8px",
          fontFamily:"'DM Mono',monospace",
        }}>
          {importMeta.title} {"\u2014"} {importMeta.artist}
        </div>
      ) : (
        <>
          <div style={{fontSize:11,letterSpacing:"0.2em",color:"rgba(90,60,30,0.35)",fontFamily:"'DM Mono',monospace"}}>
            LALO / CANVAS
          </div>
          <div style={{fontSize:9,color:"rgba(90,60,30,0.22)",fontFamily:"'DM Mono',monospace",letterSpacing:"0.08em"}}>
            your arrangement lives here
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// APP
// ═══════════════════════════════════════════════════════════════════════════════

export default function LALOApp() {
  const [song,      setSong]      = useState(INITIAL_SONG);
  const [importMeta,setImportMeta]= useState(null);
  const [importStrategy, setImportStrategy] = useState("auto-json");
  const [menu,      setMenu]      = useState(null);
  const [toast,     setToast]     = useState(null);
  const [dragOver,  setDragOver]  = useState(false);
  const [dragDepth, setDragDepth] = useState(0);
  const [dock,      setDock]      = useState("bottom");
  const [open,      setOpen]      = useState(true);
  const [sizes,     setSizes]     = useState({...DEFAULT_SIZES});
  const [panel,     setPanel]     = useState("canvas"); // "canvas" | "harmony"
  const [drawerPos, setDrawerPos] = useState(null);    // null=docked, {x,y}=floating
  const toastTimerRef             = useRef(null);
  const [audioUrl, setAudioUrl]   = useState("");
  const [audioSlug,setAudioSlug]  = useState("");
  const [audioBusy,setAudioBusy]  = useState(false);
  const [bridgeOk,setBridgeOk]    = useState(() => !!window.electronAPI?.audio?.fetch);

  const showImportToast = useCallback((message, tone = "ok") => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, tone });
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);

  const handleDropJson = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    setDragDepth(0);

    // Prefer file import if a .json is dropped
    const files = Array.from(e.dataTransfer?.files ?? []);
    const file = files.find(f => f.name.toLowerCase().endsWith(".json"));
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(String(reader.result ?? ""));
          const imported = importMcGillJson(parsed, { sectionStrategy: importStrategy });
          setSong(imported);
          const meta = imported?.[0]?.meta ?? null;
          setImportMeta(meta ? { title: meta.title, artist: meta.artist } : null);
          if (meta?.title || meta?.artist) {
            const slug = makeSlug(`${meta.title ?? "untitled"}_${meta.artist ?? "unknown"}`);
            setAudioSlug(slug);
          }
          showImportToast(`Imported (${importStrategy}): ${(meta?.title ?? "Untitled")} \u2014 ${(meta?.artist ?? "Unknown Artist")}`, "ok");
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          showImportToast(`Import failed: ${msg}`, "error");
        }
      };
      reader.onerror = () => showImportToast("Import failed: could not read file.", "error");
      reader.readAsText(file);
      return;
    }

    // If no file, try to capture a dropped URL/text (for yt-dlp fetch)
    const droppedUrl = extractUrlFromDataTransfer(e.dataTransfer);
    if (droppedUrl) {
      setAudioUrl(droppedUrl);
      showImportToast("Captured URL for audio fetch.", "ok");
      return;
    }

    showImportToast("Import failed: drop a .json file or a URL.", "error");
  }, [importStrategy, showImportToast]);

  const handleDragOverCanvas = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!dragOver) setDragOver(true);
  }, [dragOver]);

  const handleDragEnterCanvas = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragDepth((d) => d + 1);
    setDragOver(true);
  }, []);

  const handleDragLeaveCanvas = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragDepth((d) => {
      const next = Math.max(0, d - 1);
      if (next === 0) setDragOver(false);
      return next;
    });
  }, []);

  const handleCopyDebugJson = useCallback(async () => {
    try {
      const payload = JSON.stringify(song, null, 2);
      await navigator.clipboard.writeText(payload);
      showImportToast("Copied song debug JSON to clipboard.", "ok");
    } catch {
      try {
        const blob = new Blob([JSON.stringify(song, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "lalo-import-debug.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showImportToast("Downloaded song debug JSON file.", "ok");
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        showImportToast(`Debug export failed: ${msg}`, "error");
      }
    }
  }, [song, showImportToast]);

  // When dock side changes reset open state
  const handleDockChange = useCallback(side=>{
    setDock(side); setOpen(true);
  },[]);

  const handleResize = useCallback(newSize=>{
    setSizes(prev=>({...prev,[dock]:newSize}));
  },[dock]);

  const openAdd = useCallback((e,sectionId,beat)=>{
    e.preventDefault(); e.stopPropagation();
    // Find the most recent chord before this beat in the section
    const sec = song.find(s=>s.id===sectionId);
    let prevChord = null;
    if(sec){
      const before = sec.events
        .filter(ev=>ev.beat < beat)
        .sort((a,b)=>b.beat-a.beat);
      if(before.length>0){
        const ev=before[0];
        prevChord = parseLabelToContext(ev.label);
      }
    }
    setMenu({x:e.clientX,y:e.clientY,sectionId,beat,existingEv:null,prevChord,sectionKey:sec?.key??"C",sectionMode:sec?.mode??"major"});
  },[song]);

  const openEdit = useCallback((e,sectionId,ev)=>{
    e.preventDefault(); e.stopPropagation();
    const sec = song.find(s=>s.id===sectionId);
    let prevChord = null;
    if(sec){
      const before = sec.events
        .filter(e2=>e2.beat < ev.beat)
        .sort((a,b)=>b.beat-a.beat);
      if(before.length>0) prevChord = parseLabelToContext(before[0].label);
    }
    setMenu({x:e.clientX,y:e.clientY,sectionId,beat:ev.beat,existingEv:ev,prevChord,sectionKey:sec?.key??"C",sectionMode:sec?.mode??"major"});
  },[song]);

  const handleCommit = useCallback(chord=>{
    if(!menu)return;
    setSong(prev=>prev.map(sec=>{
      if(sec.id!==menu.sectionId)return sec;
      const map=beatMap(sec);
      let span=1;
      for(let b=menu.beat+1;b<sec.totalBeats&&b<menu.beat+2;b++){
        if(map[b]===null)span++; else break;
      }
      const newEv = {
        id:           evId++,
        beat:         menu.beat,
        beatFloat:    menu.beat,        // canvas places on integer beats; float preserved for sub-beat edits later
        span,
        durationBeats:span,
        label:        chord.label,
        root:         chord.root?.label ?? chord.root ?? "C",
        quality:      chord.quality?.label ?? "maj",
        extensions:   chord.extension?.symbol ? [chord.extension.symbol] : [],
        inversion:    chord.inversion ? (chord.inversion.label==="1st"?1:chord.inversion.label==="2nd"?2:chord.inversion.label==="3rd"?3:0) : 0,
        bassNote:     undefined,
        source:       "manual",
      };
      if(menu.existingEv){
        return{...sec,events:sec.events.map(ev=>
          ev.id===menu.existingEv.id?{...ev,...newEv,id:ev.id,beat:ev.beat,beatFloat:ev.beatFloat??ev.beat,span:ev.span,durationBeats:ev.durationBeats??ev.span}:ev)};
      }
      return{...sec,events:[...sec.events,newEv]};
    }));
    setMenu(null);
  },[menu]);

  const handleResizeChord = useCallback((ev,newSpan)=>{
    setSong(prev=>prev.map(sec=>({
      ...sec,
      events:sec.events.map(e=>e.id===ev.id?{...e,span:newSpan}:e),
    })));
  },[]);

  const handleChangeMeter = useCallback((sectionId,timeSig,bars)=>{
    setSong(prev=>prev.map(sec=>{
      if(sec.id!==sectionId)return sec;
      const totalBeats=timeSig*bars;
      const events=sec.events
        .filter(ev=>ev.beat<totalBeats)
        .map(ev=>({...ev,span:Math.min(ev.span,totalBeats-ev.beat)}));
      return{...sec,timeSig,bars,totalBeats,events};
    }));
  },[]);

  // Inset the canvas so it doesn't hide behind the drawer.
  // When the drawer is floating (drawerPos != null) no inset is needed.
  const isHoriz  = dock==="left"||dock==="right";
  const drawerSz = open?sizes[dock]:36;
  const canvasInset = drawerPos ? {} : {
    paddingBottom: dock==="bottom"?drawerSz:0,
    paddingTop:    dock==="top"   ?drawerSz:0,
    paddingLeft:   dock==="left"  ?drawerSz:0,
    paddingRight:  dock==="right" ?drawerSz:0,
  };

  const handleFetchAudio = useCallback(async ()=>{
    if (!audioUrl.trim() || !audioSlug.trim()) {
      showImportToast("Audio fetch: provide URL and slug", "error");
      return;
    }
    const audioApi = window.electronAPI?.audio?.fetch;
    if (!audioApi) {
      showImportToast("Audio fetch not available (electronAPI.audio missing). Run inside Electron.", "error");
      return;
    }
    setAudioBusy(true);
    try {
      await audioApi({
        url: audioUrl.trim(),
        slug: audioSlug.trim(),
        outDir: "data/audio",
      });
      showImportToast("Audio fetched to data/audio", "ok");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      showImportToast(`Audio fetch failed: ${msg}`, "error");
    } finally {
    setAudioBusy(false);
    }
  }, [audioUrl, audioSlug, showImportToast]);

  function makeSlug(str){
    return String(str ?? "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g,"_")
      .replace(/^_+|_+$/g,"")
      .replace(/_+/g,"_");
  }

  function extractUrlFromDataTransfer(dt){
    if (!dt) return "";
    if (dt.types?.includes("text/uri-list")) {
      const uri = dt.getData("text/uri-list").split(/\r?\n/).find(Boolean);
      if (uri) return uri.trim();
    }
    if (dt.types?.includes("text/plain")) {
      const txt = dt.getData("text/plain").trim();
      const m = txt.match(/https?:\/\/\S+/);
      if (m) return m[0];
    }
    return "";
  }

  // Detect bridge availability (in case Electron preload didn't load)
  useEffect(()=>{
    const ok = !!window.electronAPI?.audio?.fetch;
    setBridgeOk(ok);
  },[]);

  return (
    <div
      onDragEnter={handleDragEnterCanvas}
      onDragOver={handleDragOverCanvas}
      onDragLeave={handleDragLeaveCanvas}
      onDrop={handleDropJson}
      className="paper-bg" style={{width:"100vw",height:"100vh",overflow:"hidden",
      position:"relative",fontFamily:"'DM Mono',monospace"}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        @keyframes rcm-pop{from{opacity:0;transform:scale(0.82);}to{opacity:1;transform:scale(1);}}
        @keyframes rcm-spin{from{transform:rotate(0deg);}to{transform:rotate(360deg);}}
        @keyframes lalo-toast-fade{
          0%,78%{opacity:1;transform:translateY(0);}
          100%{opacity:0;transform:translateY(5px);}
        }
        button:focus{outline:none;}

        .paper-bg {
          background-color: #c8a97e;
          background-image:
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23n)' opacity='0.18'/%3E%3C/svg%3E"),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='f'%3E%3CfeTurbulence type='turbulence' baseFrequency='0.02 0.8' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23f)' opacity='0.06'/%3E%3C/svg%3E"),
            linear-gradient(160deg, #d4b48a 0%, #c2a070 35%, #b8945e 65%, #c9a87c 100%);
        }

        .drawer-paper {
          background-color: #e8d4b8;
          background-image:
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E"),
            linear-gradient(180deg, #eddfc6 0%, #e4ceae 100%);
        }
      `}</style>

      {/* Main canvas area */}
      <div style={{width:"100%",height:"100%",...canvasInset,transition:"padding 0.22s cubic-bezier(0.4,0,0.2,1)"}}>
        <MockCanvas importMeta={importMeta} dragActive={dragOver}/>
      </div>

      {/* Chord canvas drawer */}
      <Drawer side={dock} size={sizes[dock]} onResize={handleResize}
        open={open} onToggle={()=>setOpen(o=>!o)}
        pos={drawerPos} onPosChange={setDrawerPos}>
        {/* Panel tab bar */}
        <div style={{
          display:"flex", borderBottom:"1px solid rgba(100,65,25,0.15)",
          background:"rgba(200,165,120,0.3)", flexShrink:0,
        }}>
          {[
            { id:"canvas",  label:"CHORD CANVAS" },
            { id:"harmony", label:"HARMONY" },
          ].map(tab=>(
            <button key={tab.id} onClick={()=>setPanel(tab.id)} style={{
              background: panel===tab.id ? "rgba(100,65,25,0.12)" : "transparent",
              border:"none", borderBottom: panel===tab.id ? "2px solid rgba(100,65,25,0.6)" : "2px solid transparent",
              padding:"6px 14px", cursor:"pointer",
              fontSize:8, fontWeight:700, letterSpacing:"0.12em",
              color: panel===tab.id ? "rgba(60,35,10,0.9)" : "rgba(100,65,25,0.45)",
              fontFamily:"'DM Mono',monospace",
              transition:"all 0.12s",
            }}>{tab.label}</button>
          ))}
        </div>
        {/* Panel content */}
        {panel==="canvas" && (
          <ChordCanvas song={song}
            onAddChord={openAdd} onResizeChord={handleResizeChord}
            onEditChord={openEdit} onChangeMeter={handleChangeMeter}/>
        )}
        {panel==="harmony" && (
          <HarmonyPanel song={song} style={{height:"100%",overflowY:"auto"}}/>
        )}
      </Drawer>

      {/* Dock side picker */}
      <DockPicker current={dock} onChange={handleDockChange}/>

      <button
        onClick={handleCopyDebugJson}
        style={{
          position:"fixed",
          top:14,
          right:14,
          border:"1px solid rgba(100,65,25,0.35)",
          background:"rgba(232,212,184,0.78)",
          color:"rgba(60,35,10,0.9)",
          borderRadius:5,
          padding:"6px 8px",
          fontSize:9,
          letterSpacing:"0.08em",
          fontFamily:"'DM Mono',monospace",
          cursor:"pointer",
          zIndex:50,
          boxShadow:"0 3px 10px rgba(0,0,0,0.15)",
        }}>
        COPY DEBUG JSON
      </button>

      <button
        onClick={() => setImportStrategy((s) => (s === "auto-json" ? "dataset" : "auto-json"))}
        style={{
          position:"fixed",
          top:14,
          right:152,
          border:"1px solid rgba(100,65,25,0.35)",
          background:"rgba(232,212,184,0.78)",
          color:"rgba(60,35,10,0.9)",
          borderRadius:5,
          padding:"6px 8px",
          fontSize:9,
          letterSpacing:"0.08em",
          fontFamily:"'DM Mono',monospace",
          cursor:"pointer",
          zIndex:50,
          boxShadow:"0 3px 10px rgba(0,0,0,0.15)",
        }}>
        STRATEGY: {importStrategy.toUpperCase()}
      </button>

      {/* Audio fetch panel */}
      <div style={{
        position:"fixed",
        right:16,
        bottom:16,
        width:260,
        padding:"10px 12px",
        background:"rgba(21,18,14,0.9)",
        border:"1px solid rgba(188,135,58,0.6)",
        borderRadius:8,
        boxShadow:"0 8px 24px rgba(0,0,0,0.35)",
        color:"#d3a24b",
        fontFamily:"'DM Mono',monospace",
        fontSize:10,
        zIndex:55,
        outline: "1px dashed rgba(188,135,58,0.25)"
      }}>
        <div style={{fontWeight:700, letterSpacing:"0.08em", marginBottom:6}}>AUDIO FETCH (yt-dlp)</div>
        <div style={{fontSize:9, color: bridgeOk ? "#80e59f" : "#e07b7b", marginBottom:4}}>
          Bridge: {bridgeOk ? "connected" : "missing (restart Electron?)"}
        </div>
        <div style={{display:"flex", flexDirection:"column", gap:6}}>
          <input
            value={audioUrl}
            onChange={(e)=>setAudioUrl(e.target.value)}
            placeholder="YouTube / URL"
            style={{
              width:"100%", padding:"6px 8px", borderRadius:4,
              border:"1px solid rgba(188,135,58,0.35)", background:"rgba(255,255,255,0.04)",
              color:"#f2d6a2", fontSize:10, fontFamily:"inherit",
            }}
          />
          <input
            value={audioSlug}
            onChange={(e)=>setAudioSlug(makeSlug(e.target.value))}
            placeholder="slug (matches annotation filename)"
            style={{
              width:"100%", padding:"6px 8px", borderRadius:4,
              border:"1px solid rgba(188,135,58,0.35)", background:"rgba(255,255,255,0.04)",
              color:"#f2d6a2", fontSize:10, fontFamily:"inherit",
            }}
          />
          <button
            onClick={handleFetchAudio}
            disabled={audioBusy}
            style={{
              width:"100%", padding:"7px 8px",
              background: audioBusy ? "rgba(188,135,58,0.25)" : "rgba(188,135,58,0.85)",
              color:"#120d07",
              border:"none", borderRadius:4, cursor: audioBusy ? "wait" : "pointer",
              fontWeight:700, letterSpacing:"0.08em",
            }}>
            {audioBusy ? "FETCHING..." : "FETCH AUDIO"}
          </button>
        </div>
      </div>

      {/* Radial chord menu */}
      {menu&&(
        <RadialChordMenu position={menu} onCommit={handleCommit} onClose={()=>setMenu(null)}
          prevChord={menu.prevChord??null}
          sectionKey={menu.sectionKey??"C"} sectionMode={menu.sectionMode??"major"}/>
      )}

      {toast && (
        <div style={{
          position:"fixed",
          left:18,
          bottom:18,
          maxWidth:420,
          padding:"8px 10px",
          borderRadius:6,
          border:`1px solid ${toast.tone === "error" ? "rgba(184,72,48,0.7)" : "rgba(188,135,58,0.6)"}`,
          background:"rgba(21,18,14,0.9)",
          color: toast.tone === "error" ? "#b84830" : "#d3a24b",
          fontSize:10,
          letterSpacing:"0.04em",
          fontFamily:"'DM Mono',monospace",
          boxShadow:"0 6px 20px rgba(0,0,0,0.35)",
          pointerEvents:"none",
          zIndex:60,
          animation:"lalo-toast-fade 3s ease forwards",
        }}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
