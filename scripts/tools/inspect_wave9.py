import json
w=json.load(open('results/sections-machine-b-wave9.json'))
a=w.get('per_song',[])
wa=[p for p in a if p.get('audio')]
print('per_song_count',len(a))
print('with_audio_count',len(wa))
for p in wa[:8]:
    print(p)
