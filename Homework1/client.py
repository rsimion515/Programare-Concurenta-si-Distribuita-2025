import argparse
import socket
import random
import time

# Generate a random set of blocks in order to simulate real-world data structures
def generate_list_of_blocks(settings):
    block_sizes = []
    total_blocks_size = 0

    while total_blocks_size < settings["size"]:
        # 65535 not possible due to UDP limitation to 65507
        current_block_size = random.randint(1, 65000)
        block_sizes.append(current_block_size)
        total_blocks_size += current_block_size

    return block_sizes

def tcp_client(settings, block_sizes):

    # Pre-allocating our buffer for future slicing
    buffer_data = b'0' * 65535

    # Initializing our variables for metrics
    total_packets_sent = 0
    total_packets_size_sent = 0

    # General server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((settings["host"], settings["port"]))

    # In client, we start all the clocks before sending the first packet
    start_time = time.time()

    for block in block_sizes:
        # Sending only a slice of the buffer
        client_socket.sendall(buffer_data[:block])

        # Updating our metrics
        total_packets_sent += 1
        total_packets_size_sent += block

    # Sending the termination signal to stop the execution on server
    client_socket.sendall(settings["termination_signal"])

    end_time = time.time()

    client_socket.close()

    return total_packets_sent, total_packets_size_sent, end_time - start_time


def udp_client(settings, block_sizes):

    # Pre-allocating our buffer for future slicing
    buffer_data = b'0' * 65535

    # Initializing our variables for metrics
    total_packets_sent = 0
    total_packets_size_sent = 0
    total_packets_failed = 0

    # General server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((settings["host"], settings["port"]))

    if settings["method"] == "streaming":
        # In client, we start all the clocks before sending the first packet
        start_time = time.time()

        for block in block_sizes:
            # Sending only a slice of the buffer
            client_socket.sendto(buffer_data[:block], (settings["host"], settings["port"]))

            # Updating our metrics
            total_packets_sent += 1
            total_packets_size_sent += block
    else:
        # In client, we start all the clocks before sending the first packet
        start_time = time.time()

        for block in block_sizes:
            # Sending only a slice of the buffer
            client_socket.sendto(buffer_data[:block], (settings["host"], settings["port"]))

            try:
                _ack, _ = client_socket.recvfrom(1024)

                # Updating our metrics
                total_packets_sent += 1
                total_packets_size_sent += block
            except socket.timeout:
                total_packets_failed += 1

    # Sending the termination signal to stop the execution on server
    client_socket.sendto(settings["termination_signal"], (settings["host"], settings["port"]))

    end_time = time.time()

    client_socket.close()

    return total_packets_sent, total_packets_size_sent, end_time - start_time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", choices=["tcp", "udp", "quic"])
    parser.add_argument("--method", choices=["streaming", "stop-and-wait"])
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--termination_signal")
    parser.add_argument("--size", type=int)
    settings = vars(parser.parse_args())

    settings["termination_signal"] = settings["termination_signal"].encode()

    count_received = 0
    size_received = 0
    total_time = 0

    block_sizes = generate_list_of_blocks(settings)

    if settings["protocol"] == "tcp":
        count_received, size_received, total_time = tcp_client(settings, block_sizes)
    elif settings["protocol"] == "udp":
        count_received, size_received, total_time = udp_client(settings, block_sizes)

    print("Received packets:", count_received)
    print("Received total size:", size_received)
    print("Execution time:", total_time)


if __name__ == "__main__":
    main()