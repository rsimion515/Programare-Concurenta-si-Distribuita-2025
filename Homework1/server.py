import argparse
import asyncio
import json
import socket
import time

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol

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


class QUICServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, settings, return_values, server_stop, **kwargs):
        super().__init__(*args, **kwargs)

        self.server_stop = server_stop

        self.settings = settings
        self.return_values = return_values

        self.respond_back = False
        if self.settings['method'] == "stop-and-wait":
            self.respond_back = True

        self.start_time = 0

    def quic_event_received(self, event):
        if hasattr(event, "data"):
            if event.data == self.settings["termination_signal"]:
                self.return_values["total_time"] = time.time() - self.start_time

                self._quic.close()
                self.server_stop().set()
            else:
                if self.start_time == 0:
                    self.start_time = time.time()

                self.return_values["count_received"] += 1
                self.return_values["size_received"] += len(event.data)

                if self.respond_back:
                    self._quic.send_stream_data(0, b'ACK')

async def quic_server(settings):
    configuration = QuicConfiguration(is_client=False)
    server_stop = asyncio.Event()

    return_values = {"count_received": 0, "size_received": 0, "total_time": 0}
    server = await serve(settings["host"], settings["port"], configuration=configuration,
                         create_protocol=lambda *args, **kwargs: QUICServerProtocol(*args, settings=settings, return_values=return_values, server_stop=server_stop, **kwargs))

    print("Server initialized, ready to go")

    await server_stop.wait()

    return return_values["count_received"], return_values["size_received"], return_values["total_time"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", choices=["tcp", "udp", "quic"])
    parser.add_argument("--method", choices=["streaming", "stop-and-wait"])
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--termination_signal")
    parser.add_argument("--size", type=int)
    parser.add_argument("--block_size", type=int)
    parser.add_argument("--file_report")

    settings = vars(parser.parse_args())

    settings["termination_signal"] = settings["termination_signal"].encode()

    count_received = 0
    size_received = 0
    total_time = 0

    if settings["protocol"] == "tcp":
        count_received, size_received, total_time = tcp_server(settings)
    elif settings["protocol"] == "udp":
        count_received, size_received, total_time = udp_server(settings)
    elif settings["protocol"] == "quic":
        count_received, size_received, total_time = asyncio.run(quic_server(settings))

    if "file_report" in settings:
        with open(settings["file_report"], "w+") as file:
            settings["termination_signal"] = settings["termination_signal"].decode()

            data = {
                'type': 'server',
                'results': {
                    'count_received': count_received,
                    'size_received': size_received,
                    'total_time': total_time
                },
                'settings': settings
            }
            file.write(json.dumps(data, indent=4))
    else:
        print("Received packets: {value}".format(value=count_received))
        print("Received total size: {value}".format(value=size_received))
        print("Total time: {value}".format(value=total_time))

if __name__ == "__main__":
    main()