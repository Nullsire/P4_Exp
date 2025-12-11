import subprocess
import argparse
import json
import sys
import time

def run_iperf_client(target_ip, port, duration, bandwidth, congestion, parallel, reverse=False):
    """
    Runs iperf3 client (TCP only) and returns the parsed JSON result.
    """
    cmd = ['iperf3', '-c', target_ip, '-p', str(port), '-t', str(duration), '-J']
    
    # TCP Options
    if congestion:
        cmd.extend(['-C', congestion])
    if bandwidth:
        # iperf3 supports pacing for TCP via -b
        cmd.extend(['-b', bandwidth])
    if parallel > 1:
        cmd.extend(['-P', str(parallel)])
            
    if reverse:
        cmd.append('-R')

    print(f"[*] Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running iperf3: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"[!] Error parsing iperf3 JSON output.")
        return None
    except FileNotFoundError:
        print("[!] iperf3 not found. Please install it (e.g., 'sudo apt install iperf3').")
        sys.exit(1)

def print_tcp_stats(data):
    try:
        end = data['end']
        sum_sent = end['sum_sent']
        sum_recv = end['sum_received']
        
        print("\n" + "="*40)
        print("       TCP TRAFFIC REPORT       ")
        print("="*40)
        print(f"Duration:      {sum_sent['seconds']:.2f} s")
        print(f"Data Sent:     {sum_sent['bytes'] / (1024*1024):.2f} MB")
        print(f"Throughput:    {sum_sent['bits_per_second'] / 1e6:.2f} Mbps")
        print(f"Retransmits:   {sum_sent['retransmits']}")
        
        # RTT and CWND are usually in the streams list
        streams = end['streams']
        if streams:
            sender_stream = streams[0]['sender']
            print(f"Max RTT:       {sender_stream['max_rtt'] / 1000:.2f} ms")
            print(f"Mean RTT:      {sender_stream['mean_rtt'] / 1000:.2f} ms")
            
        print("="*40)
    except KeyError as e:
        print(f"[!] Error parsing TCP stats: Missing key {e}")

def main():
    parser = argparse.ArgumentParser(description="Traffic Generator (TCP Only)")
    parser.add_argument('--target', required=True, help='Target IP address')
    parser.add_argument('--port', type=int, default=5001, help='Target port')
    parser.add_argument('--duration', type=int, default=10, help='Duration in seconds')
    parser.add_argument('--bandwidth', help='Target bandwidth per stream (e.g., 10M). Total bandwidth = bandwidth * parallel.')
    parser.add_argument('--congestion', default='cubic', help='TCP congestion control algorithm (e.g., cubic, bbr)')
    parser.add_argument('--parallel', type=int, default=1, help='Number of parallel streams')
    parser.add_argument('--reverse', action='store_true', help='Run in reverse mode (Server sends, Client receives)')
    
    args = parser.parse_args()
    
    print(f"[*] Starting TCP traffic to {args.target}:{args.port} (Streams: {args.parallel})...")
    
    data = run_iperf_client(
        args.target, 
        args.port, 
        args.duration, 
        args.bandwidth, 
        args.congestion,
        args.parallel,
        args.reverse
    )
    
    if data:
        print_tcp_stats(data)

if __name__ == "__main__":
    main()

