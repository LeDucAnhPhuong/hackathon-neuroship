#!/usr/bin/env python3
"""
Problem B Controller - Ke thua tu BaseJetBotController  
Multi-task navigation: Load nodes + Sign reading + End
"""

import rospy
from base_controller import BaseJetBotController, RobotState

class ProblemBController(BaseJetBotController):
    """Controller cho Problem B - Multi-task Navigation"""
    
    def __init__(self, custom_config=None):
        # Config cho Problem B
        problem_b_config = {
            'problem_type': 'PROBLEM_B',
            'base_speed': 0.16,  # Toc do can bang cho detection
            'map_type': 'map_z',  # Default map type
            'yolo_conf_threshold': 0.6,  # Thap hon cho detection tot hon
            'use_api_map': True
        }
        
        # Merge voi custom config neu co
        if custom_config:
            problem_b_config.update(custom_config)
            
        super().__init__(problem_b_config)
        
        # Problem B specific attributes
        self.load_nodes_visited = set()  # Track visited load nodes
        self.signs_detected = []  # Track detected signs
        self.current_task = 'navigation'  # 'navigation', 'loading', 'completed'
        
        self.plan_initial_route()
        rospy.loginfo("Problem B Controller initialized")

    def run(self):
        """Main control loop cho Problem B"""
        rospy.loginfo("Problem B: Starting multi-task navigation...")
        rospy.loginfo("Tasks: 1) Visit load nodes, 2) Read signs, 3) Reach end")
        rospy.loginfo("Waiting 3 seconds...")
        rospy.sleep(3)
        
        rospy.loginfo("Problem B journey begins!")
        self.detector.start_scanning()
        self._set_state(RobotState.WAITING_FOR_LINE, initial=True)
        
        rate = rospy.Rate(20)
        while not rospy.is_shutdown():
            
            # STATE: WAITING FOR LINE
            if self.current_state == RobotState.WAITING_FOR_LINE:
                rospy.loginfo_throttle(5, "Waiting for line to start...")
                self.robot.stop()

                if self.latest_image is None:
                    rate.sleep()
                    continue
                
                lookahead_line = self._get_line_center(self.latest_image, self.LOOKAHEAD_ROI_Y, self.LOOKAHEAD_ROI_H)
                execution_line = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)

                if lookahead_line is not None and execution_line is not None:
                    rospy.loginfo("Line detected! Starting journey...")
                    self._set_state(RobotState.DRIVING_STRAIGHT)
            
            # STATE: DRIVING STRAIGHT
            elif self.current_state == RobotState.DRIVING_STRAIGHT:
                if self.latest_image is None:
                    rospy.logwarn_throttle(5, "Waiting for camera data...")
                    self.robot.stop()
                    rate.sleep()
                    continue

                # Priority 1: LiDAR intersection detection
                if self.detector.process_detection():
                    rospy.loginfo("INTERSECTION DETECTED (LiDAR)")
                    self.robot.stop()
                    rospy.sleep(0.5)

                    self.current_node_id = self.target_node_id
                    rospy.loginfo(f"Arrived at node {self.current_node_id}")

                    if self.current_node_id == self.navigator.end_node:
                        rospy.loginfo("GOAL REACHED! Problem B completed!")
                        self._set_state(RobotState.GOAL_REACHED)
                    else:
                        self._set_state(RobotState.HANDLING_EVENT)
                        self.handle_intersection()
                    continue

                # Priority 2: Visual line prediction
                lookahead_line_center = self._get_line_center(self.latest_image, self.LOOKAHEAD_ROI_Y, self.LOOKAHEAD_ROI_H)
                if lookahead_line_center is None:
                    rospy.logwarn("INTERSECTION APPROACHING (Vision)")
                    self._set_state(RobotState.APPROACHING_INTERSECTION)
                    continue

                # Priority 3: Normal line following
                execution_line_center = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)
                if execution_line_center is not None:
                    self.correct_course(execution_line_center)
                else:
                    rospy.logwarn("Line inconsistency detected. Stopping for safety.")
                    self.robot.stop()

            # STATE: APPROACHING INTERSECTION
            elif self.current_state == RobotState.APPROACHING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_APPROACH_DURATION:
                    rospy.loginfo("Reached intersection center")
                    self.robot.stop()
                    rospy.sleep(0.5)

                    self.current_node_id = self.target_node_id
                    rospy.loginfo(f"Arrived at node {self.current_node_id}")

                    if self.current_node_id == self.navigator.end_node:
                        rospy.loginfo("GOAL REACHED! Problem B completed!")
                        self._set_state(RobotState.GOAL_REACHED)
                    else:
                        self._set_state(RobotState.HANDLING_EVENT)
                        self.handle_intersection()

            # STATE: LEAVING INTERSECTION
            elif self.current_state == RobotState.LEAVING_INTERSECTION:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                if rospy.get_time() - self.state_change_time > self.INTERSECTION_CLEARANCE_DURATION:
                    rospy.loginfo("Cleared intersection. Searching for line...")
                    self._set_state(RobotState.REACQUIRING_LINE)
            
            # STATE: REACQUIRING LINE
            elif self.current_state == RobotState.REACQUIRING_LINE:
                self.robot.set_motors(self.BASE_SPEED, self.BASE_SPEED)
                line_center_x = self._get_line_center(self.latest_image, self.ROI_Y, self.ROI_H)
                
                if line_center_x is not None:
                    rospy.loginfo("Line reacquired! Resuming navigation...")
                    self._set_state(RobotState.DRIVING_STRAIGHT)
                    continue
                
                if rospy.get_time() - self.state_change_time > self.LINE_REACQUIRE_TIMEOUT:
                    rospy.logerr("Cannot find line after intersection")
                    self._set_state(RobotState.DEAD_END)

            # TERMINAL STATES
            elif self.current_state == RobotState.DEAD_END:
                rospy.logerr("Dead end reached. Stopping...")
                self.robot.stop()
                break
            elif self.current_state == RobotState.GOAL_REACHED:
                rospy.loginfo("PROBLEM B COMPLETED SUCCESSFULLY!")
                rospy.loginfo(f"Load nodes visited: {len(self.load_nodes_visited)}")
                rospy.loginfo(f"Signs detected: {len(self.signs_detected)}")
                self.robot.stop()
                break

            self._record_frame()
            rate.sleep()
            
        self.cleanup()

    def handle_intersection(self):
        """Handle intersection cho Problem B - co YOLO detection va task management"""
        rospy.loginfo("[PROBLEM B] Processing intersection...")
        self.robot.stop()
        rospy.sleep(0.5)

        # Check if this is a load node
        is_load_node = self.is_load_node(self.current_node_id)
        if is_load_node and self.current_node_id not in self.load_nodes_visited:
            rospy.loginfo(f"LOAD NODE {self.current_node_id} - Processing tasks...")
            self.load_nodes_visited.add(self.current_node_id)

        # YOLO Detection for signs
        current_direction = self.DIRECTIONS[self.current_direction_index]
        angle_to_sign = self.ANGLE_TO_FACE_SIGN_MAP.get(current_direction, 0)
        self.turn_robot(angle_to_sign, False)
        image_info = self.latest_image
        detections = self.detect_with_yolo(image_info)
        self.turn_robot(-angle_to_sign, False)
        
        prescriptive_cmds = {det['class_name'] for det in detections if det['class_name'] in self.PRESCRIPTIVE_SIGNS}
        prohibitive_cmds = {det['class_name'] for det in detections if det['class_name'] in self.PROHIBITIVE_SIGNS}
        data_items = [det for det in detections if det['class_name'] in self.DATA_ITEMS]

        # Process data items (QR, Math)
        rospy.loginfo("[STEP 2] Processing data items...")
        for item in data_items:
            if item['class_name'] == 'qr_code':
                rospy.loginfo("Found QR Code. Processing...")
                # Real QR code processing would be here
                qr_data = {'type': 'QR_CODE', 'value': 'simulated_qr_123', 'node': self.current_node_id}
                self.signs_detected.append(qr_data)
                self.publish_data(qr_data)

            elif item['class_name'] == 'math_problem':
                rospy.loginfo("Found Math Problem. Solving...")
                # Real math processing would be here  
                math_data = {'type': 'MATH_PROBLEM', 'value': '2+2=4', 'node': self.current_node_id}
                self.signs_detected.append(math_data)
                self.publish_data(math_data)
        
        # Navigation logic with sign commands
        rospy.loginfo("[STEP 3] Planning navigation with sign commands...")
        
        final_decision = None
        is_deviation = False
        
        while True:
            planned_direction_label = self.navigator.get_next_direction_label(self.current_node_id, self.planned_path)
            if not planned_direction_label:
                rospy.logerr("No next direction found in plan!")
                self._set_state(RobotState.DEAD_END)
                return
            
            planned_action = self.map_absolute_to_relative(planned_direction_label, current_direction)
            rospy.loginfo(f"A* Plan suggests: Go {planned_action} (direction {planned_direction_label})")

            # Priority 1: Prescriptive signs override plan
            intended_action = None
            if 'N' in prescriptive_cmds: intended_action = self.map_absolute_to_relative('N', current_direction)
            elif 'E' in prescriptive_cmds: intended_action = self.map_absolute_to_relative('E', current_direction)  
            elif 'S' in prescriptive_cmds: intended_action = self.map_absolute_to_relative('S', current_direction)
            elif 'W' in prescriptive_cmds: intended_action = self.map_absolute_to_relative('W', current_direction)
            
            # Priority 2: Follow plan if no prescriptive signs
            if intended_action is None:
                intended_action = planned_action
            else:
                if intended_action != planned_action:
                    is_deviation = True
                    rospy.logwarn(f"DEVIATION! Prescriptive sign ({intended_action}) overrides plan ({planned_action}).")

            # Priority 3: Check prohibitive signs
            is_prohibited = (intended_action == 'straight' and 'NS' in prohibitive_cmds) or \
                           (intended_action == 'right' and 'NE' in prohibitive_cmds) or \
                           (intended_action == 'left' and 'NW' in prohibitive_cmds)

            if is_prohibited:
                rospy.logwarn(f"Intended action '{intended_action}' is PROHIBITED!")
                
                if is_deviation:
                    rospy.logerr("MAP ERROR! Prescriptive sign conflicts with prohibitive sign.")
                    self._set_state(RobotState.DEAD_END)
                    return
                
                # Add banned edge and replan
                banned_edge = (self.current_node_id, self.planned_path[self.planned_path.index(self.current_node_id) + 1])
                if banned_edge not in self.banned_edges:
                    self.banned_edges.append(banned_edge)
                
                rospy.loginfo(f"Adding banned edge {banned_edge} and replanning...")
                new_path = self.navigator.find_path(self.current_node_id, self.navigator.end_node, self.banned_edges)
                
                if new_path:
                    self.planned_path = new_path
                    rospy.loginfo(f"New path found: {self.planned_path}")
                    continue
                else:
                    rospy.logerr("Cannot find alternative path after prohibition.")
                    self._set_state(RobotState.DEAD_END)
                    return
            
            final_decision = intended_action
            break

        # Execute decision
        if final_decision == 'straight':
            rospy.loginfo("[FINAL] Decision: GO STRAIGHT")
        elif final_decision == 'right':
            rospy.loginfo("[FINAL] Decision: TURN RIGHT")
            self.turn_robot(90, True)
        elif final_decision == 'left':
            rospy.loginfo("[FINAL] Decision: TURN LEFT")
            self.turn_robot(-90, True)
        else:
            rospy.logwarn("[FINAL] DEAD END! No valid paths found.")
            self._set_state(RobotState.DEAD_END)
            return
        
        # Update next target node
        if not is_deviation:
            next_node_id = self.planned_path[self.planned_path.index(self.current_node_id) + 1]
        else:
            # Find next node based on executed action
            new_robot_direction = self.DIRECTIONS[self.current_direction_index]
            executed_direction_label = None
            for label, direction_enum in self.LABEL_TO_DIRECTION_ENUM.items():
                if direction_enum == new_robot_direction:
                    executed_direction_label = label
                    break
            
            next_node_id = self.navigator.get_neighbor_by_direction(self.current_node_id, executed_direction_label)
            if next_node_id is None:
                rospy.logerr("MAP ERROR! No corresponding node after turn.")
                self._set_state(RobotState.DEAD_END)
                return
            
            # Replan from new position
            rospy.loginfo(f"Replanning from new position {next_node_id}...")
            new_path = self.navigator.find_path(next_node_id, self.navigator.end_node, self.banned_edges)
            if new_path:
                self.planned_path = new_path
                rospy.loginfo(f"New path after deviation: {self.planned_path}")
            else:
                rospy.logerr("Cannot find path to destination from new position.")
                self._set_state(RobotState.DEAD_END)
                return

        self.target_node_id = next_node_id
        rospy.loginfo(f"Next target: node {self.target_node_id}")
        self._set_state(RobotState.LEAVING_INTERSECTION)

    def is_load_node(self, node_id):
        """Check if node is a load node (Problem B specific logic)"""
        # This would be based on map data or node properties
        # For now, assume nodes with certain IDs are load nodes
        # You should implement this based on your map structure
        node_data = self.navigator.nodes_data.get(node_id, {})
        return node_data.get('type') == 'load' or node_data.get('has_load', False)

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

def main():
    rospy.init_node('problem_b_controller', anonymous=True)
    try:
        # Custom config cho Problem B neu can
        custom_config = {
            # 'map_type': 'map_b',      # Uncomment neu co map rieng
            # 'base_speed': 0.14,       # Uncomment de dieu chinh toc do
            # 'yolo_conf_threshold': 0.5  # Uncomment de dieu chinh threshold
        }
        
        controller = ProblemBController(custom_config)
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Problem B node interrupted")
    except Exception as e:
        rospy.logerr(f"Problem B error: {e}", exc_info=True)

if __name__ == '__main__':
    main()