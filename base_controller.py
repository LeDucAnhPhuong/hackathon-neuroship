#!/usr/bin/env python3
"""
Base ROS JetBot Controller - Dành cho kế thừa
Chứa tất cả logic cơ bản cho navigation và YOLO detection
"""

import rospy
import cv2
import numpy as np
import time
import os
import json
import math
from enum import Enum
import requests
from api_utils import create_api_client
from robot_changelog import get_logger, log_state_change, log_intersection, log_lidar_event, log_navigation

from jetbot import Robot
import onnxruntime as ort
from pyzbar.pyzbar import decode
import paho.mqtt.client as mqtt
from sensor_msgs.msg import LaserScan, Image
from opposite_detector import SimpleOppositeDetector
from map_navigator import MapNavigator

class RobotState(Enum):
    WAITING_FOR_LINE = 0
    DRIVING_STRAIGHT = 1
    APPROACHING_INTERSECTION = 2
    HANDLING_EVENT = 3
    LEAVING_INTERSECTION = 4
    REACQUIRING_LINE = 5
    DEAD_END = 6
    GOAL_REACHED = 7

class Direction(Enum):
    NORTH, EAST, SOUTH, WEST = 0, 1, 2, 3

class BaseJetBotController:
    """Base class cho tất cả các Problem controllers"""
    
    def __init__(self, config=None):
        """
        Khởi tạo base controller với config tùy chỉnh
        
        Args:
            config (dict): Configuration override cho controller cụ thể
        """
        rospy.loginfo("Đang khởi tạo Base JetBot Controller...")
        
        # Merge config với default
        self.config = self.get_default_config()
        if config:
            self.config.update(config)
            
        self.setup_parameters()
        self.initialize_hardware()
        self.initialize_yolo()
        self.initialize_mqtt()
        self.initialize_video_writer()
        self.initialize_map_navigator()
        
        # Initialize changelog system
        self.changelog = get_logger(f"robot_changelog_{self.config.get('problem_type', 'BASE').lower()}.md")
        self.changelog.log_navigation_event("SYSTEM_INIT", "Base controller initialized", 
                                          data={"problem_type": self.config.get('problem_type', 'BASE'),
                                                "map_type": self.config.get('map_type', 'unknown')})
        
        # State management
        self.current_state = None
        self.state_change_time = rospy.get_time()
        self.latest_scan = None
        self.latest_image = None
        
        # Navigation state
        self.current_node_id = self.navigator.start_node
        self.target_node_id = None
        self.planned_path = None
        self.banned_edges = []
        
        # Initialize sensors
        self.detector = SimpleOppositeDetector()
        rospy.Subscriber('/scan', LaserScan, self.detector.callback)
        rospy.Subscriber('/csi_cam_0/image_raw', Image, self.camera_callback)
        
        rospy.loginfo("Base Controller khởi tạo hoàn tất.")

    def get_default_config(self):
        """Override trong subclass để custom config"""
        return {
            'map_token': '28b8940a37ed20635f0d72dd1a555520',
            'map_type': 'map_z',
            'use_api_map': True,
            'base_speed': 0.16,
            'turn_speed': 0.2,
            'yolo_conf_threshold': 0.6,
            'problem_type': 'BASE'  # Override trong subclass
        }

    def setup_parameters(self):
        """Setup tất cả parameters từ config"""
        self.WIDTH, self.HEIGHT = 300, 300
        self.BASE_SPEED = self.config.get('base_speed', 0.16)
        self.TURN_SPEED = self.config.get('turn_speed', 0.2)
        self.TURN_DURATION_90_DEG = 0.8
        
        # ROI settings
        self.ROI_Y = int(self.HEIGHT * 0.85)
        self.ROI_H = int(self.HEIGHT * 0.15)
        self.ROI_CENTER_WIDTH_PERCENT = 0.5
        self.LOOKAHEAD_ROI_Y = int(self.HEIGHT * 0.60)
        self.LOOKAHEAD_ROI_H = int(self.HEIGHT * 0.15)
        
        # Navigation settings
        self.CORRECTION_GAIN = 0.5
        self.SAFE_ZONE_PERCENT = 0.3
        self.LINE_COLOR_LOWER = np.array([0, 0, 0])
        self.LINE_COLOR_UPPER = np.array([180, 255, 75])
        self.INTERSECTION_CLEARANCE_DURATION = 5
        self.INTERSECTION_APPROACH_DURATION = 0.8
        self.LINE_REACQUIRE_TIMEOUT = 3.0
        self.SCAN_PIXEL_THRESHOLD = 100
        self.MAX_CORRECTION_ADJ = 0.12
        
        # YOLO settings
        self.YOLO_MODEL_PATH = "models/best.onnx"
        self.YOLO_CONF_THRESHOLD = self.config.get('yolo_conf_threshold', 0.6)
        self.YOLO_INPUT_SIZE = (640, 640)
        self.YOLO_CLASS_NAMES = ['N', 'E', 'W', 'S', 'NN', 'NE', 'NW', 'NS', 'math']
        self.PRESCRIPTIVE_SIGNS = {'N', 'E', 'W', 'S'}
        self.PROHIBITIVE_SIGNS = {'NN', 'NE', 'NW', 'NS'}
        self.DATA_ITEMS = {'qr_code', 'math_problem'}
        
        # Direction settings
        self.DIRECTIONS = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        self.current_direction_index = 1  # Start facing EAST
        self.ANGLE_TO_FACE_SIGN_MAP = {d: a for d, a in zip(self.DIRECTIONS, [45, -45, -135, 135])}
        
        # Map settings
        self.API_TOKEN = self.config.get('map_token')
        self.MAP_TYPE = self.config.get('map_type', 'map_z')
        self.USE_API_MAP = self.config.get('use_api_map', True)
        self.MAP_FILE_PATH = "map.json"
        
        # MQTT settings
        self.MQTT_BROKER = "localhost"
        self.MQTT_PORT = 1883
        self.MQTT_DATA_TOPIC = "jetbot/corrected_event_data"
        
        # Video settings
        self.VIDEO_OUTPUT_FILENAME = f'jetbot_run_{self.config.get("problem_type", "base")}.avi'
        self.VIDEO_FPS = 20
        self.VIDEO_FOURCC = cv2.VideoWriter_fourcc(*'MJPG')
        
        # Direction mapping
        self.LABEL_TO_DIRECTION_ENUM = {
            'N': Direction.NORTH, 'E': Direction.EAST, 
            'S': Direction.SOUTH, 'W': Direction.WEST
        }

    def initialize_hardware(self):
        """Khởi tạo robot hardware"""
        try:
            self.robot = Robot()
            rospy.loginfo("✅ JetBot hardware initialized")
        except Exception as e:
            rospy.logwarn(f"⚠️ JetBot hardware not found, using Mock. Error: {e}")
            from unittest.mock import Mock
            self.robot = Mock()

    def initialize_yolo(self):
        """Khởi tạo YOLO model"""
        try:
            self.yolo_session = ort.InferenceSession(
                self.YOLO_MODEL_PATH, 
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            rospy.loginfo("✅ YOLO model loaded successfully")
        except Exception as e:
            rospy.logerr(f"❌ Cannot load YOLO model from '{self.YOLO_MODEL_PATH}': {e}")
            self.yolo_session = None

    def initialize_mqtt(self):
        """Khởi tạo MQTT client"""
        self.mqtt_client = mqtt.Client()
        def on_connect(client, userdata, flags, rc): 
            rospy.loginfo(f"MQTT: {'✅ Connected' if rc == 0 else '❌ Failed'}")
        self.mqtt_client.on_connect = on_connect
        try:
            self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e: 
            rospy.logerr(f"❌ MQTT connection failed: {e}")

    def initialize_video_writer(self):
        """Khởi tạo video writer"""
        try:
            frame_size = (self.WIDTH, self.HEIGHT)
            self.video_writer = cv2.VideoWriter(
                self.VIDEO_OUTPUT_FILENAME, 
                self.VIDEO_FOURCC, 
                self.VIDEO_FPS, 
                frame_size
            )
            if self.video_writer.isOpened():
                rospy.loginfo(f"✅ Video recording: {self.VIDEO_OUTPUT_FILENAME}")
            else:
                rospy.logerr("❌ Cannot open video file")
                self.video_writer = None
        except Exception as e:
            rospy.logerr(f"❌ Video writer error: {e}")
            self.video_writer = None

    def initialize_map_navigator(self):
        """Khởi tạo map navigator với config"""
        if self.USE_API_MAP:
            rospy.loginfo(f"🌐 Loading map from API (token: {self.API_TOKEN[:8]}..., type: {self.MAP_TYPE})")
            self.navigator = MapNavigator.create_from_api(self.API_TOKEN, self.MAP_TYPE)
        else:
            rospy.loginfo(f"📁 Loading map from file: {self.MAP_FILE_PATH}")
            self.navigator = MapNavigator.create_from_file(self.MAP_FILE_PATH)

    def camera_callback(self, image_msg):
        """Camera callback - chung cho tất cả problems"""
        try:
            if image_msg.encoding.endswith('compressed'):
                np_arr = np.frombuffer(image_msg.data, np.uint8)
                cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            else:
                cv_image = np.frombuffer(image_msg.data, dtype=np.uint8).reshape(
                    image_msg.height, image_msg.width, -1
                )
            if 'rgb' in image_msg.encoding: 
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            self.latest_image = cv2.resize(cv_image, (self.WIDTH, self.HEIGHT))
        except Exception as e: 
            rospy.logerr(f"❌ Image conversion error: {e}")

    def _set_state(self, new_state, initial=False):
        """Change robot state"""
        if self.current_state != new_state:
            old_state_name = self.current_state.name if self.current_state else "NONE"
            new_state_name = new_state.name
            
            if not initial: 
                rospy.loginfo(f"🔄 State: {old_state_name} → {new_state_name}")
                
                # Log to changelog with context
                context = {
                    'node_id': getattr(self, 'current_node_id', 'unknown'),
                    'elapsed_time': f"{rospy.get_time() - self.state_change_time:.2f}s"
                }
                if hasattr(self, 'latest_scan') and self.latest_scan:
                    context['front_distance'] = min(self.latest_scan.ranges[len(self.latest_scan.ranges)//2-5:len(self.latest_scan.ranges)//2+5])
                
                self.changelog.log_state_change(old_state_name, new_state_name, context)
            
            self.current_state = new_state
            self.state_change_time = rospy.get_time()

    def _get_line_center(self, image, roi_y, roi_h):
        """Detect line center in ROI"""
        if image is None: return None
        roi = image[roi_y : roi_y + roi_h, :]
        
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        color_mask = cv2.inRange(hsv, self.LINE_COLOR_LOWER, self.LINE_COLOR_UPPER)
        
        # Focus mask for center area
        focus_mask = np.zeros_like(color_mask)
        roi_height, roi_width = focus_mask.shape
        center_width = int(roi_width * self.ROI_CENTER_WIDTH_PERCENT)
        start_x = (roi_width - center_width) // 2
        end_x = start_x + center_width
        cv2.rectangle(focus_mask, (start_x, 0), (end_x, roi_height), 255, -1)
        
        final_mask = cv2.bitwise_and(color_mask, focus_mask)
        contours, _, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours: return None
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < self.SCAN_PIXEL_THRESHOLD: return None

        M = cv2.moments(c)
        if M["m00"] > 0:
            return int(M["m10"] / M["m00"])
        return None

    def correct_course(self, line_center_x):
        """Line following with limited correction"""
        error = line_center_x - (self.WIDTH / 2)
        
        if abs(error) < (self.WIDTH / 2) * self.SAFE_ZONE_PERCENT:
            self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
            return

        adj = (error / (self.WIDTH / 2)) * self.CORRECTION_GAIN
        adj = np.clip(adj, -self.MAX_CORRECTION_ADJ, self.MAX_CORRECTION_ADJ)
        
        left_motor = self.BASE_SPEED + adj
        right_motor = self.BASE_SPEED - adj
        self.robot.set_motors(left_motor, right_motor)

    def turn_robot(self, degrees, update_main_direction=True):
        """Turn robot by specified degrees"""
        duration = abs(degrees) / 90.0 * self.TURN_DURATION_90_DEG
        if degrees > 0: 
            self.robot.set_motors(self.TURN_SPEED, -self.TURN_SPEED)
        elif degrees < 0: 
            self.robot.set_motors(-self.TURN_SPEED, self.TURN_SPEED)
            
        if degrees != 0: 
            start_time = rospy.get_time()
            while rospy.get_time() - start_time < duration:
                self._record_frame()
                rospy.sleep(1.0 / self.VIDEO_FPS)

        self.robot.stop()
        if update_main_direction and degrees % 90 == 0 and degrees != 0:
            num_turns = round(degrees / 90)
            self.current_direction_index = (self.current_direction_index + num_turns + 4) % 4
            rospy.loginfo(f"🧭 New direction: {self.DIRECTIONS[self.current_direction_index].name}")
        time.sleep(0.5)
        self._record_frame()

    def detect_with_yolo(self, image):
        """YOLO object detection"""
        if self.yolo_session is None or image is None: 
            return []

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
        
        boxes = np.column_stack((x1, y1, x2, y2)).tolist()
        indices = self.numpy_nms(np.array(boxes), scores, 0.45)
        
        final_detections = []
        for i in indices.flatten():
            final_detections.append({
                'class_name': self.YOLO_CLASS_NAMES[class_ids[i]],
                'confidence': float(scores[i]),
                'box': [int(coord) for coord in boxes[i]]
            })

        return final_detections

    def numpy_nms(self, boxes, scores, iou_threshold):
        """Non-Maximum Suppression"""
        x1 = np.array([b[0] for b in boxes])
        y1 = np.array([b[1] for b in boxes])
        x2 = np.array([b[2] for b in boxes])
        y2 = np.array([b[3] for b in boxes])

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            intersection = w * h
            
            iou = intersection / (areas[i] + areas[order[1:]] - intersection)
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return np.array(keep)

    def _record_frame(self):
        """Record frame to video"""
        if self.video_writer is not None and self.latest_image is not None:
            debug_frame = self.draw_debug_info(self.latest_image)
            if debug_frame is not None:
                self.video_writer.write(debug_frame)

    def draw_debug_info(self, image):
        """Draw debug information on frame"""
        if image is None: return None
        debug_frame = image.copy()
        
        # Draw ROIs
        cv2.rectangle(debug_frame, (0, self.ROI_Y), (self.WIDTH-1, self.ROI_Y + self.ROI_H), (0, 255, 0), 1)
        cv2.rectangle(debug_frame, (0, self.LOOKAHEAD_ROI_Y), (self.WIDTH-1, self.LOOKAHEAD_ROI_Y + self.LOOKAHEAD_ROI_H), (0, 255, 255), 1)

        # Draw state
        state_text = f"State: {self.current_state.name if self.current_state else 'INIT'}"
        cv2.putText(debug_frame, state_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw problem type
        problem_text = f"Problem: {self.config.get('problem_type', 'BASE')}"
        cv2.putText(debug_frame, problem_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        return debug_frame

    def publish_data(self, data):
        """Publish data via MQTT and API"""
        try:
            data_json = json.dumps(data)
            self.mqtt_client.publish(self.MQTT_DATA_TOPIC, data_json)
            rospy.loginfo(f"📤 Published to MQTT: {data}")
            
            # Submit to API if available
            self.submit_sign_detection(data)
            
        except Exception as e:
            rospy.logerr(f"❌ Publish data error: {e}")

    def submit_sign_detection(self, sign_data):
        """Submit sign detection to API using api_utils"""
        try:
            api_client = create_api_client(self.API_TOKEN)
            
            # Prepare submission text based on sign type
            sign_type = sign_data.get('type', 'UNKNOWN')
            sign_value = sign_data.get('value', '')
            
            if sign_type == 'QR_CODE':
                text = f"QR:{sign_value}"
            elif sign_type == 'MATH_PROBLEM':
                text = f"MATH:{sign_value}"
            else:
                text = f"{sign_type}:{sign_value}"
            
            # Submit using api_utils
            success = api_client.submit_sign(
                text=text,
                node_id=str(self.current_node_id),
                map_type=self.MAP_TYPE
            )
            
            return success
                
        except Exception as e:
            rospy.logerr(f"❌ Sign submit error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        rospy.loginfo("🧹 Cleaning up...")
        if hasattr(self, 'robot') and self.robot is not None:
            self.robot.stop()
        if hasattr(self, 'video_writer') and self.video_writer is not None:
            self.video_writer.release()
        if hasattr(self, 'detector') and self.detector is not None:
            self.detector.stop_scanning()
        if hasattr(self, 'mqtt_client') and self.mqtt_client is not None:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
        # Finalize changelog
        if hasattr(self, 'changelog') and self.changelog:
            final_state = self.current_state.name if self.current_state else "UNKNOWN"
            self.changelog.finalize_session(f"CLEANUP_{final_state}")
            
        rospy.loginfo("✅ Cleanup completed")

    # Abstract methods - override trong subclass
    def run(self):
        """Main run loop - MUST override trong subclass"""
        raise NotImplementedError("Subclass must implement run() method")
        
    def handle_intersection(self):
        """Handle intersection - MUST override trong subclass"""  
        raise NotImplementedError("Subclass must implement handle_intersection() method")
    
    # Helper methods for logging
    def log_intersection_detection(self, intersection_type: str = "unknown"):
        """Log intersection detection with LIDAR data"""
        lidar_data = {}
        node_data = {'current_node': self.current_node_id}
        
        # Get LIDAR data if available
        if hasattr(self, 'detector') and self.detector and self.detector.latest_scan:
            scan = self.detector.latest_scan
            ranges = np.array(scan.ranges)
            ranges = np.nan_to_num(ranges, nan=float('inf'), posinf=float('inf'))
            
            n = len(ranges)
            front_idx = n // 2
            left_idx = 3 * n // 4
            right_idx = n // 4
            
            lidar_data = {
                'front_distance': float(ranges[front_idx]),
                'left_distance': float(ranges[left_idx]),
                'right_distance': float(ranges[right_idx]),
                'total_points': int(n)
            }
        
        # Add navigation context
        if hasattr(self, 'target_node_id') and self.target_node_id:
            node_data['target_node'] = self.target_node_id
        if hasattr(self, 'planned_path') and self.planned_path:
            node_data['path_length'] = len(self.planned_path)
            
        self.changelog.log_intersection_detected(intersection_type, lidar_data, node_data)
    
    def log_lidar_obstacle(self, description: str, min_distance: float = None):
        """Log LIDAR obstacle detection"""
        scan_data = {}
        if min_distance is not None:
            scan_data['min_distance'] = min_distance
            
        if hasattr(self, 'detector') and self.detector and self.detector.latest_scan:
            scan = self.detector.latest_scan
            ranges = np.array(scan.ranges)
            ranges = np.nan_to_num(ranges, nan=float('inf'), posinf=float('inf'))
            scan_data.update({
                'avg_distance': float(np.mean(ranges[np.isfinite(ranges)])),
                'scan_points': int(len(ranges))
            })
            
        self.changelog.log_lidar_event(description, scan_data)
    
    def log_navigation_decision(self, action: str, details: str, **data):
        """Log navigation decision"""
        self.changelog.log_navigation_event(action, details, data)

    def plan_initial_route(self):
        """Plan initial route - CÓ THỂ override trong subclass"""
        rospy.loginfo(f"📍 Planning route from {self.navigator.start_node} to {self.navigator.end_node}...")
        self.planned_path = self.navigator.find_path(
            self.navigator.start_node, 
            self.navigator.end_node,
            self.banned_edges
        )
        if self.planned_path and len(self.planned_path) > 1:
            self.target_node_id = self.planned_path[1]
            rospy.loginfo(f"✅ Path found: {self.planned_path}. Next target: {self.target_node_id}")
        else:
            rospy.logerr("❌ No valid path found!")
            self._set_state(RobotState.DEAD_END)