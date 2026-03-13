import { useCallback, useRef } from 'react'

import { audioService } from '../../services/audioService'
import { buildImportSongData, importSongPayload } from '../../services/importAdapter'
import { mirService } from '../../services/mirService'

// YouTube channel names often have suffixes like "VEVO", "Official", "Records", etc.
// This pattern detects them so we can prefer the parsed title artist instead.
const CHANNEL_SUFFIX_RE = /\s*(VEVO|Official|Records|Music|HD|4K|Channel|TV|Entertainment)\s*$/i

/**
 * Try to extract "Artist" from a YouTube title like "Artist - Song Title (Official Video)".
 * Returns the parsed artist if found, or the channelName as-is otherwise.
 */
function resolveArtist(videoTitle, channelName) {
  if (!videoTitle) return channelName
  // If the channel name looks like a real artist name (no suffix), trust it
  if (channelName && !CHANNEL_SUFFIX_RE.test(channelName)) return channelName
  // Parse "Artist - Title" pattern from the video title
  const dashIdx = videoTitle.indexOf(' - ')
  if (dashIdx > 0) {
    let candidate = videoTitle.slice(0, dashIdx)
    // Strip trailing parenthesis or bracketed suffix like "(Official Video)" or "[Live]"
    const i1 = candidate.indexOf('(')
    const i2 = candidate.indexOf('[')
    let brIdx = -1
    if (i1 >= 0 && i2 >= 0) brIdx = Math.min(i1, i2)
    else if (i1 >= 0) brIdx = i1
    else if (i2 >= 0) brIdx = i2
    if (brIdx >= 0) candidate = candidate.slice(0, brIdx)
    candidate = candidate.trim()
    if (candidate.length > 0 && candidate.length < 60) return candidate
  }
  // Fall back to cleaned channel name (strip VEVO suffix etc.)
  return channelName ? channelName.replace(CHANNEL_SUFFIX_RE, '').trim() : channelName
}
import { persistSongSections } from '../songPersistence/persistence'

function makeHttpAudioUrl(slug) {
  return `http://localhost:8001/audio/${slug}`
}

function withApiStartupHint(message) {
  const text = String(message ?? '')
  if (!text.includes('MIR API unreachable')) return text
  if (text.includes('npm run dev:full')) return text
  return `${text}. Start the full desktop stack with "npm run dev:full" or launch the API separately with "npm run api".`
}

function deriveAudioSlug(url, slug, makeSlug) {
  const explicitSlug = String(slug ?? '').trim()
  if (explicitSlug) return explicitSlug

  const rawUrl = String(url ?? '').trim()
  if (!rawUrl) return ''

  try {
    const parsed = new URL(rawUrl)
    const videoId = parsed.searchParams.get('v')
    if (videoId) return makeSlug(videoId)

    const segments = parsed.pathname.split('/').filter(Boolean)
    const trailingSegment = segments.at(-1)
    if (trailingSegment && trailingSegment !== 'watch') {
      return makeSlug(trailingSegment)
    }
  } catch {
    // Fall back to slugifying the raw URL when URL parsing fails.
  }

  return makeSlug(rawUrl)
}

function normalizeLyricsPayload(payload) {
  if (!payload || typeof payload !== 'object') return null

  const synced = payload.synced ?? payload.synced_lyrics ?? null
  const plain = payload.plain ?? payload.plain_lyrics ?? null
  const lyricsStatus = payload.lyrics_status ?? null

  if (!synced && !plain && !lyricsStatus) return null

  return {
    ...payload,
    synced,
    plain,
    lyrics_status: lyricsStatus,
  }
}

function hasAnyLyrics(payload) {
  return !!(payload?.synced || payload?.plain)
}

