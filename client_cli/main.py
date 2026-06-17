import os
import sys
import shutil
import atexit
import threading
from logger import log
from client import GameClient
from ui import ConsoleUI


def _cleanup():
    for root, dirs, _ in os.walk(sys.path[0]):
        for d in dirs:
            if d == '__pycache__':
                path = os.path.join(root, d)
                try:
                    shutil.rmtree(path)
                except Exception:
                    pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='NRO CLI Client')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=14445)
    parser.add_argument('--username', default='1')
    parser.add_argument('--password', default='1')
    args = parser.parse_args()

    log.auto_config()
    log._log_enabled = False
    atexit.register(_cleanup)

    client = GameClient(args.host, args.port)
    threading.Thread(target=client.session.connect, daemon=True).start()
    ConsoleUI(client).run()


if __name__ == '__main__':
    main()
