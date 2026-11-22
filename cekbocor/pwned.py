"""Cek kata sandi terhadap Have I Been Pwned (Pwned Passwords, k-anonymity).

Privasi: kata sandi di-hash SHA-1 secara lokal, dan hanya 5 karakter
pertama hash yang dikirim ke api.pwnedpasswords.com. Server mengembalikan
semua akhiran hash yang cocok dengan awalan itu; pencocokan akhir
dilakukan di sini, sehingga kata sandi utuh tidak pernah keluar
dari komputer pengguna.
"""

import hashlib
import urllib.error
import urllib.request

API_URL = "https://api.pwnedpasswords.com/range/{}"
USER_AGENT = "CekBocor"


class CekBocorError(Exception):
    """Gagal menghubungi layanan pemeriksaan (mis. tidak ada internet)."""


def sha1_hex(sandi):
    """SHA-1 kata sandi, huruf besar (format HIBP)."""
    return hashlib.sha1(sandi.encode("utf-8")).hexdigest().upper()


def _ambil_awalan(awalan, timeout=15):
    """Ambil daftar akhiran hash untuk 5 karakter awalan dari HIBP."""
    req = urllib.request.Request(
        API_URL.format(awalan),
        headers={"User-Agent": USER_AGENT, "Add-Padding": "true"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CekBocorError(
            "Tidak bisa menghubungi api.pwnedpasswords.com. "
            "Periksa koneksi internetmu lalu coba lagi."
        ) from exc


def cek_sandi(sandi, ambil=None):
    """Berapa kali kata sandi muncul di database kebocoran HIBP.

    Mengembalikan jumlah kemunculan (0 = tidak pernah bocor).
    Parameter `ambil` hanya untuk test: fungsi yang menerima awalan
    5 karakter dan mengembalikan isi respons HIBP.
    """
    if not sandi:
        raise ValueError("Kata sandi tidak boleh kosong.")
    ambil = ambil or _ambil_awalan
    kode = sha1_hex(sandi)
    awalan, akhiran = kode[:5], kode[5:]
    for baris in ambil(awalan).splitlines():
        bagian = baris.split(":")
        if len(bagian) == 2 and bagian[0].strip() == akhiran:
            return int(bagian[1].strip())
    return 0


def verdict(jumlah):
    """Status + saran ramah berdasarkan jumlah kemunculan."""
    if jumlah == 0:
        return (
            "AMAN",
            "Tidak ditemukan di database kebocoran yang diketahui. "
            "Tetap pakai kata sandi yang berbeda untuk tiap layanan, ya.",
        )
    if jumlah == 1:
        return (
            "PERNAH BOCOR",
            "Pernah muncul 1 kali di kebocoran data. Segera ganti, "
            "terutama kalau kata sandi ini dipakai di layanan lain juga. "
            "Jalankan `cekbocor panduan` untuk langkah-langkah selanjutnya.",
        )
    return (
        "PERNAH BOCOR",
        f"Pernah muncul {jumlah:,} kali di kebocoran data. Ganti segera "
        "dengan kata sandi baru yang unik, dan nyalakan verifikasi dua "
        "langkah di layanan pentingmu. "
        "Jalankan `cekbocor panduan` untuk langkah-langkah selanjutnya.",
    )
