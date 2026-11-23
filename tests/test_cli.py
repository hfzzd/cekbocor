"""Unit test CLI CekBocor end-to-end via subprocess (API HIBP asli).

Kata sandi yang dipakai di sini hanya contoh umum ("password") dan
string acak — bukan kata sandi asli siapa pun.
"""

import contextlib
import io
import json
import os
import secrets
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from cekbocor.breach import CekBocorError
from cekbocor.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def _acak():
    """Kata sandi acak yang praktis tidak mungkin pernah bocor."""
    return secrets.token_hex(16)


def _jalankan(*args, masukan=None, env=None):
    """Jalankan CLI via subprocess. `env`: override (nilai None = hapus)."""
    lingkungan = dict(os.environ)
    for kunci, nilai in (env or {}).items():
        if nilai is None:
            lingkungan.pop(kunci, None)
        else:
            lingkungan[kunci] = nilai
    return subprocess.run(
        [sys.executable, "-m", "cekbocor", *args],
        cwd=REPO_ROOT,
        input=masukan,
        capture_output=True,
        text=True,
        timeout=60,
        env=lingkungan,
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


CONTOH_BREACH_CLI = [
    {
        "Name": "Adobe",
        "BreachDate": "2013-10-04",
        "DataClasses": ["Email addresses", "Password hints"],
    },
    {
        "Name": "LinkedIn",
        "BreachDate": "2012-05-05",
        "DataClasses": ["Email addresses", "Passwords"],
    },
]


def _http_error_cli(kode):
    return urllib.error.HTTPError(
        "https://haveibeenpwned.com/api/v3/breachedaccount/a@b.id",
        kode,
        "HTTP Error",
        {},
        None,
    )


class TestEmailCLI(unittest.TestCase):
    """Perintah `email` end-to-end; HIBP live TIDAK dipakai (mock).

    haveibeenpwned.com tidak terjangkau dari VM ini, jadi jalur live
    `email` hanya teruji via mock di sini; live test menunggu laptop
    Hafizd + API key HIBP valid.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_env = {"CEKBOCOR_DATA": self._tmp.name}

    def _main(self, argv, env_extra=None):
        """Panggil main() in-process dengan stdout/stderr ditangkap."""
        keluar, galat = io.StringIO(), io.StringIO()
        env = dict(self.data_env)
        env.update(env_extra or {})
        with mock.patch.dict(os.environ, env, clear=False), \
                contextlib.redirect_stdout(keluar), \
                contextlib.redirect_stderr(galat):
            kode = main(argv)
        return kode, keluar.getvalue(), galat.getvalue()

    def test_email_tanpa_kunci_exit_1_pesan_cara_dapat_key(self):
        hasil = _jalankan(
            "email", "contoh@email.com",
            env={"HIBP_API_KEY": None, **self.data_env},
        )
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("HIBP_API_KEY", hasil.stderr)
        self.assertIn("haveibeenpwned.com/API/Key", hasil.stderr)

    def test_email_tak_valid_exit_1(self):
        hasil = _jalankan(
            "email", "bukan-email",
            env={"HIBP_API_KEY": None, **self.data_env},
        )
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("tidak valid", hasil.stderr)

    def test_email_ditemukan_di_breach(self):
        with mock.patch(
            "cekbocor.cli.cek_email", return_value=CONTOH_BREACH_CLI
        ):
            kode, keluar, _galat = self._main(
                ["email", "contoh@email.com"],
                {"HIBP_API_KEY": "KUNCI-PALSU"},
            )
        self.assertEqual(kode, 1)
        self.assertIn("muncul di 2 breach", keluar)
        self.assertIn("Adobe (2013-10-04)", keluar)
        self.assertIn("LinkedIn (2012-05-05)", keluar)
        self.assertIn("verifikasi dua langkah", keluar)

    def test_email_aman_exit_0(self):
        with mock.patch("cekbocor.cli.cek_email", return_value=[]):
            kode, keluar, _galat = self._main(
                ["email", "aman@email.com"],
                {"HIBP_API_KEY": "KUNCI-PALSU"},
            )
        self.assertEqual(kode, 0)
        self.assertIn("tidak ditemukan di breach", keluar)

    def test_email_json(self):
        with mock.patch(
            "cekbocor.cli.cek_email", return_value=CONTOH_BREACH_CLI
        ):
            kode, keluar, _galat = self._main(
                ["email", "--json", "contoh@email.com"],
                {"HIBP_API_KEY": "KUNCI-PALSU"},
            )
        self.assertEqual(kode, 1)
        data = json.loads(keluar)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["Name"], "Adobe")

    def test_email_gagal_jaringan_exit_1(self):
        with mock.patch(
            "cekbocor.cli.cek_email",
            side_effect=CekBocorError("Tidak bisa menghubungi"),
        ):
            kode, _keluar, galat = self._main(
                ["email", "a@b.id"], {"HIBP_API_KEY": "KUNCI-PALSU"}
            )
        self.assertEqual(kode, 1)
        self.assertIn("Tidak bisa menghubungi", galat)

    def test_email_http_error_sungguhan_401(self):
        # HTTPError asli dari urllib, lewat jalur _ambil_breach yang
        # sebenarnya (hanya urlopen yang dipalsukan) — tanpa jaringan.
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=_http_error_cli(401),
        ):
            kode, _keluar, galat = self._main(
                ["email", "a@b.id"], {"HIBP_API_KEY": "KUNCI-SALAH"}
            )
        self.assertEqual(kode, 1)
        self.assertIn("401", galat)

    def test_email_mencatat_riwayat_tanpa_kata_sandi(self):
        with mock.patch(
            "cekbocor.cli.cek_email", return_value=CONTOH_BREACH_CLI
        ):
            self._main(
                ["email", "contoh@email.com"],
                {"HIBP_API_KEY": "KUNCI-PALSU"},
            )
        isi = (Path(self._tmp.name) / "riwayat.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("contoh@email.com: 2 breach", isi)
        self.assertIn("Adobe", isi)


class TestRiwayatCLI(unittest.TestCase):
    """Perintah `riwayat` end-to-end via subprocess (riwayat terisolasi)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_env = {"CEKBOCOR_DATA": self._tmp.name}
        self.jalur = Path(self._tmp.name) / "riwayat.json"

    def _seed(self, entri):
        self.jalur.write_text(
            json.dumps(entri, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_riwayat_kosong(self):
        hasil = _jalankan("riwayat", env=self.data_env)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Belum ada riwayat", hasil.stdout)

    def test_riwayat_terisi(self):
        self._seed([
            {"waktu": "2026-11-23T01:00:00+00:00", "jenis": "sandi",
             "ringkasan": "AMAN, 0 kemunculan"},
            {"waktu": "2026-11-23T02:00:00+00:00", "jenis": "email",
             "ringkasan": "a@b.id: 2 breach (Adobe, LinkedIn)"},
        ])
        hasil = _jalankan("riwayat", env=self.data_env)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("AMAN, 0 kemunculan", hasil.stdout)
        self.assertIn("a@b.id: 2 breach", hasil.stdout)
        self.assertIn("[sandi]", hasil.stdout)
        self.assertIn("[email]", hasil.stdout)

    def test_riwayat_hapus(self):
        self._seed([
            {"waktu": "2026-11-23T01:00:00+00:00", "jenis": "sandi",
             "ringkasan": "AMAN, 0 kemunculan"},
        ])
        hasil = _jalankan("riwayat", "--hapus", env=self.data_env)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("dihapus", hasil.stdout)
        self.assertFalse(self.jalur.exists())
        hasil = _jalankan("riwayat", env=self.data_env)
        self.assertIn("Belum ada riwayat", hasil.stdout)

    def test_riwayat_hapus_tanpa_riwayat(self):
        hasil = _jalankan("riwayat", "--hapus", env=self.data_env)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("Tidak ada riwayat", hasil.stdout)

    def test_riwayat_terisi_otomatis_dari_sandi(self):
        acak = _acak()
        hasil = _jalankan("sandi", masukan=acak + "\n", env=self.data_env)
        self.assertEqual(hasil.returncode, 0)
        hasil = _jalankan("riwayat", env=self.data_env)
        self.assertIn("[sandi]", hasil.stdout)
        self.assertIn("AMAN, 0 kemunculan", hasil.stdout)
        # Kata sandi tidak pernah tersimpan di riwayat.
        self.assertNotIn(acak, self.jalur.read_text(encoding="utf-8"))


class TestBatchKomentar(unittest.TestCase):
    """`batch` melewati baris komentar # end-to-end (live API sandi)."""

    def _berkas_batch(self, isi):
        berkas = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        berkas.write(isi)
        berkas.close()
        return berkas.name

    def test_batch_lewati_komentar(self):
        acak = _acak()
        jalur = self._berkas_batch(
            f"# berkas contoh\npassword\n# komentar di tengah\n{acak}\n"
        )
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 1)
        self.assertIn("2 dicek, 1 aman, 1 pernah bocor", hasil.stdout)
        self.assertNotIn("# berkas contoh", hasil.stdout)

    def test_batch_hanya_komentar(self):
        jalur = self._berkas_batch("# semua baris komentar\n# baris kedua\n")
        hasil = _jalankan("batch", jalur)
        self.assertEqual(hasil.returncode, 0)
        self.assertIn("tidak berisi kata sandi", hasil.stdout)


if __name__ == "__main__":
    unittest.main()
