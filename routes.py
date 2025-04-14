import os
import json
from flask import render_template, request, jsonify, Response
import logging
from datetime import datetime, timedelta
from database_handlers import get_recent_packets, get_traffic_stats, get_network_graph, get_attack_paths
from models import NetworkStats, AttackEvent, NetworkNode, NetworkEdge
from dqn_model import dqn_agent

# Setup logging
logger = logging.getLogger(__name__)

def init_routes(app):
    logger.info("Routes initialized")
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/network')
    def network():
        """Network visualization page"""
        return render_template('network.html')
    
    @app.route('/logs')
    def logs():
        """Attack logs page"""
        return render_template('logs.html')
    
    @app.route('/settings')
    def settings():
        """Settings page"""
        return render_template('settings.html')
    
    @app.route('/api/stats')
    def get_stats():
        """Get the current network statistics"""
        try:
            # Get latest network stats using our in-memory model
            latest_stats = NetworkStats.get_latest_stats()
            
            # Get historical stats for graphing
            historical_stats = NetworkStats.get_historical_stats(limit=60)
            
            # Format the data
            if latest_stats:
                latest = {
                    "timestamp": latest_stats.timestamp.isoformat(),
                    "total_packets": latest_stats.total_packets,
                    "total_bandwidth": latest_stats.total_bandwidth,
                    "average_latency": latest_stats.average_latency,
                    "connection_count": latest_stats.connection_count,
                    "suspicious_traffic_percent": latest_stats.suspicious_traffic_percent,
                    "is_under_attack": latest_stats.is_under_attack
                }
            else:
                latest = {
                    "timestamp": datetime.now().isoformat(),
                    "total_packets": 0,
                    "total_bandwidth": 0,
                    "average_latency": 0,
                    "connection_count": 0,
                    "suspicious_traffic_percent": 0,
                    "is_under_attack": False
                }
            
            historical = [{
                "timestamp": stat.timestamp.isoformat(),
                "total_bandwidth": stat.total_bandwidth,
                "suspicious_traffic_percent": stat.suspicious_traffic_percent,
                "is_under_attack": stat.is_under_attack
            } for stat in historical_stats]
            
            # Get active attacks
            active_attacks = AttackEvent.get_active_attacks()
            
            active = [{
                "id": attack.id,
                "start_time": attack.start_time.isoformat(),
                "attack_type": attack.attack_type,
                "severity": attack.severity,
                "mitigation_applied": attack.mitigation_applied,
                "mitigation_action": attack.mitigation_action
            } for attack in active_attacks]
            
            return jsonify({
                "latest": latest,
                "historical": historical,
                "active_attacks": active
            })
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/traffic')
    def get_traffic():
        """Get traffic data from MongoDB"""
        try:
            minutes = int(request.args.get('minutes', 10))
            traffic_data = get_traffic_stats(minutes=minutes)
            return jsonify(traffic_data)
        except Exception as e:
            logger.error(f"Error getting traffic data: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/packets')
    def get_packets():
        """Get recent packets"""
        try:
            limit = int(request.args.get('limit', 100))
            attack_only = request.args.get('attack_only', 'false').lower() == 'true'
            
            packets = get_recent_packets(limit=limit, attack_only=attack_only)
            return jsonify(packets)
        except Exception as e:
            logger.error(f"Error getting packets: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/network')
    def get_network():
        """Get network graph data"""
        try:
            graph = get_network_graph()
            return jsonify(graph)
        except Exception as e:
            logger.error(f"Error getting network graph: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/attack_paths')
    def get_paths():
        """Get attack paths from Neo4j"""
        try:
            paths = get_attack_paths()
            return jsonify(paths)
        except Exception as e:
            logger.error(f"Error getting attack paths: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/attacks')
    def get_attacks():
        """Get attack events"""
        try:
            # Get recent attacks from our in-memory model
            recent_attacks = AttackEvent.get_recent_attacks(limit=50)
            
            attacks = [{
                "id": attack.id,
                "start_time": attack.start_time.isoformat(),
                "end_time": attack.end_time.isoformat() if attack.end_time else None,
                "attack_type": attack.attack_type,
                "severity": attack.severity,
                "source_ips": attack.source_ips,
                "target_ip": attack.target_ip,
                "packet_count": attack.packet_count,
                "mitigation_applied": attack.mitigation_applied,
                "mitigation_action": attack.mitigation_action,
                "is_active": attack.end_time is None
            } for attack in recent_attacks]
            
            return jsonify(attacks)
        except Exception as e:
            logger.error(f"Error getting attack events: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/model')
    def get_model():
        """Get DQN model information"""
        try:
            # Get training statistics
            training_stats = dqn_agent.get_training_stats()
            
            return jsonify({
                "actions": dqn_agent.actions,
                "epsilon": dqn_agent.epsilon,
                "memory_size": len(dqn_agent.memory),
                "average_loss": float(training_stats["average_loss"]) if training_stats["average_loss"] is not None else None,
                "average_reward": float(training_stats["average_reward"]) if training_stats["average_reward"] is not None else None,
                "last_training": training_stats["last_training"].isoformat() if training_stats["last_training"] else None
            })
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return jsonify({"error": str(e)}), 500
    
    logger.info("Routes initialized")
