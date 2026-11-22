"""Unit test CLI CekBocor end-to-end via subprocess (API HIBP asli).

Kata sandi yang dipakai di sini hanya contoh umum ("password") dan
string acak — bukan kata sandi asli siapa pun.
"""

import json
import secrets
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _acak():
    """Kata sandi acak yang praktis tidak mungkin pernah bocor."""
    return secrets.token_hex(16)


def _jalankan(*args, masukan=None):
    return subprocess.run(
        [sys.executable, "-m", "cekbocor", *args],
        cwd=REPO_ROOT,
        input=masukan,
        capture_output=True,
        text=True,
        timeout=60,
    )


class TestSandi(unittest.TestCase):
    def test_password_pernah_bocor(self):
        hasil = _jalankan("sandi", masukan="password\n")
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("PERNAH BOCOR", hasil.stdout)
        self.assertIn("52,373,976", hasil.stdout)
        self.assertIn("cekbocor panduan", hasil.stdout)

    def test_sandi_acak_aman(self):
        hasil = _jalankan("sandi", masukan=_acak() + "\n")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("AMAN", hasil.stdout)

    def test_sandi_json_bocor(self):
        hasil = _jalankan("sandi", "--json", masukan="password\n")
        self.assertEqual(hasil.returncode, 1)
        data = json.loads(hasil.stdout)
        self.assertEqual(data["status"], "PERNAH BOCOR")
        self.assertEqual(data["jumlah_kemunculan"], 52373976)
        self.assertIn("saran", data)

    def test_sandi_json_aman(self):
        hasil = _jalankan("sandi", "--json", masukan=_acak() + "\n")
        self.assertEqual(hasil.returncode, 0)
        data = json.loads(hasil.stdout)
        self.assertEqual(data["status"], "AMAN")
        self.assertEqual(data["jumlah_kemunculan"], 0)

    def test_sandi_kosong_ditolak(self):
        hasil = _jalankan("sandi", masukan="\n")
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("tidak boleh kosong", hasil.stderr)

    def test_sandi_bocor_tampil_jumlah(self):
        hasil = _jalankan("sandi", masukan="password\n")
        self.assertIn("Jumlah kemunculan di kebocoran data: 52,373,976", hasil.stdout)

    def test_tanpa_perintah_keluar_2(self):
        hasil = _jalankan()
        self.assertEqual(hasil.returncode, 2)

    def test_version(self):
        hasil = _jalankan("--version")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("CekBocor 0.1.0", hasil.stdout)


class TestBatch(unittest.TestCase):
    def _berkas_batch(self, isi):
        berkas = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        berkas.write(isi)
        berkas.close()
        return berkas.name

    def test_batch_campuran(self):
        acak1, acak2 = _acak(), _acak()
        jalur = self._berkas_batch(f"password\n{acak1}\n\n{acak2}\n")
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("PERNAH BOCOR", hasil.stdout)
        self.assertIn("52,373,976", hasil.stdout)
        self.assertIn("3 dicek, 2 aman, 1 pernah bocor", hasil.stdout)
        # Kata sandi tidak pernah ditampilkan kembali.
        self.assertNotIn(acak1, hasil.stdout)
        self.assertNotIn(acak2, hasil.stdout)

    def test_batch_semua_aman(self):
        jalur = self._berkas_batch(f"{_acak()}\n{_acak()}\n")
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("2 dicek, 2 aman, 0 pernah bocor", hasil.stdout)

    def test_batch_satu_baris_bocor(self):
        jalur = self._berkas_batch("password\n")
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("1 dicek, 0 aman, 1 pernah bocor", hasil.stdout)

    def test_batch_berkas_tak_ada(self):
        hasil = _jalankan("batch", "/tmp/cekbocor-tidak-ada-xyz.txt")
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("Tidak bisa membaca berkas", hasil.stderr)

    def test_batch_berkas_kosong(self):
        jalur = self._berkas_batch("\n\n")
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("tidak berisi kata sandi", hasil.stdout)


class TestPanduan(unittest.TestCase):
    def test_panduan_tampil(self):
        hasil = _jalankan("panduan")
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Sudah bocor, lalu apa?", hasil.stdout)
        self.assertIn("verifikasi dua langkah", hasil.stdout)
        self.assertIn("pengelola kata sandi", hasil.stdout)

    def test_panduan_lima_langkah(self):
        hasil = _jalankan("panduan")
        for nomor in ("1.", "2.", "3.", "4.", "5."):
            self.assertIn(nomor, hasil.stdout)


if __name__ == "__main__":
    unittest.main()
