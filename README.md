# CekBocor

Cek apakah kata sandimu pernah bocor di kebocoran data — dari terminal, berbahasa Indonesia, tanpa mengirim kata sandi utuh ke mana pun.

## Cara kerja (privasi dulu)

CekBocor memakai [Have I Been Pwned — Pwned Passwords](https://haveibeenpwned.com/Passwords) dengan teknik **k-anonymity**:

1. Kata sandimu di-hash SHA-1 **di komputermu sendiri**.
2. Hanya **5 karakter pertama** hash itu yang dikirim ke `api.pwnedpasswords.com`.
3. Server mengembalikan daftar ratusan hash yang cocok dengan 5 karakter itu — kata sandimu **tidak pernah** terkirim utuh, dan tidak bisa ditebak dari 5 karakter itu.
4. Pencocokan dilakukan lokal: kalau hash lengkapmu ada di daftar, berarti kata sandi itu pernah muncul di kebocoran data.

Tidak ada akun, tidak ada data yang disimpan, tidak ada pelacakan. Butuh internet — pemeriksaan dilakukan ke `api.pwnedpasswords.com`.

## Cara pakai

```bash
pip install .
cekbocor sandi
```

Perintah `sandi` meminta kata sandi (ketikan tidak tampil di layar), lalu menampilkan:

- **AMAN** — kata sandi tidak ditemukan di database kebocoran yang diketahui.
- **PERNAH BOCOR** — kata sandi ditemukan sekian kali di kebocoran data; ganti segera, terutama kalau dipakai di banyak layanan.

### Contoh: satu kata sandi

```bash
$ cekbocor sandi
Kata sandi (ketikan tidak tampil):
Status: PERNAH BOCOR
Jumlah kemunculan di kebocoran data: 52,373,976
Saran: Pernah muncul 52,373,976 kali di kebocoran data. Ganti segera
dengan kata sandi baru yang unik, dan nyalakan verifikasi dua langkah
di layanan pentingmu. Jalankan `cekbocor panduan` untuk
langkah-langkah selanjutnya.
```

Itu hasil untuk kata sandi contoh `password` — kata sandi paling umum yang bocor, muncul 52.373.976 kali. Kata sandi acak yang kuat hasilnya lain:

```bash
$ cekbocor sandi
Kata sandi (ketikan tidak tampil):
Status: AMAN
Saran: Tidak ditemukan di database kebocoran yang diketahui. Tetap
pakai kata sandi yang berbeda untuk tiap layanan, ya.
```

Keluaran JSON untuk dipakai skrip lain:

```bash
$ cekbocor sandi --json
{
  "status": "PERNAH BOCOR",
  "jumlah_kemunculan": 52373976,
  "saran": "Pernah muncul 52,373,976 kali di kebocoran data. ..."
}
```

### Contoh: cek banyak kata sandi sekaligus

```bash
$ cekbocor batch contoh/contoh-batch.txt
No.  Status        Kemunculan
  1  PERNAH BOCOR  52,373,976
  2  AMAN          0
  3  AMAN          0

Ringkasan: 3 dicek, 2 aman, 1 pernah bocor.
Ada kata sandi yang pernah bocor — jalankan `cekbocor panduan` untuk langkah selanjutnya.
```

Berkas batch berisi satu kata sandi contoh per baris (baris kosong dilewati). Kata sandi **tidak pernah ditampilkan kembali** di keluaran — hanya status dan jumlah kemunculan. Berkas contoh di `contoh/contoh-batch.txt` berisi 3 kata sandi contoh; jangan taruh kata sandi aslimu di berkas contoh.

### Contoh: sudah bocor, lalu apa?

```bash
$ cekbocor panduan
Sudah bocor, lalu apa?

Kata sandimu pernah muncul di kebocoran data. Jangan panik — ikuti
langkah-langkah ini:

1. Ganti kata sandi yang bocor, segera.
   Mulai dari layanan yang paling penting: email, perbankan,
   dompet digital, dan media sosial.
2. Jangan pakai ulang kata sandi yang sama di layanan lain.
   Satu layanan, satu kata sandi — supaya satu kebocoran tidak
   membuka semua akunmu.
3. Nyalakan verifikasi dua langkah (2FA) di layanan pentingmu.
   Pakai aplikasi autentikator kalau tersedia.
4. Cek layanan penting dulu.
   Periksa email, bank, dan dompet digital: ada aktivitas
   atau percobaan login yang aneh?
5. Pakai pengelola kata sandi (password manager).
   Supaya tiap layanan punya kata sandi yang kuat dan berbeda,
   tanpa harus dihafal semuanya.

Intinya: ganti yang bocor, jangan dipakai ulang, dan kunci akun
pentingmu dengan verifikasi dua langkah.
```

## Perintah

| Perintah | Fungsi |
| --- | --- |
| `sandi` | Cek satu kata sandi lewat HIBP (ketikan tersembunyi) |
| `sandi --json` | Sama, keluaran JSON |
| `batch BERKAS` | Cek banyak kata sandi dari berkas (satu per baris) |
| `panduan` | Langkah-langkah kalau kata sandimu sudah bocor |
| `--version` | Tampilkan versi CekBocor (0.1.0) |

Kode keluar: `0` kalau aman, `1` kalau ada yang pernah bocor atau ada kesalahan input/jaringan.

## Rencana

- [x] Day-1: cek kata sandi (HIBP k-anonymity) + CLI dasar (`sandi`, `batch`, `panduan`) + 30 unit test
- [ ] Day-2: cek email (butuh API key HIBP, opsional) + riwayat cek lokal

## Menjalankan test

```bash
python3 -m unittest discover -s tests
```

30 test (15 `test_pwned.py` + 15 `test_cli.py`), semua lolos. Test `pwned` memakai fetcher palsu (tanpa jaringan); test CLI end-to-end via subprocess memakai API HIBP asli dengan kata sandi contoh saja.

## Lisensi

MIT — © 2026 Hafizd Ammar
