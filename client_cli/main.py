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


def _parse_args(argv=None):
    """Parse CLI arguments for connection settings and quick commands."""
    import argparse
    parser = argparse.ArgumentParser(
        description='NRO CLI Client - Thuc thi nhanh 1 hoac nhieu lenh',
        epilog='''
VD: py main.py -u 1 -p 1 -c "/map" -c "/xmap 19"
    py main.py --login 1 1 -c "/items" -c "/info" --show-log
    py main.py -c "/autonappa kuku" -c "/autoboss list"
        '''
    )
    # Connection
    parser.add_argument('--host', default='127.0.0.1', help='Server host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=14445, help='Server port (default: 14445)')
    parser.add_argument('-u', '--username', default='1', help='Tai khoan (default: 1)')
    parser.add_argument('-p', '--password', default='1', help='Mat khau (default: 1)')
    parser.add_argument('--login', nargs=2, metavar=('USER', 'PASS'),
                        help='Dang nhap nhanh: --login 1 1')
    # Commands
    parser.add_argument('-c', '--cmd', action='append', default=[],
                        help='Lenh can thuc thi (co the dung nhieu -c). VD: -c "/info" -c "/map"')
    parser.add_argument('--show-log', '--log', action='store_true',
                        help='Hien thi log ra console (mac dinh an log de dep)')
    # Auto-exit after commands
    parser.add_argument('--exit', '--quit', action='store_true', dest='auto_exit',
                        help='Tu dong thoat sau khi thuc thi cac lenh --cmd')

    if argv is None:
        args, unknown = parser.parse_known_args()
    else:
        args, unknown = parser.parse_known_args(argv)

    # Override username/password if --login is used
    if args.login:
        args.username = args.login[0]
        args.password = args.login[1]

    # Try to interpret unknown args as commands
    # e.g. --map --xmap 19 -> treated as commands
    if unknown:
        # Convert unknown flags to commands: --map -> /map, --xmap 19 -> /xmap 19
        i = 0
        while i < len(unknown):
            token = unknown[i]
            if token.startswith('--'):
                cmd_name = token[2:]  # remove --
                # Check if next token could be a value (not starting with --)
                if i + 1 < len(unknown) and not unknown[i + 1].startswith('--'):
                    args.cmd.append(f"/{cmd_name} {unknown[i + 1]}")
                    i += 2
                else:
                    args.cmd.append(f"/{cmd_name}")
                    i += 1
            elif token.startswith('-'):
                cmd_name = token[1:]
                args.cmd.append(f"/{cmd_name}")
                i += 1
            else:
                # Bare word, treat as chat or simple command
                args.cmd.append(token)
                i += 1

    return args


def main():
    args = _parse_args()

    log.auto_config()
    if not args.show_log:
        log._log_enabled = False
    atexit.register(_cleanup)

    client = GameClient(args.host, args.port)
    threading.Thread(target=client.session.connect, daemon=True).start()
    ConsoleUI(
        client,
        initial_commands=args.cmd,
        auto_exit=args.auto_exit,
        username=args.username,
        password=args.password,
    ).run()


if __name__ == '__main__':
    main()
