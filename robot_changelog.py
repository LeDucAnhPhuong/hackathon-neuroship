#!/usr/bin/env python3
"""
Robot Changelog System - Ghi lại state changes và intersection detections
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

class RobotChangeLogger:
    """
    Ghi lại các thay đổi quan trọng của robot
    - State transitions
    - Intersection detections
    - LIDAR events
    - Navigation decisions
    """
    
    def __init__(self, log_file: str = "robot_changelog.md"):
        """
        Initialize changelog system
        
        Args:
            log_file (str): Path to markdown log file
        """
        self.log_file = log_file
        self.session_id = self._generate_session_id()
        self.session_start = time.time()
        self.lock = threading.Lock()
        
        # Initialize log file
        self._initialize_log_file()
        
        # State tracking
        self.last_state = None
        self.intersection_count = 0
        self.total_state_changes = 0
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{int(time.time())}"
        
    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _get_elapsed_time(self) -> str:
        """Get elapsed time since session start"""
        elapsed = time.time() - self.session_start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    def _initialize_log_file(self):
        """Initialize or create log file with header"""
        with self.lock:
            # Create header for new session
            header = f"""# Robot Navigation Changelog

## Session: {self.session_id}
**Started:** {self._get_timestamp()}  
**Robot:** JetBot Hackathon 2025  

---

"""
            
            # If file exists, append new session
            if os.path.exists(self.log_file):
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n{header}")
            else:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write(header)
    
    def log_state_change(self, 
                        old_state: str, 
                        new_state: str, 
                        context: Dict[str, Any] = None):
        """
        Log robot state change
        
        Args:
            old_state (str): Previous robot state
            new_state (str): New robot state  
            context (dict): Additional context information
        """
        with self.lock:
            self.total_state_changes += 1
            
            # Prepare context info
            ctx_info = ""
            if context:
                ctx_parts = []
                for key, value in context.items():
                    if isinstance(value, (int, float)):
                        ctx_parts.append(f"{key}={value:.2f}" if isinstance(value, float) else f"{key}={value}")
                    else:
                        ctx_parts.append(f"{key}={str(value)}")
                if ctx_parts:
                    ctx_info = f" `{', '.join(ctx_parts)}`"
            
            # Create log entry
            log_entry = f"""### 🔄 State Change #{self.total_state_changes}
**Time:** {self._get_timestamp()} (+{self._get_elapsed_time()})  
**Transition:** `{old_state}` → `{new_state}`{ctx_info}

"""
            
            # Write to file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            print(f"📝 [LOG] State: {old_state} → {new_state}")
            
            self.last_state = new_state
    
    def log_intersection_detected(self, 
                                 intersection_type: str = "unknown",
                                 lidar_data: Dict[str, Any] = None,
                                 node_info: Dict[str, Any] = None):
        """
        Log intersection detection from LIDAR
        
        Args:
            intersection_type (str): Type of intersection detected
            lidar_data (dict): LIDAR sensor data
            node_info (dict): Current node/navigation info
        """
        with self.lock:
            self.intersection_count += 1
            
            # Prepare LIDAR info
            lidar_info = ""
            if lidar_data:
                lidar_parts = []
                for key, value in lidar_data.items():
                    if key in ['front_distance', 'left_distance', 'right_distance']:
                        lidar_parts.append(f"{key}={value:.2f}m")
                    elif isinstance(value, bool):
                        lidar_parts.append(f"{key}={value}")
                if lidar_parts:
                    lidar_info = f"  \n**LIDAR:** `{', '.join(lidar_parts)}`"
            
            # Prepare node info
            node_info_str = ""
            if node_info:
                node_parts = []
                for key, value in node_info.items():
                    node_parts.append(f"{key}={value}")
                if node_parts:
                    node_info_str = f"  \n**Navigation:** `{', '.join(node_parts)}`"
            
            # Create log entry
            log_entry = f"""### 🚦 Intersection #{self.intersection_count}
**Time:** {self._get_timestamp()} (+{self._get_elapsed_time()})  
**Type:** `{intersection_type}`{lidar_info}{node_info_str}

