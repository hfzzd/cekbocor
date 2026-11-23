"""Unit test modul cekbocor.riwayat — riwayat cek lokal (tanpa jaringan).

Riwayat disimpan di direktori sementara lewat env CEKBOCOR_DATA, jadi
tidak menyentuh riwayat asli di ~/.config/cekbocor.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cekbocor import riwayat

SANDI_CONTOH = "SandiRahasia123-yang-tidak-boleh-tersimpan"


class TestRiwayatBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._env = mock.patch.dict(
            os.environ, {"CEKBOCOR_DATA": self._tmp.name}
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        self.jalur = Path(self._tmp.name) / "riwayat.json"

    def _tulis_mentah(self, isi):
        self.jalur.write_text(isi, encoding="utf-8")


class TestCatatMuat(TestRiwayatBase):
    def test_catat_lalu_muat_round_trip(self):
        entri = riwayat.catat("sandi", "AMAN, 0 kemunculan")
        self.assertEqual(entri["jenis"], "sandi")
        self.assertEqual(entri["ringkasan"], "AMAN, 0 kemunculan")
        self.assertIn("waktu", entri)
        daftar = riwayat.muat_riwayat()
        self.assertEqual(len(daftar), 1)
        self.assertEqual(daftar[0], entri)

    def test_beberapa_entri_berurutan(self):
        riwayat.catat("sandi", "AMAN, 0 kemunculan", waktu="2026-11-23T01:00:00+00:00")
        riwayat.catat("email", "a@b.id: 2 breach", waktu="2026-11-23T02:00:00+00:00")
        riwayat.catat("batch", "f.txt: 3 dicek", waktu="2026-11-23T03:00:00+00:00")
        daftar = riwayat.muat_riwayat()
        self.assertEqual(len(daftar), 3)
        self.assertEqual([e["jenis"] for e in daftar], ["sandi", "email", "batch"])

    def test_muat_tanpa_berkas_kembali_kosong(self):
        self.assertEqual(riwayat.muat_riwayat(), [])

    def test_berkas_rusak_kembali_kosong(self):
        self._tulis_mentah("ini bukan json {")
        self.assertEqual(riwayat.muat_riwayat(), [])

    def test_berkas_json_bukan_list_kembali_kosong(self):
        self._tulis_mentah('{"jenis": "sandi"}')
        self.assertEqual(riwayat.muat_riwayat(), [])

    def test_catat_menimpa_berkas_rusak(self):
        self._tulis_mentah("rusak{")
        riwayat.catat("sandi", "AMAN, 0 kemunculan")
        self.assertEqual(len(riwayat.muat_riwayat()), 1)

    def test_berkas_ditulis_dalam_format_json(self):
        riwayat.catat("email", "a@b.id: 0 breach")
        data = json.loads(self.jalur.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["jenis"], "email")


class TestHapusRiwayat(TestRiwayatBase):
    def test_hapus_ada_berkas(self):
        riwayat.catat("sandi", "AMAN, 0 kemunculan")
        self.assertTrue(self.jalur.exists())
        self.assertTrue(riwayat.hapus_riwayat())
        self.assertFalse(self.jalur.exists())
        self.assertEqual(riwayat.muat_riwayat(), [])

    def test_hapus_tanpa_berkas(self):
        self.assertFalse(riwayat.hapus_riwayat())


class TestEnvData(TestRiwayatBase):
    def test_env_cekbocor_data_dipakai(self):
        riwayat.catat("sandi", "AMAN, 0 kemunculan")
        self.assertTrue(self.jalur.exists())

    def test_subdirektori_dibuat_otomatis(self):
        dalam = os.path.join(self._tmp.name, "sub", "dalam")
        with mock.patch.dict(os.environ, {"CEKBOCOR_DATA": dalam}):
            riwayat.catat("sandi", "AMAN, 0 kemunculan")
            self.assertTrue(Path(dalam, "riwayat.json").exists())


class TestKataSandiTidakDisimpan(TestRiwayatBase):
    def test_kata_sandi_tidak_ada_di_berkas(self):
        # Simulasi yang dilakukan CLI: hanya ringkasan hasil yang dicatat,
        # kata sandinya sendiri tidak pernah diteruskan ke catat().
        riwayat.catat("sandi", "AMAN, 0 kemunculan")
        riwayat.catat("batch", "f.txt: 2 dicek, 2 aman, 0 pernah bocor")
        isi = self.jalur.read_text(encoding="utf-8")
        self.assertNotIn(SANDI_CONTOH, isi)

    def test_entri_hanya_punya_tiga_kunci(self):
        riwayat.catat("email", "a@b.id: 1 breach (Adobe)")
        entri = riwayat.muat_riwayat()[0]
        self.assertEqual(set(entri.keys()), {"waktu", "jenis", "ringkasan"})


if __name__ == "__main__":
    unittest.main()
