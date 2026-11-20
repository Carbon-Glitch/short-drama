"""Build one continuous music gain curve from final-clock speech intervals."""
from __future__ import annotations


def envelope(intervals, duration, *, depth_db=-10, lead=.12, release=.35, merge_gap=.3):
    merged=[]
    for start,end in sorted(intervals):
        start=max(0,float(start));end=min(duration,float(end))
        if end<=start:continue
        if merged and start-merged[-1][1]<=max(merge_gap,lead+release):
            merged[-1][1]=max(end,merged[-1][1])
        else:merged.append([start,end])
    points={0.:0.,duration:0.}
    for start,end in merged:
        points[max(0,start-lead)]=0.
        points[start]=depth_db
        points[end]=depth_db
        if end<duration:points[min(duration,end+release)]=0.
    return [{'time':t,'db':v} for t,v in sorted(points.items())]


def speech_windows(clips,audio):
    windows=[];basis=[]
    for clip in clips:
        if not clip['native_audio']:continue
        evidence=clip.get('speech_evidence',{})
        if evidence.get('status')!='ok':
            basis.append({'id':clip['id'],'basis':'native speech timing unavailable'})
            continue
        for segment in evidence.get('segments',[]):
            for part in clip['mapping']:
                a=max(segment['start'],part['source_start']);b=min(segment['end'],part['source_end'])
                if b>a:windows.append((clip['at']+part['target_start']+(a-part['source_start'])/part['speed'],
                                      clip['at']+part['target_start']+(b-part['source_start'])/part['speed']))
        basis.append({'id':clip['id'],'basis':'source ASR mapped to final clock'})
    for event in audio:
        if event['bus'] not in {'dialogue','native'}:continue
        evidence=event.get('speech_evidence',{})
        if evidence.get('status')=='ok':
            for segment in evidence.get('segments',[]):
                a=max(event['start'],segment['start']);b=min(event['end'],segment['end'])
                if b>a:windows.append((event['at']+(a-event['start'])/event['speed'],
                                      min(event['until'],event['at']+(b-event['start'])/event['speed'])))
            basis.append({'id':event['id'],'basis':'source ASR mapped to final clock'})
        elif event['bus']=='dialogue':
            windows.append((event['at'],event['until']))
            basis.append({'id':event['id'],'basis':'declared dialogue event; phrase-level timing unavailable'})
    return windows,basis