"""
            
            # Write to file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            print(f"🚦 [LOG] Intersection detected: {intersection_type}")
    
    def log_navigation_event(self, 
                           event_type: str,
                           description: str,
                           data: Dict[str, Any] = None):
        """
        Log general navigation event
        
        Args:
            event_type (str): Type of event (TURN, GOAL_REACHED, ERROR, etc.)
            description (str): Event description
            data (dict): Additional event data
        """
        with self.lock:
            # Prepare data info
            data_info = ""
            if data:
                data_parts = []
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        data_parts.append(f"{key}={value:.2f}" if isinstance(value, float) else f"{key}={value}")
                    else:
                        data_parts.append(f"{key}={str(value)}")
                if data_parts:
                    data_info = f"  \n**Data:** `{', '.join(data_parts)}`"
            
            # Map event types to icons
            icons = {
                'TURN': '🔄',
                'GOAL_REACHED': '🎯', 
                'ERROR': '❌',
                'WARNING': '⚠️',
                'INFO': 'ℹ️',
                'SUCCESS': '✅',
                'YOLO_DETECTION': '👁️',
                'QR_SCAN': '📱',
                'MATH_SOLVE': '🔢'
            }
            icon = icons.get(event_type, '📋')
            
            # Create log entry
            log_entry = f"""### {icon} {event_type}
**Time:** {self._get_timestamp()} (+{self._get_elapsed_time()})  
**Event:** {description}{data_info}

"""
            
            # Write to file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            print(f"{icon} [LOG] {event_type}: {description}")
    
    def log_lidar_event(self,
                       event_description: str,
                       scan_data: Dict[str, Any] = None):
        """
        Log LIDAR-specific events
        
        Args:
            event_description (str): Description of LIDAR event
            scan_data (dict): LIDAR scan data
        """
        self.log_navigation_event(
            event_type="LIDAR", 
            description=event_description,
            data=scan_data
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        elapsed = time.time() - self.session_start
        return {
            'session_id': self.session_id,
            'session_duration': f"{int(elapsed//60):02d}:{int(elapsed%60):02d}",
            'total_state_changes': self.total_state_changes,
            'intersection_count': self.intersection_count,
            'current_state': self.last_state,
            'log_file': self.log_file
        }
    
    def finalize_session(self, final_status: str = "SESSION_ENDED"):
        """
        Finalize session with summary
        
        Args:
            final_status (str): Final session status
        """
        with self.lock:
            summary = self.get_session_summary()
            
            # Create session summary
            summary_entry = f"""---

## Session Summary
**Duration:** {summary['session_duration']}  
**State Changes:** {summary['total_state_changes']}  
**Intersections:** {summary['intersection_count']}  
**Final Status:** `{final_status}`  
**End Time:** {self._get_timestamp()}

---
"""
            
            # Write summary to file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(summary_entry)
                
            print(f"📊 [LOG] Session finalized: {summary}")

# Global logger instance
_global_logger = None

def get_logger(log_file: str = "robot_changelog.md") -> RobotChangeLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = RobotChangeLogger(log_file)
    return _global_logger

def log_state_change(old_state: str, new_state: str, **context):
    """Quick function to log state change"""
    logger = get_logger()
    logger.log_state_change(old_state, new_state, context)

def log_intersection(intersection_type: str = "unknown", **data):
    """Quick function to log intersection"""
    logger = get_logger()
    logger.log_intersection_detected(intersection_type, data)

def log_lidar_event(description: str, **data):
    """Quick function to log LIDAR event"""
    logger = get_logger()
    logger.log_lidar_event(description, data)

def log_navigation(event_type: str, description: str, **data):
    """Quick function to log navigation event"""
    logger = get_logger()
    logger.log_navigation_event(event_type, description, data)

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Robot Changelog System")
    print("=" * 50)
    
    # Create logger
    logger = RobotChangeLogger("test_changelog.md")
    
    # Test state changes
    logger.log_state_change("WAITING_FOR_LINE", "DRIVING_STRAIGHT", 
                           context={'speed': 0.16, 'line_detected': True})
    
    time.sleep(1)
    
    # Test intersection detection
    logger.log_intersection_detected("T_INTERSECTION", 
                                    lidar_data={
                                        'front_distance': 0.25,
                                        'left_open': True,
                                        'right_blocked': False
                                    },
                                    node_info={'current_node': 'G', 'target_node': 'F'})
    
    time.sleep(1)
    
    # Test navigation events
    logger.log_navigation_event("TURN", "Turning left at intersection", 
                               data={'degrees': -90, 'duration': 0.8})
    
    logger.log_lidar_event("Obstacle detected ahead", 
                          scan_data={'min_distance': 0.15, 'obstacle_angle': 0})
    
    # Finalize session
    logger.finalize_session("TEST_COMPLETED")
    
    print("✅ Test completed - check test_changelog.md")