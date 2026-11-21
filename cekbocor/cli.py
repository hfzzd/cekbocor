"""CLI CekBocor: cek kata sandi lewat HIBP tanpa mengirim kata sandi utuh."""

import argparse
import getpass
import json
import sys

from . import __version__
from .pwned import CekBocorError, cek_sandi, verdict


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
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
