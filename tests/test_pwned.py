"""Unit test modul cekbocor.pwned — tanpa jaringan (fetcher palsu)."""

import unittest
import urllib.error
from unittest import mock

from cekbocor.pwned import CekBocorError, _ambil_awalan, cek_sandi, sha1_hex, verdict


def _respons_untuk(sandi, jumlah, baris_lain=()):
    """Buat isi respons HIBP palsu untuk satu kata sandi + baris lain."""
    kode = sha1_hex(sandi)
    akhiran = kode[5:]
    baris = [f"{akhiran}:{jumlah}"]
    baris.extend(baris_lain)
    return "\n".join(baris) + "\n"


class TestSha1Hex(unittest.TestCase):
    def test_password_nilai_dikenal(self):
        self.assertEqual(
            sha1_hex("password"),
            "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8",
        )

    def test_string_kosong(self):
        self.assertEqual(
            sha1_hex(""),
            "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709",
        )

    def test_hasil_huruf_besar(self):
        kode = sha1_hex("SandiKuat123")
        self.assertEqual(kode, kode.upper())
        self.assertEqual(len(kode), 40)


class TestCekSandi(unittest.TestCase):
    def test_ditemukan_banyak_kali(self):
        respons = _respons_untuk("password", 52373976)
        self.assertEqual(cek_sandi("password", ambil=lambda awalan: respons), 52373976)

    def test_ditemukan_satu_kali(self):
        respons = _respons_untuk("qwerty123", 1)
        self.assertEqual(cek_sandi("qwerty123", ambil=lambda awalan: respons), 1)

    def test_tidak_ditemukan(self):
        respons = _respons_untuk(
            "sandi-lain-yang-acak",
            42,
            baris_lain=["AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:7"],
        )
        self.assertEqual(cek_sandi("sandi-yang-aman-xyz", ambil=lambda awalan: respons), 0)

    def test_respons_kosong(self):
        self.assertEqual(cek_sandi("apa-saja", ambil=lambda awalan: ""), 0)

    def test_hanya_awalan_lima_karakter_yang_dikirim(self):
        diterima = []

        def ambil_palsu(awalan):
            diterima.append(awalan)
            return _respons_untuk("password", 3)

        cek_sandi("password", ambil=ambil_palsu)
        self.assertEqual(diterima, ["5BAA6"])

    def test_baris_rusak_dilewati(self):
        # Baris tanpa titik dua / tiga bagian / akhiran salah: diabaikan.
        kode = sha1_hex("password")
        respons = "\n".join([
            "BARISTANPATITIKDUA",
            "AAA:1:2",
            f"  {kode[5:]}  :  99  ",
            "BBBBB:5",
        ])
        self.assertEqual(cek_sandi("password", ambil=lambda awalan: respons), 99)

    def test_sandi_kosong_ditolak(self):
        with self.assertRaises(ValueError):
            cek_sandi("")

    def test_fetcher_tidak_dipanggil_untuk_sandi_kosong(self):
        def ambil_palsu(awalan):
            raise AssertionError("fetcher tidak boleh dipanggil")

        with self.assertRaises(ValueError):
            cek_sandi("", ambil=ambil_palsu)


class TestVerdict(unittest.TestCase):
    def test_nol_aman(self):
        status, saran = verdict(0)
        self.assertEqual(status, "AMAN")
        self.assertIn("Tidak ditemukan", saran)

    def test_satu_kali(self):
        status, saran = verdict(1)
        self.assertEqual(status, "PERNAH BOCOR")
        self.assertIn("1 kali", saran)
        self.assertIn("cekbocor panduan", saran)

    def test_banyak_kali_format_angka(self):
        status, saran = verdict(52373976)
        self.assertEqual(status, "PERNAH BOCOR")
        self.assertIn("52,373,976", saran)
        self.assertIn("cekbocor panduan", saran)


class TestAmbilAwalan(unittest.TestCase):
    def test_gagal_jaringan_jadi_cekbocor_error(self):
        with mock.patch(
            "cekbocor.pwned.urllib.request.urlopen",
            side_effect=urllib.error.URLError("tidak ada internet"),
        ):
            with self.assertRaises(CekBocorError) as ctx:
                _ambil_awalan("5BAA6")
        self.assertIn("api.pwnedpasswords.com", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
