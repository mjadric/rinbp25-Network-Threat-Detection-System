import os
import logging
import json
import random
import time
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

# Simulated data storage
packet_store = []
network_nodes = []
network_links = []

# Simulation helper
is_under_attack = False
attack_start_time = None
attack_duration = 0

def init_mongo_db():
    """Initialize simulated MongoDB"""
    logger.info("Using simulated MongoDB for packet storage")
    return True

def init_neo4j_db():
    """Initialize simulated Neo4j graph database"""
    logger.info("Using simulated Neo4j for network graph")
    return True

def store_packet_mongodb(packet):
    """Store a network packet in simulated MongoDB"""
    global packet_store
    
    # Add timestamp if not present
    if "timestamp" not in packet:
        packet["timestamp"] = datetime.now().isoformat()
    
    # Store packet in memory
    packet_store.append(packet)
    
    # Limit the size of our in-memory store
    if len(packet_store) > 5000:
        packet_store = packet_store[-5000:]
    
    return True

def get_recent_packets(limit=100, attack_only=False):
    """Get recent packets from simulated MongoDB"""
    global packet_store
    
    # If we have no packets, generate some simulated ones
    if not packet_store:
        generate_simulated_packets(100)
    
    # Filter by attack if needed
    if attack_only:
        filtered_packets = [p for p in packet_store if p.get("is_attack", False)]
    else:
        filtered_packets = packet_store.copy()
    
    # Sort by timestamp (newest first) and limit
    sorted_packets = sorted(filtered_packets, 
                            key=lambda p: p.get("timestamp", ""), 
                            reverse=True)
    
    return sorted_packets[:limit]

def get_traffic_stats(minutes=10):
    """Get traffic statistics from simulated MongoDB"""
    global packet_store
    
    # If we have no packets, generate some simulated ones
    if not packet_store:
        generate_simulated_packets(100)
    
    # Calculate time threshold
    time_threshold = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    
    # Filter by time
    recent_packets = [p for p in packet_store if p.get("timestamp", "") >= time_threshold]
    
    # Count attacks
    attack_packets = [p for p in recent_packets if p.get("is_attack", False)]
    total_count = len(recent_packets)
    attack_count = len(attack_packets)
    
    # Calculate protocol distribution
    protocols = {}
    for packet in recent_packets:
        protocol = packet.get("protocol", "Other")
        protocols[protocol] = protocols.get(protocol, 0) + 1
    
    protocol_dist = [{"_id": proto, "count": count} for proto, count in protocols.items()]
    protocol_dist = sorted(protocol_dist, key=lambda x: x["count"], reverse=True)
    
    # Count source IPs
    source_ips = {}
    for packet in recent_packets:
        source_ip = packet.get("source_ip", "unknown")
        source_ips[source_ip] = source_ips.get(source_ip, 0) + 1
    
    top_sources = [{"_id": ip, "count": count} for ip, count in source_ips.items()]
    top_sources = sorted(top_sources, key=lambda x: x["count"], reverse=True)[:10]
    
    # Count destination IPs
    dest_ips = {}
    for packet in recent_packets:
        dest_ip = packet.get("destination_ip", "unknown")
        dest_ips[dest_ip] = dest_ips.get(dest_ip, 0) + 1
    
    top_destinations = [{"_id": ip, "count": count} for ip, count in dest_ips.items()]
    top_destinations = sorted(top_destinations, key=lambda x: x["count"], reverse=True)[:10]
    
    return {
        "total_packets": total_count,
        "attack_packets": attack_count,
        "attack_percentage": (attack_count / total_count * 100) if total_count > 0 else 0,
        "protocol_distribution": protocol_dist,
        "top_sources": top_sources,
        "top_destinations": top_destinations
    }

def update_network_graph(node, connections):
    """Update the network graph in simulated Neo4j"""
    global network_nodes, network_links
    
    # Add or update node
    node_exists = False
    for i, existing_node in enumerate(network_nodes):
        if existing_node["id"] == node["id"]:
            network_nodes[i] = node
            node_exists = True
            break
    
    if not node_exists:
        network_nodes.append(node)
    
    # Add connections
    for connected_id in connections:
        # Check if connection already exists
        connection_exists = False
        for link in network_links:
            if (link["source"] == node["id"] and link["target"] == connected_id) or \
               (link["source"] == connected_id and link["target"] == node["id"]):
                connection_exists = True
                break
        
        if not connection_exists:
            network_links.append({
                "source": node["id"],
                "target": connected_id,
                "is_attack_path": False
            })
    
    return True

