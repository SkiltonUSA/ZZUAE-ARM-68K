from pathlib import Path
import re,json,statistics

p=Path(__file__).resolve().parent
g=p.parent/'gameplay'
rows=[]
signature=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
expected=None
pixels=None
for variant,tag in [('pixel4','sprite-neon-locked'),('sprite-neon','sprite-neon-locked'),('sprite-neon','sprite-neon-repeat-locked'),('pixel4','sprite-neon-repeat-locked')]:
    folder=g/f'banshee-demo-{variant}-interpreter020-paula-6000-{tag}'
    s=(folder/'run.log').read_text()
    metrics=json.loads((folder/'metrics.json').read_text())
    state=re.search(signature,s).groups()
    if expected is None:expected,pixels=state,metrics['pixels_sha256']
    assert state==expected and metrics['pixels_sha256']==pixels
    for marker in ('UAE_MACHINE PASS','failed=0','witness_bad=0',
                   'register_mismatches=00000000','owned memory released',
                   'error=0 stopped=1','input_events=0','simd_errors=0'):
        assert marker in s,marker
    pcm=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',s).groups()
    assert pcm[0]==pcm[1]==pcm[2]=='3330048'
    assert 'nonzero_frames=2296574' in s
    rows.append(dict(variant=variant,tag=tag,**metrics,audio_gaps=int(pcm[3]),
                     pcm_frames=int(pcm[0]),guest_signature=state))
medians={v:statistics.median(r['mean_emulated_fps'] for r in rows if r['variant']==v) for v in ('pixel4','sprite-neon')}
gain=(medians['sprite-neon']/medians['pixel4']-1)*100
result={'scope':'Matched whole-run emulated FPS; not displayed/game FPS or listening acceptance',
        'median_fps_change_percent':gain,'median_fps':medians,'pair_changes_percent':[(rows[1]['mean_emulated_fps']/rows[0]['mean_emulated_fps']-1)*100,(rows[2]['mean_emulated_fps']/rows[3]['mean_emulated_fps']-1)*100],'runs':rows}
(p/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
print('PASS matching guest state, pixels, complete PCM delivery and clean teardown')
