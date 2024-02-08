from datetime import datetime
import threading
import socket
import os
import random
# from watchdog.observers import Observer

WORKER_HOST = os.getenv("LOADBALANCER_WORKER_HOST", "localhost")
WORKER_PORT = os.getenv("LOADBALANCER_WORKER_PORT", "12345")

HOST = os.getenv("LOADBALANCER_HOST", "localhost")
PORT = os.getenv("LOADBALANCER_PORT", "12346")

class QueueItem:

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.node_ids = []

class QueueLoadBalancer:

    def __init__(self) -> None:
        self.key_to_nodes: dict[str, QueueItem] = dict()
        self.worker_connections_lock = threading.Lock()
        self.worker_connections = dict() # worket_id -> connection
    
    def push(self, key: str, value: bytes):
        if len(self.worker_connections) == 0: 
            return
        if not key in self.key_to_nodes:
            self.key_to_nodes[key] = QueueItem()
        self.key_to_nodes[key].lock.acquire()
        worker_ids = list(self.worker_connections.keys())
        the_chosen_ones = []        
        try:
            the_chosen_ones = random.sample(worker_ids, 2)
        except ValueError:
            the_chosen_ones = worker_ids[0]
        for worker_id in the_chosen_ones:
            self.worker_connections_lock.acquire()
            conn = self.worker_connections[worker_id]
            self.worker_connections_lock.release()
            conn.sendall(f"push:{key}:{value}".encode("utf-8"))

        self.key_to_nodes[key].lock.release()

    def pull(self):
        key = list(self.key_to_nodes.keys())[0]
        self.key_to_nodes[key].lock.acquire()
        self.key_to_nodes[key].lock.release()
    
    def run(self):
        ...

class WorkerConnectionHandler:

    def __init__(self, server: QueueLoadBalancer) -> None:
        self.server = server
    
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((WORKER_HOST, int(WORKER_PORT)))
            s.listen()
            while True:
                worker_socket, _ = s.accept()
                threading.Thread(target=self.handle, args=[worker_socket]).start()

    def handle(self, conn):
        data = conn.recv(2048)
        worker_id = data.decode("utf-8")
        self.server.worker_connections_lock.acquire()
        self.server.worker_connections[worker_id] = conn
        self.server.worker_connections_lock.release()

