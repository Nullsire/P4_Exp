import subprocess
import argparse
import sys

def run_iperf_server(port, one_off=False):
    """
    Runs iperf3 server.
    """
    cmd = ['iperf3', '-s', '-p', str(port)]
    
    if one_off:
        cmd.append('-1')

    print(f"[*] Starting iperf3 server on port {port}...")
    print(f"[*] Command: {' '.join(cmd)}")
    
    try:
        # We don't capture output here, we let it stream to stdout so the user can see it.
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running iperf3 server: {e}")
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
    except FileNotFoundError:
        print("[!] iperf3 not found. Please install it (e.g., 'sudo apt install iperf3').")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Traffic Receiver (Wrapper around iperf3)")
    parser.add_argument('--port', type=int, default=5001, help='Listen port')
    parser.add_argument('--one-off', action='store_true', help='Exit after one connection')
    
    args = parser.parse_args()
    
    run_iperf_server(args.port, args.one_off)

if __name__ == "__main__":
    main()
