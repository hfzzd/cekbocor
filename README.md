# CekBocor

Cek apakah kata sandimu pernah bocor di kebocoran data — dari terminal, berbahasa Indonesia, tanpa mengirim kata sandi utuh ke mana pun.

## Cara kerja (privasi dulu)

CekBocor memakai [Have I Been Pwned — Pwned Passwords](https://haveibeenpwned.com/Passwords) dengan teknik **k-anonymity**:

1. Kata sandimu di-hash SHA-1 **di komputermu sendiri**.
2. Hanya **5 karakter pertama** hash itu yang dikirim ke `api.pwnedpasswords.com`.
3. Server mengembalikan daftar ratusan hash yang cocok dengan 5 karakter itu — kata sandimu **tidak pernah** terkirim utuh, dan tidak bisa ditebak dari 5 karakter itu.
4. Pencocokan dilakukan lokal: kalau hash lengkapmu ada di daftar, berarti kata sandi itu pernah muncul di kebocoran data.

Tidak ada akun, tidak ada data yang disimpan, tidak ada pelacakan.

## Cara pakai

```bash
pip install .
cekbocor sandi
```

Perintah `sandi` akan meminta kata sandi (ketikan tidak tampil di layar), lalu menampilkan:

- **AMAN** — kata sandi tidak ditemukan di database kebocoran yang diketahui.
- **PERNAH BOCOR** — kata sandi ditemukan sekian kali di kebocoran data; ganti segera, terutama kalau dipakai di banyak layanan.

```bash
cekbocor sandi --json   # keluaran JSON untuk dipakai skrip lain
cekbocor --version      # tampilkan versi
```

Butuh internet — pemeriksaan dilakukan ke `api.pwnedpasswords.com`.

## Perintah

| Perintah | Fungsi |
| --- | --- |
| `sandi` | Cek satu kata sandi lewat HIBP (ketikan tersembunyi) |
| `sandi --json` | Sama, keluaran JSON |
| `--version` | Tampilkan versi CekBocor |

## Rencana

- [x] Day-1: cek kata sandi (HIBP k-anonymity) + CLI dasar
- [ ] Day-2: cek email (butuh API key HIBP, opsional) + panduan "sudah bocor, lalu apa?" + mode batch

## Menjalankan test

```bash
python3 -m unittest discover -s tests
```

## Lisensi

MIT — © 2026 Hafizd Ammar
