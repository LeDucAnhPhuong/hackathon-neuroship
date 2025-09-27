#!/usr/bin/env python3
"""
Example: How to integrate changelog system into robot controllers
Demonstrates proper usage patterns for state logging
"""

from base_controller import BaseJetBotController, RobotState
from robot_changelog import get_logger
import time

class ExampleProblemController(BaseJetBotController):
    """Example implementation showing changelog integration"""
    
    def get_default_config(self):
        """Override config for this problem"""
        config = super().get_default_config()
        config.update({
            'problem_type': 'EXAMPLE',
            'base_speed': 0.15,
            'map_type': 'map_z'
        })
        return config
    
    def run(self):
        """Main run loop with proper logging"""
        rospy.loginfo("🚀 Starting Example Problem Controller")
        
        # Initialize state with logging
        self._set_state(RobotState.WAITING_FOR_LINE, initial=True)
        
        while not rospy.is_shutdown():
            try:
                # State machine with logging
                if self.current_state == RobotState.WAITING_FOR_LINE:
                    self.handle_waiting_for_line()
                    
                elif self.current_state == RobotState.DRIVING_STRAIGHT:
                    self.handle_driving_straight()
                    
                elif self.current_state == RobotState.APPROACHING_INTERSECTION:
                    self.handle_approaching_intersection()
                    
                elif self.current_state == RobotState.HANDLING_EVENT:
                    self.handle_intersection()
                    
                elif self.current_state == RobotState.GOAL_REACHED:
                    self.log_navigation_decision("GOAL_REACHED", "Successfully reached target node",
                                               target_node=self.target_node_id)
                    break
                    
                elif self.current_state == RobotState.DEAD_END:
                    self.log_navigation_decision("ERROR", "Dead end reached - no valid path",
                                               current_node=self.current_node_id)
                    break
                    
                rospy.sleep(0.1)
                
            except Exception as e:
                rospy.logerr(f"❌ Control loop error: {e}")
                self.log_navigation_decision("ERROR", f"Control loop exception: {str(e)}")
                break
        
        self.cleanup()
        
    def handle_waiting_for_line(self):
        """Handle waiting for line state with logging"""
        if self.latest_image is not None:
            line_center = self._get_line_center(self.latest_image, self.ROI_Y_MAIN, self.ROI_HEIGHT)
            if line_center is not None:
                self.log_navigation_decision("LINE_FOUND", "Line detected, starting navigation",
                                           line_center=line_center)
                self._set_state(RobotState.DRIVING_STRAIGHT)
                
    def handle_driving_straight(self):
        """Handle driving straight with intersection detection logging"""
        if self.latest_image is not None:
            line_center = self._get_line_center(self.latest_image, self.ROI_Y_MAIN, self.ROI_HEIGHT)
            
            if line_center is not None:
                self.correct_course(line_center)
                
                # Check for intersection using opposite detector
                if hasattr(self, 'detector') and self.detector.process_detection():
                    # Log intersection detection
                    self.log_intersection_detection("LIDAR_DETECTED")
                    self._set_state(RobotState.APPROACHING_INTERSECTION)
                    
            else:
                # Lost line - log it
                self.log_lidar_obstacle("Line lost during navigation")
                self._set_state(RobotState.REACQUIRING_LINE)
    
    def handle_approaching_intersection(self):
        """Handle approaching intersection with timing logs"""
        approach_duration = 1.5  # seconds
        
        if rospy.get_time() - self.state_change_time > approach_duration:
            self.log_navigation_decision("INTERSECTION_APPROACH", 
                                       f"Approached intersection for {approach_duration}s",
                                       duration=approach_duration)
            self._set_state(RobotState.HANDLING_EVENT)
    
    def handle_intersection(self):
        """Handle intersection - example implementation"""
        try:
            # Example: turn left
            turn_degrees = -90
            self.log_navigation_decision("TURN", f"Turning {abs(turn_degrees)} degrees left",
                                       degrees=turn_degrees, node=self.current_node_id)
            
            # Perform turn
            self.turn_robot(turn_degrees)
            
            # Log completion
            self.log_navigation_decision("TURN_COMPLETE", "Turn completed successfully",
                                       new_direction=self.main_direction.name)
            
            # Move to next state
            self._set_state(RobotState.LEAVING_INTERSECTION)
            
        except Exception as e:
            self.log_navigation_decision("ERROR", f"Intersection handling failed: {str(e)}")
            self._set_state(RobotState.DEAD_END)

def example_usage():
    """Example of how to use changelog in different scenarios"""
    
    print("📝 Changelog Integration Examples")
    print("=" * 50)
    
    # Example 1: Manual logging
    logger = get_logger("example_manual.md")
    
    # Log state changes manually
    logger.log_state_change("INIT", "WAITING_FOR_LINE", 
                           context={'speed': 0.0, 'position': 'start'})
    
    time.sleep(0.5)
    
    # Log intersection detection
    logger.log_intersection_detected("T_INTERSECTION",
                                    lidar_data={'front_clear': True, 'left_open': True},
                                    node_info={'current': 'A', 'target': 'B'})
    
    time.sleep(0.5)
    
    # Log navigation decisions  
    logger.log_navigation_event("TURN", "Decided to turn right based on path planning",
                               data={'degrees': 90, 'reason': 'shortest_path'})
    
    # Log LIDAR events
    logger.log_lidar_event("Obstacle detected in path", 
                          scan_data={'distance': 0.12, 'angle': 45})
    
    # Finalize
    logger.finalize_session("EXAMPLE_COMPLETED")
    
    print("✅ Manual logging example completed")
    print("📄 Check: example_manual.md")
    
    # Example 2: Integration patterns
    print("\n🔧 Integration Patterns:")
    print("1. State changes: Use _set_state() method (auto-logged)")
    print("2. Intersections: Call log_intersection_detection() when LIDAR detects")
    print("3. Navigation: Use log_navigation_decision() for important decisions")
    print("4. LIDAR events: Use log_lidar_obstacle() for obstacle detection")
    print("5. Cleanup: Ensure finalize_session() is called in cleanup()")

if __name__ == "__main__":
    example_usage()
    
    print("\n🎯 Ready for Integration!")
    print("- Add changelog to your problem controllers")
    print("- Use the logging methods shown above")
    print("- Check generated .md files for debugging")