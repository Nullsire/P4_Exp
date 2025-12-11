import subprocess
import time
import re
import argparse
import sys
import select

def get_qdisc_stats(interface):
    """
    Runs 'tc -s qdisc show dev <interface>' and parses the output.
    """
    try:
        result = subprocess.run(['tc', '-s', 'qdisc', 'show', 'dev', interface], 
                                capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        return None

def parse_stats(output):
    """
    Parses the tc output to extract backlog, drops, and requeues.
    """
    stats = {
        'dropped': 0,
        'backlog_pkts': 0,
        'backlog_bytes': 0
    }
    
    # Regex for dropped
    drop_match = re.search(r'dropped\s+(\d+)', output)
    if drop_match:
        stats['dropped'] = int(drop_match.group(1))
        
    # Regex for backlog
    backlog_match = re.search(r'backlog\s+(\d+)b\s+(\d+)p', output)
    if backlog_match:
        stats['backlog_bytes'] = int(backlog_match.group(1))
        stats['backlog_pkts'] = int(backlog_match.group(2))
        
    return stats

def main():
    parser = argparse.ArgumentParser(description="Monitor TC Queue Stats")
    parser.add_argument('--interface', required=True, help='Interface to monitor (e.g., veth_rr)')
    parser.add_argument('--interval', type=float, default=0.5, help='Refresh interval in seconds')
    
    args = parser.parse_args()
    
    print(f"[*] Monitoring queue on {args.interface}")
    print("[*] Type 'clear' and press Enter to reset drop counter.")
    print("[*] Press Ctrl+C to stop.")
    print("-" * 55)
    print(f"{'Time':<10} | {'Queue Depth (pkts)':<20} | {'Drops (Session)':<15}")
    print("-" * 55)
    # Print initial empty stats line to reserve space, then newline so cursor is below it
    print(f"{'--:--:--':<10} | {'0':<20} | {'0':<15}")
    
    # Initialize drop_offset with the current total drops from TC
    # This ensures we start counting from 0 for this session
    initial_output = get_qdisc_stats(args.interface)
    initial_stats = parse_stats(initial_output) if initial_output else {'dropped': 0}
    drop_offset = initial_stats['dropped']
    
    current_stats = {'dropped': 0}
    
    try:
        while True:
            # Check for user input (non-blocking)
            # select.select works on Unix-like systems (including WSL)
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if line:
                    cmd = line.strip().lower()
                    if cmd == 'clear':
                        # Reset offset to current total drops
                        drop_offset = current_stats['dropped']
                        # We need to reprint the header because the user's input (and our print) scrolled the screen
                        # But to keep it simple, we just acknowledge on the input line
                        # Actually, if we print, we scroll. Let's just update the stats line.
                        # But the user wants to see "Drop counter reset".
                        # Let's print that on the input line, then a new input line?
                        # No, let's just reset and let the stats update show 0.
                        pass

            # Update stats
            output = get_qdisc_stats(args.interface)
            if output:
                stats = parse_stats(output)
                current_stats = stats
                
                display_drops = stats['dropped'] - drop_offset
                current_time = time.strftime("%H:%M:%S")
                stats_line = f"{current_time:<10} | {stats['backlog_pkts']:<20} | {display_drops:<15}"
                
                # \0337: Save cursor position
                # \033[1A: Move up 1 line
                # \r: Move to start of line
                # stats_line: Print stats
                # \033[K: Clear rest of line
                # \0338: Restore cursor position
                sys.stdout.write(f"\0337\033[1A\r{stats_line}\033[K\0338")
                sys.stdout.flush()
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n[*] Stopped.")

if __name__ == "__main__":
    main()
