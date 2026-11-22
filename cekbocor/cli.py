"""CLI CekBocor: cek kata sandi lewat HIBP tanpa mengirim kata sandi utuh."""

import argparse
import getpass
import json
import sys

from . import __version__
from .pwned import CekBocorError, cek_sandi, verdict


def _cmd_batch(args):
    try:
        with open(args.berkas, encoding="utf-8", errors="replace") as berkas:
            baris_list = berkas.read().splitlines()
    except OSError as exc:
        print(f"Tidak bisa membaca berkas {args.berkas}: "
              f"{exc.strerror or exc}", file=sys.stderr)
        return 1
    kata_sandi = [b for b in baris_list if b.strip()]
    if not kata_sandi:
        print("Berkas tidak berisi kata sandi (semua baris kosong).")
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
    return 0 if bocor == 0 else 1


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
                    "per baris; baris kosong dilewati) lalu cek tiap baris "
                    "lewat HIBP. Kata sandi tidak pernah ditampilkan kembali.",
    )
    p_batch.add_argument("berkas", help="Berkas teks berisi kata sandi")
    p_batch.set_defaults(func=_cmd_batch)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
