SETTINGS_TEST_MODE_TCP       = 1
SETTINGS_TEST_MODE_UDP       = 2
SETTINGS_TEST_MODE_QUIC      = 3

SETTINGS_TEST_MODES = [SETTINGS_TEST_MODE_TCP, SETTINGS_TEST_MODE_UDP]

SETTINGS_METHOD_STREAMING     = 1
SETTINGS_METHOD_STOP_AND_WAIT = 2

SETTINGS_METHODS = [SETTINGS_METHOD_STREAMING, SETTINGS_METHOD_STOP_AND_WAIT]

SETTINGS_TEST_SIZE_500MB = 500 * 1024 * 1024
SETTINGS_TEST_SIZE_1GB   = 1024 * 1024 * 1024

SETTINGS_TEST_SIZES = [SETTINGS_TEST_SIZE_500MB, SETTINGS_TEST_SIZE_1GB]

SETTINGS_BLOCK_SIZES_RANDOM = 1
SETTINGS_BLOCK_SIZES_FIXED_1024 = 2
SETTINGS_BLOCK_SIZES_FIXED_32768 = 3

SETTINGS_BLOCK_SIZES = [SETTINGS_BLOCK_SIZES_RANDOM, SETTINGS_BLOCK_SIZES_FIXED_1024, SETTINGS_BLOCK_SIZES_FIXED_32768]

def get_settings_json(test_mode, method, size, block_size):
    settings = {
        "termination_signal": "END",
        "host": "127.0.0.1",
        "port": 8080,
    }

    if test_mode == SETTINGS_TEST_MODE_TCP:
        settings["protocol"] = "tcp"
    elif test_mode == SETTINGS_TEST_MODE_UDP:
        settings["protocol"] = "udp"
    elif test_mode == SETTINGS_TEST_MODE_QUIC:
        settings["protocol"] = "quic"
    else:
        return {}

    if method == SETTINGS_METHOD_STREAMING:
        settings["method"] = "streaming"
    elif method == SETTINGS_METHOD_STOP_AND_WAIT:
        settings["method"] = "stop_and_wait"
    else:
        return {}

    if size not in SETTINGS_TEST_SIZES:
        return {}
    else:
        settings["size"] = size

    if block_size == SETTINGS_BLOCK_SIZES_FIXED_1024:
        settings["block_size_fixed"] = 1024
    elif block_size == SETTINGS_BLOCK_SIZES_FIXED_32768:
        settings["block_size_fixed"] = 32768
    elif block_size == SETTINGS_BLOCK_SIZES_RANDOM:
        settings["block_size_random"] = True
    else:
        return {}

    return settings

def generate_cmdline(test_mode, method, size, block_size, file_report = None):
    command_line = '--host "127.0.0.1" --port 8080 --termination_signal "END"'

    if test_mode == SETTINGS_TEST_MODE_TCP:
        command_line += ' --protocol "tcp"'
    elif test_mode == SETTINGS_TEST_MODE_UDP:
        command_line += ' --protocol "udp"'
    elif test_mode == SETTINGS_TEST_MODE_QUIC:
        command_line += ' --protocol "quic"'
    else:
        return ""

    if method == SETTINGS_METHOD_STREAMING:
        command_line += ' --method "streaming"'
    elif method == SETTINGS_METHOD_STOP_AND_WAIT:
        command_line += ' --method "stop-and-wait"'
    else:
        return ""

    if size not in SETTINGS_TEST_SIZES:
        return ""
    else:
        command_line += ' --size "{}"'.format(size)

    if block_size == SETTINGS_BLOCK_SIZES_FIXED_1024:
        command_line += ' --block_size "{}"'.format(1024)
    elif block_size == SETTINGS_BLOCK_SIZES_FIXED_32768:
        command_line += ' --block_size "{}"'.format(32768)
    elif block_size == SETTINGS_BLOCK_SIZES_RANDOM:
        command_line += ' --block_size {}'.format(0)
    else:
        return ""

    if file_report is not None:
        command_line += ' --file_report "{}"'.format(file_report)

    return command_line