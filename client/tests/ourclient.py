import socket
from threading import Thread
import base64
import time

class ServerInfo:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def __str__(self) -> str:
        return f"{self.ip}:{self.port}"

    def __repr__(self) -> str:
        return f"{self.ip}:{self.port}"
    
class Client:
    def __init__(self, servers: list[ServerInfo]):
        self.servers = servers
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((servers[0].ip, servers[0].port))
        print("Connected")

    def send_request(self, type: str, data: str):
        try:
            self.socket.sendall(f"{type}{data}".encode("utf-8"))
        except Exception as e:
            print(f"Could not send {type}{data} request to load balancer:\n {e}")
            self.socket.close()
            # Retry next socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.servers[1].ip, self.servers[1].port))
            self.socket.sendall(f"{type}{data}".encode("utf-8"))
        
        if type == 'push':
            response = self.socket.recv(4)
            if response != b'ack':
                print("Non ack response:", response)
                self.socket.close()
                # Retry next socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.servers[1].ip, self.servers[1].port))
                self.socket.sendall(f"{type}{data}".encode("utf-8"))
                response = self.socket.recv(4)
            assert response == b'ack'
        else:
            response = self.socket.recv(2048)
            response = response.decode("utf-8").strip()
            return response
        

    def push(self, key: str, val: bytes):
        self.send_request("push", f":{key}:{base64.b64encode(val).decode()}")

    
    def pull(self) -> tuple[str, bytes]:
        response = self.send_request("pull", "")
        if response == '':
            return None, None
        response_parts = response.split(":")
        return response_parts[0], base64.b64decode(response_parts[1])
    
    def __do_subscribe(self, f):
        for server in self.servers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((server.ip, server.port))
                    while True:
                        s.sendall(b"pull")
                        response = s.recv(2048).decode().strip()
                        if response != '':
                            response_parts = response.split(":")
                            f(response_parts[0], base64.b64decode(response_parts[1]))
                        ''' 
                           No else case is needed because this happens nearly always in out infinite loop.
                           Cases which there is an error with server are logged inside the send_request method. 
                        '''
            except Exception as ex:
                print(f"Sub exception: {ex}")
                time.sleep(5)
                print(f"Sub trying next server")
            
        print("Sub finished")

    def subscribe(self, f):
        thread = Thread(target=self.__do_subscribe, args=(f,))
        thread.daemon = True
        thread.start()
