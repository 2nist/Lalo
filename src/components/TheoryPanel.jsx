import { useCallback, useMemo } from 'react';

const DEFAULT_THEORY_GROUPS = [
  {
    id: 'cadences',
    label: 'Cadences',
    color: 'rgba(58,94,138,0.9)',
    items: [
      { id: 'cad-auth', label: 'Authentic V–I', tokens: ['V', 'I'] },
      { id: 'cad-plag', label: 'Plagal IV–I', tokens: ['IV', 'I'] },
      { id: 'cad-decept', label: 'Deceptive V–vi', tokens: ['V', 'vi'] },
      { id: 'cad-ii-v-i', label: 'ii–V–I', tokens: ['ii', 'V', 'I'] },
    ],
  },
  {
    id: 'progressions',
    label: 'Preset Progressions',
    color: 'rgba(122,88,36,0.9)',
    items: [
      { id: 'prog-pop', label: 'Pop I–V–vi–IV', tokens: ['I', 'V', 'vi', 'IV'] },
      { id: 'prog-alt', label: 'vi–IV–I–V', tokens: ['vi', 'IV', 'I', 'V'] },
      { id: 'prog-circle', label: 'iii–vi–ii–V', tokens: ['iii', 'vi', 'ii', 'V'] },
      { id: 'prog-minor', label: 'i–♭VII–♭VI–V', tokens: ['i', '♭VII', '♭VI', 'V'] },
    ],
  },
  {
    id: 'subs',
    label: 'Substitutions',
    color: 'rgba(108,58,124,0.9)',
    items: [
      { id: 'sub-tritone', label: 'Tritone Sub ♭II7–I', tokens: ['♭II7', 'I'] },
      { id: 'sub-borrowed', label: 'Borrowed iv–I', tokens: ['iv', 'I'] },
      { id: 'sub-backdoor', label: 'Backdoor ♭VII7–I', tokens: ['♭VII7', 'I'] },
      { id: 'sub-neap', label: 'Neapolitan ♭II–V–I', tokens: ['♭II', 'V', 'I'] },
    ],
  },
];

export default function TheoryPanel({ groups = DEFAULT_THEORY_GROUPS, detectedGroups = [] }) {
  const mergedGroups = useMemo(() => {
    const detected = Array.isArray(detectedGroups)
      ? detectedGroups.filter(group => Array.isArray(group?.items) && group.items.length)
      : [];
    return [...detected, ...groups];
  }, [detectedGroups, groups]);

  const handleDragStart = useCallback((e, group, item) => {
    const payload = {
      kind: 'theory-progression',
      groupId: group.id,
      groupLabel: group.label,
      itemId: item.id,
      label: item.label,
      tokens: item.tokens,
    };
    e.dataTransfer.setData('application/x-lalo-theory', JSON.stringify(payload));
    e.dataTransfer.setData('text/plain', JSON.stringify(payload));
    e.dataTransfer.effectAllowed = 'copy';
  }, []);

  return (
    <div style={{padding:'12px 14px 20px', display:'flex', flexDirection:'column', gap:12}}>
      <div style={{fontSize:8, letterSpacing:'0.16em', color:'rgba(100,65,25,0.5)'}}>THEORY MENU</div>
      <div style={{fontSize:8, color:'rgba(100,65,25,0.55)', lineHeight:1.5}}>
        Drag any pill to a section row in the song map to populate contextual chords.
      </div>
      {mergedGroups.map(group => (
        <div key={group.id} style={{display:'flex', flexDirection:'column', gap:6}}>
          <div style={{
            fontSize:8,
            letterSpacing:'0.08em',
            fontWeight:700,
            color:'rgba(60,35,10,0.82)',
            borderLeft:`3px solid ${group.color}`,
            paddingLeft:6,
          }}>{group.label.toUpperCase()}</div>
          <div style={{display:'flex', flexWrap:'wrap', gap:6}}>
            {group.items.map(item => (
              <div
                key={item.id}
                draggable
                onDragStart={(e) => handleDragStart(e, group, item)}
                style={{
                  border:`1px solid ${group.color}`,
                  background:'rgba(255,247,236,0.92)',
                  borderRadius:999,
                  padding:'5px 9px',
                  fontSize:8,
                  color:'rgba(45,25,8,0.92)',
                  letterSpacing:'0.04em',
                  cursor:'grab',
                  userSelect:'none',
                }}
                title={`Drag to song map · ${item.tokens.join(' – ')}`}>
                {item.label}
              </div>
            ))}
          </div>
        </div>
      ))}
      {!mergedGroups.length && (
        <div style={{fontSize:8, color:'rgba(100,65,25,0.55)', lineHeight:1.5}}>
          No theory groups available yet.
        </div>
      )}
    </div>
  );
}
