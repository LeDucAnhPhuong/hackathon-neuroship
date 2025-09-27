#!/usr/bin/env python3
"""
Test changelog integration patterns
"""

from robot_changelog import get_logger
import time

def test_changelog_patterns():
    """Test different changelog patterns"""
    
    print("📝 Testing Changelog Integration Patterns")
    print("=" * 50)
    
    # Test 1: State machine simulation
    logger = get_logger("state_machine_test.md")
    
    # Simulate state changes
    states = [
        ("INIT", "WAITING_FOR_LINE"),
        ("WAITING_FOR_LINE", "DRIVING_STRAIGHT"), 
        ("DRIVING_STRAIGHT", "APPROACHING_INTERSECTION"),
        ("APPROACHING_INTERSECTION", "HANDLING_EVENT"),
        ("HANDLING_EVENT", "LEAVING_INTERSECTION"),
        ("LEAVING_INTERSECTION", "DRIVING_STRAIGHT"),
        ("DRIVING_STRAIGHT", "GOAL_REACHED")
    ]
    
    for i, (old, new) in enumerate(states):
        context = {
            'step': i+1,
            'elapsed': f"{(i+1)*2.5:.1f}s", 
            'node_id': f"Node_{i%4 + 1}"
        }
        logger.log_state_change(old, new, context)
        time.sleep(0.2)
    
    # Test 2: Intersection detections
    intersections = [
        {"type": "T_INTERSECTION", "lidar": {"front": 0.3, "left": True, "right": False}},
        {"type": "CROSS_INTERSECTION", "lidar": {"front": 0.25, "left": True, "right": True}},
        {"type": "L_INTERSECTION", "lidar": {"front": False, "left": True, "right": False}}
    ]
    
    for i, intersection in enumerate(intersections):
        logger.log_intersection_detected(
            intersection["type"],
            lidar_data=intersection["lidar"],
            node_info={"current": f"Node_{i+2}", "target": f"Node_{i+3}"}
        )
        time.sleep(0.3)
    
    # Test 3: Navigation events
    nav_events = [
        ("TURN", "Turning left at intersection", {"degrees": -90, "duration": 0.8}),
        ("GOAL_REACHED", "Successfully reached target", {"target": "Node_F", "total_time": "45.2s"}),
        ("ERROR", "Path blocked by obstacle", {"distance": 0.15, "retry_count": 2})
    ]
    
    for event_type, description, data in nav_events:
        logger.log_navigation_event(event_type, description, data)
        time.sleep(0.2)
    
    # Test 4: LIDAR events
    lidar_events = [
        ("Wall detected on left side", {"distance": 0.18, "angle": -90}),
        ("Clear path ahead", {"min_distance": 0.45, "max_distance": 2.0}),
        ("Obstacle cluster detected", {"count": 3, "avg_distance": 0.22})
    ]
    
    for description, data in lidar_events:
        logger.log_lidar_event(description, data)
        time.sleep(0.2)
        
    # Finalize session
    logger.finalize_session("TEST_COMPLETED")
    
    print("✅ State machine test completed")
    print("📄 Check: state_machine_test.md")
    
    # Show summary
    summary = logger.get_session_summary()
    print(f"\n📊 Session Summary:")
    print(f"   Duration: {summary['session_duration']}")
    print(f"   State Changes: {summary['total_state_changes']}")
    print(f"   Intersections: {summary['intersection_count']}")

def show_integration_guide():
    """Show how to integrate into existing controllers"""
    
    print("\n🔧 Integration Guide for Robot Controllers")
    print("=" * 50)
    
    integration_code = '''
# 1. Import changelog system
from robot_changelog import get_logger

# 2. In __init__:
self.changelog = get_logger(f"robot_{problem_type}.md")

# 3. In _set_state method (already done in base_controller):
def _set_state(self, new_state, initial=False):
    if self.current_state != new_state:
        old_name = self.current_state.name if self.current_state else "NONE"
        self.changelog.log_state_change(old_name, new_state.name, context_data)

# 4. When LIDAR detects intersection:
if self.detector.process_detection():
    self.log_intersection_detection("T_INTERSECTION")
    self._set_state(RobotState.APPROACHING_INTERSECTION)

# 5. For navigation decisions:
self.log_navigation_decision("TURN", f"Turning {degrees} degrees", 
                           degrees=degrees, reason="path_planning")

# 6. For LIDAR obstacles:
self.log_lidar_obstacle("Obstacle detected", min_distance=0.15)

# 7. In cleanup():
self.changelog.finalize_session("NORMAL_EXIT")
'''
    
    print("📋 Code Integration Pattern:")
    print(integration_code)
    
    print("\n📁 Generated Files:")
    print("- robot_problem_a.md  # Problem A navigation log")
    print("- robot_problem_b.md  # Problem B navigation log") 
    print("- robot_base.md       # Base controller log")
    
    print("\n🎯 Benefits:")
    print("✅ Track state machine behavior")
    print("✅ Debug intersection detection") 
    print("✅ Monitor LIDAR performance")
    print("✅ Record navigation decisions")
    print("✅ Timestamp all events")
    print("✅ Markdown format for easy reading")

if __name__ == "__main__":
    test_changelog_patterns()
    show_integration_guide()