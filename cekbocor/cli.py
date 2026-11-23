"""CLI CekBocor: cek kata sandi lewat HIBP tanpa mengirim kata sandi utuh."""

import argparse
import getpass
import json
import sys

from . import __version__
from .breach import CekBocorError as BreachError
from .breach import cek_email, ringkas_breach
from .panduan import PANDUAN
from .pwned import CekBocorError, cek_sandi, verdict
from . import riwayat


def _cmd_batch(args):
    try:
        with open(args.berkas, encoding="utf-8", errors="replace") as berkas:
            baris_list = berkas.read().splitlines()
    except OSError as exc:
        print(f"Tidak bisa membaca berkas {args.berkas}: "
              f"{exc.strerror or exc}", file=sys.stderr)
        return 1
    # Baris kosong dan baris komentar (# ...) dilewati.
    kata_sandi = [b for b in baris_list
                  if b.strip() and not b.strip().startswith("#")]
    if not kata_sandi:
        print("Berkas tidak berisi kata sandi (semua baris kosong "
              "atau komentar).")
        return 0
    print(f"{'No.':>3}  {'Status':<12}  Kemunculan")
    aman = bocor = 0
    for nomor, sandi in enumerate(kata_sandi, 1):
        try:
            jumlah = cek_sandi(sandi)
        except CekBocorError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        status, _saran = verdict(jumlah)
        if jumlah == 0:
            aman += 1
        else:
            bocor += 1
        print(f"{nomor:>3}  {status:<12}  {jumlah:,}")
    print(f"\nRingkasan: {len(kata_sandi)} dicek, {aman} aman, "
          f"{bocor} pernah bocor.")
    if bocor:
        print("Ada kata sandi yang pernah bocor — jalankan "
              "`cekbocor panduan` untuk langkah selanjutnya.")
    riwayat.catat(
        "batch",
        f"{args.berkas}: {len(kata_sandi)} dicek, {aman} aman, "
        f"{bocor} pernah bocor",
    )
    return 0 if bocor == 0 else 1


def _cmd_panduan(args):
    print(PANDUAN, end="")
    return 0


def _cmd_sandi(args):
    sandi = getpass.getpass("Kata sandi (ketikan tidak tampil): ")
    if not sandi:
        print("Kata sandi tidak boleh kosong.", file=sys.stderr)
        return 1
    try:
        jumlah = cek_sandi(sandi)
    except CekBocorError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    status, saran = verdict(jumlah)
    riwayat.catat("sandi", f"{status}, {jumlah:,} kemunculan")
    if args.json:
        print(json.dumps(
            {"status": status, "jumlah_kemunculan": jumlah, "saran": saran},
            ensure_ascii=False, indent=2,
        ))
        return 0 if jumlah == 0 else 1
    print(f"Status: {status}")
    if jumlah:
        print(f"Jumlah kemunculan di kebocoran data: {jumlah:,}")
    print(f"Saran: {saran}")
    return 0 if jumlah == 0 else 1


def _cmd_email(args):
    try:
        daftar = cek_email(args.email)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except BreachError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(daftar, ensure_ascii=False, indent=2))
    elif not daftar:
        print(f"{args.email} tidak ditemukan di breach yang diketahui HIBP.")
    else:
        print(f"{args.email} muncul di {len(daftar)} breach:")
        for breach in daftar:
            print(f"  - {ringkas_breach(breach)}")
        print("Ganti kata sandi di layanan itu (dan di mana pun kata sandi "
              "yang sama dipakai), lalu nyalakan verifikasi dua langkah.")
    riwayat.catat(
        "email",
        f"{args.email}: {len(daftar)} breach"
        + (f" ({', '.join(b.get('Name', '?') for b in daftar)})"
           if daftar else ""),
    )
    return 0 if not daftar else 1


def _cmd_riwayat(args):
    if args.hapus:
        if riwayat.hapus_riwayat():
            print("Riwayat cek lokal dihapus.")
        else:
            print("Tidak ada riwayat yang tersimpan.")
        return 0
    daftar = riwayat.muat_riwayat()
    if not daftar:
        print("Belum ada riwayat cek. Cek kata sandi, batch, atau email "
              "dulu — hasilnya tercatat otomatis di sini.")
        return 0
    print("Riwayat cek (lokal, kata sandi tidak pernah disimpan):")
    for entri in daftar[-20:]:
        print(f"  {entri['waktu'][:19].replace('T', ' ')}  "
              f"[{entri['jenis']}] {entri['ringkasan']}")
    if len(daftar) > 20:
        print(f"  ... dan {len(daftar) - 20} entri lebih lama.")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="cekbocor",
        description="Cek apakah kata sandimu pernah bocor (HIBP k-anonymity).",
    )
    parser.add_argument("--version", action="version",
                        version=f"CekBocor {__version__}")
    sub = parser.add_subparsers(dest="perintah", required=True)
    p_sandi = sub.add_parser("sandi", help="Cek satu kata sandi")
    p_sandi.add_argument("--json", action="store_true",
                         help="Keluaran JSON")
    p_sandi.set_defaults(func=_cmd_sandi)
    p_batch = sub.add_parser(
        "batch",
        help="Cek banyak kata sandi dari berkas (satu per baris)",
        description="Baca kata sandi dari berkas teks (satu kata sandi "
                    "per baris; baris kosong dan baris komentar # "
                    "dilewati) lalu cek tiap baris "
                    "lewat HIBP. Kata sandi tidak pernah ditampilkan kembali.",
    )
    p_batch.add_argument("berkas", help="Berkas teks berisi kata sandi")
    p_batch.set_defaults(func=_cmd_batch)
    p_panduan = sub.add_parser(
        "panduan",
        help="Langkah-langkah kalau kata sandimu sudah bocor",
        description="Tampilkan langkah-langkah setelah kata sandi "
                    "diketahui pernah bocor.",
    )
    p_panduan.set_defaults(func=_cmd_panduan)
    p_email = sub.add_parser(
        "email",
        help="Cek alamat email di breach yang diketahui HIBP",
        description="Cek alamat email terhadap Have I Been Pwned "
                    "(butuh API key HIBP di variabel lingkungan "
                    "HIBP_API_KEY; alamat email dikirim ke HIBP).",
    )
    p_email.add_argument("email", help="Alamat email yang dicek")
    p_email.add_argument("--json", action="store_true",
                         help="Keluaran JSON")
    p_email.set_defaults(func=_cmd_email)
    p_riwayat = sub.add_parser(
        "riwayat",
        help="Lihat riwayat cek lokal",
        description="Tampilkan riwayat cek yang tersimpan lokal "
                    "(kata sandi tidak pernah disimpan).",
    )
    p_riwayat.add_argument("--hapus", action="store_true",
                           help="Hapus seluruh riwayat lokal")
    p_riwayat.set_defaults(func=_cmd_riwayat)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