async function loadSongLyrics(songMeta, showImportToast) {
  if (!mirService.canSongLyrics() || !songMeta?.id) return null

  try {
    const payload = normalizeLyricsPayload(await mirService.songLyrics(songMeta.id))

    if (!hasAnyLyrics(payload) && ['hit_synced', 'hit_plain'].includes(songMeta?.lyrics_status)) {
      showImportToast('Lyrics were expected for this pipeline song, but none were returned by the API.', 'error')
    }

    return payload
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    showImportToast(`Lyrics fetch failed: ${msg}`, 'error')
    return null
  }
}

function attachLegacySectionIds(song, sourceSections) {
  const sections = Array.isArray(song) ? song : []
  const originals = Array.isArray(sourceSections) ? sourceSections : []
  return sections.map((section, index) => ({
    ...section,
    dbSectionId: originals[index]?.id ?? originals[index]?.dbSectionId ?? null,
  }))
}

function mapStoredProgression(row) {
  const payload = row?.events_json ?? {}
  return {
    id: row.id,
    fingerprint: row.interval_key,
    name: row.roman_name,
    events: payload.events ?? [],
    occurrences: payload.occurrences ?? [],
    isVariant: !!row.is_variant,
    variantOf: row.variant_of_id ?? null,
    analysis: {
      canonical: row.pattern_common_name,
      cadence: row.pattern_category,
    },
  }
}

async function hydrateSongProgressions(song, songId) {
  if (!mirService.canSongProgressions() || !songId) return song
  const rows = await mirService.songProgressions({ songId })
  if (!Array.isArray(rows) || rows.length === 0) return song

  const bySectionId = new Map()
  for (const row of rows) {
    const key = row.legacy_section_id
    if (!key) continue
    if (!bySectionId.has(key)) bySectionId.set(key, [])
    bySectionId.get(key).push(mapStoredProgression(row))
  }

  return (Array.isArray(song) ? song : []).map(section => ({
    ...section,
    progressions: bySectionId.get(section.dbSectionId) ?? section.progressions,
  }))
}

async function persistImportedSong(song, options) {
  return persistSongSections(song, options, mirService)
}

