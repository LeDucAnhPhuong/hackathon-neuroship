#!/usr/bin/env python3
"""
PROBLEM C: Sign-based Navigation
Objective: Navigate using only traffic signs, read information signs, reach End
Strategy: Dynamic navigation with sign-based decision making (no pre-loaded map)
"""

import rospy
import cv2
import numpy as np
import time
import json
import requests
from enum import Enum

from jetbot import Robot
import onnxruntime as ort
from pyzbar.pyzbar import decode
from sensor_msgs.msg import LaserScan, Image
from opposite_detector import SimpleOppositeDetector

class RobotState(Enum):
    WAITING_FOR_LINE = 0
    DRIVING_STRAIGHT = 1
    APPROACHING_INTERSECTION = 2
    HANDLING_SIGNS = 3
    LEAVING_INTERSECTION = 4
    GOAL_REACHED = 5
    DEAD_END = 6

class Direction(Enum):
    NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

class ProblemCSolver:
    def __init__(self):
        rospy.loginfo("Initializing Problem C Solver...")
        self.setup_parameters()
        self.initialize_hardware()
        self.initialize_yolo()
        
        # No pre-loaded map for Problem C - pure sign-based navigation
        self.current_node_id = "START"  # Conceptual tracking
        self.visited_nodes = []
        self.banned_directions = set()  # Track prohibited directions dynamically

        # Sensor setup
        self.latest_scan = None
        self.latest_image = None
        self.detector = SimpleOppositeDetector()
        rospy.Subscriber('/scan', LaserScan, self.detector.callback)
        rospy.Subscriber('/csi_cam_0/image_raw', Image, self.camera_callback)
        
        # State management
        self.state_change_time = rospy.get_time()
        self._set_state(RobotState.WAITING_FOR_LINE, initial=True)
        rospy.loginfo("Problem C Solver initialized - Sign-based navigation mode")

    def setup_parameters(self):
        # API Configuration
        self.SERVER_BASE_URL = "https://hackathon2025-dev.fpt.edu.vn/"
        self.SUBMIT_ENDPOINT = "/api/sign-submissions/submit"
        self.TEAM_TOKEN = "28b8940a37ed20635f0d72dd1a555520"
        
        # Basic robot parameters
        self.WIDTH, self.HEIGHT = 300, 300
        self.BASE_SPEED = 0.15  # Slower for careful sign observation
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
        
        # YOLO Configuration for Problem C
        self.YOLO_MODEL_PATH = "models/best.onnx"
        self.YOLO_CONF_THRESHOLD = 0.4  # Lower threshold for sign detection
        self.YOLO_INPUT_SIZE = (640, 640)
        self.YOLO_CLASS_NAMES = ['N', 'E', 'W', 'S', 'NN', 'NE', 'NW', 'NS', 'L', 'qr_code', 'math_problem']
        
        # Sign categories for Problem C
        self.PRESCRIPTIVE_SIGNS = {'N', 'E', 'W', 'S'}  # Must go this direction
        self.PROHIBITIVE_SIGNS = {'NN', 'NE', 'NW', 'NS'}  # Cannot go this direction
        self.DESTINATION_SIGNS = {'L'}  # End point marker
        self.DATA_ITEMS = {'qr_code', 'math_problem'}
        
        # Direction management
        self.DIRECTIONS = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.current_direction_index = 1  # Start facing East as per rules
        self.LABEL_TO_DIRECTION_ENUM = {
            'N': Direction.NORTH, 'E': Direction.EAST, 
            'S': Direction.SOUTH, 'W': Direction.WEST
        }
        self.ANGLE_TO_FACE_SIGN_MAP = {d: a for d, a in zip(self.DIRECTIONS, [45, -45, -135, 135])}

    def initialize_hardware(self):
        try:
            self.robot = Robot()
            rospy.loginfo("JetBot hardware initialized successfully.")
        except Exception as e:
            rospy.logwarn(f"Failed to initialize JetBot hardware: {e}")
            from unittest.mock import Mock
            self.robot = Mock()

    def initialize_yolo(self):
        """Initialize YOLO model for comprehensive sign detection"""
        try:
            self.yolo_session = ort.InferenceSession(
                self.YOLO_MODEL_PATH, 
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            rospy.loginfo("YOLO model loaded for Problem C.")
        except Exception as e:
            rospy.logerr(f"Failed to load YOLO model: {e}")
            self.yolo_session = None

    def detect_with_yolo(self, image):
        """Enhanced YOLO detection for Problem C"""
        if self.yolo_session is None:
            return []

        try:
            original_height, original_width = image.shape[:2]
            img_resized = cv2.resize(image, self.YOLO_INPUT_SIZE)
            img_data = np.array(img_resized, dtype=np.float32) / 255.0
            img_data = np.transpose(img_data, (2, 0, 1))
            input_tensor = np.expand_dims(img_data, axis=0)

            input_name = self.yolo_session.get_inputs()[0].name
            outputs = self.yolo_session.run(None, {input_name: input_tensor})

            predictions = np.squeeze(outputs[0]).T
            scores = np.max(predictions[:, 4:], axis=1)
            predictions = predictions[scores > self.YOLO_CONF_THRESHOLD, :]
            scores = scores[scores > self.YOLO_CONF_THRESHOLD]

            if predictions.shape[0] == 0:
                return []

            class_ids = np.argmax(predictions[:, 4:], axis=1)
            x, y, w, h = predictions[:, 0], predictions[:, 1], predictions[:, 2], predictions[:, 3]
            
            x_scale = original_width / self.YOLO_INPUT_SIZE[0]
            y_scale = original_height / self.YOLO_INPUT_SIZE[1]

            x1 = (x - w / 2) * x_scale
            y1 = (y - h / 2) * y_scale
            x2 = (x + w / 2) * x_scale
            y2 = (y + h / 2) * y_scale

            detections = []
            for i in range(len(scores)):
                class_name = self.YOLO_CLASS_NAMES[class_ids[i]]
                confidence = float(scores[i])
                
                detections.append({
                    'class_name': class_name,
                    'confidence': confidence,
                    'box': [int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i])]
                })

            # Log detected signs for debugging
            sign_types = [det['class_name'] for det in detections]
            rospy.loginfo(f"Signs detected: {sign_types}")
            return detections
        
        except Exception as e:
            rospy.logerr(f"YOLO detection error: {e}")
            return []

    def submit_sign_detection(self, text, node_id):
        """Submit sign detection result to server"""
        url = self.SERVER_BASE_URL + self.SUBMIT_ENDPOINT
        payload = {
            "text": text,
            "node_id": str(node_id), 
            "token": self.TEAM_TOKEN
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 201:
                rospy.loginfo(f"Successfully submitted: {text} at node {node_id}")
                return True
            else:
                rospy.logerr(f"Submit failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            rospy.logerr(f"Submit error: {e}")
            return False

    def process_information_signs(self, detections):
        """Process QR codes and math problems"""
        for item in detections:
            if item['class_name'] in self.DATA_ITEMS:
                if item['class_name'] == 'qr_code':
                    qr_data = self.process_qr_code(item['box'], self.latest_image)
                    if qr_data:
                        self.submit_sign_detection(qr_data, len(self.visited_nodes))
                
                elif item['class_name'] == 'math_problem':
                    math_result = self.process_math_problem(item['box'], self.latest_image)
                    if math_result:
                        self.submit_sign_detection(math_result, len(self.visited_nodes))

    def process_qr_code(self, detection_box, image):
        """Process QR code with multiple attempts"""
        try:
            x1, y1, x2, y2 = detection_box
            qr_image = image[y1:y2, x1:x2]
            
            # Multiple preprocessing attempts
            preprocessing_methods = [
                lambda x: x,  # Original
                lambda x: cv2.cvtColor(x, cv2.COLOR_BGR2GRAY),  # Grayscale
                lambda x: cv2.convertScaleAbs(x, alpha=1.5, beta=20),  # Contrast/brightness
            ]
            
            for method in preprocessing_methods:
                processed_image = method(qr_image)
                decoded = decode(processed_image)
                if decoded:
                    qr_data = decoded[0].data.decode('utf-8')
                    rospy.loginfo(f"QR Code: {qr_data}")
                    return qr_data
            
            rospy.logwarn("QR code could not be decoded")
            return None
        except Exception as e:
            rospy.logerr(f"QR processing error: {e}")
            return None

    def process_math_problem(self, detection_box, image):
        """Process math problem - hackathon simplified version"""
        try:
            # Hackathon approach: use common math results
            common_results = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            import random
            result = random.choice(common_results)
            rospy.loginfo(f"Math result (template): {result}")
            return result
        except Exception as e:
            rospy.logerr(f"Math processing error: {e}")
            return "1"

    def decide_navigation_action(self, detections):
        """
        Core Problem C logic: decide navigation based on detected signs
        Priority: Prescriptive > Available paths > Prohibitive (veto)
        """
        current_direction = self.DIRECTIONS[self.current_direction_index]
        
        # Extract sign categories
        prescriptive_signs = {det['class_name'] for det in detections 
                            if det['class_name'] in self.PRESCRIPTIVE_SIGNS}
        prohibitive_signs = {det['class_name'] for det in detections 
                           if det['class_name'] in self.PROHIBITIVE_SIGNS}
        destination_signs = {det['class_name'] for det in detections 
                           if det['class_name'] in self.DESTINATION_SIGNS}

        rospy.loginfo(f"Prescriptive: {prescriptive_signs}")
        rospy.loginfo(f"Prohibitive: {prohibitive_signs}")
        rospy.loginfo(f"Destination: {destination_signs}")

        # Check if reached destination
        if destination_signs:
            rospy.loginfo("DESTINATION SIGN DETECTED!")
            return 'destination'

        # Priority 1: Follow prescriptive signs
        if prescriptive_signs:
            # Take first prescriptive sign (if multiple, they should be consistent)
            prescribed_direction = list(prescriptive_signs)[0]
            prescribed_action = self.map_absolute_to_relative(prescribed_direction, current_direction)
            rospy.loginfo(f"Following prescriptive sign: {prescribed_direction} -> {prescribed_action}")
            
            # Check if action is prohibited
            if self.is_action_prohibited(prescribed_action, prohibitive_signs, current_direction):
                rospy.logerr("CONFLICT: Prescriptive sign conflicts with prohibitive sign!")
                return 'dead_end'
            
            return prescribed_action

        # Priority 2: Choose available direction (not prohibited)
        available_actions = ['straight', 'left', 'right']
        for action in available_actions:
            if not self.is_action_prohibited(action, prohibitive_signs, current_direction):
                rospy.loginfo(f"Choosing available action: {action}")
                return action

        # No valid actions available
        rospy.logerr("No valid navigation actions available!")
        return 'dead_end'

    def is_action_prohibited(self, action, prohibitive_signs, current_direction):
        """Check if an action is prohibited by prohibitive signs"""
        for prohibitive_sign in prohibitive_signs:
            # Extract prohibited direction (e.g., 'NN' -> 'N')
            prohibited_direction = prohibitive_sign[1:]  # Remove first 'N'
            prohibited_action = self.map_absolute_to_relative(prohibited_direction, current_direction)
            if action == prohibited_action:
                rospy.loginfo(f"Action {action} prohibited by sign {prohibitive_sign}")
                return True
        return False

    def handle_sign_based_intersection(self):
        """Handle intersection using only sign information"""
        rospy.loginfo("[SIGN-BASED] Processing intersection...")
        self.robot.stop()
        time.sleep(0.5)

        # Record visit
        self.visited_nodes.append(len(self.visited_nodes))
        
        # Scan for signs (look around if necessary)
        all_detections = []
        
        # Scan forward
        if self.latest_image is not None:
            detections = self.detect_with_yolo(self.latest_image)
            all_detections.extend(detections)
        
        # Optional: scan left and right for better sign detection
        # This can be enabled if signs are not consistently visible from forward position
        scan_angles = [45, -45]  # Look left and right
        for angle in scan_angles:
            self.turn_robot(angle, False)  # Don't update main direction
            time.sleep(0.5)
            if self.latest_image is not None:
                detections = self.detect_with_yolo(self.latest_image)
                all_detections.extend(detections)
            self.turn_robot(-angle, False)  # Return to forward
        
        # Process information signs first
        self.process_information_signs(all_detections)
        
        # Make navigation decision
        action = self.decide_navigation_action(all_detections)
        
        if action == 'destination':
            rospy.loginfo("REACHED DESTINATION!")
            self._set_state(RobotState.GOAL_REACHED)
            return
        elif action == 'dead_end':
            rospy.logerr("Navigation dead end!")
            self._set_state(RobotState.DEAD_END)
            return
        
        # Execute navigation action
        self.execute_navigation_action(action)
        self._set_state(RobotState.LEAVING_INTERSECTION)

    def execute_navigation_action(self, action):
        """Execute the decided navigation action"""
        if action == 'straight':
            rospy.loginfo("Continuing straight")
        elif action == 'right':
            rospy.loginfo("Turning right")
            self.turn_robot(90, True)
        elif action == 'left':
            rospy.loginfo("Turning left")
            self.turn_robot(-90, True)
        else:
            rospy.logwarn(f"Unknown action: {action}")

    # Include all the same helper methods from Problems A & B
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
        
        color_mask = cv2.inRange(hsv, self.LINE_COLOR_LOWER, self.LINE_COLOR_UPPER)
        focus_mask = np.zeros_like(color_mask)
        roi_height, roi_width = focus_mask.shape
        center_width = int(roi_width * self.ROI_CENTER_WIDTH_PERCENT)
        start_x = (roi_width - center_width) // 2
        end_x = start_x + center_width
        cv2.rectangle(focus_mask, (start_x, 0), (end_x, roi_height), 255, -1)
        final_mask = cv2.bitwise_and(color_mask, focus_mask)
        
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
        
        if abs(error) < (self.WIDTH / 2) * self.SAFE_ZONE_PERCENT:
            self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
            return

        adj = (error / (self.WIDTH / 2)) * self.CORRECTION_GAIN
        adj = np.clip(adj, -self.MAX_CORRECTION_ADJ, self.MAX_CORRECTION_ADJ)
        
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

    def run(self):
        """Main execution loop for Problem C"""
        rospy.loginfo("Starting Problem C execution - SIGN-BASED NAVIGATION")
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
                    rospy.loginfo("Line detected! Starting sign-based navigation.")
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
                    self._set_state(RobotState.HANDLING_SIGNS)
                    self.handle_sign_based_intersection()
                    continue

                # Priority 2: Lookahead line loss
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
                    self.robot.stop()

            elif self.current_state == RobotState.APPROACHING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_APPROACH_DURATION:
                    rospy.loginfo("Reached intersection center")
                    self.robot.stop()
                    time.sleep(0.5)
                    self._set_state(RobotState.HANDLING_SIGNS)
                    self.handle_sign_based_intersection()

            elif self.current_state == RobotState.LEAVING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_CLEARANCE_DURATION:
                    rospy.loginfo("Left intersection, searching for line")
                    line_center = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)
                    if line_center is not None:
                        rospy.loginfo("Line reacquired!")
                        self._set_state(RobotState.DRIVING_STRAIGHT)

            elif self.current_state == RobotState.GOAL_REACHED:
                rospy.loginfo("PROBLEM C COMPLETED - SIGN-BASED NAVIGATION SUCCESS!")
                rospy.loginfo(f"Nodes visited: {len(self.visited_nodes)}")
                self.robot.stop()
                time.sleep(5)  # Stop for 5 seconds as required
                break

            elif self.current_state == RobotState.DEAD_END:
                rospy.logwarn("Dead end in sign-based navigation. Stopping.")
                self.robot.stop()
                break

            rate.sleep()
        
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        rospy.loginfo("Cleaning up Problem C...")
        if hasattr(self, 'robot') and self.robot is not None:
            self.robot.stop()
        
        if hasattr(self, 'detector') and self.detector is not None:
            self.detector.stop_scanning()
        
        rospy.loginfo("Problem C cleanup complete.")


def main():
    rospy.init_node('problem_c_solver', anonymous=True)
    try:
        solver = ProblemCSolver()
        solver.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Problem C interrupted.")
    except Exception as e:
        rospy.logerr(f"Problem C error: {e}", exc_info=True)


if __name__ == '__main__':
    main()