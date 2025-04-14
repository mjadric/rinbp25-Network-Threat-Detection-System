import os
import time
import logging
import threading
import json
import numpy as np
from datetime import datetime
from database_handlers import get_recent_packets, get_traffic_stats
from models import NetworkStats, AttackEvent
from dqn_model import dqn_agent

# Setup logging
logger = logging.getLogger(__name__)

# Detector configuration
class AttackDetectorConfig:
    def __init__(self):
        # Detection thresholds
        self.packet_rate_threshold = 500  # packets per second
        self.connection_threshold = 200   # simultaneous connections
        self.syn_ratio_threshold = 0.8    # SYN to total packet ratio
        self.entropy_threshold = 5.0      # Source IP entropy threshold
        
        # DQN parameters
        self.detection_interval = 2.0     # seconds between detection runs
        self.reward_decay = 0.95          # reward decay factor
        self.training_interval = 10       # how often to train (in detection cycles)
        
        # Detector state
        self.is_attack_ongoing = False
        self.current_action = 0           # 0: no action, 1: rate limit, 2: block IPs, 3: challenge
        self.current_attack_event_id = None
        self.cycle_count = 0
        self.last_metrics = {}
        self.metrics_history = []

# Global detector configuration
detector_config = AttackDetectorConfig()

def calculate_entropy(ip_counts):
    """Calculate Shannon entropy of IP distribution"""
    if not ip_counts:
        return 0
    
    total = sum(ip_counts.values())
    probabilities = [count / total for count in ip_counts.values()]
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    return entropy

def extract_network_metrics():
    """Extract metrics from network traffic for attack detection"""
    # Get recent packets from MongoDB (simulated)
    recent_packets = get_recent_packets(limit=1000)
    
    if not recent_packets:
        return {
            "packet_rate": 0,
            "bandwidth_usage": 0,
            "connection_count": 0,
            "syn_ratio": 0,
            "udp_ratio": 0,
            "avg_packet_size": 0,
            "source_ip_entropy": 0,
            "dst_port_entropy": 0,
            "is_attack": False,
            "attack_intensity": 0
        }
    
    # Get the latest network stats (from in-memory storage)
    latest_stats = NetworkStats.get_latest_stats()
    
    # Calculate metrics
    # Count occurrences of each source IP and destination port
    source_ips = {}
    destination_ports = {}
    protocols = {"TCP": 0, "UDP": 0, "HTTP": 0, "ICMP": 0, "Other": 0}
    flags = {"SYN": 0, "ACK": 0, "FIN": 0, "RST": 0, "Other": 0}
    total_size = 0
    attack_packets = 0
    
    for packet in recent_packets:
        # Count source IPs
        src_ip = packet.get("source_ip", "unknown")
        source_ips[src_ip] = source_ips.get(src_ip, 0) + 1
        
        # Count destination ports
        dst_port = packet.get("destination_port", 0)
        destination_ports[dst_port] = destination_ports.get(dst_port, 0) + 1
        
        # Count protocols
        protocol = packet.get("protocol", "Other")
        if protocol in protocols:
            protocols[protocol] += 1
        else:
            protocols["Other"] += 1
        
        # Count TCP flags
        if protocol == "TCP":
            flag = packet.get("flags", "Other")
            if flag in flags:
                flags[flag] += 1
            else:
                flags["Other"] += 1
        
        # Sum packet sizes
        total_size += packet.get("length", 0)
        
        # Count attack packets
        if packet.get("is_attack", False):
            attack_packets += 1
    
    # Calculate metrics
    total_packets = len(recent_packets)
    
    # Calculate entropy values
    source_ip_entropy = calculate_entropy(source_ips)
    dst_port_entropy = calculate_entropy(destination_ports)
    
    # Calculate protocol ratios
    tcp_count = protocols.get("TCP", 0)
    udp_count = protocols.get("UDP", 0)
    syn_count = flags.get("SYN", 0)
    
    syn_ratio = syn_count / tcp_count if tcp_count > 0 else 0
    udp_ratio = udp_count / total_packets if total_packets > 0 else 0
    
    # Get packet rate and bandwidth from latest stats
    packet_rate = latest_stats.total_packets if latest_stats else 0
    bandwidth_usage = latest_stats.total_bandwidth if latest_stats else 0
    connection_count = latest_stats.connection_count if latest_stats else 0
    
    # Determine if there's an attack (ground truth from simulation)
    is_attack = latest_stats.is_under_attack if latest_stats else False
    
    # Calculate attack intensity based on metrics
    attack_indicators = [
        packet_rate / detector_config.packet_rate_threshold if packet_rate > 0 else 0,
        connection_count / detector_config.connection_threshold if connection_count > 0 else 0,
        syn_ratio / detector_config.syn_ratio_threshold if syn_ratio > 0 else 0,
        source_ip_entropy / detector_config.entropy_threshold if source_ip_entropy > 0 else 0
    ]
    attack_intensity = sum(attack_indicators) / len(attack_indicators)
    attack_intensity = min(1.0, attack_intensity)  # Cap at 1.0
    
    # Compile metrics
    metrics = {
        "packet_rate": packet_rate,
        "bandwidth_usage": bandwidth_usage,
        "connection_count": connection_count,
        "syn_ratio": syn_ratio,
        "udp_ratio": udp_ratio,
        "avg_packet_size": total_size / total_packets if total_packets > 0 else 0,
        "source_ip_entropy": source_ip_entropy,
        "dst_port_entropy": dst_port_entropy,
        "is_attack": is_attack,
        "attack_intensity": attack_intensity,
        "attack_packets": attack_packets,
        "total_packets": total_packets,
        "unique_src_ips": len(source_ips),
        "unique_dst_ports": len(destination_ports)
    }
    
    return metrics

