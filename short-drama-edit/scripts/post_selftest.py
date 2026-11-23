"""Focused regressions for exact cues, reusable stages and measured music onsets."""
from pathlib import Path
import math
import shutil
import sys
import tempfile
import unittest

from edit_tool import _display_cues
from post_runtime import StageCache, cue_ass


class PostRuntimeTests(unittest.TestCase):
    def test_long_sentence_keeps_measured_window(self):
        line='先把这句话完整说完，然后再看听者的反应。'
        result=_display_cues([(1.23,4.56,line,('反应',))],exact=True)
        self.assertEqual([(c.start,c.end,c.text) for c in result],[(1.23,4.56,line)])
        rendered=cue_ass([{'start':1.23,'end':4.56,'text':line,'keys':['反应']}],1080,1920,{'preset':'cinema'})
        self.assertEqual(rendered.count('Dialogue:'),1)
        self.assertIn('0:00:01.23,0:00:04.56',rendered)

    def test_text_cannot_create_an_ass_override(self):
        rendered=cue_ass([{'start':0,'end':1,'text':r'{\pos(0,0)} H','keys':['H']}],540,960,{'preset':'clear'})
        self.assertNotIn(r'{\pos(0,0)}',rendered)
        self.assertIn('｛',rendered)

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg build identity unavailable')
    def test_cache_reuses_only_unchanged_input_and_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';output=root/'result';source.write_bytes(b'first')
            cache=StageCache(root/'cache',shutil.which('ffmpeg'),[Path(__file__)])
            calls=[]
            def execute(command):
                calls.append(1);output.write_bytes(source.read_bytes().upper())
            command=['local-transform',str(output)]
            cache.run('test',command,[source],execute)
            cache.run('test',command,[source],execute)
            self.assertEqual(len(calls),1)
            source.write_bytes(b'second')
            cache.run('test',command,[source],execute)
            self.assertEqual(output.read_bytes(),b'SECOND')
            output.write_bytes(b'corrupted')
            cache.run('test',command,[source],execute)
            self.assertEqual(len(calls),3)
            self.assertEqual(output.read_bytes(),b'SECOND')

    def test_music_onsets_are_measured_not_a_fixed_grid(self):
        sibling=Path(__file__).resolve().parents[2]/'hypit/scripts'
        if not sibling.exists():self.skipTest('Optional hypit music helper unavailable')
        sys.path.insert(0,str(sibling))
        from music_beats import onset_candidates
        rate=10000;times=[.2,.7,1.3,1.9]
        samples=[]
        for i in range(rate*3):
            t=i/rate;age=min((t-p for p in times if p<=t),default=100)
            samples.append(int(25000*math.exp(-age*70)*math.sin(2*math.pi*1000*t)))
        peaks=onset_candidates(samples,rate)
        self.assertEqual(len(peaks),len(times))
        for observed,expected in zip(peaks,times):self.assertLess(abs(observed['time']-expected),.025)
        self.assertEqual(onset_candidates([0]*rate,rate),[])

    @unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg build identity unavailable')
    def test_local_transient_retry_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';output=root/'result';source.write_bytes(b'input')
            cache=StageCache(root/'cache',shutil.which('ffmpeg'),[Path(__file__)])
            calls=[]
            def fail(command):
                calls.append(1)
                raise RuntimeError('Resource temporarily unavailable')
            with self.assertRaises(RuntimeError):cache.run('transient',['tool',str(output)],[source],fail)
            self.assertEqual(len(calls),2)
            self.assertIn('Attempt 1', (root/'cache/transient.errors.txt').read_text())
            calls.clear()
            def invalid(command):
                calls.append(1)
                raise ValueError('Invalid media input')
            with self.assertRaises(ValueError):cache.run('invalid',['tool',str(output)],[source],invalid)
            self.assertEqual(len(calls),1)

    def test_optional_dependencies_are_declared(self):
        root=Path(__file__).resolve().parents[1]
        requirements=(root/'requirements-optional.txt').read_text(encoding='utf-8')
        self.assertIn('faster-whisper==1.2.1',requirements)
        self.assertTrue((root/'assets/remotion/package-lock.json').is_file())
        self.assertTrue((root/'references/runtime-dependencies.md').is_file())


if __name__=='__main__':unittest.main()
