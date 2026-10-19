"""Broker: menerima request client dan mendistribusikannya ke 3 worker.

Dua strategi alokasi (pilih dengan --strategy):
  balanced   : pemerataan, pilih worker dengan jumlah request terlayani paling sedikit
               (seri -> worker dengan id terkecil)
  roundrobin : berurutan sesuai server-id berdasar counter milik broker (1,2,3,1,2,3,...)

Protokol client -> broker (satu baris):
  REQ|<app_id>|<payload>      app_id: 1 = Long, 2 = Short
Balasan broker -> client: balasan worker diteruskan apa adanya, diawali info broker:
  OK|worker-<id>|<NamaApp>|<hasil>   atau   ERR|...
"""
import argparse
import socket
import threading

# id worker -> (host, port)
WORKERS = {
    1: ("127.0.0.1", 9001),
    2: ("127.0.0.1", 9002),
    3: ("127.0.0.1", 9003),
}

lock = threading.Lock()
served = {wid: 0 for wid in WORKERS}  # jumlah request yang sudah dialokasikan/dilayani
rr_counter = 0


def pick_worker(strategy: str) -> int:
    """Pilih id worker sesuai strategi. Harus dipanggil dalam lock."""
    global rr_counter
    ids = sorted(WORKERS)
    if strategy == "roundrobin":
        wid = ids[rr_counter % len(ids)]
        rr_counter += 1
    else:  # balanced
        wid = min(ids, key=lambda i: (served[i], i))
    served[wid] += 1
    return wid


def forward(wid: int, request: str) -> str:
    host, port = WORKERS[wid]
    try:
        with socket.create_connection((host, port), timeout=10) as s:
            f = s.makefile("rw", encoding="utf-8", newline="\n")
            f.write(request + "\n")
            f.flush()
            return f.readline().strip()
    except OSError as e:
        return f"ERR|worker-{wid}|tidak dapat dihubungi ({e})"


def handle_client(conn: socket.socket, addr, strategy: str) -> None:
    with conn:
        f = conn.makefile("rw", encoding="utf-8", newline="\n")
        request = f.readline().strip()
        print(f"[broker] Request dari {addr}: {request!r}")

        if not request.startswith("REQ|"):
            reply = "ERR|broker|format request tidak valid (gunakan REQ|<app_id>|<payload>)"
        else:
            with lock:
                wid = pick_worker(strategy)
                snapshot = dict(served)
            print(f"[broker] Strategi={strategy} -> dialokasikan ke worker-{wid} | total terlayani: {snapshot}")
            reply = forward(wid, request)
            print(f"[broker] Balasan dari worker-{wid}: {reply!r}")

        f.write(reply + "\n")
        f.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Broker load balancer sederhana")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument(
        "--strategy", choices=["balanced", "roundrobin"], default="balanced",
        help="balanced = pemerataan jumlah request; roundrobin = berurutan sesuai counter",
    )
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(20)
    print(f"[broker] Siap di {args.host}:{args.port} | strategi: {args.strategy}")
    print(f"[broker] Worker: {WORKERS}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client, args=(conn, addr, args.strategy), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[broker] Berhenti")
    finally:
        server.close()


if __name__ == "__main__":
    main()
