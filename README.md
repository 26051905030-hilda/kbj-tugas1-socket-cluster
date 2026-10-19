# Tugas 1 - Socket untuk Cluster Computing

Mata kuliah Komputasi Berbasis Jaringan (Unesa). Simulasi sederhana *load balancing* dengan
socket Python: satu **broker** menerima request **client** lalu meneruskannya ke salah satu
dari 3 **worker**.

```
client  --->  broker (:9000)  --->  worker-1 (:9001)
                              --->  worker-2 (:9002)
                              --->  worker-3 (:9003)
```

## Struktur

| File | Fungsi |
|---|---|
| `worker.py` | Server pekerja. Melayani 2 aplikasi: `1 = Long` (komputasi kompleks, disimulasikan dengan `sleep` + Fibonacci) dan `2 = Short` (echo). |
| `broker.py` | Server utama. Memilih worker dengan 2 strategi alokasi. |
| `client.py` | Mengirim request ke broker dengan menyebutkan Application ID. |

## Protokol / format pesan

Teks satu baris, dipisah `|`, diakhiri newline.

- Request (client -> broker -> worker): `REQ|<app_id>|<payload>`
  - `app_id`: `1` (Long) atau `2` (Short)
  - `payload`: untuk Long berupa angka n (hitung fib(n)); untuk Short berupa teks bebas
- Balasan sukses: `OK|worker-<id>|<NamaApp>|<hasil>`
- Balasan gagal: `ERR|<sumber>|<alasan>`

## Strategi alokasi (opsi `--strategy` pada broker)

1. `balanced` (default) - **pemerataan**: broker memilih worker dengan jumlah request terlayani
   paling sedikit (jika seri, id terkecil). Jumlah dihitung saat request dialokasikan agar tetap
   merata walau request datang bersamaan.
2. `roundrobin` - **berurutan** sesuai server-id berdasarkan counter milik broker: 1, 2, 3, 1, 2, 3, ...

## Cara menjalankan

Butuh Python 3 (tanpa library tambahan). Buka 5 terminal:

```bash
python worker.py --id 1 --port 9001
python worker.py --id 2 --port 9002
python worker.py --id 3 --port 9003
python broker.py --strategy balanced      # atau: --strategy roundrobin
python client.py --app 2 --msg "halo" --count 6   # app Short, 6 request
python client.py --app 1 --msg 25                 # app Long, fib(25)
```

Broker dan worker mencetak log ke layar (request masuk, worker terpilih, jumlah terlayani, balasan).

## Contoh output broker (balanced)

```
[broker] Request dari ('127.0.0.1', 51000): 'REQ|2|halo'
[broker] Strategi=balanced -> dialokasikan ke worker-1 | total terlayani: {1: 1, 2: 0, 3: 0}
[broker] Balasan dari worker-1: 'OK|worker-1|Short|echo: halo'
```
