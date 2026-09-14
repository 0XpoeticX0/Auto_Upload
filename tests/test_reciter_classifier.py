import sys, os
sys.path.insert(0, os.path.abspath('.'))
# -*- coding: utf-8 -*-
import unittest
from app.quran_verse.quran_data import (
    determine_best_reciter_for_passage,
    RECITERS_CONFIG,
    CURATED_COMPLETE_PASSAGES
)
from app.quran_verse.metadata import generate_quran_metadata

class TestReciterClassifier(unittest.TestCase):
    def test_reciter_config_integrity(self):
        self.assertIn('alafasy', RECITERS_CONFIG)
        self.assertIn('dossari', RECITERS_CONFIG)
        for r_id in ['alafasy', 'dossari']:
            info = RECITERS_CONFIG[r_id]
            self.assertEqual(info['id'], r_id)
            self.assertTrue(info['name_bn'])
            self.assertTrue(info['name_en'])
            self.assertTrue(info['folder'])

    def test_landmark_alafasy_passages(self):
        # Comfort, solace, repentance, heartfelt prayer
        self.assertEqual(determine_best_reciter_for_passage(94, 1, 8), 'alafasy')  # Ash-Sharh
        self.assertEqual(determine_best_reciter_for_passage(93, 1, 11), 'alafasy') # Ad-Duha
        self.assertEqual(determine_best_reciter_for_passage(21, 87, 88), 'alafasy') # Yunus Dua
        self.assertEqual(determine_best_reciter_for_passage(28, 24, 24), 'alafasy') # Musa Dua
        self.assertEqual(determine_best_reciter_for_passage(2, 285, 286), 'alafasy') # Amanar Rasul
        self.assertEqual(determine_best_reciter_for_passage(55, 1, 13), 'alafasy') # Ar-Rahman
        self.assertEqual(determine_best_reciter_for_passage(89, 27, 30), 'alafasy') # Al-Fajr

    def test_landmark_dossari_passages(self):
        # Divine majesty, sovereignty, Day of Judgment, firm Tawakkul
        self.assertEqual(determine_best_reciter_for_passage(2, 255, 255), 'dossari') # Ayatul Kursi
        self.assertEqual(determine_best_reciter_for_passage(65, 2, 3), 'dossari')     # At-Talaq
        self.assertEqual(determine_best_reciter_for_passage(3, 173, 174), 'dossari')  # Hasbunallah
        self.assertEqual(determine_best_reciter_for_passage(59, 22, 24), 'dossari')  # Al-Hashr
        self.assertEqual(determine_best_reciter_for_passage(101, 1, 11), 'dossari')  # Al-Qariah
        self.assertEqual(determine_best_reciter_for_passage(75, 1, 15), 'dossari')   # Al-Qiyamah
        self.assertEqual(determine_best_reciter_for_passage(67, 1, 5), 'dossari')    # Al-Mulk

    def test_safe_fallback_on_unmapped_surah(self):
        # Unmapped or out of bound values should always safely fall back to alafasy
        self.assertEqual(determine_best_reciter_for_passage(999, 1, 1), 'alafasy')
        self.assertEqual(determine_best_reciter_for_passage(0, 0, 0), 'alafasy')

    def test_metadata_attribution(self):
        mock_verse_data = {
            'surah_name_bn': 'সূরা আশ-শারহ',
            'verse_range_str': '১-৮',
            'theme_headline': 'কঠিন সময়ে পরম প্রশান্তি',
            'reflection_bn': 'ধৈর্য ধারণ করুন।',
            'verses': [{'ayah_number': 1, 'arabic': 'أَلَمْ نَشْرَحْ لَكَ صَدْرَكَ', 'bengali': 'আমি কি আপনার বক্ষ উন্মুক্ত করে দেইনি?'}]
        }
        mock_audio_data = {
            'reciter': RECITERS_CONFIG['alafasy']
        }
        meta = generate_quran_metadata(mock_verse_data, mock_audio_data)
        self.assertIn('EveryAyah.com', meta['description'])
        self.assertIn('Quran.com API', meta['description'])
        self.assertIn(RECITERS_CONFIG['alafasy']['name_bn'], meta['description'])

if __name__ == '__main__':
    unittest.main()
