import socket
import sys
from threading import Thread
from time import sleep


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

    def run_client(self):
        while True:
            print("---- Client Menu ----")
            print("1. Push")
            print("2. Pull")
            print("3. Subscribe")
            print("4. Exit")
            choice = input("Enter your choice: ")
            if choice == "1":
                key = input("Enter key: ")
                val = input("Enter value: ")
                self.push(key, val)
                print(f"Pushed {key}:{val} to server")
            elif choice == "2":
                key, val = self.pull()
                if key != None:
                    print(f"Got key:value pair -> {key}:{val}")
                else:
                    print("No key:value pairs available")
            elif choice == "3":
                print("[Subscription] started")
                thread = Thread(
                            target=self.subscribe, 
                            args=[lambda key, value: print(f"[Subscription] got key:value pair -> {key}:{value}")]
                        )
                thread.start()
            elif choice == "4":
                break
            else:
                print("Invalid choice")


    def send_request(self, type: str, data: str):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((self.servers[0].ip, self.servers[0].port))
        except Exception as e:
            print(f"Error connecting to the load balancer, retrying with the backup LB:\n {e}")
            client.connect((self.servers[1].ip, self.servers[1].port))
        
        try:
            client.sendall(f"{type}{data}".encode("utf-8"))
        except Exception as e:
            print(f"Could not send {type}{data} request to load balancer:\n {e}")
        
        if type != 'push':
            response = client.recv(2048)
            response = response.decode("utf-8").strip()
            client.close()
            return response
        client.close()
        

    def push(self, key: str, val: str):
        response = self.send_request("push", f":{key}:{val}")
        return response

    
    def pull(self) -> tuple[str, str]:
        response = self.send_request("pull", "")
        if response == '':
            return None, None
        response_parts = response.split(":")
        return response_parts[0], response_parts[1]
    
    def subscribe(self, f):
        while True:
            response = self.send_request("pull", "")
            if response != '':
                response_parts = response.split(":")
                f(response_parts[0], response_parts[1])
            ''' 
               No else case is needed because this happens nearly always in out infinite loop.
               Cases which there is an error with server are logged inside the send_request method. 
            '''

    

def main():
    servers = []
    for arg in sys.argv:
        if arg.endswith(".py"):
            continue
        arg_parts = arg.split(":")
        ip, port = arg_parts[0], int(arg_parts[1])
        server = ServerInfo(ip, int(port))
        servers.append(server)
    client = Client(servers)
    print(f"client is up...\nTarget Servers:\n{client.servers}")
    client.run_client()


if __name__ == "__main__":
    main()