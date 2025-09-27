#!/usr/bin/env python3
"""
PROBLEM A: Basic Navigation
Objective: Navigate from Start node to End node using A* pathfinding
Strategy: Reliability-first approach with robust line following and intersection detection
"""

import rospy
import cv2
import numpy as np
import time
import json
from enum import Enum

from jetbot import Robot
from sensor_msgs.msg import LaserScan, Image
from opposite_detector import SimpleOppositeDetector
from map_navigator import MapNavigator

class RobotState(Enum):
    WAITING_FOR_LINE = 0
    DRIVING_STRAIGHT = 1
    APPROACHING_INTERSECTION = 2
    LEAVING_INTERSECTION = 3
    GOAL_REACHED = 4
    DEAD_END = 5

class Direction(Enum):
    NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

class ProblemASolver:
    def __init__(self):
        rospy.loginfo("Initializing Problem A Solver...")
        self.setup_parameters()
        self.initialize_hardware()
        
        # Navigation setup
        self.navigator = MapNavigator(self.MAP_FILE_PATH)
        self.current_node_id = self.navigator.start_node
        self.target_node_id = None
        self.planned_path = None
        self.plan_initial_route()

        # Sensor setup
        self.latest_scan = None
        self.latest_image = None
        self.detector = SimpleOppositeDetector()
        rospy.Subscriber('/scan', LaserScan, self.detector.callback)
        rospy.Subscriber('/csi_cam_0/image_raw', Image, self.camera_callback)
        
        # State management
        self.state_change_time = rospy.get_time()
        self._set_state(RobotState.WAITING_FOR_LINE, initial=True)
        rospy.loginfo("Problem A Solver initialized.")

    def setup_parameters(self):
        # Basic robot parameters
        self.WIDTH, self.HEIGHT = 300, 300
        self.BASE_SPEED = 0.18  # Slightly faster for Problem A
        self.TURN_SPEED = 0.2
        self.TURN_DURATION_90_DEG = 0.8
        
        # Line detection parameters
        self.ROI_Y = int(self.HEIGHT * 0.85)
        self.ROI_H = int(self.HEIGHT * 0.15)
        self.ROI_CENTER_WIDTH_PERCENT = 0.5
        self.LOOKAHEAD_ROI_Y = int(self.HEIGHT * 0.60)
        self.LOOKAHEAD_ROI_H = int(self.HEIGHT * 0.15)
        
        # Control parameters
        self.CORRECTION_GAIN = 0.5
        self.SAFE_ZONE_PERCENT = 0.3
        self.MAX_CORRECTION_ADJ = 0.12
        
        # Color filtering
        self.LINE_COLOR_LOWER = np.array([0, 0, 0])
        self.LINE_COLOR_UPPER = np.array([180, 255, 75])
        self.SCAN_PIXEL_THRESHOLD = 100
        
        # Intersection handling
        self.INTERSECTION_CLEARANCE_DURATION = 1.5
        self.INTERSECTION_APPROACH_DURATION = 0.5
        self.LINE_REACQUIRE_TIMEOUT = 3.0
        
        # Direction management
        self.DIRECTIONS = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.current_direction_index = 1  # Start facing East
        self.LABEL_TO_DIRECTION_ENUM = {
            'N': Direction.NORTH, 'E': Direction.EAST, 
            'S': Direction.SOUTH, 'W': Direction.WEST
        }
        
        # File paths
        self.MAP_FILE_PATH = "map.json"

    def initialize_hardware(self):
        try:
            self.robot = Robot()
            rospy.loginfo("JetBot hardware initialized successfully.")
        except Exception as e:
            rospy.logwarn(f"Failed to initialize JetBot hardware: {e}")
            from unittest.mock import Mock
            self.robot = Mock()

    def plan_initial_route(self):
        """Plan optimal route from Start to End"""
        rospy.loginfo(f"Planning route from {self.navigator.start_node} to {self.navigator.end_node}...")
        self.planned_path = self.navigator.find_path(
            self.navigator.start_node, 
            self.navigator.end_node
        )
        if self.planned_path and len(self.planned_path) > 1:
            self.target_node_id = self.planned_path[1]
            rospy.loginfo(f"Route found: {self.planned_path}")
            rospy.loginfo(f"First target: {self.target_node_id}")
        else:
            rospy.logerr("No route found!")
            self._set_state(RobotState.DEAD_END)

    def _set_state(self, new_state, initial=False):
        if self.current_state != new_state:
            if not initial:
                rospy.loginfo(f"State transition: {self.current_state.name} -> {new_state.name}")
            self.current_state = new_state
            self.state_change_time = rospy.get_time()

    def camera_callback(self, image_msg):
        try:
            if image_msg.encoding.endswith('compressed'):
                np_arr = np.frombuffer(image_msg.data, np.uint8)
                cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            else:
                cv_image = np.frombuffer(image_msg.data, dtype=np.uint8).reshape(
                    image_msg.height, image_msg.width, -1)
            
            if 'rgb' in image_msg.encoding:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            self.latest_image = cv2.resize(cv_image, (self.WIDTH, self.HEIGHT))
        except Exception as e:
            rospy.logerr(f"Camera callback error: {e}")

    def _get_line_center(self, image, roi_y, roi_h):
        """Detect line center in specified ROI"""
        if image is None:
            return None
            
        roi = image[roi_y : roi_y + roi_h, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Color filtering
        color_mask = cv2.inRange(hsv, self.LINE_COLOR_LOWER, self.LINE_COLOR_UPPER)
        
        # Focus mask for center region
        focus_mask = np.zeros_like(color_mask)
        roi_height, roi_width = focus_mask.shape
        center_width = int(roi_width * self.ROI_CENTER_WIDTH_PERCENT)
        start_x = (roi_width - center_width) // 2
        end_x = start_x + center_width
        cv2.rectangle(focus_mask, (start_x, 0), (end_x, roi_height), 255, -1)
        
        # Combine masks
        final_mask = cv2.bitwise_and(color_mask, focus_mask)
        
        # Find contours
        _, contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < self.SCAN_PIXEL_THRESHOLD:
            return None

        M = cv2.moments(c)
        if M["m00"] > 0:
            return int(M["m10"] / M["m00"])
        return None

    def correct_course(self, line_center_x):
        """Line following with PD control"""
        error = line_center_x - (self.WIDTH / 2)
        
        # Dead zone for straight movement
        if abs(error) < (self.WIDTH / 2) * self.SAFE_ZONE_PERCENT:
            self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
            return

        # Calculate adjustment
        adj = (error / (self.WIDTH / 2)) * self.CORRECTION_GAIN
        adj = np.clip(adj, -self.MAX_CORRECTION_ADJ, self.MAX_CORRECTION_ADJ)
        
        # Apply motor speeds
        left_motor = self.BASE_SPEED + adj
        right_motor = self.BASE_SPEED - adj
        self.robot.set_motors(left_motor, right_motor)

    def map_absolute_to_relative(self, target_direction_label, current_robot_direction):
        """Convert absolute direction to relative action"""
        target_dir = self.LABEL_TO_DIRECTION_ENUM.get(target_direction_label)
        if target_dir is None:
            return None

        current_idx = current_robot_direction.value
        target_idx = target_dir.value
        
        diff = (target_idx - current_idx + 4) % 4
        
        if diff == 0:
            return 'straight'
        elif diff == 1:
            return 'right'
        elif diff == 3:
            return 'left'
        else:
            return 'turn_around'

    def turn_robot(self, degrees, update_direction=True):
        """Execute turn with specified angle"""
        duration = abs(degrees) / 90.0 * self.TURN_DURATION_90_DEG
        
        if degrees > 0:
            self.robot.set_motors(self.TURN_SPEED, -self.TURN_SPEED)
        elif degrees < 0:
            self.robot.set_motors(-self.TURN_SPEED, self.TURN_SPEED)
        
        if degrees != 0:
            time.sleep(duration)
        
        self.robot.stop()
        
        if update_direction and degrees % 90 == 0 and degrees != 0:
            num_turns = round(degrees / 90)
            self.current_direction_index = (self.current_direction_index + num_turns + 4) % 4
            rospy.loginfo(f"New direction: {self.DIRECTIONS[self.current_direction_index].name}")
        
        time.sleep(0.5)

    def handle_intersection(self):
        """Handle intersection navigation for Problem A"""
        rospy.loginfo("[INTERSECTION] Processing...")
        self.robot.stop()
        time.sleep(0.5)

        # Update current position
        self.current_node_id = self.target_node_id
        rospy.loginfo(f"Arrived at node {self.current_node_id}")

        # Check if reached goal
        if self.current_node_id == self.navigator.end_node:
            rospy.loginfo("GOAL REACHED!")
            self._set_state(RobotState.GOAL_REACHED)
            return

        # Get next direction from planned path
        current_direction = self.DIRECTIONS[self.current_direction_index]
        planned_direction_label = self.navigator.get_next_direction_label(
            self.current_node_id, self.planned_path)
        
        if not planned_direction_label:
            rospy.logerr("No next direction found in path!")
            self._set_state(RobotState.DEAD_END)
            return

        planned_action = self.map_absolute_to_relative(planned_direction_label, current_direction)
        rospy.loginfo(f"Planned action: {planned_action} (direction: {planned_direction_label})")

        # Execute planned action
        if planned_action == 'straight':
            rospy.loginfo("Going straight")
        elif planned_action == 'right':
            rospy.loginfo("Turning right")
            self.turn_robot(90, True)
        elif planned_action == 'left':
            rospy.loginfo("Turning left")
            self.turn_robot(-90, True)
        else:
            rospy.logwarn("Invalid action!")
            self._set_state(RobotState.DEAD_END)
            return

        # Update target for next node
        next_node_id = self.planned_path[self.planned_path.index(self.current_node_id) + 1]
        self.target_node_id = next_node_id
        rospy.loginfo(f"Next target: {self.target_node_id}")
        
        self._set_state(RobotState.LEAVING_INTERSECTION)

    def run(self):
        """Main execution loop for Problem A"""
        rospy.loginfo("Starting Problem A execution...")
        time.sleep(3)  # Startup delay
        
        self.detector.start_scanning()
        rate = rospy.Rate(20)
        
        while not rospy.is_shutdown():
            
            if self.current_state == RobotState.WAITING_FOR_LINE:
                rospy.loginfo_throttle(5, "Waiting for line detection...")
                self.robot.stop()

                if self.latest_image is None:
                    rate.sleep()
                    continue
                
                lookahead_line = self._get_line_center(self.latest_image, self.LOOKAHEAD_ROI_Y, self.LOOKAHEAD_ROI_H)
                execution_line = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)

                if lookahead_line is not None and execution_line is not None:
                    rospy.loginfo("Line detected! Starting navigation.")
                    self._set_state(RobotState.DRIVING_STRAIGHT)

            elif self.current_state == RobotState.DRIVING_STRAIGHT:
                if self.latest_image is None:
                    self.robot.stop()
                    rate.sleep()
                    continue

                # Priority 1: LIDAR intersection detection
                if self.detector.process_detection():
                    rospy.loginfo("LIDAR: Intersection detected")
                    self.robot.stop()
                    time.sleep(0.5)
                    self.handle_intersection()
                    continue

                # Priority 2: Lookahead line loss (approaching intersection)
                lookahead_line_center = self._get_line_center(self.latest_image, self.LOOKAHEAD_ROI_Y, self.LOOKAHEAD_ROI_H)
                if lookahead_line_center is None:
                    rospy.logwarn("Lookahead: Line lost, approaching intersection")
                    self._set_state(RobotState.APPROACHING_INTERSECTION)
                    continue

                # Priority 3: Normal line following
                execution_line_center = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)
                if execution_line_center is not None:
                    self.correct_course(execution_line_center)
                else:
                    rospy.logwarn("Execution line lost, stopping for safety")
                    self.robot.stop()

            elif self.current_state == RobotState.APPROACHING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_APPROACH_DURATION:
                    rospy.loginfo("Reached intersection center")
                    self.robot.stop()
                    time.sleep(0.5)
                    self.handle_intersection()

            elif self.current_state == RobotState.LEAVING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_CLEARANCE_DURATION:
                    rospy.loginfo("Left intersection, searching for line")
                    line_center = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)
                    if line_center is not None:
                        rospy.loginfo("Line reacquired!")
                        self._set_state(RobotState.DRIVING_STRAIGHT)
                    else:
                        # Continue moving forward briefly
                        pass

            elif self.current_state == RobotState.GOAL_REACHED:
                rospy.loginfo("PROBLEM A COMPLETED SUCCESSFULLY!")
                self.robot.stop()
                time.sleep(5)  # Stop for 5 seconds as required
                break

            elif self.current_state == RobotState.DEAD_END:
                rospy.logwarn("Dead end reached. Stopping.")
                self.robot.stop()
                break

            rate.sleep()
        
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        rospy.loginfo("Cleaning up Problem A...")
        if hasattr(self, 'robot') and self.robot is not None:
            self.robot.stop()
        
        if hasattr(self, 'detector') and self.detector is not None:
            self.detector.stop_scanning()
        
        rospy.loginfo("Problem A cleanup complete.")


def main():
    rospy.init_node('problem_a_solver', anonymous=True)
    try:
        solver = ProblemASolver()
        solver.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Problem A interrupted.")
    except Exception as e:
        rospy.logerr(f"Problem A error: {e}", exc_info=True)


if __name__ == '__main__':
    main()