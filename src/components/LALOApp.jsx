import { useRef, useCallback, useMemo } from 'react';
import { parseLabelToContext } from '../utils/chordUtils';
import { beatMap } from '../utils/harmonyEngine';
import { importMcGillJson } from '../utils/mirImport';
import { ROOTS } from '../constants/music';
import Drawer, { DockPicker } from '../components/Drawer';
import ChordCanvas from '../components/Canvas';
import RadialChordMenu from '../components/RadialMenu';
import HarmonyPanel from './HarmonyPanel';
import TheoryPanel from './TheoryPanel';
import { buildTheoryEventsForSection } from '../utils/theoryUtils';
import { useSongStore } from '../store/useSongStore';

// ═══════════════════════════════════════════════════════════════════════════════
// CHORD CANVAS — data model
// ═══════════════════════════════════════════════════════════════════════════════

let evId = 1;
let canvasWidgetId = 1;

const DEFAULT_SONG_META = {
  title: 'New Song',
  tempo: 120,
  key: 'C',
  mode: 'major',
};

const MODE_OPTIONS = ['major', 'minor', 'dorian', 'mixolydian', 'phrygian', 'lydian', 'locrian'];

const CANVAS_WIDGET_ROLE_PRESETS = {
  sectionMenu: {
    role: 'Section Menu',
    colors: {
      border: 'rgba(56,96,128,0.85)',
      header: 'rgba(56,96,128,0.22)',
      title: 'rgba(26,54,76,0.95)',
      chip: 'rgba(56,96,128,0.14)',
    },
    rect: { x: 100, y: 180, width: 240, height: 170 },
    behavior: { movable: true, resizable: true, collapsible: true },
    options: ['Intro', 'Verse', 'Pre-Chorus', 'Chorus'],
  },
  cues: {
    role: 'Performance Cues',
    colors: {
      border: 'rgba(122,96,44,0.88)',
      header: 'rgba(122,96,44,0.24)',
      title: 'rgba(76,54,20,0.95)',
      chip: 'rgba(122,96,44,0.16)',
    },
    rect: { x: 380, y: 160, width: 220, height: 150 },
    behavior: { movable: true, resizable: false, collapsible: true },
    options: ['Drop dynamics @ bar 9', 'Open hi-hat @ chorus'],
  },
  routing: {
    role: 'Routing Menu',
    colors: {
      border: 'rgba(108,58,124,0.88)',
      header: 'rgba(108,58,124,0.24)',
      title: 'rgba(66,26,78,0.95)',
      chip: 'rgba(108,58,124,0.16)',
    },
    rect: { x: 640, y: 190, width: 240, height: 180 },
    behavior: { movable: true, resizable: true, collapsible: false },
    options: ['Piano → Bus A', 'Bass → Bus B', 'Vox FX → Parallel'],
  },
};

function createCanvasWidget(roleKey, point = null) {
  const preset = CANVAS_WIDGET_ROLE_PRESETS[roleKey] ?? CANVAS_WIDGET_ROLE_PRESETS.sectionMenu;
  return {
    id: canvasWidgetId++,
    roleKey,
    title: preset.role,
    colors: { ...preset.colors },
    behavior: { ...preset.behavior },
    rect: {
      x: point?.x ?? preset.rect.x,
      y: point?.y ?? preset.rect.y,
      width: preset.rect.width,
      height: preset.rect.height,
    },
    collapsed: false,
    options: [...preset.options],
    draftOption: '',
  };
}



// ═══════════════════════════════════════════════════════════════════════════════
// CANVAS AREA — the main "song" content behind the drawer
// ═══════════════════════════════════════════════════════════════════════════════

