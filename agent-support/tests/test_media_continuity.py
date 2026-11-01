import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts/check-media-continuity.py'
spec = importlib.util.spec_from_file_location('continuity', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TimingTests(unittest.TestCase):
    def setUp(self):
        self.streams = [dict(index=0, codec_type='video', avg_frame_rate='30/1'),
                        dict(index=1, codec_type='audio', codec_name='aac', sample_rate='48000')]
        self.packets = {0: [(i/30, 1/30) for i in range(30)],
                        1: [(i*1024/48000, 1024/48000) for i in range(47)]}

    def test_normal_and_b_frame_storage_order(self):
        self.packets[0].reverse()
        result = m.check_timing(self.streams, self.packets)
        self.assertTrue(result['file_timing_pass'])
        self.assertFalse(result['playback_verified'])
        self.assertFalse(result['silence_checked'])

    def test_missing_audio_packet_fails(self):
        self.packets[1].pop(20)
        self.assertIn('audio_pts_gap', m.check_timing(self.streams, self.packets)['errors'])

    def test_video_half_second_gap_fails(self):
        self.packets[0] = self.packets[0][:3] + self.packets[0][20:]
        self.assertIn('video_pts_gap', m.check_timing(self.streams, self.packets)['errors'])

    def test_start_and_end_shift(self):
        self.packets[1] = [(t+.2, d) for t, d in self.packets[1]]
        self.assertEqual(['start_mismatch', 'end_mismatch'], m.check_timing(self.streams, self.packets)['errors'])

    def test_invalid_missing_and_non_aac_fail_closed(self):
        for packets in ({0: self.packets[0]}, {**self.packets, 1: [(float('nan'), .02)]*2}):
            with self.assertRaises(ValueError):
                m.check_timing(self.streams, packets)
        self.streams[1]['codec_name'] = 'opus'
        with self.assertRaises(ValueError):
            m.check_timing(self.streams, self.packets)