def get_network_graph():
    """Get the entire network graph from simulated Neo4j"""
    global network_nodes, network_links
    
    # If we have no network data, generate a simulated network
    if not network_nodes:
        generate_simulated_network()
    
    # Check for attacks and update attack paths
    update_attack_paths()
    
    return {
        "nodes": network_nodes,
        "links": network_links
    }

def get_attack_paths():
    """Get attack paths from simulated Neo4j"""
    global network_nodes, network_links, is_under_attack
    
    # If we have no network data, generate a simulated network
    if not network_nodes:
        generate_simulated_network()
    
    # If no attack is happening, return empty paths
    if not is_under_attack:
        return []
    
    # Find attackers and victims
    attackers = [node["id"] for node in network_nodes if node.get("is_attacker", False)]
    victims = [node["id"] for node in network_nodes if node.get("is_victim", False)]
    
    # If no attackers or victims, return empty paths
    if not attackers or not victims:
        return []
    
    # For each attacker-victim pair, create a path
    paths = []
    for attacker in attackers:
        for victim in victims:
            # Simple path generation - in a real system, this would use graph algorithms
            # For simulation, we'll create a direct path through a router
            router_nodes = [node["id"] for node in network_nodes if node.get("type") == "router"]
            
            if router_nodes:
                router = random.choice(router_nodes)
                path = [attacker, router, victim]
                path_length = len(path) - 1
            else:
                # Direct path if no routers
                path = [attacker, victim]
                path_length = 1
            
            paths.append({
                "attacker": attacker,
                "victim": victim,
                "path": path,
                "length": path_length
            })
    
    return paths

# ----- Simulation helper functions -----

def generate_simulated_packets(count=100):
    """Generate simulated network packets for demonstration"""
    global packet_store, is_under_attack
    
    protocols = ["TCP", "UDP", "HTTP", "ICMP"]
    flags = ["SYN", "ACK", "FIN", "RST", "PSH"]
    
    # Generate IP addresses
    source_ips = [f"192.168.1.{i}" for i in range(1, 20)]
    dest_ips = [f"10.0.0.{i}" for i in range(1, 10)]
    
    # Add some external IPs for attackers
    attacker_ips = [f"77.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}" 
                    for _ in range(5)]
    
    # Check if we should simulate an attack
    if random.random() < 0.3:  # 30% chance of attack
        is_under_attack = True
        attack_source_ips = random.sample(attacker_ips, min(3, len(attacker_ips)))
        attack_dest_ip = random.choice(dest_ips)
    else:
        is_under_attack = False
        attack_source_ips = []
        attack_dest_ip = None
    
    # Generate packets
    for i in range(count):
        timestamp = (datetime.now() - timedelta(seconds=random.randint(0, 600))).isoformat()
        
        # Determine if this is an attack packet
        is_attack = False
        attack_type = None
        
        if is_under_attack and random.random() < 0.4:  # 40% of packets during attack are attack packets
            is_attack = True
            attack_type = "DDoS"
            source_ip = random.choice(attack_source_ips)
            dest_ip = attack_dest_ip
            protocol = "TCP" if random.random() < 0.8 else "UDP"  # Mostly TCP for attacks
            flag = "SYN" if protocol == "TCP" else None  # SYN flood
        else:
            source_ip = random.choice(source_ips)
            dest_ip = random.choice(dest_ips)
            protocol = random.choice(protocols)
            flag = random.choice(flags) if protocol == "TCP" else None
        
        # Generate packet
        packet = {
            "timestamp": timestamp,
            "source_ip": source_ip,
            "source_port": random.randint(1024, 65535),
            "destination_ip": dest_ip,
            "destination_port": random.choice([80, 443, 22, 25, 53, 8080]),
            "protocol": protocol,
            "length": random.randint(64, 1500),
            "is_attack": is_attack
        }
        
        if flag and protocol == "TCP":
            packet["flags"] = flag
            
        if is_attack:
            packet["attack_type"] = attack_type
        
        packet_store.append(packet)
    
    # Sort by timestamp
    packet_store = sorted(packet_store, key=lambda p: p.get("timestamp", ""))

