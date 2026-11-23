"""Riwayat cek lokal CekBocor.

Semua riwayat hanya tersimpan di komputer pengguna
(~/.config/cekbocor/riwayat.json, bisa dipindah lewat variabel
lingkungan CEKBOCOR_DATA untuk test). Yang dicatat HANYA hasil
ceknya — kata sandi TIDAK PERNAH disimpan, dalam bentuk apa pun.
Alamat email disimpan karena itu milik pengguna sendiri dan perlu
ditampilkan di riwayat; hapus dengan `cekbocor riwayat --hapus`.
"""

import json
import os
from datetime import datetime, timezone

NAMA_BERKAS = "riwayat.json"


def _jalur_riwayat():
    dasar = os.environ.get("CEKBOCOR_DATA")
    if dasar:
        return os.path.join(dasar, NAMA_BERKAS)
    return os.path.join(
        os.path.expanduser("~"), ".config", "cekbocor", NAMA_BERKAS
    )


def muat_riwayat():
    """Daftar entri riwayat (list dict); [] bila belum ada / berkas rusak."""
    try:
        with open(_jalur_riwayat(), encoding="utf-8") as berkas:
            data = json.load(berkas)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def catat(jenis, ringkasan, waktu=None):
    """Tambah satu entri riwayat. `ringkasan` teks bebas tanpa rahasia."""
    jalur = _jalur_riwayat()
    entri = {
        "waktu": waktu or datetime.now(timezone.utc).isoformat(),
        "jenis": jenis,
        "ringkasan": ringkasan,
    }
    daftar = muat_riwayat()
    daftar.append(entri)
    os.makedirs(os.path.dirname(jalur), exist_ok=True)
    with open(jalur, "w", encoding="utf-8") as berkas:
        json.dump(daftar, berkas, ensure_ascii=False, indent=2)
    return entri


def hapus_riwayat():
    """Hapus seluruh riwayat lokal. True bila ada berkas yang dihapus."""
    try:
        os.remove(_jalur_riwayat())
        return True
    except OSError:
        return False
