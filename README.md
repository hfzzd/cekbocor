# CekBocor

Cek apakah kata sandimu pernah bocor di kebocoran data — dari terminal, berbahasa Indonesia, tanpa mengirim kata sandi utuh ke mana pun. Sekarang juga bisa cek alamat email dan melihat riwayat cekmu sendiri.

## Cara kerja (privasi dulu)

CekBocor memakai [Have I Been Pwned — Pwned Passwords](https://haveibeenpwned.com/Passwords) dengan teknik **k-anonymity**:

1. Kata sandimu di-hash SHA-1 **di komputermu sendiri**.
2. Hanya **5 karakter pertama** hash itu yang dikirim ke `api.pwnedpasswords.com`.
3. Server mengembalikan daftar ratusan hash yang cocok dengan 5 karakter itu — kata sandimu **tidak pernah** terkirim utuh, dan tidak bisa ditebak dari 5 karakter itu.
4. Pencocokan dilakukan lokal: kalau hash lengkapmu ada di daftar, berarti kata sandi itu pernah muncul di kebocoran data.

Tidak ada akun dan tidak ada pelacakan. Butuh internet — pemeriksaan kata sandi ke `api.pwnedpasswords.com`, pemeriksaan email ke `haveibeenpwned.com`.

**Perbedaan penting antara cek kata sandi dan cek email:** kata sandi tidak pernah keluar dari komputermu (hanya 5 karakter hash), tapi alamat email **memang dikirim ke HIBP** untuk dicek — tidak ada cara k-anonymity untuk email. Jadi perintah `email` hanya dipakai kalau kamu memang mau alamat emailmu dicek ke HIBP, dan perintah itu butuh API key HIBP berbayar (lihat di bawah).

**Riwayat cek** tersimpan lokal di komputermu (`~/.config/cekbocor/riwayat.json`, bisa dipindah lewat variabel lingkungan `CEKBOCOR_DATA` — lihat bagian riwayat). Yang dicatat hanya hasil ceknya; kata sandi **tidak pernah disimpan**, dalam bentuk apa pun.

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

Berkas batch berisi satu kata sandi contoh per baris (baris kosong dan baris komentar `#` dilewati). Kata sandi **tidak pernah ditampilkan kembali** di keluaran — hanya status dan jumlah kemunculan. Berkas contoh di `contoh/contoh-batch.txt` berisi 3 kata sandi contoh; jangan taruh kata sandi aslimu di berkas contoh.

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

### Contoh: cek alamat email

Perintah `email` memakai BreachedAccount API v3 HIBP dan **butuh API key HIBP** (berbayar, dibeli sendiri di <https://haveibeenpwned.com/API/Key>). Isi key lewat variabel lingkungan `HIBP_API_KEY`. Tanpa key, CekBocor menjelaskan cara mendapatkannya — bukan error misterius:

```bash
$ cekbocor email saya@email.com
Cek email butuh API key Have I Been Pwned (HIBP_API_KEY belum diisi).
API key ini berbayar dan dibeli sendiri di https://haveibeenpwned.com/API/Key — kami tidak pernah membeli atau meminta API key siapa pun.
Setelah punya key, jalankan: HIBP_API_KEY=<key-mu> cekbocor email alamat@email.com
Catatan privasi: alamat emailmu dikirim ke HIBP untuk dicek, berbeda dengan cek kata sandi yang tidak pernah mengirim kata sandi utuh.
```

Alamat yang tidak valid ditolak dengan ramah:

```bash
$ cekbocor email bukan-email
Alamat email tidak valid.
```

Dengan key yang salah, HIBP menolaknya (401) dan CekBocor meneruskan pesannya:

```bash
$ HIBP_API_KEY=kunci-contoh cekbocor email saya@email.com
API key HIBP ditolak (401). Periksa lagi HIBP_API_KEY-mu.
```

Dengan key valid, perintahnya:

```bash
HIBP_API_KEY=<key-mu> cekbocor email saya@email.com
```

Kalau email ditemukan, CekBocor menampilkan jumlah breach dan satu baris per breach — nama breach, tanggal breach, dan kelas data yang bocor — lalu mengingatkan untuk mengganti kata sandi di layanan itu dan menyalakan verifikasi dua langkah. Kalau tidak ditemukan, tampil `saya@email.com tidak ditemukan di breach yang diketahui HIBP.` Dengan `--json`, keluarannya daftar breach mentah dari HIBP (JSON).

> **Catatan jujur:** perintah `email` belum pernah diuji langsung dengan API key valid — key-nya berbayar dan tidak dibeli di sini. Yang teruji: jalur permintaannya jalan (dengan kunci contoh, HIBP menjawab 401 "kunci ditolak" — jadi servernya terjangkau dan penolakan key-nya ditangani dengan benar), dan semua perilaku `email` lainnya teruji lewat unit test. Uji langsung dengan API key valid menunggu laptop Hafizd + API key-nya sendiri.

### Contoh: riwayat cek lokal

Setiap cek `sandi`, `batch`, dan `email` otomatis tercatat di riwayat lokal. Yang dicatat hanya hasil ceknya — kata sandi tidak pernah disimpan. Contoh setelah satu cek `sandi` (`password`, PERNAH BOCOR) dan satu `batch` contoh:

```bash
$ cekbocor riwayat
Riwayat cek (lokal, kata sandi tidak pernah disimpan):
  2026-11-23 06:15:10  [sandi] PERNAH BOCOR, 52,373,976 kemunculan
  2026-11-23 06:15:21  [batch] contoh/contoh-batch.txt: 3 dicek, 2 aman, 1 pernah bocor
```

(Waktu di atas dalam UTC; contoh ini dari verifikasi di mesin pengembangan.)

Riwayat tersimpan di `~/.config/cekbocor/riwayat.json`. Untuk test atau pemindahan, atur variabel lingkungan `CEKBOCOR_DATA` ke direktori lain — berkasnya tetap bernama `riwayat.json` di direktori itu. Hapus seluruh riwayat kapan saja:

```bash
$ cekbocor riwayat --hapus
Riwayat cek lokal dihapus.

$ cekbocor riwayat
Belum ada riwayat cek. Cek kata sandi, batch, atau email dulu — hasilnya tercatat otomatis di sini.
```

## Perintah

| Perintah | Fungsi |
| --- | --- |
| `sandi` | Cek satu kata sandi lewat HIBP (ketikan tersembunyi) |
| `sandi --json` | Sama, keluaran JSON |
| `batch BERKAS` | Cek banyak kata sandi dari berkas (satu per baris; baris kosong dan `#` dilewati) |
| `email ALAMAT` | Cek alamat email di breach HIBP (butuh `HIBP_API_KEY`) |
| `email ALAMAT --json` | Sama, keluaran JSON (daftar breach mentah) |
| `riwayat` | Lihat riwayat cek lokal (kata sandi tidak pernah disimpan) |
| `riwayat --hapus` | Hapus seluruh riwayat lokal |
| `panduan` | Langkah-langkah kalau kata sandimu sudah bocor |
| `--version` | Tampilkan versi CekBocor (0.2.0) |

Kode keluar: `0` kalau aman, `1` kalau ada yang pernah bocor atau ada kesalahan input/jaringan.

## Rencana

- [x] Day-1: cek kata sandi (HIBP k-anonymity) + CLI dasar (`sandi`, `batch`, `panduan`) + 30 unit test
- [x] Day-2: cek email (butuh API key HIBP, berbayar) + riwayat cek lokal + perbaikan batch lewati baris komentar `#`

## Menjalankan test

```bash
python3 -m unittest discover -s tests
```

76 test (15 `test_pwned.py` + 30 `test_cli.py` + 18 `test_breach.py` + 13 `test_riwayat.py`), semua lolos. Test memakai fetcher palsu / `urlopen` yang dipalsukan (tanpa jaringan) untuk jalur HIBP; test CLI end-to-end via subprocess memakai API HIBP asli dengan kata sandi contoh saja, plus `email` dengan kunci contoh (HIBP menjawab 401).

## Lisensi

MIT — © 2026 Hafizd Ammar
