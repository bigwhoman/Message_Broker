import asyncio
import time
import random
import string

PRIMARY_HOST = "192.168.56.6"
PRIMARY_PORT = 12345
CONNECTION_COUNT = 4 # How many connections we shall open?
TOTAL_ACTIONS = 1_000 # How many actions each connection does?
KEY_POOL = [str(i) for i in range(10)] # The keys we use to benchmark broker

def random_key() -> str:
    """
    Create a random key from the KEY_POOL
    """
    return random.choice(KEY_POOL)

def random_data() -> str:
    """
    Generate a random string to be used as the value for the key
    """
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(10))

async def load_test(id: int):
    print(f"Starting load test {id}")
    start = time.perf_counter()
    pushed_data = 0 # number of relative pushed data
    try:
        # Open the socket
        reader, writer = await asyncio.open_connection(PRIMARY_HOST, PRIMARY_PORT)
        for _ in range(TOTAL_ACTIONS):
            # always push something new push randomly or if there is nothing to pull
            if random.randint(0, 1) == 0 or pushed_data == 0:
                pushed_data += 1
                writer.write(f"push:{random_key()}:{random_data()}".encode())
                await writer.drain()
                read_back = await reader.readexactly(3)
                if read_back != b"ack":
                    raise Exception(f"Did not receive ack for push: {read_back}")
            else: # otherwise, pull something from the server
                pushed_data -= 1
                writer.write(b"pull")
                await writer.drain()
                await reader.read(1024) # also, fuck the data
        end = time.perf_counter()
        print(f"Load test {id} done: TPS: {TOTAL_ACTIONS / (end - start)}")
    except Exception as ex:
        print(f"Load test {id} failed: {ex}")
        pass
    finally:
        # Close the socket
        writer.close()
        await writer.wait_closed()


async def main():
    print("Starting load tests...")
    tasks = []
    for id in range(CONNECTION_COUNT):
        tasks.append(asyncio.create_task(load_test(id)))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
