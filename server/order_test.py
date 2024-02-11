import socket
import random
import string

PRIMARY_HOST = "192.168.56.6"
PRIMARY_PORT = 12345
KEY_COUNT = 10
TOTAL_PUSHES = 10_000

def random_data() -> str:
    """
    Generate a random string to be used as the value for the key
    """
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(10))

def main():
    pushed_stuff: list[list[str]] = [[] for _ in range(KEY_COUNT)]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((PRIMARY_HOST, PRIMARY_PORT))
        # At first push everything
        print("Pushing...")
        for _ in range(TOTAL_PUSHES):
            key = random.randint(0, KEY_COUNT - 1)
            value = random_data()
            s.sendall(f"push:{key}:{value}".encode())
            assert s.recv(4) == b'ack'
            pushed_stuff[key].append(value)
        # Now pop and check
        print("Pulling...")
        for _ in range(TOTAL_PUSHES):
            s.sendall(b"pull")
            (key, value) = s.recv(2024).decode().split(":")
            key = int(key)
            expected_value = pushed_stuff[key].pop(0)
            if expected_value != value:
                print(f"Mismatch: {expected_value} != {value}")
            assert expected_value == value

if __name__ == "__main__":
    main()