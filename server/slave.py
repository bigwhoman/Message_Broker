import socket
import os

LOAD_BALANCER_HOST = os.getenv("LOAD_BALANCER_HOST", "localhost")
LOAD_BALANCER_PORT = os.getenv("LOAD_BALANCER_PORT", "12345")

class QueueManager:
    def __init__(self):
        self.queue: list[tuple[str, str]] = []
    
    def push(self, key: str, value: str):
        self.queue.append((key, value))

    def pull(self) -> tuple[str, str]:
        return self.queue.pop(0)

class BalancerConnectionHandler:

    def __init__(self, queue: QueueManager):
        self.queue = queue
    
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LOAD_BALANCER_HOST, int(LOAD_BALANCER_PORT)))
            while True:
                packet = s.recv(2048)
                if not packet:
                    print(f"connection {s.getpeername()} closed")
                    break
                packet = packet.decode("utf-8").strip()
                if packet.startswith("push"):
                    (_, key, value) = packet.split(":")
                    print(f"pushing {key}:{value}")
                    self.queue.push(key, value)
                    s.sendall(b"ok")
                elif packet.startswith("pull"):
                    (key, value) = self.queue.pull()
                    print(f"pulled {key}:{value}")
                    s.sendall(f"{key}:{value}".encode("utf-8"))
                elif packet == "ping":
                    print("ping!")
                    s.sendall(b"pong")
                else:
                    print(f"Unknown packet: {packet}")
                

if __name__ == "__main__":
    server = BalancerConnectionHandler(QueueManager())
    server.run()