#!/bin/bash

# ==========================================
# Traffic Congestion Experiment Setup Script (Router Topology)
# ==========================================
# Topology:
# [Sender] --(veth_s/veth_rs)-- [Router] --(veth_rr/veth_r)-- [Receiver]
#
# IPs:
# Sender:   10.0.1.1/24 (GW: 10.0.1.2)
# Router:   10.0.1.2/24 (Left), 10.0.2.1/24 (Right)
# Receiver: 10.0.2.2/24 (GW: 10.0.2.1)
# ==========================================

# 0. Check dependencies
if ! command -v iperf3 &> /dev/null; then
    echo "[!] Error: iperf3 is not installed."
    echo "    Please install it using: sudo apt update && sudo apt install -y iperf3"
    exit 1
fi

# 1. Cleanup previous setup
echo "[*] Cleaning up previous namespaces..."
sudo ip netns del ns_sender 2>/dev/null
sudo ip netns del ns_receiver 2>/dev/null
sudo ip netns del ns_router 2>/dev/null

# 2. Create Namespaces
echo "[*] Creating network namespaces..."
sudo ip netns add ns_sender
sudo ip netns add ns_router
sudo ip netns add ns_receiver

# 3. Create veth pairs
echo "[*] Creating veth pairs..."
# Link 1: Sender <-> Router
sudo ip link add veth_s type veth peer name veth_rs
# Link 2: Router <-> Receiver
sudo ip link add veth_rr type veth peer name veth_r

# 4. Assign interfaces to namespaces
echo "[*] Assigning interfaces..."
sudo ip link set veth_s netns ns_sender
sudo ip link set veth_rs netns ns_router
sudo ip link set veth_rr netns ns_router
sudo ip link set veth_r netns ns_receiver

# 5. Configure IPs and Routes
echo "[*] Configuring IPs and Routes..."

# --- Sender ---
sudo ip netns exec ns_sender ip addr add 10.0.1.1/24 dev veth_s
sudo ip netns exec ns_sender ip link set veth_s up
sudo ip netns exec ns_sender ip link set lo up
sudo ip netns exec ns_sender ip route add default via 10.0.1.2

# --- Router ---
sudo ip netns exec ns_router ip addr add 10.0.1.2/24 dev veth_rs
sudo ip netns exec ns_router ip addr add 10.0.2.1/24 dev veth_rr
sudo ip netns exec ns_router ip link set veth_rs up
sudo ip netns exec ns_router ip link set veth_rr up
sudo ip netns exec ns_router ip link set lo up
# Enable IP Forwarding
sudo ip netns exec ns_router sysctl -w net.ipv4.ip_forward=1 > /dev/null

# --- Receiver ---
sudo ip netns exec ns_receiver ip addr add 10.0.2.2/24 dev veth_r
sudo ip netns exec ns_receiver ip link set veth_r up
sudo ip netns exec ns_receiver ip link set lo up
sudo ip netns exec ns_receiver ip route add default via 10.0.2.1

# 6. Disable TSO/GSO (Important for accurate TC simulation)
echo "[*] Disabling TSO/GSO..."
sudo ip netns exec ns_sender ethtool -K veth_s tso off gso off
sudo ip netns exec ns_router ethtool -K veth_rs tso off gso off
sudo ip netns exec ns_router ethtool -K veth_rr tso off gso off
sudo ip netns exec ns_receiver ethtool -K veth_r tso off gso off

# 7. Apply Traffic Control (TC) on Router -> Receiver interface
# This simulates the bottleneck link queue.
# Bandwidth: 50Mbps, Delay: 20ms, Queue Limit: 20 packets
echo "[*] Applying TC rules on Router (veth_rr)..."
sudo ip netns exec ns_router tc qdisc add dev veth_rr root netem delay 20ms rate 50mbit limit 20

# 8. Tune TCP Buffers
echo "[*] Tuning TCP buffers..."
sudo ip netns exec ns_sender sysctl -w net.ipv4.tcp_wmem="4096 16384 4194304" > /dev/null
sudo ip netns exec ns_receiver sysctl -w net.ipv4.tcp_rmem="4096 87380 6291456" > /dev/null

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Topology: [Sender 10.0.1.1] <--> [Router] <--> [Receiver 10.0.2.2]"
echo "Bottleneck: Router -> Receiver link (50Mbps, 20pkt queue)"
echo ""
echo "--- Terminal 1: Start Receiver ---"
echo "sudo ip netns exec ns_receiver python3 traffic_tool/receiver.py --port 5001"
echo ""
echo "--- Terminal 2: Monitor Queue (Run in Router NS) ---"
echo "sudo ip netns exec ns_router python3 traffic_tool/monitor_queue.py --interface veth_rr"
echo ""
echo "--- Terminal 3: Start Sender (Single flow) ---"
echo "sudo ip netns exec ns_sender python3 traffic_tool/sender.py --target 10.0.2.2 --congestion cubic"
echo ""
echo "--- Terminal 4: Start Sender (Multiple flows) ---"
echo "sudo ip netns exec ns_sender python3 traffic_tool/sender.py --target 10.0.2.2 --congestion cubic --parallel 5"
echo ""

