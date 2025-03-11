import argparse
import asyncio
import json
import socket
import random
import time

from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import StreamDataReceived


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

def generate_list_of_blocks_fixed(settings):
    block_sizes = []

    count_of_full_blocks = settings["size"] // settings["block_size"]
    size_remainder = settings["size"] % settings["block_size"]
    block_sizes.extend([settings["block_size"]] * count_of_full_blocks)

    if size_remainder > 0:
        block_sizes.append(size_remainder)

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


class QUICClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, settings, return_values, block_sizes, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = settings
        self.return_values = return_values

        self.start_time = 0

        self.block_sizes = block_sizes

        self.await_response = False
        if self.settings['method'] == "stop-and-wait":
            self.await_response = True
            self.received_ack = asyncio.Event()

    async def send_data(self):
        # Pre-allocating our buffer for future slicing
        buffer_data = b'0' * 65535

        stream_id = self._quic.get_next_available_stream_id()

        self.start_time = time.time()

        for block in self.block_sizes:
            # Sending only a slice of the buffer
            self._quic.send_stream_data(stream_id, buffer_data[:block])
            self.transmit()

            # Updating our metrics
            self.return_values["count_sent"] += 1
            self.return_values["size_sent"] += block

            if self.await_response:
                # Wait for server response
                await self.received_ack.wait()
                # Reset for next message
                self.received_ack.clear()

        self._quic.send_stream_data(stream_id, self.settings["termination_signal"])
        if self.await_response:
            # Wait for server response
            await self.received_ack.wait()
            # Reset for next message
            self.received_ack.clear()

        self.return_values["total_time"] = time.time() - self.start_time

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived) and event.data == b'ACK':
            self.received_ack.set()

async def quic_client(settings, block_sizes):
    configuration = QuicConfiguration(is_client=True)

    # Disable TLS verification for testing
    configuration.verify_mode = False

    return_values = {"count_sent": 0, "size_sent": 0, "total_time": 0}
    async with connect(settings["host"], settings["port"], configuration=configuration,
                       create_protocol=lambda *args, **kwargs: QUICClientProtocol(*args, settings=settings, return_values=return_values, block_sizes=block_sizes, **kwargs)) as client:
        await client.send_data()

    return return_values["count_sent"], return_values["size_sent"], return_values["total_time"]


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

    if settings["block_size"] == 0:
        block_sizes = generate_list_of_blocks(settings)
    else:
        block_sizes = generate_list_of_blocks_fixed(settings)

    if settings["protocol"] == "tcp":
        count_received, size_received, total_time = tcp_client(settings, block_sizes)
    elif settings["protocol"] == "udp":
        count_received, size_received, total_time = udp_client(settings, block_sizes)
    elif settings["protocol"] == "quic":
        count_received, size_received, total_time = asyncio.run(quic_client(settings, block_sizes))

    if "file_report" in settings and settings["file_report"] is not None:
        with open(settings["file_report"], "w+") as file:
            settings["termination_signal"] = settings["termination_signal"].decode()

            data = {
                'type': 'client',
                'results': {
                    'count_sent': count_received,
                    'size_sent': size_received,
                    'total_time': total_time
                },
                'settings': settings
            }
            if settings['block_size'] == 0:
                data['block_sizes'] = block_sizes

            file.write(json.dumps(data, indent=4))
    else:
        print("Sent packets: {value}".format(value=count_received))
        print("Sent total size: {value}".format(value=size_received))
        print("Total time: {value}".format(value=total_time))

    print("Client finished execution")


if __name__ == "__main__":
    main()