function MockCanvas({
  songMeta,
  artist,
  dragActive,
  titleStyle,
  widgets,
  contextMenu,
  onOpenContextMenu,
  onCloseContextMenu,
  onCreateWidget,
  onUpdateWidget,
  onRemoveWidget,
  onToggleWidgetCollapsed,
  onSetWidgetDraft,
  onAddWidgetOption,
}) {
  const displayTitle = titleStyle?.uppercase ? songMeta.title.toUpperCase() : songMeta.title;
  const canvasRef = useRef(null);

  const beginMoveWidget = useCallback((e, widget) => {
    if (!widget.behavior.movable || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const host = canvasRef.current;
    if (!host) return;
    const startX = e.clientX;
    const startY = e.clientY;

    const onMove = (me) => {
      const dx = me.clientX - startX;
      const dy = me.clientY - startY;
      const maxX = Math.max(0, host.clientWidth - widget.rect.width);
      const maxY = Math.max(0, host.clientHeight - widget.rect.height);
      onUpdateWidget(widget.id, {
        rect: {
          ...widget.rect,
          x: Math.max(0, Math.min(maxX, widget.rect.x + dx)),
          y: Math.max(0, Math.min(maxY, widget.rect.y + dy)),
        },
      });
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [onUpdateWidget]);

  const beginResizeWidget = useCallback((e, widget) => {
    if (!widget.behavior.resizable || e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const host = canvasRef.current;
    if (!host) return;
    const startX = e.clientX;
    const startY = e.clientY;

    const onMove = (me) => {
      const dx = me.clientX - startX;
      const dy = me.clientY - startY;
      const maxWidth = Math.max(180, host.clientWidth - widget.rect.x);
      const maxHeight = Math.max(90, host.clientHeight - widget.rect.y);
      onUpdateWidget(widget.id, {
        rect: {
          ...widget.rect,
          width: Math.max(180, Math.min(maxWidth, widget.rect.width + dx)),
          height: Math.max(90, Math.min(maxHeight, widget.rect.height + dy)),
        },
      });
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [onUpdateWidget]);

  const handleCanvasContextMenu = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    const host = canvasRef.current;
    if (!host) return;
    const r = host.getBoundingClientRect();
    onOpenContextMenu({
      x: e.clientX - r.left,
      y: e.clientY - r.top,
    });
  }, [onOpenContextMenu]);

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
      overflow: 'hidden',
    }}>
      <div
        ref={canvasRef}
        onContextMenu={handleCanvasContextMenu}
        onMouseDown={() => contextMenu && onCloseContextMenu()}
        style={{ position: 'absolute', inset: 0 }}
      />
      <div style={{
        position:"absolute", top:12, left:14,
        fontSize:titleStyle?.size ?? 10,
        letterSpacing:`${titleStyle?.letterSpacing ?? 0.06}em`,
        fontWeight:titleStyle?.weight ?? 700,
        color:"rgba(52,30,10,0.82)",
        background:"rgba(232,212,184,0.7)",
        border:"1px solid rgba(100,65,25,0.2)",
        borderRadius:4, padding:"6px 8px",
        fontFamily:"'DM Mono',monospace",
      }}>
        {displayTitle}{artist ? ` — ${artist}` : ''}
      </div>
      <div style={{
        position:"absolute", top:42, left:14,
        display:"inline-flex", alignItems:"center", gap:8,
        fontSize:9, letterSpacing:"0.08em",
        color:"rgba(62,38,12,0.82)",
        background:"rgba(232,212,184,0.64)",
        border:"1px solid rgba(100,65,25,0.2)",
        borderRadius:4, padding:"4px 8px",
        fontFamily:"'DM Mono',monospace",
      }}>
        <span>{songMeta.tempo} BPM</span>
        <span>•</span>
        <span>{songMeta.key}</span>
        <span>{songMeta.mode.toUpperCase()}</span>
      </div>
      {!artist && (
        <div style={{
          fontSize:11,letterSpacing:"0.2em",color:"rgba(90,60,30,0.35)",fontFamily:"'DM Mono',monospace"
        }}>
          LALO / CANVAS
        </div>
      )}
      {(!artist || songMeta.title === DEFAULT_SONG_META.title) && (
        <div style={{fontSize:9,color:"rgba(90,60,30,0.22)",fontFamily:"'DM Mono',monospace",letterSpacing:"0.08em"}}>
          your arrangement lives here
        </div>
      )}

      {widgets.map(widget => (
        <div key={widget.id} style={{
          position: 'absolute',
          left: widget.rect.x,
          top: widget.rect.y,
          width: widget.rect.width,
          height: widget.collapsed ? 28 : widget.rect.height,
          border: `1px solid ${widget.colors.border}`,
          borderRadius: 6,
          background: 'rgba(244,235,220,0.92)',
          boxShadow: '0 3px 12px rgba(0,0,0,0.15)',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 15,
          overflow: 'hidden',
        }}>
          <div
            onMouseDown={(e) => beginMoveWidget(e, widget)}
            style={{
              height: 28,
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 8px',
              cursor: widget.behavior.movable ? 'grab' : 'default',
              background: widget.colors.header,
              borderBottom: `1px solid ${widget.colors.border}`,
              color: widget.colors.title,
              fontSize: 8,
              letterSpacing: '0.08em',
              fontWeight: 700,
              userSelect: 'none',
            }}
          >
            <span>{widget.title.toUpperCase()}</span>
            <div style={{display:'inline-flex', gap:4}}>
              {widget.behavior.collapsible && (
                <button
                  onMouseDown={(e) => e.stopPropagation()}
                  onClick={() => onToggleWidgetCollapsed(widget.id)}
                  style={{
                    width:16,height:16,border:'1px solid rgba(60,35,10,0.28)',borderRadius:3,
                    background:'rgba(255,255,255,0.45)',cursor:'pointer',fontSize:10,lineHeight:1,
                    color:'rgba(60,35,10,0.75)'
                  }}
                >{widget.collapsed ? '+' : '–'}</button>
              )}
              <button
                onMouseDown={(e) => e.stopPropagation()}
                onClick={() => onRemoveWidget(widget.id)}
                style={{
                  width:16,height:16,border:'1px solid rgba(60,35,10,0.28)',borderRadius:3,
                  background:'rgba(255,255,255,0.45)',cursor:'pointer',fontSize:9,lineHeight:1,
                  color:'rgba(60,35,10,0.75)'
                }}
              >×</button>
            </div>
          </div>

          {!widget.collapsed && (
            <div style={{
              flex: 1,
              padding: 8,
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
              position: 'relative',
              overflow: 'auto',
            }}>
              <div style={{display:'flex', flexWrap:'wrap', gap:4}}>
                {widget.options.map((opt, idx) => (
                  <span key={`${widget.id}-${idx}`} style={{
                    fontSize: 8,
                    border: `1px solid ${widget.colors.border}`,
                    background: widget.colors.chip,
                    borderRadius: 999,
                    padding: '2px 6px',
                    color: 'rgba(44,26,10,0.9)',
                    lineHeight: 1.2,
                  }}>{opt}</span>
                ))}
              </div>
              <div style={{display:'flex', gap:4}}>
                <input
                  value={widget.draftOption}
                  onChange={(e) => onSetWidgetDraft(widget.id, e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') onAddWidgetOption(widget.id);
                  }}
                  placeholder="Add option"
                  style={{
                    flex: 1,
                    minWidth: 0,
                    border: '1px solid rgba(100,65,25,0.28)',
                    borderRadius: 4,
                    background: 'rgba(255,248,238,0.9)',
                    color: 'rgba(60,35,10,0.92)',
                    fontSize: 8,
                    padding: '4px 6px',
                    fontFamily: "'DM Mono',monospace",
                  }}
                />
                <button
                  onClick={() => onAddWidgetOption(widget.id)}
                  style={{
                    border: '1px solid rgba(100,65,25,0.35)',
                    borderRadius: 4,
                    background: 'rgba(255,245,232,0.9)',
                    color: 'rgba(60,35,10,0.92)',
                    fontSize: 8,
                    padding: '4px 7px',
                    cursor: 'pointer',
                    fontFamily: "'DM Mono',monospace",
                  }}
                >ADD</button>
              </div>

              {widget.behavior.resizable && (
                <div
                  onMouseDown={(e) => beginResizeWidget(e, widget)}
                  style={{
                    position: 'absolute',
                    right: 3,
                    bottom: 2,
                    fontSize: 11,
                    cursor: 'nwse-resize',
                    userSelect: 'none',
                    color: 'rgba(60,35,10,0.55)',
                  }}
                >◢</div>
              )}
            </div>
          )}
        </div>
      ))}

      {contextMenu && (
        <div style={{
          position: 'absolute',
          left: contextMenu.x,
          top: contextMenu.y,
          width: 188,
          border: '1px solid rgba(100,65,25,0.35)',
          borderRadius: 6,
          background: 'rgba(248,238,224,0.96)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
          zIndex: 30,
          overflow: 'hidden',
        }}>
          <div style={{
            fontSize: 8,
            letterSpacing: '0.1em',
            fontWeight: 700,
            color: 'rgba(60,35,10,0.75)',
            background: 'rgba(120,80,30,0.14)',
            borderBottom: '1px solid rgba(100,65,25,0.2)',
            padding: '6px 8px',
          }}>
            CREATE MENU INSTANCE
          </div>
          <div style={{padding: 6, display:'flex', flexDirection:'column', gap:4}}>
            {Object.entries(CANVAS_WIDGET_ROLE_PRESETS).map(([roleKey, preset]) => (
              <button
                key={roleKey}
                onClick={() => {
                  onCreateWidget(roleKey, contextMenu);
                  onCloseContextMenu();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 8,
                  border: `1px solid ${preset.colors.border}`,
                  borderRadius: 5,
                  background: preset.colors.header,
                  color: 'rgba(44,26,10,0.92)',
                  padding: '6px 7px',
                  fontSize: 8,
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                  fontFamily: "'DM Mono',monospace",
                }}
              >
                <span>{preset.role}</span>
                <span style={{opacity:0.65}}>+</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FloatingWidget({ title, rect, onRectChange, minWidth = 180, minHeight = 44, children }) {
  const dragRef = useRef(null);

  const handleMoveStart = useCallback((e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    dragRef.current = {
      mode: 'move',
      startX: e.clientX,
      startY: e.clientY,
      startRect: rect,
    };

    const onMove = (me) => {
      const dx = me.clientX - dragRef.current.startX;
      const dy = me.clientY - dragRef.current.startY;
      onRectChange({
        ...dragRef.current.startRect,
        x: Math.max(0, dragRef.current.startRect.x + dx),
        y: Math.max(0, dragRef.current.startRect.y + dy),
      });
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [onRectChange, rect]);

  const handleResizeStart = useCallback((e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    dragRef.current = {
      mode: 'resize',
      startX: e.clientX,
      startY: e.clientY,
      startRect: rect,
    };

    const onMove = (me) => {
      const dx = me.clientX - dragRef.current.startX;
      const dy = me.clientY - dragRef.current.startY;
      onRectChange({
        ...dragRef.current.startRect,
        width: Math.max(minWidth, dragRef.current.startRect.width + dx),
        height: Math.max(minHeight, dragRef.current.startRect.height + dy),
      });
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [minHeight, minWidth, onRectChange, rect]);

  return (
    <div style={{
      position: 'fixed',
      left: rect.x,
      top: rect.y,
      width: rect.width,
      height: rect.height,
      border: '1px solid rgba(100,65,25,0.35)',
      background: 'rgba(232,212,184,0.86)',
      color: 'rgba(60,35,10,0.9)',
      borderRadius: 6,
      zIndex: 55,
      boxShadow: '0 4px 12px rgba(0,0,0,0.16)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      <div
        onMouseDown={handleMoveStart}
        style={{
          height: 20,
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 8px',
          cursor: 'grab',
          background: 'rgba(120,80,30,0.16)',
          borderBottom: '1px solid rgba(100,65,25,0.18)',
          fontSize: 8,
          letterSpacing: '0.1em',
          fontFamily: "'DM Mono',monospace",
          userSelect: 'none',
        }}
      >
        <span>{title}</span>
        <span style={{opacity: 0.5}}>⠿</span>
      </div>
      <div style={{
        position: 'relative',
        flex: 1,
        padding: 8,
        overflow: 'auto',
      }}>
        {children}
        <div
          onMouseDown={handleResizeStart}
          style={{
            position: 'absolute',
            right: 2,
            bottom: 2,
            width: 12,
            height: 12,
            cursor: 'nwse-resize',
            opacity: 0.55,
            userSelect: 'none',
          }}
        >
          ◢
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// APP
// ═══════════════════════════════════════════════════════════════════════════════

export default function LALOApp() {
  const {
    song,
    menu,
    dock,
    drawerOpen,
    drawerSizes,
    drawerPos,
    activePanel,
    openMenu,
    closeMenu,
    setDock: handleDockChange,
    setDrawerOpen,
    setDrawerSize,
    setDrawerPos,
    setActivePanel,
    setImportMeta,
    addChordEvent,
    updateChordEvent,
    changeMeter,
    applyTheoryToSection,
    importSong,
    progressionTypes,
    songMeta,
    setSongMeta,
    importArtist,
    importStrategy,
    setImportStrategy,
    titleStyle,
    setTitleStyle,
    toast,
    setToast,
    dragOver,
    setDragOver,
    setDragDepth,
    widgetRects,
    setWidgetRect,
    canvasWidgets,
    setCanvasWidgets,
    canvasContextMenu,
    setCanvasContextMenu,
  } = useSongStore();
  const toastTimerRef = useRef(null);

  const openCanvasContextMenu = useCallback((position) => {
    setCanvasContextMenu(position);
  }, []);

  const closeCanvasContextMenu = useCallback(() => {
    setCanvasContextMenu(null);
  }, []);

  const createCanvasWidgetInstance = useCallback((roleKey, position) => {
    setCanvasWidgets(prev => [...prev, createCanvasWidget(roleKey, position)]);
  }, []);

  const updateCanvasWidget = useCallback((widgetId, patch) => {
    setCanvasWidgets(prev => prev.map(widget => {
      if (widget.id !== widgetId) return widget;
      return {
        ...widget,
        ...patch,
        rect: patch.rect ? { ...widget.rect, ...patch.rect } : widget.rect,
      };
    }));
  }, []);

  const removeCanvasWidget = useCallback((widgetId) => {
    setCanvasWidgets(prev => prev.filter(widget => widget.id !== widgetId));
  }, []);

  const toggleCanvasWidgetCollapsed = useCallback((widgetId) => {
    setCanvasWidgets(prev => prev.map(widget => (
      widget.id === widgetId ? { ...widget, collapsed: !widget.collapsed } : widget
    )));
  }, []);

  const setCanvasWidgetDraft = useCallback((widgetId, draftOption) => {
    setCanvasWidgets(prev => prev.map(widget => (
      widget.id === widgetId ? { ...widget, draftOption } : widget
    )));
  }, []);

  const addCanvasWidgetOption = useCallback((widgetId) => {
    setCanvasWidgets(prev => prev.map(widget => {
      if (widget.id !== widgetId) return widget;
      const value = widget.draftOption.trim();
      if (!value) return widget;
      return {
        ...widget,
        options: [...widget.options, value],
        draftOption: '',
      };
    }));
  }, []);

  const showImportToast = useCallback((message, tone = "ok") => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, tone });
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);

  const handleApplyTheoryToSection = useCallback((sectionId, payload) => {
    if (!payload || payload.kind !== 'theory-progression') return;
    const section = song.find(s => s.id === sectionId);
    if (!section) return;
    const events = buildTheoryEventsForSection(section, payload, {
      createEventId: () => evId++,
      source: 'theory',
      sectionId,
    });
    if (!events.length) return;
    applyTheoryToSection(sectionId, events);

    showImportToast(`Applied theory: ${payload.label}`, 'ok');
  }, [applyTheoryToSection, showImportToast, song]);

  const theoryGroups = useMemo(() => {
    const detectedItems = (progressionTypes ?? []).map((type) => {
      const displayName = type.displayName ?? type.namedMatch?.name ?? type.id;
      return {
        id: `det-${type.id}`,
        label: `${displayName} · ${type.occurrenceCount ?? 0}x`,
        tokens: type.numerals ?? [],
      };
    });

    if (!detectedItems.length) return undefined;

    return [{
      id: 'detected',
      label: 'Detected Progressions',
      color: 'rgba(184,72,48,0.92)',
      items: detectedItems,
    }];
  }, [progressionTypes]);

  const updateSongMeta = useCallback((patch) => {
    setSongMeta(patch);
  }, [setSongMeta]);

  const handleDropJson = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    setDragDepth(0);

    const files = Array.from(e.dataTransfer?.files ?? []);
    const file = files.find(f => f.name.toLowerCase().endsWith(".json"));
    if (!file) {
      showImportToast("Import failed: drop a .json file.", "error");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result ?? ""));
        const imported = (importMcGillJson(parsed, { sectionStrategy: importStrategy }) ?? []).map(section => ({
          ...section,
          events: [...(section.events ?? [])].sort((a, b) => a.beat - b.beat),
        }));
        const meta = imported?.[0]?.meta ?? null;
        importSong(imported, meta);
        setImportMeta(meta);
        showImportToast(`Imported (${importStrategy}): ${(meta?.title ?? "Untitled")} \u2014 ${(meta?.artist ?? "Unknown Artist")}`, "ok");
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        showImportToast(`Import failed: ${msg}`, "error");
      }
    };
    reader.onerror = () => showImportToast("Import failed: could not read file.", "error");
    reader.readAsText(file);
  }, [importSong, importStrategy, setImportMeta, showImportToast]);

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
    openMenu({x:e.clientX,y:e.clientY,sectionId,beat,existingEv:null,prevChord,sectionKey:sec?.key??"C",sectionMode:sec?.mode??"major"});
  },[openMenu, song]);

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
    openMenu({x:e.clientX,y:e.clientY,sectionId,beat:ev.beat,existingEv:ev,prevChord,sectionKey:sec?.key??"C",sectionMode:sec?.mode??"major"});
  },[openMenu, song]);

  const handleCommit = useCallback(chord=>{
    if(!menu)return;
    const sec = song.find(s => s.id === menu.sectionId);
    if (!sec) return;
    const map=beatMap(sec);
    let span=1;
    for(let b=menu.beat+1;b<sec.totalBeats&&b<menu.beat+2;b++){
      if(map[b]===null)span++; else break;
    }
    const newEv = {
      id:           evId++,
      sectionId:    menu.sectionId,
      beat:         menu.beat,
      beatFloat:    menu.beat,
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
      updateChordEvent(menu.sectionId, menu.existingEv.id, newEv);
    } else {
      addChordEvent(menu.sectionId, newEv);
    }
    closeMenu();
  },[addChordEvent, closeMenu, menu, song, updateChordEvent]);

  const handleResizeChord = useCallback((ev,newSpan)=>{
    updateChordEvent(ev.sectionId, ev.id, {
      span:newSpan,
      durationBeats:newSpan,
    });
  },[updateChordEvent]);

  const handleChangeMeter = useCallback((sectionId,timeSig,bars)=>{
    changeMeter(sectionId, timeSig, bars);
  },[changeMeter]);

  // Inset the canvas so it doesn't hide behind the drawer.
  // When the drawer is floating (drawerPos != null) no inset is needed.
  const drawerSz = drawerOpen ? drawerSizes[dock] : 36;

  const handleTempoChange = useCallback((e) => {
    const n = Number.parseInt(e.target.value, 10);
    if (Number.isNaN(n)) {
      updateSongMeta({ tempo: DEFAULT_SONG_META.tempo });
      return;
    }
    const tempo = Math.max(40, Math.min(240, n));
    updateSongMeta({ tempo });
  }, [updateSongMeta]);
  const canvasInset = drawerPos ? {} : {
    paddingBottom: dock==="bottom"?drawerSz:0,
    paddingTop:    dock==="top"   ?drawerSz:0,
    paddingLeft:   dock==="left"  ?drawerSz:0,
    paddingRight:  dock==="right" ?drawerSz:0,
  };

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
        <MockCanvas
          songMeta={songMeta}
          artist={importArtist}
          dragActive={dragOver}
          titleStyle={titleStyle}
          widgets={canvasWidgets}
          contextMenu={canvasContextMenu}
          onOpenContextMenu={openCanvasContextMenu}
          onCloseContextMenu={closeCanvasContextMenu}
          onCreateWidget={createCanvasWidgetInstance}
          onUpdateWidget={updateCanvasWidget}
          onRemoveWidget={removeCanvasWidget}
          onToggleWidgetCollapsed={toggleCanvasWidgetCollapsed}
          onSetWidgetDraft={setCanvasWidgetDraft}
          onAddWidgetOption={addCanvasWidgetOption}
        />
      </div>

      <FloatingWidget
        title="SONG SETUP"
        rect={widgetRects.song}
        onRectChange={(next) => setWidgetRect('song', next)}
        minWidth={500}
        minHeight={90}
      >
        <div style={{display:'flex', alignItems:'center', gap:6, flexWrap:'wrap'}}>
          <input
            value={songMeta.title}
            onChange={(e) => updateSongMeta({ title: e.target.value })}
            placeholder="Title"
            style={{
              width:140,
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          />
          <input
            type="number"
            min={40}
            max={240}
            value={songMeta.tempo}
            onChange={handleTempoChange}
            style={{
              width:62,
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          />
          <select
            value={songMeta.key}
            onChange={(e) => updateSongMeta({ key: e.target.value })}
            style={{
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          >
            {ROOTS.map(root => (
              <option key={root} value={root}>{root}</option>
            ))}
          </select>
          <select
            value={songMeta.mode}
            onChange={(e) => updateSongMeta({ mode: e.target.value })}
            style={{
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          >
            {MODE_OPTIONS.map(mode => (
              <option key={mode} value={mode}>{mode.toUpperCase()}</option>
            ))}
          </select>
          <label style={{display:'inline-flex', alignItems:'center', gap:4, fontSize:8, letterSpacing:'0.04em'}}>
            <input
              type="checkbox"
              checked={titleStyle.uppercase}
              onChange={(e) => setTitleStyle(prev => ({ ...prev, uppercase: e.target.checked }))}
            />
            UPPER
          </label>
          <input
            type="number"
            min={8}
            max={18}
            value={titleStyle.size}
            onChange={(e) => setTitleStyle(prev => ({ ...prev, size: Math.max(8, Math.min(18, Number.parseInt(e.target.value || '11', 10))) }))}
            title="title size"
            style={{
              width:54,
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          />
          <input
            type="range"
            min={0}
            max={0.2}
            step={0.01}
            value={titleStyle.letterSpacing}
            onChange={(e) => setTitleStyle(prev => ({ ...prev, letterSpacing: Number.parseFloat(e.target.value) }))}
            title="title spacing"
            style={{width:72}}
          />
          <select
            value={titleStyle.weight}
            onChange={(e) => setTitleStyle(prev => ({ ...prev, weight: Number.parseInt(e.target.value, 10) }))}
            style={{
              border:"1px solid rgba(100,65,25,0.3)",
              background:"rgba(255,250,242,0.72)",
              color:"rgba(60,35,10,0.92)",
              borderRadius:4,
              padding:"3px 5px",
              fontSize:9,
              fontFamily:"'DM Mono',monospace",
            }}
          >
            {[400, 500, 600, 700].map(weight => (
              <option key={weight} value={weight}>{weight}</option>
            ))}
          </select>
        </div>
      </FloatingWidget>

      {/* Chord canvas drawer */}
      <Drawer side={dock} size={drawerSizes[dock]} onResize={(size) => setDrawerSize(dock, size)}
        open={drawerOpen} onToggle={()=>setDrawerOpen(!drawerOpen)}
        pos={drawerPos} onPosChange={setDrawerPos}>
        {/* Panel tab bar */}
        <div style={{
          display:"flex", borderBottom:"1px solid rgba(100,65,25,0.15)",
          background:"rgba(200,165,120,0.3)", flexShrink:0,
        }}>
          {[
            { id:"canvas",  label:"CHORD CANVAS" },
            { id:"harmony", label:"HARMONY" },
            { id:"theory", label:"THEORY" },
          ].map(tab=>(
            <button key={tab.id} onClick={()=>setActivePanel(tab.id)} style={{
              background: activePanel===tab.id ? "rgba(100,65,25,0.12)" : "transparent",
              border:"none", borderBottom: activePanel===tab.id ? "2px solid rgba(100,65,25,0.6)" : "2px solid transparent",
              padding:"6px 14px", cursor:"pointer",
              fontSize:8, fontWeight:700, letterSpacing:"0.12em",
              color: activePanel===tab.id ? "rgba(60,35,10,0.9)" : "rgba(100,65,25,0.45)",
              fontFamily:"'DM Mono',monospace",
              transition:"all 0.12s",
            }}>{tab.label}</button>
          ))}
        </div>
        {/* Panel content */}
        {activePanel==="canvas" && (
          <ChordCanvas
            onAddChord={openAdd} onResizeChord={handleResizeChord}
            onEditChord={openEdit} onChangeMeter={handleChangeMeter}
            titleStyle={titleStyle}
            onDropTheory={handleApplyTheoryToSection}/>
        )}
        {activePanel==="harmony" && (
          <HarmonyPanel style={{height:"100%",overflowY:"auto"}}/>
        )}
        {activePanel==="theory" && (
          <TheoryPanel detectedGroups={theoryGroups} />
        )}
      </Drawer>

      {/* Dock side picker */}
      <DockPicker current={dock} onChange={handleDockChange}/>

      <FloatingWidget
        title="IMPORT"
        rect={widgetRects.strategy}
        onRectChange={(next) => setWidgetRect('strategy', next)}
        minWidth={180}
        minHeight={56}
      >
        <button
          onClick={() => setImportStrategy((s) => (s === "auto-json" ? "dataset" : "auto-json"))}
          style={{
            width: '100%',
            border:"1px solid rgba(100,65,25,0.35)",
            background:"rgba(255,245,232,0.84)",
            color:"rgba(60,35,10,0.9)",
            borderRadius:5,
            padding:"7px 8px",
            fontSize:9,
            letterSpacing:"0.08em",
            fontFamily:"'DM Mono',monospace",
            cursor:"pointer",
          }}>
          STRATEGY: {importStrategy.toUpperCase()}
        </button>
      </FloatingWidget>

      <FloatingWidget
        title="DEBUG"
        rect={widgetRects.debug}
        onRectChange={(next) => setWidgetRect('debug', next)}
        minWidth={180}
        minHeight={56}
      >
        <button
          onClick={handleCopyDebugJson}
          style={{
            width: '100%',
            border:"1px solid rgba(100,65,25,0.35)",
            background:"rgba(255,245,232,0.84)",
            color:"rgba(60,35,10,0.9)",
            borderRadius:5,
            padding:"7px 8px",
            fontSize:9,
            letterSpacing:"0.08em",
            fontFamily:"'DM Mono',monospace",
            cursor:"pointer",
          }}>
          COPY DEBUG JSON
        </button>
      </FloatingWidget>

      {/* Radial chord menu */}
      {menu&&(
        <RadialChordMenu position={menu} onCommit={handleCommit} onClose={closeMenu}
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
