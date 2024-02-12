from ourclient import Client, ServerInfo

qc = Client([ServerInfo("192.168.207.8", 12345), ServerInfo("192.168.207.8", 12346)])

def pull():
    return qc.pull()

def push(key,val):
    qc.push(key,val)


def subscribe(action):
    qc.subscribe(action)
