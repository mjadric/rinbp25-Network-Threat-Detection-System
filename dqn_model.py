import os
import numpy as np
import logging
from datetime import datetime
from collections import deque
import random

# Configuration
logger = logging.getLogger(__name__)

class SimplifiedDQNAgent:
    """
    Simplified DQN agent for DDoS attack detection and defense
    Uses numpy instead of TensorFlow for compatibility
    """
    def __init__(self):
        # Environment parameters
        self.state_size = 8  # Number of features in our state (network metrics)
        self.action_size = 4  # Number of possible actions to take
        
        # Define the actions
        self.actions = [
            "no_action",             # No defense action
            "rate_limit",            # Apply rate limiting
            "block_suspicious_ips",  # Block suspicious IPs
            "activate_challenge"     # Activate challenge-response mechanism
        ]
        
        # DQN hyperparameters
        self.memory = deque(maxlen=2000)  # Experience replay buffer
        self.gamma = 0.95               # Discount factor
        self.epsilon = 1.0              # Exploration rate
        self.epsilon_min = 0.01         # Minimum exploration rate
        self.epsilon_decay = 0.995      # Exploration rate decay
        self.learning_rate = 0.001      # Learning rate
        self.batch_size = 32            # Batch size for training
        
        # Simple linear model parameters (weights and biases)
        # In a simple linear model: Q(s,a) = W * s + b
        # Initialize with small random values
        self.weights = np.random.randn(self.state_size, self.action_size) * 0.1
        self.bias = np.zeros(self.action_size)
        
        # Target network parameters
        self.target_weights = self.weights.copy()
        self.target_bias = self.bias.copy()
        
        # Keep track of training metrics
        self.loss_history = []
        self.reward_history = []
        self.last_training_time = None
        
        logger.info("Simplified DDoS Defense Agent initialized")
    
    def update_target_model(self):
        """
        Update the target network to match the primary network
        """
        self.target_weights = self.weights.copy()
        self.target_bias = self.bias.copy()
        logger.debug("Target model updated")
    
    def remember(self, state, action, reward, next_state, done):
        """
        Store experience in replay memory
        """
        # Convert to 1D arrays for simpler storage
        if state is not None:
            state = state.flatten()
        if next_state is not None:
            next_state = next_state.flatten()
            
        self.memory.append((state, action, reward, next_state, done))
        
    def predict(self, state):
        """
        Predict Q-values for a state
        """
        # Linear model: Q(s,a) = W * s + b
        if state.ndim == 2:  # If state is a batch
            return np.dot(state, self.weights) + self.bias
        else:  # If state is a single sample
            return np.dot(state.reshape(1, -1), self.weights) + self.bias
    
    def target_predict(self, state):
        """
        Predict Q-values using target network
        """
        # Linear model with target parameters
        if state.ndim == 2:  # If state is a batch
            return np.dot(state, self.target_weights) + self.target_bias
        else:  # If state is a single sample
            return np.dot(state.reshape(1, -1), self.target_weights) + self.target_bias
    
    def act(self, state):
        """
        Choose an action based on the current state
        """
        # Epsilon-greedy action selection
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # Use the model to predict the best action
        state_flat = state.flatten()
        act_values = self.predict(state_flat)
        return np.argmax(act_values)
    
    def replay(self, batch_size=None):
        """
        Train the model using experience replay
        """
        if batch_size is None:
            batch_size = self.batch_size
            
        if len(self.memory) < batch_size:
            return None
        
        # Sample a random minibatch from memory
        minibatch = random.sample(self.memory, batch_size)
        
        total_loss = 0
        
        for state, action, reward, next_state, done in minibatch:
            # Get the current Q-value prediction
            target = self.predict(state)
            
            if done:
                # If done, the target is just the reward
                target[0][action] = reward
            else:
                # Otherwise, it's reward plus discounted future reward
                next_q_values = self.target_predict(next_state)
                target[0][action] = reward + self.gamma * np.max(next_q_values)
            
            # Current prediction
            current_prediction = self.predict(state)
            
            # Calculate loss (MSE)
            loss = np.mean((target - current_prediction) ** 2)
            total_loss += loss
            
            # Update weights and bias using gradient descent
            # Simple update rule: W = W - learning_rate * gradient
            error = target - current_prediction
            
            # Update weights
            gradient_w = -2 * np.outer(state, error[0]) / batch_size
            self.weights -= self.learning_rate * gradient_w
            
            # Update bias
            gradient_b = -2 * error[0] / batch_size
            self.bias -= self.learning_rate * gradient_b
        
        # Calculate average loss
        avg_loss = total_loss / batch_size
        self.loss_history.append(avg_loss)
        
        # Update epsilon (exploration rate)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        self.last_training_time = datetime.now()
        
        return avg_loss
    
    def preprocess_state(self, network_metrics):
        """
        Preprocess network metrics into a state vector for the DQN
        """
        # Extract the relevant features from network metrics
        # Example features:
        # 1. Packet rate (packets per second)
        # 2. Bandwidth usage (Mbps)
        # 3. Connection count
        # 4. TCP SYN packet ratio
        # 5. UDP packet ratio
        # 6. Average packet size
        # 7. Source IP entropy
        # 8. Destination port entropy
        
        # Normalize features to [0, 1] range
        normalized_state = np.array([
            min(1.0, network_metrics.get('packet_rate', 0) / 10000),
            min(1.0, network_metrics.get('bandwidth_usage', 0) / 1000),
            min(1.0, network_metrics.get('connection_count', 0) / 5000),
            min(1.0, network_metrics.get('syn_ratio', 0)),
            min(1.0, network_metrics.get('udp_ratio', 0)),
            min(1.0, network_metrics.get('avg_packet_size', 0) / 1500),
            min(1.0, network_metrics.get('source_ip_entropy', 0) / 10),
            min(1.0, network_metrics.get('dst_port_entropy', 0) / 10)
        ])
        
        return normalized_state.reshape(1, self.state_size)
    
    def calculate_reward(self, metrics, action_taken):
        """
        Calculate the reward based on network metrics and action taken
        """
        # Base reward starts at 0
        reward = 0
        
        # Check if there's an attack
        is_attack = metrics.get('is_attack', False)
        attack_intensity = metrics.get('attack_intensity', 0)  # 0 to 1 scale
        false_positive_penalty = -50
        true_positive_reward = 30
        
        # Action costs
        action_costs = {
            0: 0,       # No action has no cost
            1: -5,      # Rate limiting has a small cost (might affect legitimate traffic)
            2: -10,     # Blocking IPs has a medium cost (might block legitimate users)
            3: -15      # Challenge-response has a high cost (creates friction for users)
        }
        
        # Add the base action cost
        reward += action_costs[action_taken]
        
        # Check if the action was appropriate based on attack status
        if is_attack:
            if action_taken > 0:  # Any defensive action when there is an attack
                # Reward depends on attack intensity and action effectiveness
                action_effectiveness = {
                    1: 0.3,  # Rate limiting is somewhat effective
                    2: 0.7,  # Blocking IPs is more effective
                    3: 0.9   # Challenge-response is most effective
                }.get(action_taken, 0)
                
                # Higher reward for appropriate defense against more severe attacks
                reward += true_positive_reward * attack_intensity * action_effectiveness
            else:
                # Penalty for not taking action during an attack
                # More severe penalty for ignoring intense attacks
                reward -= 40 * attack_intensity
        else:
            if action_taken > 0:
                # Penalty for false positive (taking defense action when no attack)
                # More severe penalty for more disruptive actions
                action_disruptiveness = {
                    1: 0.2,  # Rate limiting is minimally disruptive
                    2: 0.6,  # Blocking IPs is moderately disruptive
                    3: 1.0   # Challenge-response is most disruptive
                }.get(action_taken, 0)
                
                reward += false_positive_penalty * action_disruptiveness
            else:
                # Small reward for correctly not taking action
                reward += 5
        
        # Add rewards for maintaining good network performance
        if metrics.get('latency', 1000) < 100:  # Low latency is good
            reward += 2
        
        if metrics.get('packet_loss', 100) < 1:  # Low packet loss is good
            reward += 2
        
        if metrics.get('bandwidth_usage', 0) < metrics.get('bandwidth_capacity', 1000) * 0.9:
            # Reward for keeping bandwidth usage under 90% of capacity
            reward += 1
            
        return reward
    
    def get_action_description(self, action_idx):
        """
        Get a human-readable description of an action
        """
        if action_idx < len(self.actions):
            return self.actions[action_idx]
        return f"Unknown action: {action_idx}"
    
    def get_model_summary(self):
        """
        Get a summary of the simplified model
        """
        return f"Simplified Linear DQN Model\nState size: {self.state_size}\nAction size: {self.action_size}"
    
    def get_training_stats(self):
        """
        Get statistics about the training process
        """
        stats = {
            "epsilon": self.epsilon,
            "memory_size": len(self.memory),
            "last_training": self.last_training_time,
            "average_loss": np.mean(self.loss_history[-100:]) if self.loss_history else None,
            "average_reward": np.mean(self.reward_history[-100:]) if self.reward_history else None
        }
        return stats

# Create a singleton instance
dqn_agent = SimplifiedDQNAgent()
