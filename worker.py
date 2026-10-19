"""Worker server untuk simulasi cluster computing.

Setiap worker melayani 2 jenis aplikasi (disimulasikan):
  Application ID 1 -> Long  : perhitungan kompleks (disimulasikan: sleep + hitung Fibonacci)
  Application ID 2 -> Short : echo / perhitungan sederhana

Protokol (teks, satu baris diakhiri newline):
  Request  : REQ|<app_id>|<payload>
  Response : OK|worker-<id>|<NamaApp>|<hasil>
             ERR|worker-<id>|<alasan>
"""
import argparse
import socket
import threading
import time

APPS = {"1": "Long", "2": "Short"}
LONG_DELAY = 2  # detik, simulasi komputasi berat


def run_long(payload: str) -> str:
    time.sleep(LONG_DELAY)
    n = int(payload) if payload.isdigit() else 30
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return f"fib({n}) = {a}"


def run_short(payload: str) -> str:
    return f"echo: {payload}"


def handle_client(conn: socket.socket, addr, worker_id: int) -> None:
    name = f"worker-{worker_id}"
    with conn:
        f = conn.makefile("rw", encoding="utf-8", newline="\n")
        line = f.readline().strip()
        print(f"[{name}] Terima dari {addr}: {line!r}")

        parts = line.split("|", 2)
        if len(parts) != 3 or parts[0] != "REQ":
            reply = f"ERR|{name}|format request tidak valid"
        elif parts[1] not in APPS:
            reply = f"ERR|{name}|application id '{parts[1]}' tidak dikenal"
        else:
            app_id, payload = parts[1], parts[2]
            app_name = APPS[app_id]
            print(f"[{name}] Menjalankan aplikasi {app_name} (id={app_id})")
            result = run_long(payload) if app_id == "1" else run_short(payload)
            reply = f"OK|{name}|{app_name}|{result}"

        f.write(reply + "\n")
        f.flush()
        print(f"[{name}] Kirim balasan: {reply!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker server")
    parser.add_argument("--id", type=int, required=True, help="ID worker (1..3)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(5)
    print(f"[worker-{args.id}] Siap di {args.host}:{args.port}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client, args=(conn, addr, args.id), daemon=True
            ).start()
    except KeyboardInterrupt:
        print(f"\n[worker-{args.id}] Berhenti")
    finally:
        server.close()


if __name__ == "__main__":
    main()
