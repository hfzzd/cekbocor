"""Unit test modul cekbocor.breach — tanpa jaringan (fetcher palsu).

Alamat email yang dipakai hanya contoh (bukan email asli siapa pun).
"""

import json
import os
import unittest
import urllib.error
from unittest import mock

from cekbocor.breach import (
    CekBocorError,
    KUNCI_TIDAK_ADA,
    _ambil_breach,
    cek_email,
    ringkas_breach,
)

CONTOH_BREACH = [
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


def _http_error(kode):
    return urllib.error.HTTPError(
        "https://haveibeenpwned.com/api/v3/breachedaccount/x@y.z",
        kode,
        "HTTP Error",
        {},
        None,
    )


class _ResponsPalsu:
    """Pengganti respons urlopen: context manager berisi byte JSON."""

    def __init__(self, data):
        self._data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._data


class TestCekEmail(unittest.TestCase):
    def test_ditemukan_di_beberapa_breach(self):
        daftar = cek_email(
            "contoh@email.com",
            kunci="KUNCI-PALSU",
            ambil=lambda email, kunci: CONTOH_BREACH,
        )
        self.assertEqual(len(daftar), 2)
        self.assertEqual(daftar[0]["Name"], "Adobe")
        self.assertEqual(daftar[1]["Name"], "LinkedIn")

    def test_tidak_ditemukan_aman(self):
        daftar = cek_email(
            "aman@email.com",
            kunci="KUNCI-PALSU",
            ambil=lambda email, kunci: [],
        )
        self.assertEqual(daftar, [])

    def test_fetcher_menerima_email_dan_kunci(self):
        diterima = {}

        def ambil_palsu(email, kunci):
            diterima["email"] = email
            diterima["kunci"] = kunci
            return []

        cek_email("siapa@contoh.id", kunci="KUNCI-ABC", ambil=ambil_palsu)
        self.assertEqual(diterima["email"], "siapa@contoh.id")
        self.assertEqual(diterima["kunci"], "KUNCI-ABC")

    def test_kunci_dibaca_dari_env(self):
        diterima = {}
        with mock.patch.dict(os.environ, {"HIBP_API_KEY": "KUNCI-DARI-ENV"}):
            cek_email(
                "a@b.id",
                ambil=lambda email, kunci: diterima.setdefault("kunci", kunci),
            )
        self.assertEqual(diterima["kunci"], "KUNCI-DARI-ENV")

    def test_tanpa_kunci_jadi_error_berisi_cara_dapat_key(self):
        def ambil_palsu(email, kunci):
            raise AssertionError("fetcher tidak boleh dipanggil")

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CekBocorError) as ctx:
                cek_email("a@b.id", ambil=ambil_palsu)
        pesan = str(ctx.exception)
        self.assertIn("HIBP_API_KEY", pesan)
        self.assertIn("haveibeenpwned.com/API/Key", pesan)
        self.assertEqual(str(ctx.exception), KUNCI_TIDAK_ADA)

    def test_email_tak_valid(self):
        for buruk in ("", "   ", "tanpa-at"):
            with self.subTest(email=buruk):
                with self.assertRaises(ValueError):
                    cek_email(buruk, kunci="KUNCI-PALSU", ambil=lambda e, k: [])

    def test_email_tak_valid_tanpa_kunci_tetap_value_error(self):
        # Validasi alamat jalan dulu, sebelum memeriksa kunci.
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                cek_email("bukan-email", ambil=lambda e, k: [])

    def test_email_dengan_spasi_dipangkas(self):
        diterima = {}
        cek_email(
            "  a@b.id  ",
            kunci="KUNCI-PALSU",
            ambil=lambda email, kunci: diterima.setdefault("email", email),
        )
        self.assertEqual(diterima["email"], "a@b.id")


class TestAmbilBreach(unittest.TestCase):
    def test_404_jadi_daftar_kosong(self):
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=_http_error(404),
        ):
            self.assertEqual(_ambil_breach("aman@email.com", "KUNCI-PALSU"), [])

    def test_respons_json_dikembalikan(self):
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            return_value=_ResponsPalsu(CONTOH_BREACH),
        ):
            self.assertEqual(
                _ambil_breach("contoh@email.com", "KUNCI-PALSU"),
                CONTOH_BREACH,
            )

    def test_401_jadi_cekbocor_error(self):
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=_http_error(401),
        ):
            with self.assertRaises(CekBocorError) as ctx:
                _ambil_breach("a@b.id", "KUNCI-SALAH")
        self.assertIn("401", str(ctx.exception))

    def test_429_jadi_cekbocor_error(self):
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=_http_error(429),
        ):
            with self.assertRaises(CekBocorError) as ctx:
                _ambil_breach("a@b.id", "KUNCI-PALSU")
        self.assertIn("429", str(ctx.exception))

    def test_http_lain_jadi_cekbocor_error(self):
        for kode in (403, 500, 503):
            with self.subTest(kode=kode):
                with mock.patch(
                    "cekbocor.breach.urllib.request.urlopen",
                    side_effect=_http_error(kode),
                ):
                    with self.assertRaises(CekBocorError) as ctx:
                        _ambil_breach("a@b.id", "KUNCI-PALSU")
                self.assertIn(str(kode), str(ctx.exception))

    def test_gagal_jaringan_jadi_cekbocor_error(self):
        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=urllib.error.URLError("tidak ada internet"),
        ):
            with self.assertRaises(CekBocorError) as ctx:
                _ambil_breach("a@b.id", "KUNCI-PALSU")
        self.assertIn("haveibeenpwned.com", str(ctx.exception))

    def test_header_api_key_dikirim(self):
        diterima = {}

        def urlopen_palsu(req, timeout=None):
            diterima["kunci"] = req.get_header("Hibp-api-key")
            diterima["agen"] = req.get_header("User-agent")
            return _ResponsPalsu([])

        with mock.patch(
            "cekbocor.breach.urllib.request.urlopen",
            side_effect=urlopen_palsu,
        ):
            _ambil_breach("a@b.id", "KUNCI-RAHASIA")
        self.assertEqual(diterima["kunci"], "KUNCI-RAHASIA")
        self.assertEqual(diterima["agen"], "CekBocor")


class TestRingkasBreach(unittest.TestCase):
    def test_format_lengkap(self):
        self.assertEqual(
            ringkas_breach(CONTOH_BREACH[0]),
            "Adobe (2013-10-04) — Email addresses, Password hints",
        )

    def test_tanpa_kelas_data(self):
        self.assertEqual(
            ringkas_breach({"Name": "X", "BreachDate": "2020-01-01"}),
            "X (2020-01-01) — -",
        )

    def test_tanpa_nama_dan_tanggal(self):
        self.assertEqual(ringkas_breach({}), "? (?) — -")


if __name__ == "__main__":
    unittest.main()
