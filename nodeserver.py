import socket,os,io
import re
import pp2pn.helper

global version
version = 1.0

global ip_regex
ip_regex = "^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

class nodeServer():
    def __init__(self,
                 port: int = 63925,
                 peer_sharing: bool = True,
                 peer_list: list[tuple[str,int]] = [],
                 peer_file: str | None = None
    ):
        self.port: int = port
        self.peers: list[tuple[str,int]] = peer_list

        if peer_file != None:
            try:
                peer_file = open(peer_file,'r').read().splitlines()
            except:
                print("Error trying to open peer_file")
            else:
                for idx,i in enumerate(peer_file):
                    line_split = i.split(" ")
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

    def start():
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', port))
        self.sock.listen(5)

    def _listenloop(self):
        while True:
            connection,address = self.sock.accept()
            connection.send(f"pp2pn\\s\\{version}")
            buffer = connection.recv(1024)
            if buffer.decode() != "pp2pn\\c\\{version}":
                connection.close()
            else:
                self._handle_connection(connection)

    def _handle_connection(connection):
        while True:
            buffer = connection.recv(1024)
            parts = buffer.decode.split("\\")
            cmd = parts[0]
            match cmd:
                case "close":
                    connection.close()
                    break
                case "get":
                    if parts[1] == "peers":
                        connection.send()
