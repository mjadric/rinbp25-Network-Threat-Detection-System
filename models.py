from datetime import datetime

# In-memory storage for model instances
network_stats_data = []
attack_events_data = []
network_nodes_data = []
network_edges_data = []
next_id = {'NetworkStats': 1, 'AttackEvent': 1, 'NetworkNode': 1, 'NetworkEdge': 1}

class NetworkStats:
    """Model for storing network statistics in memory"""
    def __init__(self, **kwargs):
        self.id = next_id['NetworkStats']
        next_id['NetworkStats'] += 1
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.total_packets = kwargs.get('total_packets', 0)
        self.total_bandwidth = kwargs.get('total_bandwidth', 0.0)  # in Mbps
        self.average_latency = kwargs.get('average_latency', 0.0)  # in ms
        self.connection_count = kwargs.get('connection_count', 0)
        self.suspicious_traffic_percent = kwargs.get('suspicious_traffic_percent', 0.0)
        self.is_under_attack = kwargs.get('is_under_attack', False)
        
        # Add to storage
        network_stats_data.append(self)
    
    def __repr__(self):
        return f"<NetworkStats {self.timestamp} {'[ATTACK]' if self.is_under_attack else ''}>"

    @classmethod
    def query(cls):
        return Query(network_stats_data)
    
    @classmethod
    def get_latest_stats(cls):
        if not network_stats_data:
            return None
        return sorted(network_stats_data, key=lambda x: x.timestamp, reverse=True)[0]
    
    @classmethod
    def get_historical_stats(cls, limit=100):
        return sorted(network_stats_data, key=lambda x: x.timestamp, reverse=True)[:limit]

class AttackEvent:
    """Model for storing attack events in memory"""
    def __init__(self, **kwargs):
        self.id = next_id['AttackEvent']
        next_id['AttackEvent'] += 1
        self.start_time = kwargs.get('start_time', datetime.utcnow())
        self.end_time = kwargs.get('end_time', None)
        self.attack_type = kwargs.get('attack_type', "DDoS")
        self.severity = kwargs.get('severity', 1)  # 1-10 scale
        self.source_ips = kwargs.get('source_ips', "")  # Comma-separated list of IPs
        self.target_ip = kwargs.get('target_ip', "")
        self.packet_count = kwargs.get('packet_count', 0)
        self.mitigation_applied = kwargs.get('mitigation_applied', False)
        self.mitigation_action = kwargs.get('mitigation_action', None)
        self.notes = kwargs.get('notes', None)
        
        # Add to storage
        attack_events_data.append(self)
    
    def __repr__(self):
        return f"<AttackEvent {self.start_time} {self.attack_type}>"
    
    @classmethod
    def query(cls):
        return Query(attack_events_data)
    
    @classmethod
    def get_recent_attacks(cls, limit=10):
        return sorted(attack_events_data, key=lambda x: x.start_time, reverse=True)[:limit]
    
    @classmethod
    def get_active_attacks(cls):
        return [event for event in attack_events_data if event.end_time is None]

class NetworkNode:
    """Model for storing network nodes in memory"""
    def __init__(self, **kwargs):
        self.id = next_id['NetworkNode']
        next_id['NetworkNode'] += 1
        self.node_id = kwargs.get('node_id', f"node_{self.id}")
        self.ip_address = kwargs.get('ip_address', f"192.168.1.{self.id}")
        self.node_type = kwargs.get('node_type', "host")  # host, router, server, etc.
        self.is_attacker = kwargs.get('is_attacker', False)
        self.is_victim = kwargs.get('is_victim', False)
        self.last_seen = kwargs.get('last_seen', datetime.utcnow())
        self.geo_location = kwargs.get('geo_location', None)
        
        # Add to storage
        network_nodes_data.append(self)
    
    def __repr__(self):
        node_status = "ATTACKER" if self.is_attacker else ("VICTIM" if self.is_victim else "")
        return f"<NetworkNode {self.ip_address} [{self.node_type}] {node_status}>"
    
    @classmethod
    def query(cls):
        return Query(network_nodes_data)

class NetworkEdge:
    """Model for storing network edges in memory"""
    def __init__(self, **kwargs):
        self.id = next_id['NetworkEdge']
        next_id['NetworkEdge'] += 1
        self.source_id = kwargs.get('source_id', "")
        self.target_id = kwargs.get('target_id', "")
        self.edge_type = kwargs.get('edge_type', "connection")
        self.packets_count = kwargs.get('packets_count', 0)
        self.bandwidth = kwargs.get('bandwidth', 0.0)  # in Mbps
        self.is_attack_path = kwargs.get('is_attack_path', False)
        self.last_updated = kwargs.get('last_updated', datetime.utcnow())
        
        # Add to storage
        network_edges_data.append(self)
        
        # Set relationships
        self.source = next((node for node in network_nodes_data if node.node_id == self.source_id), None)
        self.target = next((node for node in network_nodes_data if node.node_id == self.target_id), None)
    
    def __repr__(self):
        attack_path = "[ATTACK PATH]" if self.is_attack_path else ""
        return f"<NetworkEdge {self.source_id} -> {self.target_id} {attack_path}>"
    
    @classmethod
    def query(cls):
        return Query(network_edges_data)

# Simple query class to simulate SQLAlchemy query API
class Query:
    def __init__(self, data):
        self.data = data
        self._filter = lambda x: True
        self._order = None
        self._desc = False
    
    def filter(self, condition):
        # Very simplified - ignores the actual condition and returns all data
        return self
    
    def filter_by(self, **kwargs):
        # Basic implementation that filters by attribute values
        def filter_func(item):
            for key, value in kwargs.items():
                if not hasattr(item, key) or getattr(item, key) != value:
                    return False
            return True
        
        new_query = Query(self.data)
        new_query._filter = filter_func
        return new_query
    
    def order_by(self, *fields):
        # Simple implementation that takes the first field
        # and ignores the rest
        if fields and hasattr(fields[0], '_sort_key'):
            self._order = fields[0]._sort_key
            self._desc = hasattr(fields[0], 'desc')
        return self
    
    def first(self):
        filtered_data = [item for item in self.data if self._filter(item)]
        if not filtered_data:
            return None
        
        if self._order:
            filtered_data.sort(key=lambda x: getattr(x, self._order), reverse=self._desc)
        
        return filtered_data[0] if filtered_data else None
    
    def all(self):
        filtered_data = [item for item in self.data if self._filter(item)]
        
        if self._order:
            filtered_data.sort(key=lambda x: getattr(x, self._order), reverse=self._desc)
            
        return filtered_data
    
    def limit(self, count):
        filtered_data = [item for item in self.data if self._filter(item)]
        
        if self._order:
            filtered_data.sort(key=lambda x: getattr(x, self._order), reverse=self._desc)
            
        return filtered_data[:count]
