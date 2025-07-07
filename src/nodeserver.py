import socket,os,io
import re
import threading
import time
from . import helper

version = 1.0
ip_regex = "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

class nodeServer():
    def __init__(self,
                 port: int = 63925,
                 peer_sharing: bool = True,
                 peer_list: list[tuple[str,int]] = [],
                 peer_file: str | None = None,
                 check_delay: int = 300
    ):
        self.check_delay: int = check_delay
        self.port: int = port
        self.peers: list[tuple[str,int]] = peer_list

        self.stats: dict = {
            "uptime": 0,
            "visits": 0,
            "peers": 0,
            "check_delay": check_delay,
            "port": port
        }

        if peer_file != None:
            self.load_peers(peer_file)

    def save_peers(self, path: str):
        open(path,'w').write(f"{i[0]} {i[1]} {i[2]}" for i in self.peers)

    def load_peers(self, path: str):
        try:
            peer_file: list[str] = open(path,'r').read().splitlines()
        except:
            print("Error trying to open peer file")
        else:
            for idx,i in enumerate(peer_file):
                line_split: list[str] = i.split(" ")
                if len(line_split) == 0:
                    continue
                elif len(line_split) == 1 and re.fullmatch(ip_regex,line_split[0]):
                    self.peers.append((line_split[0],63924,'c'))
                elif len(line_split) == 2 and re.fullmatch(ip_regex,line_split[0]) \
                and int(line_split[1]) > 0 and int(line_split[1]) < 65535:
                    self.peers.append((line_split[0],line_split[1],'c'))
                elif len(line_split) == 3 and re.fullmatch(ip_regex,line_split[0]) \
                and int(line_split[1]) > 0 and int(line_split[1]) < 65535 and \
                line_split[2].lower() in ("s","c","server","client"):
                    if line_split[2] in ("c","client"):
                        self.peers.append((line_split[0],line_split[1],'c'))
                    else:
                        self.peers.append((line_split[0],line_split[1],'s'))
                else:
                    print(f"Invalid peer definition at line {idx+1}")
        self.stats["peers"] = len(self.peers)

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(5)
        threading.Thread(target=self._listenloop, daemon=True).start()
    
    def _peer_check(self):
        if self.check_delay == -1:
            return

        while True:
            time.sleep(self.check_delay)
            to_remove = []
            for peer in self.peers:
                if peer[2] == "c":
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    try:
                        sock.connect((peer[0], peer[1]))
                    except Exception:
                        to_remove.append(peer)
                    finally:
                        sock.close()

            for peer in to_remove:
                self.peers.remove(peer)

    def _listenloop(self):
        while True:
            connection,address = self.sock.accept()
            connection.send(f"pp2pn\\s\\{version}".encode())
            buffer: bytes = connection.recv(1024)
            if buffer.decode() != f"pp2pn\\c\\{version}":
                connection.close()
            else:
                threading.Thread(target=self._handle_connection, args=(connection,), daemon=True).start()

    def _handle_connection(self, connection):
        while True:
            buffer: bytes = connection.recv(1024)
            if not buffer:
                break

            try:
                parts: list[str] = buffer.decode().split("\\")
            except UnicodeDecodeError:
                connection.send(b"error\\10\\invalid message format")
                continue

            if not parts:
                connection.send(b"error\\10\\invalid message format")
                continue

            cmd: str = parts[0]
            match cmd:
                case "close":
                    connection.close()
                    break
                case "get":
                    if len(parts) < 2:
                        connection.send(b"error\\14\\missing target field")
                    elif parts[1] == "peers":
                        try:
                            connection.send(helper.encode_peers(self.peers))
                        except:
                            connection.send(b"error\\21\\internal node error")
                    elif parts[1] == "stats":
                        try:
                            connection.send(helper.encode_dict(self.stats))
                        except:
                            connection.send(b"error\\21\\internal node error")
                    else:
                        connection.send(b"error\\15\\target not found")
                case "add":
                    match parts[2]:
                        case "peers":
                            try:
                                encoded = buffer.split(b"add\\peers\\", 1)[1]
                                new_peers = helper.decode_peers(encoded)
                                self.peers += new_peers
                                connection.send(b"ok\\peers\\added")
                            except Exception as e:
                                connection.send(b"error\\16\\invalid peer data")
                        case "stats":
                            connection.send(b"error\\53\\access denied")
                case _:
                    connection.send(b"error\\12\\unknown request type")
