from . import helper
import socket
import threading

version = 1.0

class peer():
    def __init__(self,
                 port: int = 63924,
                 peer_list: list[tuple[str,int]] = [],
                 peer_file: str | None = None,
        ):
        self.port: int = port
        self.peers: list[tuple[str,int]] = peer_list

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

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(5)
        threading.Thread(target=self._listenloop, daemon=True).start()

    def _listenloop(self):
        while True:
            connection,address = self.sock.accept()
            connection.send(f"pp2pn\\s\\{version}".encode())

    def update(self):
        for i in self.peers:
            if i[2] == 's':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((i[0],i[1]))
                buffer: bytes = sock.recv(1024)
                if buffer.decode() != f"pp2pn\\s\\{version}":
                    sock.send(b"error\\61\\version mismatch with node")
                    sock.close()
                    continue
                sock.send(f"pp2pn\\c\\{version}".encode())
                buffer = sock.recv(1024)
                if buffer.decode() == "ok":
                    sock.send(str(self.port).encode())
                    sock.send(b"get\\peers")

                    peers = helper.decode_peers(sock.recv(1024))
                    self.peers += peers
                elif buffer.decode().startswith("error"):
                    print("error")
                    print(buffer.decode())
        self.peers = list(dict.fromkeys(self.peers))
