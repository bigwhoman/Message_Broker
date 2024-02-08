import socket
import os
import uuid
import time

LOAD_BALANCER_HOST = os.getenv("LOAD_BALANCER_HOST", "localhost")
LOAD_BALANCER_PORT = int(os.getenv("LOAD_BALANCER_PORT", "12345"))
LOAD_BALANCER_BACKUP_HOST = os.getenv("LOAD_BALANCER_BACKUP_HOST", "localhost")
LOAD_BALANCER_BACKUP_PORT = int(os.getenv("LOAD_BALANCER_BACKUP_PORT", "12347"))

class QueueManager:
    def __init__(self):
        self.queue: list[tuple[str, str]] = []
    
    def push(self, key: str, value: str):
        self.queue.append((key, value))

    def pull(self) -> tuple[str, str]:
        return self.queue.pop(0)

class BalancerConnectionHandler:

    def __init__(self, queue: QueueManager, id: str):
        self.queue = queue
        self.id = id
        print("We are worker", id)
    
    def run(self):
        # At first, run in primary mode
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((LOAD_BALANCER_HOST, LOAD_BALANCER_PORT))
                self.handle_master(s)
        except IOError:
            pass
        # Now run in backup mode
        print("PRIMARY FAILED. FALLING BACK TO BACKUP MASTER")
        time.sleep(5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LOAD_BALANCER_BACKUP_HOST, LOAD_BALANCER_BACKUP_PORT))
            self.handle_master(s)

    def handle_master(self, s: socket.socket):
        s.sendall(self.id.encode("utf-8"))
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
    server = BalancerConnectionHandler(QueueManager(), str(uuid.uuid4()))
    server.run()