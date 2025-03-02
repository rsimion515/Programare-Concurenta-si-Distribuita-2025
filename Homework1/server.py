import argparse
import socket
import time

def tcp_server(settings):
    # Initializing our variables for metrics
    total_packets_received = 0
    total_packets_size_received = 0
    start_time = 0
    end_time = 0

    # General server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((settings["host"], settings["port"]))
    server_socket.listen(1)

    print("Server initialized, ready to go")

    client_socket, addr = server_socket.accept()

    while True:
        data = client_socket.recv(65535)

        # due to UDP not having an accept method to trigger the clock
        # and in order to make it fair, all clock will start after the first message
        # and all tests will end after the termination signal is received
        if start_time == 0:
            start_time = time.time()

        if data == settings["termination_signal"]:
            print("Received termination signal")
            end_time = time.time()
            break

        if not data:
            break

        # Updating our metrics
        total_packets_received += 1
        total_packets_size_received += len(data)

    client_socket.close()
    server_socket.close()

    # Return values
    return total_packets_received, total_packets_size_received, end_time - start_time


def udp_server(settings):
    # Initializing our variables for metrics
    total_packets_received = 0
    total_packets_size_received = 0
    start_time = 0
    end_time = 0

    # General server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((settings["host"], settings["port"]))

    print("Server initialized, ready to go")

    if settings["method"] == "streaming":
        while True:
            data, addr = server_socket.recvfrom(65535)

            if start_time == 0:
                start_time = time.time()

            if not data:
                break

            if data == settings["termination_signal"]:
                end_time = time.time()
                break

            # Updating our metrics
            total_packets_received += 1
            total_packets_size_received += len(data)
    elif settings["method"] == "stop-and-wait":
        while True:
            data, addr = server_socket.recvfrom(65535)

            if start_time == 0:
                start_time = time.time()

            if not data:
                break

            if data == settings["termination_signal"]:
                end_time = time.time()
                break

            # Updating our metrics
            total_packets_received += 1
            total_packets_size_received += len(data)

            # Send back acknowledgment
            server_socket.sendto(b'ACK', addr)

    server_socket.close()

    # Return values
    return total_packets_received, total_packets_size_received, end_time - start_time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", choices=["tcp", "udp", "quic"])
    parser.add_argument("--method", choices=["streaming", "stop-and-wait"])
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--termination_signal")
    parser.add_argument("--size", type=int)
    parser.add_argument("--block_size", type=int)
    settings = vars(parser.parse_args())

    settings["termination_signal"] = settings["termination_signal"].encode()

    count_received = 0
    size_received = 0
    total_time = 0

    if settings["protocol"] == "tcp":
        count_received, size_received, total_time = tcp_server(settings)
    elif settings["protocol"] == "udp":
        count_received, size_received, total_time = udp_server(settings)

    print("Received packets:", count_received)
    print("Received total size:", size_received)
    print("Execution time:", total_time)

if __name__ == "__main__":
    main()