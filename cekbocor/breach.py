"""Cek alamat email terhadap Have I Been Pwned (BreachedAccount API v3).

Berbeda dengan cek kata sandi: endpoint ini MEMBUTUHKAN API key HIBP
(berbayar, dibeli sendiri di haveibeenpwned.com/API/Key) dan alamat
emailnya MEMANG dikirim ke HIBP — tidak ada cara k-anonymity untuk
email. Jadi perintah `email` hanya jalan kalau variabel lingkungan
HIBP_API_KEY sudah diisi; kalau belum, pengguna diberi tahu dengan
jelas cara mendapatkannya, bukan error misterius.
"""

import json
import os
import urllib.error
import urllib.request
import urllib.parse

API_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"
USER_AGENT = "CekBocor"

KUNCI_TIDAK_ADA = (
    "Cek email butuh API key Have I Been Pwned (HIBP_API_KEY belum diisi).\n"
    "API key ini berbayar dan dibeli sendiri di "
    "https://haveibeenpwned.com/API/Key — kami tidak pernah membeli atau "
    "meminta API key siapa pun.\n"
    "Setelah punya key, jalankan: HIBP_API_KEY=<key-mu> cekbocor email "
    "alamat@email.com\n"
    "Catatan privasi: alamat emailmu dikirim ke HIBP untuk dicek, berbeda "
    "dengan cek kata sandi yang tidak pernah mengirim kata sandi utuh."
)


class CekBocorError(Exception):
    """Gagal menghubungi layanan pemeriksaan (mis. tidak ada internet)."""


def _ambil_breach(email, kunci, timeout=15):
    """Ambil daftar breach untuk satu email dari HIBP (atau [] bila aman)."""
    url = API_URL.format(urllib.parse.quote(email))
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "hibp-api-key": kunci,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        if exc.code == 401:
            raise CekBocorError(
                "API key HIBP ditolak (401). Periksa lagi HIBP_API_KEY-mu."
            ) from exc
        if exc.code == 429:
            raise CekBocorError(
                "HIBP membatasi permintaan (429). Tunggu sebentar lalu "
                "coba lagi."
            ) from exc
        raise CekBocorError(
            f"HIBP menjawab HTTP {exc.code}. Coba lagi nanti."
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise CekBocorError(
            "Tidak bisa menghubungi haveibeenpwned.com. "
            "Periksa koneksi internetmu lalu coba lagi."
        ) from exc


def cek_email(email, kunci=None, ambil=None):
    """Daftar breach tempat email ini muncul (list dict HIBP; [] = aman).

    `kunci` dibaca dari argumen atau variabel lingkungan HIBP_API_KEY.
    Parameter `ambil` hanya untuk test: fungsi yang menerima (email,
    kunci) dan mengembalikan daftar breach.
    """
    email = (email or "").strip()
    if not email or "@" not in email:
        raise ValueError("Alamat email tidak valid.")
    kunci = kunci or os.environ.get("HIBP_API_KEY")
    if not kunci:
        raise CekBocorError(KUNCI_TIDAK_ADA)
    ambil = ambil or _ambil_breach
    return ambil(email, kunci)


def ringkas_breach(breach):
    """Satu baris ringkas per breach: nama, tanggal, kelas data bocor."""
    tanggal = breach.get("BreachDate", "?")
    kelas = ", ".join(breach.get("DataClasses", [])) or "-"
    return f"{breach.get('Name', '?')} ({tanggal}) — {kelas}"
