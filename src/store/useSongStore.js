import { create } from 'zustand'
import { INITIAL_SONG } from '../utils/harmonyEngine'
import { detectProgressions, buildProgressionLibrary } from '../core/index.js'

const DEFAULT_SONG_META = {
  title: 'New Song',
  tempo: 120,
  key: 'C',
  mode: 'major',
}

const DEFAULT_TITLE_STYLE = {
  uppercase: true,
  size: 11,
  letterSpacing: 0.08,
  weight: 700,
}

const DEFAULT_WIDGET_RECTS = {
  song: { x: 14, y: 14, width: 620, height: 98 },
  strategy: { x: 14, y: 118, width: 220, height: 62 },
  debug: { x: 240, y: 118, width: 220, height: 62 },
}

function buildProgressionState(song = []) {
  try {
    const detectionResult = detectProgressions(song)
    const library = buildProgressionLibrary(detectionResult, song)
    return {
      progressionTypes: library.types,
      progressionInstances: library.instances,
      selectedInstanceId: null,
    }
  } catch (e) {
    console.warn('Detection failed:', e)
    return {
      progressionTypes: [],
      progressionInstances: [],
      selectedInstanceId: null,
    }
  }
}

export const useSongStore = create((set) => ({
  // -- Song data ---------------------------------------------------------------
  song: INITIAL_SONG,

  // -- Progression layer -------------------------------------------------------
  progressionTypes: [],
  progressionInstances: [],

  // -- UI state ----------------------------------------------------------------
  selectedInstanceId: null,
  importMeta: null,

  // -- Drawer/dock -------------------------------------------------------------
  dock: 'bottom',
  drawerOpen: true,
  drawerSizes: { bottom: 260, top: 260, left: 340, right: 340 },
  drawerPos: null,
  activePanel: 'canvas',

  // -- Radial menu -------------------------------------------------------------
  menu: null,

  // -- Extra app UI state (lifted from LALOApp) -------------------------------
  songMeta: DEFAULT_SONG_META,
  importArtist: null,
  importStrategy: 'auto-json',
  titleStyle: DEFAULT_TITLE_STYLE,
  toast: null,
  dragOver: false,
  dragDepth: 0,
  widgetRects: DEFAULT_WIDGET_RECTS,
  canvasWidgets: [],
  canvasContextMenu: null,

  // -- Song actions ------------------------------------------------------------
  setSong: (newSong) => set(() => ({
    song: newSong,
    ...buildProgressionState(newSong),
  })),

  updateSection: (sectionId, patch) => set(state => {
    const song = state.song.map(s => (s.id === sectionId ? { ...s, ...patch } : s))
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  addChordEvent: (sectionId, event) => set(state => {
    const song = state.song.map(s => {
      if (s.id !== sectionId) return s
      const events = [...s.events, event].sort((a, b) => a.beat - b.beat)
      return { ...s, events }
    })
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  updateChordEvent: (sectionId, eventId, patch) => set(state => {
    const song = state.song.map(s => {
      if (s.id !== sectionId) return s
      const events = s.events
        .map(e => (e.id === eventId ? { ...e, ...patch } : e))
        .sort((a, b) => a.beat - b.beat)
      return { ...s, events }
    })
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  removeChordEvent: (sectionId, eventId) => set(state => {
    const song = state.song.map(s => {
      if (s.id !== sectionId) return s
      return { ...s, events: s.events.filter(e => e.id !== eventId) }
    })
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  applyTheoryToSection: (sectionId, events) => set(state => {
    const song = state.song.map(s => {
      if (s.id !== sectionId) return s
      return { ...s, events: [...events].sort((a, b) => a.beat - b.beat) }
    })
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  changeMeter: (sectionId, timeSig, bars) => set(state => {
    const song = state.song.map(s => {
      if (s.id !== sectionId) return s
      const totalBeats = timeSig * bars
      const events = s.events
        .filter(e => e.beat < totalBeats)
        .map(e => {
          const span = Math.min(e.span, totalBeats - e.beat)
          return {
            ...e,
            span,
            durationBeats: Math.min(e.durationBeats ?? e.span, totalBeats - e.beat),
          }
        })
      return { ...s, timeSig, bars, totalBeats, events }
    })
    return {
      song,
      ...buildProgressionState(song),
    }
  }),

  // -- Progression actions -----------------------------------------------------
  runDetection: () => set(state => {
    if (!state.song.length) return {}
    return buildProgressionState(state.song)
  }),

  setProgressionLibrary: (types, instances) => set({
    progressionTypes: types,
    progressionInstances: instances,
  }),

  placeInstance: (instance) => set(state => ({
    progressionInstances: [...state.progressionInstances, instance],
  })),

  updateInstance: (instanceId, patch) => set(state => ({
    progressionInstances: state.progressionInstances.map(inst =>
      (inst.id === instanceId ? { ...inst, ...patch } : inst)
    ),
  })),

  removeInstance: (instanceId) => set(state => ({
    progressionInstances: state.progressionInstances.filter(i => i.id !== instanceId),
  })),

  setSelectedInstance: (id) => set({ selectedInstanceId: id }),

  // -- Import actions ----------------------------------------------------------
  setImportMeta: (meta) => set({ importMeta: meta }),

  importSong: (song, meta) => set(() => {
    const progressionState = buildProgressionState(song)

    const first = song?.[0] ?? {}
    return {
      song,
      importMeta: meta,
      ...progressionState,
      songMeta: {
        title: meta?.title ?? DEFAULT_SONG_META.title,
        tempo: first?.bpm ?? meta?.bpm ?? DEFAULT_SONG_META.tempo,
        key: first?.key ?? DEFAULT_SONG_META.key,
        mode: first?.mode ?? DEFAULT_SONG_META.mode,
      },
      importArtist: meta?.artist ?? null,
    }
  }),

  // -- UI actions --------------------------------------------------------------
  setDock: (dock) => set({ dock, drawerOpen: true }),
  setDrawerOpen: (open) => set({ drawerOpen: open }),
  setDrawerSize: (dock, size) => set(state => ({
    drawerSizes: { ...state.drawerSizes, [dock]: size },
  })),
  setDrawerPos: (pos) => set({ drawerPos: pos }),
  setActivePanel: (panel) => set({ activePanel: panel }),

  openMenu: (menuState) => set({ menu: menuState }),
  closeMenu: () => set({ menu: null }),

  setSongMeta: (patch) => set(state => {
    const songMeta = { ...state.songMeta, ...patch }
    const shouldSync = patch.tempo !== undefined || patch.key !== undefined || patch.mode !== undefined
    const song = shouldSync
      ? state.song.map(sec => ({
          ...sec,
          bpm: songMeta.tempo,
          key: songMeta.key,
          mode: songMeta.mode,
        }))
      : state.song
    return {
      songMeta,
      song,
      ...(shouldSync ? buildProgressionState(song) : {}),
    }
  }),
  setImportArtist: (importArtist) => set({ importArtist }),
  setImportStrategy: (importStrategy) => set({ importStrategy }),
  setTitleStyle: (updater) => set(state => ({
    titleStyle: typeof updater === 'function' ? updater(state.titleStyle) : updater,
  })),
  setToast: (toast) => set({ toast }),
  setDragOver: (dragOver) => set({ dragOver }),
  setDragDepth: (updater) => set(state => ({
    dragDepth: typeof updater === 'function' ? updater(state.dragDepth) : updater,
  })),
  setWidgetRect: (key, nextRect) => set(state => ({
    widgetRects: { ...state.widgetRects, [key]: nextRect },
  })),
  setCanvasWidgets: (updater) => set(state => ({
    canvasWidgets: typeof updater === 'function' ? updater(state.canvasWidgets) : updater,
  })),
  setCanvasContextMenu: (canvasContextMenu) => set({ canvasContextMenu }),
}))

export const selectInstancesForSection = (state, sectionId) =>
  state.progressionInstances.filter(i => i.sectionId === sectionId)

export const selectTypeById = (state, typeId) =>
  state.progressionTypes.find(t => t.id === typeId) ?? null

export const selectSelectedInstance = (state) =>
  state.progressionInstances.find(i => i.id === state.selectedInstanceId) ?? null

export const selectSectionsForType = (state, typeId) => {
  const instanceSectionIds = state.progressionInstances
    .filter(i => i.typeId === typeId)
    .map(i => i.sectionId)
  return state.song.filter(s => instanceSectionIds.includes(s.id))
}

export const selectSongSummary = (state) => ({
  sectionCount: state.song.length,
  typeCount: state.progressionTypes.length,
  instanceCount: state.progressionInstances.length,
  vampCount: state.progressionTypes.filter(t => t.isVamp).length,
  namedCount: state.progressionTypes.filter(t => t.namedMatch).length,
  importMeta: state.importMeta,
})
