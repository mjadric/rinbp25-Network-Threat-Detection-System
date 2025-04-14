import os
import time
import random
import threading
import logging
from datetime import datetime, timedelta
from database_handlers import store_packet_mongodb, update_network_graph
from models import NetworkStats, AttackEvent, NetworkNode, NetworkEdge

# Setup logging
logger = logging.getLogger(__name__)

# Simple simulation configuration
class NetworkSimulationConfig:
    def __init__(self):
        # Simplified settings
        self.is_attack_ongoing = False
        self.attack_start_time = None
        self.attack_end_time = None
        self.total_packets = 0
        self.attack_packets = 0
        self.last_stats_update = datetime.now()
        
        # Generate random MAC addresses for simulation
        def random_mac():
            return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
            
        # Generate random IPs
        def random_ip():
            return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
        
        # Basic network structure
        self.nodes = []
        
        # Add routers
        for i in range(3):
            self.nodes.append({
                "id": f"router{i+1}",
                "ip": f"172.16.0.{i+1}",
                "mac": random_mac(),
                "type": "router",
                "connections": []
            })
        
        # Add servers
        for i in range(2):
            self.nodes.append({
                "id": f"server{i+1}",
                "ip": f"10.0.0.{i+1}",
                "mac": random_mac(),
                "type": "server",
                "connections": [],
                "is_victim": i == 0  # First server is the victim
            })
        
        # Add hosts
        for i in range(15):
            self.nodes.append({
                "id": f"host{i+1}",
                "ip": f"192.168.1.{i+1}",
                "mac": random_mac(),
                "type": "host",
                "connections": [],
                "is_attacker": i < 3  # First 3 hosts are attackers
            })

# Global simulation configuration
sim_config = NetworkSimulationConfig()

def update_network_stats():
    """Update network statistics in the database"""
    try:
        # Generate random network stats
        now = datetime.now()
        is_attack = random.random() < 0.3  # 30% chance of attack
        
        # Create reasonable statistics
        if is_attack:
            bandwidth = random.uniform(50, 200)
            latency = random.uniform(50, 200)
            conn_count = random.randint(200, 500)
            susp_traffic = random.uniform(30, 80)
        else:
            bandwidth = random.uniform(5, 50)
            latency = random.uniform(1, 20)
            conn_count = random.randint(10, 100)
            susp_traffic = random.uniform(0, 10)
        
        # Create network stats entry - this will be stored in-memory
        stats = NetworkStats(
            timestamp=now,
            total_packets=random.randint(500, 5000),
            total_bandwidth=bandwidth,
            average_latency=latency,
            connection_count=conn_count,
            suspicious_traffic_percent=susp_traffic,
            is_under_attack=is_attack
        )
            
        logger.debug(f"Updated network stats: {bandwidth:.2f} Mbps, {susp_traffic:.2f}% suspicious")
        return True
    except Exception as e:
        logger.error(f"Error updating network stats: {e}")
        return False

def generate_simulated_attack_event():
    """Generate a simulated attack event"""
    try:
        # Decide if we'll create a new attack or close an existing one
        now = datetime.now()
        
        # Check for ongoing attacks
        ongoing_attacks = AttackEvent.get_active_attacks()
        
        if ongoing_attacks and random.random() < 0.4:  # 40% chance to end an ongoing attack
            attack = random.choice(ongoing_attacks)
            attack.end_time = now
            attack.packet_count = random.randint(10000, 1000000)
            logger.info(f"Ended attack event {attack.id}")
        elif random.random() < 0.2:  # 20% chance to create a new attack if none ongoing or by chance
            attack_types = ["SYN Flood", "UDP Flood", "HTTP Flood", "ICMP Flood"]
            attack = AttackEvent(
                start_time=now,
                attack_type=random.choice(attack_types),
                severity=random.randint(1, 10),
                source_ips=",".join([f"77.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}" for _ in range(3)]),
                target_ip=f"10.0.0.{random.randint(1, 2)}",
                mitigation_applied=random.random() < 0.7,  # 70% chance of mitigation
                mitigation_action=random.choice(["rate_limit", "block_suspicious_ips", "activate_challenge"])
            )
            logger.info(f"Created new attack event {attack.id}")
                
        return True
    except Exception as e:
        logger.error(f"Error generating attack event: {e}")
        return False

def generate_packets(count=10):
    """Generate simulated network packets"""
    try:
        protocols = ["TCP", "UDP", "HTTP", "ICMP"]
        flags = ["SYN", "ACK", "FIN", "RST", "PSH"]
        
        # Determine if we're under attack
        is_attack = random.random() < 0.3  # 30% chance of attack
        
        for _ in range(count):
            # Decide if this packet is an attack packet
            is_attack_packet = is_attack and random.random() < 0.7  # 70% of packets during attack are attack packets
            
            if is_attack_packet:
                # Generate attack packet
                source_ip = f"77.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                dest_ip = "10.0.0.1"  # Target server
                protocol = "TCP" if random.random() < 0.8 else "UDP"
                flag = "SYN" if protocol == "TCP" else None
                dst_port = 80
            else:
                # Generate normal packet
                source_ip = f"192.168.1.{random.randint(1, 20)}"
                dest_ip = f"10.0.0.{random.randint(1, 2)}"
                protocol = random.choice(protocols)
                flag = random.choice(flags) if protocol == "TCP" else None
                dst_port = random.choice([80, 443, 22, 25, 53, 8080])
            
            # Create packet
            packet = {
                "timestamp": datetime.now().isoformat(),
                "source_ip": source_ip,
                "source_port": random.randint(1024, 65535),
                "destination_ip": dest_ip,
                "destination_port": dst_port,
                "protocol": protocol,
                "length": random.randint(64, 1500),
                "is_attack": is_attack_packet
            }
            
            if flag and protocol == "TCP":
                packet["flags"] = flag
                
            if is_attack_packet:
                packet["attack_type"] = "DDoS"
            
            # Store packet
            store_packet_mongodb(packet)
            
        return True
    except Exception as e:
        logger.error(f"Error generating packets: {e}")
        return False

def simulation_thread():
    """Main simulation thread function"""
    logger.info("Starting simplified network simulation")
    
    stats_timer = datetime.now()
    event_timer = datetime.now()
    packet_timer = datetime.now()
    
    while True:
        try:
            now = datetime.now()
            
            # Update network statistics every 5 seconds
            if (now - stats_timer).total_seconds() >= 5:
                update_network_stats()
                stats_timer = now
            
            # Generate attack events every 20 seconds
            if (now - event_timer).total_seconds() >= 20:
                generate_simulated_attack_event()
                event_timer = now
            
            # Generate packets every second
            if (now - packet_timer).total_seconds() >= 1:
                generate_packets(random.randint(5, 20))
                packet_timer = now
            
            # Sleep to avoid using too much CPU
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in simulation thread: {e}")
            time.sleep(1)

def start_simulation():
    """Start the network simulation in a background thread"""
    sim_thread = threading.Thread(target=simulation_thread)
    sim_thread.daemon = True
    sim_thread.start()
    logger.info("Network simulation thread started")
    return sim_thread