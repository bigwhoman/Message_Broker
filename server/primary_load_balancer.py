import load_balancer
import threading
import os

WORKER_LISTEN = os.getenv("LOADBALANCER_WORKER_HOST", "localhost")
WORKER_PORT = int(os.getenv("LOADBALANCER_WORKER_PORT", "12345"))

CLIENT_LISTEN = os.getenv("LOADBALANCER_HOST", "localhost")
CLIENT_PORT = int(os.getenv("LOADBALANCER_PORT", "12346"))

SECONDARY_MASTER_LISTEN = os.getenv("SECONDARY_HOST", "localhost")
SECONDARY_MASTER_PORT = int(os.getenv("SECONDARY_PORT", "51234"))


if __name__ == "__main__":
    queue_lb = load_balancer.QueueLoadBalancer()
    wch = load_balancer.WorkerConnectionHandler(queue_lb)
    wch_thread = threading.Thread(target=wch.run, args=(WORKER_LISTEN, WORKER_PORT))
    secondary_thread = threading.Thread(target=queue_lb.listen_for_backup, args=(SECONDARY_MASTER_LISTEN, SECONDARY_MASTER_PORT))
    wch_thread.start()
    secondary_thread.start()
    queue_lb.run(host=CLIENT_LISTEN, port=CLIENT_PORT)