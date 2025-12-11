# Traffic Generator Tool

This tool consists of a sender and a receiver to generate and monitor TCP traffic.

## Requirements
- Python 3.x

## Usage

### 1. Start the Receiver
The receiver listens for incoming connections and measures the received traffic.

```bash
python receiver.py
```
It listens on `0.0.0.0:5001` by default.

### 2. Start the Sender
The sender connects to the receiver and sends a specified amount of random data.

```bash
python sender.py <TARGET_IP> [--port PORT] [--size SIZE_MB]
```

**Arguments:**
- `ip`: The IP address of the receiver (e.g., `127.0.0.1` for local testing).
- `--port`: The port to connect to (default: 5001).
- `--size`: The amount of data to send in MB (default: 100).

### Example (Local Test)

**Terminal 1 (Receiver):**
```bash
python receiver.py
```

**Terminal 2 (Sender):**
```bash
python sender.py 127.0.0.1 --size 500
```
This will send 500MB of data to localhost and print real-time statistics on both ends.