export function useAudioImportFlow({
  audioUrl,
  setAudioUrl,
  audioSlug,
  setAudioSlug,
  makeSlug,
  importMeta,
  playableSrc,
  setPlayableSrc,
  showImportToast,
  setSong,
  setImportMeta,
  setSongLyrics,
  setPipelineStatus,
  setPipelineNote,
  setAudioBusy,
  setAudioAnalyzeBusy,
  setLyricsMode,
  setLyricsOpen,
  setPipelineModalOpen,
}) {
  const fetchAndAnalyzeRef = useRef(null)

  const handleLoadPipelineSong = useCallback(async (songMeta, sections) => {
    try {
      const songData = buildImportSongData(songMeta, sections)
      const imported = importSongPayload(songData, { sectionStrategy: 'dataset' })
      const withIds = attachLegacySectionIds(imported, sections)
      const hydrated = await hydrateSongProgressions(withIds, songMeta?.id)
      setSong(hydrated)
      setImportMeta({ title: songData.title, artist: songData.artist })
      setAudioSlug(makeSlug(`${songData.title}_${songData.artist}`))

      const lyricsPayload = await loadSongLyrics(songMeta, showImportToast)

      setSongLyrics(lyricsPayload ?? null)
      if (lyricsPayload?.synced) {
        setLyricsMode('align')
        setLyricsOpen(true)
      } else if (lyricsPayload?.plain) {
        setLyricsMode('read')
        setLyricsOpen(true)
      }

      showImportToast(`Loaded from pipeline: ${songData.title} — ${songData.artist}`, 'ok')
      setPipelineModalOpen(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      showImportToast(`Pipeline load failed: ${msg}`, 'error')
    }
  }, [makeSlug, setAudioSlug, setImportMeta, setLyricsMode, setLyricsOpen, setPipelineModalOpen, setSong, setSongLyrics, showImportToast])

  const handleFetchAudio = useCallback(async () => {
    const resolvedUrl = audioUrl.trim()
    const resolvedSlug = deriveAudioSlug(resolvedUrl, audioSlug, makeSlug)

    if (!resolvedUrl) {
      showImportToast('Audio fetch: provide a URL', 'error')
      return null
    }
    if (!resolvedSlug) {
      showImportToast('Audio fetch: could not derive a slug from the URL', 'error')
      return null
    }
    if (!audioService.canFetch()) {
      showImportToast('Audio fetch not available (electronAPI.audio missing). Run inside Electron.', 'error')
      return null
    }

    if (resolvedSlug !== audioSlug.trim()) {
      setAudioSlug(resolvedSlug)
    }

    setAudioBusy(true)
    setPipelineStatus('fetching')
    setPipelineNote('Downloading audio…')
    try {
      const result = await audioService.fetch({
        url: resolvedUrl,
        slug: resolvedSlug,
        outDir: 'data/audio',
      })
      const src = result?.fileUrl ?? `data/audio/${resolvedSlug}.m4a`
      setPlayableSrc(src)
      showImportToast('Audio fetched to data/audio', 'ok')
      return src
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      showImportToast(`Audio fetch failed: ${msg}`, 'error')
      setPipelineStatus('error')
      setPipelineNote(msg)
      return null
    } finally {
      setAudioBusy(false)
    }
  }, [audioSlug, audioUrl, makeSlug, setAudioBusy, setAudioSlug, setPipelineNote, setPipelineStatus, setPlayableSrc, showImportToast])

  const handleAnalyzeAudio = useCallback(async () => {
    const resolvedSlug = deriveAudioSlug(audioUrl, audioSlug, makeSlug)

    if (!resolvedSlug) {
      showImportToast('Audio analysis: provide a URL or slug first', 'error')
      return
    }
    if (!mirService.canAnalyzeAudio()) {
      showImportToast('Audio analysis not available (mir.analyzeAudio missing)', 'error')
      return
    }

    if (resolvedSlug !== audioSlug.trim()) {
      setAudioSlug(resolvedSlug)
    }

    setAudioAnalyzeBusy(true)
    setPipelineStatus('analyzing')
    setPipelineNote('Extracting chords + beat map…')
    try {
      const analyzePayload = {
        slug: resolvedSlug,
        title: importMeta?.title ?? 'Untitled',
        artist: importMeta?.artist ?? 'Unknown Artist',
        bars_per_section: 8,
        chord_detector: 'auto',
      }
      console.log('[LALO] handleAnalyzeAudio payload', analyzePayload)
      const payload = await mirService.analyzeAudio(analyzePayload)
      console.log('[LALO] handleAnalyzeAudio result', Object.keys(payload ?? {}))

      const songData = payload?.song
      if (!songData?.sections?.length) {
        throw new Error('No sections were produced by audio analysis')
      }

      const imported = importSongPayload(songData, { sectionStrategy: 'auto-json' })
      const persistedSong = await persistImportedSong(imported, {
        slug: resolvedSlug,
        analysis: {
          analysis_kind: 'audio-to-sections',
          provider: 'audioanalysis',
          model_name: payload?.analysis?.source ?? null,
          runtime_backend: 'fastapi',
          input_ref: resolvedSlug,
          metrics_json: payload?.analysis ?? null,
        },
      })
      setSong(persistedSong)
      setImportMeta(prev => ({
        title: prev?.title && prev.title !== 'Untitled' ? prev.title : (songData.title ?? 'Untitled'),
        artist: prev?.artist && prev.artist !== 'Unknown Artist' ? prev.artist : (songData.artist ?? 'Unknown Artist'),
      }))
      setSongLyrics(normalizeLyricsPayload(payload?.lyrics) ?? null)

      if (!playableSrc) {
        setPlayableSrc(makeHttpAudioUrl(resolvedSlug))
      }

      const model = payload?.analysis?.source ? ` [${payload.analysis.source}]` : ''
      const boundaries = payload?.analysis?.section_boundaries
      const secNote = boundaries?.length ? ` — ${boundaries.length} sections detected` : ''
      showImportToast(`Audio analysis imported${model}${secNote}`, 'ok')
      setPipelineStatus('ready')
      setPipelineNote(`${payload?.analysis?.source ?? 'ok'} · ${songData.sections.length} sections`)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[LALO] handleAnalyzeAudio error:', err)
      showImportToast(`Audio analysis failed: ${msg}`, 'error')
      setPipelineStatus('error')
      setPipelineNote(msg.slice(0, 120))
    } finally {
      setAudioAnalyzeBusy(false)
    }
  }, [audioSlug, audioUrl, importMeta, makeSlug, playableSrc, setAudioAnalyzeBusy, setAudioSlug, setImportMeta, setPipelineNote, setPipelineStatus, setPlayableSrc, setSong, setSongLyrics, showImportToast])

  const handleFetchAndAnalyze = useCallback(async (url, slug) => {
    console.log('[LALO] handleFetchAndAnalyze start', { url, slug })
    if (url) setAudioUrl(url)
    if (slug) setAudioSlug(slug)
    await new Promise(resolve => setTimeout(resolve, 0))

    const resolvedUrl = String(url ?? audioUrl ?? '').trim()
    const resolvedSlug = deriveAudioSlug(resolvedUrl, slug ?? audioSlug, makeSlug)

    if (resolvedSlug && resolvedSlug !== audioSlug.trim()) {
      setAudioSlug(resolvedSlug)
    }

    console.log('[LALO] bridge check', {
      hasFetch: audioService.canFetch(),
      hasAnalyze: mirService.canAnalyzeAudio(),
      hasFindFile: audioService.canFindFile(),
      resolvedUrl,
      resolvedSlug,
    })

    if (!resolvedUrl) {
      showImportToast('Fetch+Analyze: URL is required', 'error')
      return
    }
    if (!resolvedSlug) {
      showImportToast('Fetch+Analyze: could not derive a slug from the URL', 'error')
      return
    }
    if (!audioService.canFetch()) {
      showImportToast('Electron bridge unavailable — is the app running inside Electron? (window.electronAPI.audio missing)', 'error')
      return
    }
    if (!mirService.canAnalyzeAudio()) {
      showImportToast('MIR analyze API unavailable — is the Python API server running on port 8001? (window.electronAPI.mir.analyzeAudio missing)', 'error')
      return
    }

    setAudioBusy(true)
    setPipelineStatus('fetching')
    setPipelineNote('Downloading audio…')

    let oEmbedTitle = null
    let oEmbedArtist = null
    const ytVideoId = resolvedUrl.match(/[?&]v=([^&]+)/)?.[1]
    if (ytVideoId) {
      try {
        const response = await fetch(`https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=${ytVideoId}&format=json`)
        if (response.ok) {
          const meta = await response.json()
          oEmbedTitle = meta?.title ?? null
          oEmbedArtist = resolveArtist(meta?.title ?? null, meta?.author_name ?? null)
          if (oEmbedTitle) {
            setImportMeta({ title: oEmbedTitle, artist: oEmbedArtist ?? 'Unknown Artist' })
            console.log('[LALO] oEmbed meta:', oEmbedTitle, '—', oEmbedArtist)
          }
        }
      } catch {
        // non-fatal
      }
    }

    let fileSrc = null
    try {
      console.log('[LALO] calling audio:fetch', { url: resolvedUrl, slug: resolvedSlug })
      const result = await audioService.fetch({ url: resolvedUrl, slug: resolvedSlug, outDir: 'data/audio' })
      console.log('[LALO] audio:fetch result', result)
      fileSrc = result?.fileUrl ?? makeHttpAudioUrl(resolvedSlug)
      setPlayableSrc(fileSrc)
      if (!result?.ok) {
        throw new Error(result?.stdout ?? 'yt-dlp returned not-ok')
      }
      showImportToast('Audio fetched — starting analysis…', 'ok')
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      console.error('[LALO] audio:fetch threw', err)
      showImportToast(`Fetch failed: ${msg}`, 'error')
      setPipelineStatus('error')
      setPipelineNote(msg.slice(0, 120))
      setAudioBusy(false)
      return
    }
    setAudioBusy(false)

    setAudioAnalyzeBusy(true)
    setPipelineStatus('analyzing')
    setPipelineNote('Extracting chords + beat map…')
    try {
      const resolvedTitle = oEmbedTitle ?? importMeta?.title ?? 'Untitled'
      const resolvedArtist = oEmbedArtist ?? importMeta?.artist ?? 'Unknown Artist'
      const analyzePayload = {
        slug: resolvedSlug,
        title: resolvedTitle,
        artist: resolvedArtist,
        bars_per_section: 8,
        chord_detector: 'auto',
      }
      console.log('[LALO] calling mir:analyze-audio', analyzePayload)
      const payload = await mirService.analyzeAudio(analyzePayload)
      console.log('[LALO] mir:analyze-audio result keys', Object.keys(payload ?? {}))
      const songData = payload?.song
      if (!songData?.sections?.length) {
        console.error('[LALO] analyze returned no sections. Full payload:', payload)
        throw new Error(`No sections produced by analysis. API returned: ${JSON.stringify(payload).slice(0, 200)}`)
      }

      const imported = importSongPayload(songData, { sectionStrategy: 'auto-json' })
      const persistedSong = await persistImportedSong(imported, {
        slug: resolvedSlug,
        analysis: {
          analysis_kind: 'audio-to-sections',
          provider: 'audioanalysis',
          model_name: payload?.analysis?.source ?? null,
          runtime_backend: 'fastapi',
          input_ref: resolvedSlug,
          metrics_json: payload?.analysis ?? null,
        },
      })
      setSong(persistedSong)
      setImportMeta(prev => ({
        title: prev?.title && prev.title !== 'Untitled' ? prev.title : (songData.title ?? 'Untitled'),
        artist: prev?.artist && prev.artist !== 'Unknown Artist' ? prev.artist : (songData.artist ?? 'Unknown Artist'),
      }))
      setSongLyrics(normalizeLyricsPayload(payload?.lyrics) ?? null)
      if (!fileSrc) {
        fileSrc = makeHttpAudioUrl(resolvedSlug)
        setPlayableSrc(fileSrc)
        console.log('[LALO] set audio via HTTP fallback:', fileSrc)
      }
      const model = payload?.analysis?.source ? ` [${payload.analysis.source}]` : ''
      showImportToast(`Analysis done${model} — ${songData.sections.length} sections`, 'ok')
      setPipelineStatus('ready')
      setPipelineNote(`${payload?.analysis?.source ?? 'ok'} · ${songData.sections.length} sections`)
    } catch (err) {
      const msg = withApiStartupHint(err instanceof Error ? err.message : String(err))
      console.error('[LALO] mir:analyze-audio threw', err)
      showImportToast(`Analysis failed: ${msg}`, 'error')
      setPipelineStatus('error')
      setPipelineNote(msg.slice(0, 120))
    } finally {
      setAudioAnalyzeBusy(false)
    }
  }, [audioSlug, audioUrl, importMeta, makeSlug, setAudioAnalyzeBusy, setAudioBusy, setAudioSlug, setAudioUrl, setImportMeta, setPipelineNote, setPipelineStatus, setPlayableSrc, setSong, setSongLyrics, showImportToast])

  fetchAndAnalyzeRef.current = handleFetchAndAnalyze

  return {
    fetchAndAnalyzeRef,
    handleLoadPipelineSong,
    handleFetchAudio,
    handleAnalyzeAudio,
    handleFetchAndAnalyze,
  }
}