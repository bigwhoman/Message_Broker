import slave
import socket
import threading

def test_queue_manager():
    KEY = "key"
    queue = slave.QueueManager()
    items = [str(i) for i in range(10)]
    for data in items:
        queue.push(KEY, data)
    for data in items:
        value = queue.pull(KEY)
        assert value == data

def test_queue_server():
    # Start a server as master
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        slave.LOAD_BALANCER_PRIMARY_PORT = s.getsockname()[1]
        slave.LOAD_BALANCER_BACKUP_PORT = 0 # kill if we reach backup
        SLAVE_ID = "SLAVE_ID"
        slaveThread = threading.Thread(target=slave.BalancerConnectionHandler(slave.QueueManager(), SLAVE_ID).run)
        slaveThread.daemon = True
        slaveThread.start()
        # Accept the connection
        slaveSocket, _ = s.accept()
        # First packet must be the id
        assert slaveSocket.recv(1024).decode() == SLAVE_ID
        # Send a push request
        KEY = "key"
        VALUE = "value"
        ACK = "ack"
        slaveSocket.sendall(f"push:{KEY}:{VALUE}".encode())
        assert slaveSocket.recv(1024).decode() == ACK
        # Pull the result
        slaveSocket.sendall(f"pull:{KEY}".encode())
        assert slaveSocket.recv(1024).decode() == f"{KEY}:{VALUE}"
