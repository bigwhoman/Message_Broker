from datetime import datetime
import threading
import item_service_pb2
import item_service_pb2_grpc
import yaml
# from watchdog.observers import Observer

class Item:
    def __init__(self, key, value) -> None:
        self.key = key
        self.value = value
        self.created_at = datetime.now()

    def __eq__(self, other):
        return self.key == other.key and \
                self.value == other.value


class Server:

    ping_timeout = 0.3

    def __init__(self, ip, port) -> None:
        self.queue: list[Item] = list()
        self.queue_lock : threading.Lock = threading.Lock()
        self.worker_list_lock: threading.Lock = threading.Lock()
        self.worker_list: list[Server] = list()
        self.ip = ip
        self.port = port
        self.is_master = False
        self.synchronizer = None
        

    def push(self, item: Item) -> Item:
        if not self.is_master:
            return item
        self.queue_lock.acquire()
        self.queue.append(Item)
        self.synchronizer.sync(server = self, workers = self.worker_list)
        self.queue_lock.release()
    

    def pull(self) -> Item:
        if not self.is_master:
            return item
        self.queue_lock.acquire()
        item = self.queue.pop()
        self.synchronizer.sync(server = self, workers = self.worker_list)
        self.queue_lock.release()
        return item
    
    def run(self) :
        pass 


    def broadcast_message(self, item: Item) -> bool:
        ...

class Synchronizer:
    
    def __init__(self) -> None:
        ...        

    def ping_worker(self, worker: Server) -> list[Item] :
        ...

    def update_worker(self, worker : Server, updated_queue : list[Item]) :
        ...

    def sync(self, server: Server, workers: list[Server]):  
        for worker in self.workers : 
            workers_items = self.ping_worker(worker)
            if workers_items :
                for count ,item in enumerate(workers_items) : 
                    if server.queue[count] != item : 
                        self.update_worker(worker, server.queue)
                        break


class LeaderElection:

    def __init__(self) -> None:
        ...

    def run(self):
        ...



class ConfigLoader:

    config_file_path = "./config/config.yaml"

    def __init__(self, server: Server) -> None:        
        self.server = server

    def propagate_config(self, event):
        if event.src_path.endswith("config.yaml"):
            try:
                with open(event.src_path, 'r') as file:
                    yaml_content = yaml.safe_load(file)
                    peers_ips = yaml_content["peers"]
            except Exception as e:
                print(f'Error reading file: {e}')


    def run(self) -> None:
        ...   
        # observer = Observer()
        # observer.schedule(self.propagate_config, self.config_file_path, recursive=False)
        # observer.start()
        # observer.join()
