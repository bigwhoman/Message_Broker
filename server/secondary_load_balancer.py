import load_balancer
import threading
import os
from prometheus_client import start_http_server

WORKER_LISTEN = os.getenv("WORKER_LISTEN", "localhost")
WORKER_PORT = int(os.getenv("WORKER_PORT", "12347"))

CLIENT_LISTEN = os.getenv("CLIENT_LISTEN", "localhost")
CLIENT_PORT = int(os.getenv("CLIENT_PORT", "12356"))

PRIMARY_HOST = os.getenv("PRIMARY_HOST","localhost")
PRIMARY_PORT = int(os.getenv("PRIMARY_PORT","51234"))


if __name__ == "__main__":
    start_http_server(port=9090, addr="0.0.0.0")
    queue_lb = load_balancer.QueueLoadBalancer()
    wch = load_balancer.WorkerConnectionHandler(queue_lb)
    wch_thread = threading.Thread(target=wch.run, args=(WORKER_LISTEN, WORKER_PORT))
    wch_thread.daemon = True
    sync_thread = threading.Thread(target=queue_lb.sync_from_primary, args=(PRIMARY_HOST, PRIMARY_PORT))
    sync_thread.start()
    sync_thread.join()
    wch_thread.start()
    queue_lb.run(host=CLIENT_LISTEN, port=CLIENT_PORT)
