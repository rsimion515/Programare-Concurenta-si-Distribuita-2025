import os.path
import shlex
import shutil
import subprocess
import time

from environment_settings import *

REPORT_FOLDER = os.path.join(os.getcwd(), "results")
if os.path.exists(REPORT_FOLDER):
    shutil.rmtree(REPORT_FOLDER)
os.makedirs(REPORT_FOLDER)

for iteration in range(100):
    for protocol in SETTINGS_TEST_MODES:
        for method in SETTINGS_METHODS:
            for test_size in SETTINGS_TEST_SIZES:
                for block_size in SETTINGS_BLOCK_SIZES:
                    settings = get_settings_json(protocol, method, test_size, block_size)

                    report_file_name_server = ("server_{protocol}_{method}_{test_size}_{block_size}_{iteration}.json"
                                               .format(protocol=protocol, method=method, test_size=test_size,
                                                       block_size=block_size, iteration=iteration))
                    report_file_server = os.path.join(REPORT_FOLDER, report_file_name_server)

                    report_file_name_client = ("client_{protocol}_{method}_{test_size}_{block_size}_{iteration}.json"
                                               .format(protocol=protocol, method=method, test_size=test_size,
                                                       block_size=block_size, iteration=iteration))
                    report_file_client = os.path.join(REPORT_FOLDER, report_file_name_client)

                    command_line_server = generate_cmdline(protocol, method, test_size, block_size, report_file_server)

                    command_line_client = generate_cmdline(protocol, method, test_size, block_size, report_file_client)

                    print("Executing the test:", generate_cmdline(protocol, method, test_size, block_size))

                    server_args = ["py", "server.py"]
                    server_args += shlex.split(command_line_server)

                    client_args = ["py", "client.py"]
                    client_args += shlex.split(command_line_client)

                    server_process = subprocess.Popen(server_args, shell=True)
                    time.sleep(2)
                    client_process = subprocess.Popen(client_args, shell=True)

                    try:
                        # Wait for up to 60 seconds
                        server_process.wait(timeout=60)
                        client_process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        print("Test failed for command: ", generate_cmdline(protocol, method, test_size, block_size))
                        server_process.terminate()
                        client_process.terminate()

                        server_process.wait()
                        client_process.wait()
