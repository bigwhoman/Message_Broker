import threading
import socket
import random
import time
import util
import copy
from prometheus_client import Counter
"""
push:key:value
pull -> key:value
"""
PUSH_REQUEST = Counter('push_request_counter', 'all pushes', )

class WorkerSocket:
    def __init__(self, s: socket.socket) -> None:
        self.__s = s
        self.__lock = threading.Lock()
    
    def push(self, key: str, value: str):
        with self.__lock:
            self.__s.sendall(f"push:{key}:{value}".encode("utf-8"))
            read_buffer = self.__s.recv(4)
            if read_buffer != b"ack":
                raise Exception(f"HUGE FUCKUP: {read_buffer}")

    def prepare_pull(self):
        # Just get the lock
        self.__lock.acquire()

    def pull(self):
        try:
            self.__s.sendall(b"pull")
            packet = self.__s.recv(2048)
            if not packet:
                raise Exception("socket closed")
            data = packet.decode("utf-8").strip().split(":")
            if len(data) == 2:
                (key, value) = data
                return key, value
        except:
            # Socket closed, close the socket and 
            self.close()
            return None
        finally:
            self.__lock.release()
    
    def close(self):
        self.__s.close()


class QueueItem:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.node_ids: list[list[str]] = [] # list of (conn_id, conn_id)
    
    def to_simple(self) -> list[list[str]]:
        return copy.deepcopy(self.node_ids)

    def __str__(self) -> str:
        return str(self.node_ids)

class QueueLoadBalancer:

    def __init__(self) -> None:
        self.key_to_nodes: dict[str, QueueItem] = dict()
        # This condvar is only used when we want to notify pull clients that we have added something to keys
        self.added_condvar = threading.Condition()
        """
        l = []
        push(1,2) -> l = l.append(10)
        lock(l)
        l = {
            1: [([54, 2], [2, 44], [1, 34])]
        }
        """
        self.worker_connections: dict[str, WorkerSocket] = dict() # worket_id -> connection
    
    def push(self, key: str, value: bytes):        
        # Check if there is any worker at all
        if len(self.worker_connections) == 0: 
            return
        # Create a new queue in keys if it does not exists
        # We get the added_condvar lock but dont use it as condvar
        with self.added_condvar:
            if not key in self.key_to_nodes:
                self.key_to_nodes[key] = QueueItem()
        queueItem = self.key_to_nodes[key]
        # Select two workers to push this key in them
        worker_ids = list(self.worker_connections.keys())
        the_chosen_ones = []        
        try:
            the_chosen_ones = sorted(random.sample(worker_ids, 2))
        except ValueError:
            the_chosen_ones = [worker_ids[0]]
        print(f"Pushing {key}:{value} To Workers = {the_chosen_ones}")

        with queueItem.lock: # Hold the lock. This makes the sending in client synchronous
            for worker_id in the_chosen_ones:
                try:
                    self.worker_connections[worker_id].push(key, value)
                    PUSH_REQUEST.inc()
                    print(f"Sent {key}:{value} to {worker_id}")
                except Exception:
                    print(f"Removing connection {worker_id}")
                    self.worker_connections[worker_id].close()
                    del self.worker_connections[worker_id]
            queueItem.node_ids.append(the_chosen_ones)
        # Notify if needed
        with self.added_condvar:
            self.added_condvar.notify()

        

    def pull(self) -> tuple[str, str]:
        # Atomically get the next item to pull
        with self.added_condvar:
            while True:
                node_ids = None
                for key, queue in self.key_to_nodes.items():
                    with queue.lock:
                        if len(queue.node_ids) != 0:
                            node_ids = queue.node_ids.pop(0)
                            for node in node_ids:
                                if node in self.worker_connections:
                                    self.worker_connections[node].prepare_pull()
                            break
                if node_ids:
                    break
                self.added_condvar.wait() # wait until someone add a new key to our queue
        print(f"Pulling {key} from {node_ids}")
        # Pull from workers
        results: list[tuple[str, str]] = []
        for node in node_ids:
            if node in self.worker_connections:
                result = self.worker_connections[node].pull()
                if result:
                    results.append(result)
                else:
                    print(f"Removing connection {node}")
                    del self.worker_connections[node]
        return results[0]
        
    

    def ping_other(self):
        while True : 
            time.sleep(2)

    def run(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, int(port)))
            s.listen()
            while True:
                client_socket, _ = s.accept()
                threading.Thread(target=self.handle, args=[client_socket]).start()

    def handle(self, conn: socket.socket):
        with conn:
            while True:
                packet = conn.recv(2048)
                if not packet:
                    #print(f"connection {conn.getpeername()} closed")
                    break
                packet = packet.decode("utf-8").strip()
                if packet.startswith("push"):
                    (_, key, value) = packet.split(":")
                    print(f"pushing {key}:{value}")
                    self.push(key, value)
                    conn.sendall(b'ack')
                elif packet.startswith("pull"):
                    (key, value) = self.pull()
                    conn.sendall(f'{key}:{value}'.encode("utf-8"))
                    print(f"pulled {key}:{value}")
                else:
                    print(f"Unknown packet: {packet}")

    def sync_from_primary(self, listen: str, port: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((listen, port))
            while True:
                serialized_data = util.get_json(s)
                self.key_to_nodes.clear()
                for key, value in serialized_data.items():
                    item = QueueItem()
                    item.node_ids = value
                    self.key_to_nodes[key] = item
                #print("Nodes are", self.key_to_nodes)


    def listen_for_backup(self, listen: str, port: int):
        """
        Listen for backup load balancer and sync data with it
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((listen, port))
            s.listen()
            backup_socket, _ = s.accept()
            while True:
                time.sleep(5)
                # This is a bad way
                to_serialize = {}
                for (key, l) in self.key_to_nodes.items():
                    to_serialize[key] = l.to_simple()
                util.send_json(backup_socket, to_serialize)


class WorkerConnectionHandler:

    def __init__(self, server: QueueLoadBalancer) -> None:
        self.server = server
    
    def run(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, int(port)))
            s.listen()
            while True:
                worker_socket, _ = s.accept()
                threading.Thread(target=self.handle, args=[worker_socket]).start()

    def handle(self, conn: socket.socket):
        data = conn.recv(2048)
        worker_id = data.decode("utf-8").strip()
        print(f"Worker {worker_id} joined")
        self.server.worker_connections[worker_id] = WorkerSocket(conn)