def generate_simulated_network():
    """Generate a simulated network for demonstration"""
    global network_nodes, network_links
    
    # Create nodes
    # Routers
    for i in range(3):
        network_nodes.append({
            "id": f"router{i+1}",
            "ip": f"10.0.0.{i+1}",
            "type": "router",
            "is_attacker": False,
            "is_victim": False
        })
    
    # Servers
    for i in range(2):
        network_nodes.append({
            "id": f"server{i+1}",
            "ip": f"10.0.1.{i+1}",
            "type": "server",
            "is_attacker": False,
            "is_victim": i == 0  # Mark first server as victim
        })
    
    # Hosts
    for i in range(15):
        is_attacker = i < 3  # First 3 hosts are attackers
        network_nodes.append({
            "id": f"host{i+1}",
            "ip": f"192.168.1.{i+1}",
            "type": "host",
            "is_attacker": is_attacker,
            "is_victim": False
        })
    
    # Create connections
    # Connect hosts to routers
    for i in range(15):
        router_id = f"router{(i % 3) + 1}"
        network_links.append({
            "source": f"host{i+1}",
            "target": router_id,
            "is_attack_path": False
        })
    
    # Connect routers to each other
    for i in range(3):
        for j in range(i+1, 3):
            network_links.append({
                "source": f"router{i+1}",
                "target": f"router{j+1}",
                "is_attack_path": False
            })
    
    # Connect servers to routers
    for i in range(2):
        router_id = f"router{(i % 3) + 1}"
        network_links.append({
            "source": f"server{i+1}",
            "target": router_id,
            "is_attack_path": False
        })

def update_attack_paths():
    """Update attack paths in the network graph based on current state"""
    global network_links, is_under_attack
    
    # Reset all attack paths
    for link in network_links:
        link["is_attack_path"] = False
    
    # If there's no attack, we're done
    if not is_under_attack:
        return
    
    # Find attackers and victims
    attackers = [node["id"] for node in network_nodes if node.get("is_attacker", False)]
    victims = [node["id"] for node in network_nodes if node.get("is_victim", False)]
    
    # For each attacker-victim pair, mark the path
    for attacker in attackers:
        for victim in victims:
            # Find a router that connects to both
            attacker_routers = []
            victim_routers = []
            
            for link in network_links:
                if link["source"] == attacker and "router" in link["target"]:
                    attacker_routers.append(link["target"])
                elif link["target"] == attacker and "router" in link["source"]:
                    attacker_routers.append(link["source"])
                
                if link["source"] == victim and "router" in link["target"]:
                    victim_routers.append(link["target"])
                elif link["target"] == victim and "router" in link["source"]:
                    victim_routers.append(link["source"])
            
            # Find common routers or connected routers
            common_routers = list(set(attacker_routers) & set(victim_routers))
            
            if common_routers:
                # Direct path through common router
                router = common_routers[0]
                
                # Mark attacker to router
                for link in network_links:
                    if (link["source"] == attacker and link["target"] == router) or \
                       (link["source"] == router and link["target"] == attacker):
                        link["is_attack_path"] = True
                
                # Mark router to victim
                for link in network_links:
                    if (link["source"] == victim and link["target"] == router) or \
                       (link["source"] == router and link["target"] == victim):
                        link["is_attack_path"] = True
            else:
                # No common router, find a path through connected routers
                if attacker_routers and victim_routers:
                    router1 = attacker_routers[0]
                    router2 = victim_routers[0]
                    
                    # Mark attacker to router1
                    for link in network_links:
                        if (link["source"] == attacker and link["target"] == router1) or \
                           (link["source"] == router1 and link["target"] == attacker):
                            link["is_attack_path"] = True
                    
                    # Mark router1 to router2
                    for link in network_links:
                        if (link["source"] == router1 and link["target"] == router2) or \
                           (link["source"] == router2 and link["target"] == router1):
                            link["is_attack_path"] = True
                    
                    # Mark router2 to victim
                    for link in network_links:
                        if (link["source"] == victim and link["target"] == router2) or \
                           (link["source"] == router2 and link["target"] == victim):
                            link["is_attack_path"] = True
