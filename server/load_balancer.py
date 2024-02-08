import threading
import socket
import os
import random
import time
# from watchdog.observers import Observer

WORKER_HOST = os.getenv("LOADBALANCER_WORKER_HOST", "localhost")
WORKER_PORT = os.getenv("LOADBALANCER_WORKER_PORT", "12345")

HOST = os.getenv("LOADBALANCER_HOST", "localhost")
PORT = os.getenv("LOADBALANCER_PORT", "12346")

"""
push:key:value -> ack
pull -> key:value
"""

class QueueItem:

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.read_lock = threading.Lock()
        self.node_ids: list[tuple[str, str]] = [] # list of (conn_id, conn_id)

class QueueLoadBalancer:

    def __init__(self) -> None:
        self.key_to_nodes: dict[str, QueueItem] = dict()
        """
        l = []
        push(1,2) -> l = l.append(10)
        lock(l)
        l = {
                    1: [([54, 2], [2, 44], [1, 34])]
        }
        """
        self.worker_connections_lock = threading.Lock()
        self.worker_connections: dict[str, socket.socket] = dict() # worket_id -> connection
        self.t
    
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
        self.key_to_nodes[key].read_lock.acquire()

        self.key_to_nodes[key].lock.acquire()
        node_ids = self.key_to_nodes[key].node_ids.pop()
        self.key_to_nodes[key].lock.release()
        conn_list: list[socket.socket] = []
        for node in node_ids:
            self.worker_connections_lock.acquire()
            conn = self.worker_connections[node]
            self.worker_connections_lock.release()
            conn.sendall(f"pull".encode("utf-8"))            
            conn_list.append(conn)

        def read_response(conn):
            while True:
                packet = conn.recv(2048)
                if not packet: return None
                data = data.decode("utf-8").strip().split(":")
                if len(data) == 2:
                    return data
                elif len(data) == 1 and data[0].strip() == "ack":
                    pass
                else:
                    return None
             
        key = value = None
        for c in conn_list:
            response = read_response(c)
            if response:
                key, value = response
        self.key_to_nodes[key].read_lock.release()
        return key, value
    

    def ping_other(self):
        while True : 
            time.sleep(2)
            

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, int(PORT)))
            s.listen()
            while True:
                client_socket, _ = s.accept()
                threading.Thread(target=self.handle, args=[client_socket]).start()
    
    def handle(self, conn: socket.socket):
        with conn:
            while True:
                packet = conn.recv(2048)
                if not packet:
                    print(f"connection {conn.getpeername()} closed")
                    break
                packet = packet.decode("utf-8").strip()
                if packet.startswith("push"):
                    (_, key, value) = packet.split(":")
                    print(f"pushing {key}:{value}")
                    self.push(key, value)
                elif packet.startswith("pull"):
                    (key, value) = self.pull()
                    print(f"pulled {key}:{value}")
                else:
                    print(f"Unknown packet: {packet}")

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

    def handle(self, conn: socket.socket):
        data = conn.recv(2048)
        worker_id = data.decode("utf-8").strip()
        self.server.worker_connections_lock.acquire()
        self.server.worker_connections[worker_id] = conn
        self.server.worker_connections_lock.release()

if __name__ == "__main__":
    queue_lb = QueueLoadBalancer()
    wch = WorkerConnectionHandler(queue_lb)
    wch_thread = threading.threading(target=wch.run)
    wch_thread.start()
    queue_lb.run()
