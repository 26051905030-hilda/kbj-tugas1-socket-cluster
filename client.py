"""Client: mengirim request ke broker dengan menyebutkan Application ID.

Contoh:
  python client.py --app 2 --msg "halo"            # 1 request ke app Short
  python client.py --app 1 --msg 25                # 1 request ke app Long (fib(25))
  python client.py --app 2 --msg tes --count 6     # kirim 6 request berurutan
"""
import argparse
import socket


def send_request(host: str, port: int, app_id: str, payload: str) -> str:
    request = f"REQ|{app_id}|{payload}"
    with socket.create_connection((host, port), timeout=15) as s:
        f = s.makefile("rw", encoding="utf-8", newline="\n")
        f.write(request + "\n")
        f.flush()
        return f.readline().strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Client broker-worker")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--app", required=True, help="Application ID: 1 = Long, 2 = Short")
    parser.add_argument("--msg", default="hello", help="Isi pesan / parameter")
    parser.add_argument("--count", type=int, default=1, help="Jumlah request yang dikirim")
    args = parser.parse_args()

    for i in range(1, args.count + 1):
        print(f"[client] #{i} Kirim: REQ|{args.app}|{args.msg}")
        reply = send_request(args.host, args.port, args.app, args.msg)
        print(f"[client] #{i} Terima: {reply}")


if __name__ == "__main__":
    main()