def apply_defense_action(action_idx, metrics):
    """Apply the selected defense action"""
    action_name = dqn_agent.get_action_description(action_idx)
    
    if action_idx == 0:  # No action
        logger.info("Defense: No action taken")
        return "No defense action taken"
    
    elif action_idx == 1:  # Rate limiting
        logger.info("Defense: Applied rate limiting")
        # In a real system, this would apply rate limiting to incoming traffic
        return "Applied rate limiting to incoming traffic"
    
    elif action_idx == 2:  # Block suspicious IPs
        logger.info("Defense: Blocking suspicious IPs")
        # In a real system, this would block IPs with suspicious behavior
        return "Blocked suspicious IP addresses"
    
    elif action_idx == 3:  # Challenge-response
        logger.info("Defense: Activated challenge-response mechanism")
        # In a real system, this would enable CAPTCHA or similar challenge
        return "Activated challenge-response mechanism"
    
    return f"Unknown action: {action_idx}"

def update_attack_event(metrics, action):
    """Update or create an attack event in the database"""
    global detector_config
    
    is_attack = metrics.get("is_attack", False)
    
    if is_attack and not detector_config.is_attack_ongoing:
        # Start of a new attack
        detector_config.is_attack_ongoing = True
        
        # Create a new attack event (in-memory)
        attack_event = AttackEvent(
            start_time=datetime.now(),
            attack_type="DDoS",
            severity=int(metrics.get("attack_intensity", 0) * 10),
            mitigation_applied=action > 0,
            mitigation_action=dqn_agent.get_action_description(action)
        )
        
        detector_config.current_attack_event_id = attack_event.id
        logger.info(f"New attack detected, created event ID {attack_event.id}")
        
    elif is_attack and detector_config.is_attack_ongoing:
        # Update existing attack
        if detector_config.current_attack_event_id:
            # Find the attack event in memory
            active_attacks = AttackEvent.get_active_attacks()
            attack_event = next((a for a in active_attacks if a.id == detector_config.current_attack_event_id), None)
            
            if attack_event:
                attack_event.severity = max(attack_event.severity, int(metrics.get("attack_intensity", 0) * 10))
                attack_event.packet_count += metrics.get("attack_packets", 0)
                
                if action > 0:
                    attack_event.mitigation_applied = True
                    attack_event.mitigation_action = dqn_agent.get_action_description(action)
            
    elif not is_attack and detector_config.is_attack_ongoing:
        # End of attack
        if detector_config.current_attack_event_id:
            # Find the attack event in memory
            active_attacks = AttackEvent.get_active_attacks()
            attack_event = next((a for a in active_attacks if a.id == detector_config.current_attack_event_id), None)
            
            if attack_event:
                attack_event.end_time = datetime.now()
                logger.info(f"Attack ended, updated event ID {attack_event.id}")
        
        detector_config.is_attack_ongoing = False
        detector_config.current_attack_event_id = None
        detector_config.current_action = 0

def detector_thread_function():
    """Main attack detector thread function"""
    from app import app
    
    # Create application context for the entire thread
    with app.app_context():
        logger.info("Starting attack detector")
        
        while True:
            try:
                # Increment cycle count
                detector_config.cycle_count += 1
                
                # Extract metrics from network traffic
                metrics = extract_network_metrics()
                
                # Save metrics for history
                detector_config.metrics_history.append(metrics)
                if len(detector_config.metrics_history) > 100:
                    detector_config.metrics_history.pop(0)
                    
                # Preprocess state for DQN
                current_state = dqn_agent.preprocess_state(metrics)
                
                # Get action from DQN agent
                action = dqn_agent.act(current_state)
                
                # Apply defense action
                result = apply_defense_action(action, metrics)
                
                # Update attack event in database
                update_attack_event(metrics, action)
                
                # Check if we have a previous state to learn from
                if detector_config.last_metrics:
                    # Calculate reward
                    reward = dqn_agent.calculate_reward(metrics, detector_config.current_action)
                    
                    # Store experience in DQN replay memory
                    last_state = dqn_agent.preprocess_state(detector_config.last_metrics)
                    done = not metrics.get("is_attack", False)
                    dqn_agent.remember(last_state, detector_config.current_action, reward, current_state, done)
                    
                    # Add reward to history
                    dqn_agent.reward_history.append(reward)
                
                # Update state for next iteration
                detector_config.last_metrics = metrics
                detector_config.current_action = action
                
                # Train the model periodically
                if detector_config.cycle_count % detector_config.training_interval == 0:
                    loss = dqn_agent.replay()
                    if loss is not None:
                        logger.debug(f"DQN training - loss: {loss:.4f}, epsilon: {dqn_agent.epsilon:.4f}")
                    
                    # Update target model occasionally
                    if detector_config.cycle_count % (detector_config.training_interval * 10) == 0:
                        dqn_agent.update_target_model()
                        logger.debug("Updated DQN target model")
                
                # Sleep until next detection cycle
                time.sleep(detector_config.detection_interval)
                
            except Exception as e:
                logger.error(f"Error in attack detector thread: {e}")
                time.sleep(1)

def start_monitoring():
    """Start the attack monitoring in a background thread"""
    detector_thread = threading.Thread(target=detector_thread_function)
    detector_thread.daemon = True
    detector_thread.start()
    logger.info("Attack detector thread started")
    return detector_thread
