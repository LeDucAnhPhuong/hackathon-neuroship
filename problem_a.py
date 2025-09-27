#!/usr/bin/env python3
"""
Problem A Controller - Ke thua tu BaseJetBotController
Navigation don gian tu Start -> End
"""

import rospy
from base_controller import BaseJetBotController, RobotState

class ProblemAController(BaseJetBotController):
    """Controller cho Problem A - Basic Navigation"""
    
    def __init__(self, custom_config=None):
        # Config cho Problem A
        problem_a_config = {
            'problem_type': 'PROBLEM_A',
            'base_speed': 0.18,  # Toc do an toan cho Problem A
            'map_type': 'map_z',  # Default map type
            'yolo_conf_threshold': 0.7,  # Cao hon cho do chinh xac
            'use_api_map': True
        }
        
        # Merge voi custom config neu co
        if custom_config:
            problem_a_config.update(custom_config)
            
        super().__init__(problem_a_config)
        self.plan_initial_route()
        rospy.loginfo("Problem A Controller initialized")

    def run(self):
        """Main control loop cho Problem A"""
        rospy.loginfo("Problem A: Starting basic navigation...")
        rospy.loginfo("Waiting 3 seconds...")
        rospy.sleep(3)
        
        rospy.loginfo("Problem A journey begins!")
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
                        rospy.loginfo("GOAL REACHED! Problem A completed!")
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
                        rospy.loginfo("GOAL REACHED! Problem A completed!")
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
                rospy.loginfo("PROBLEM A COMPLETED SUCCESSFULLY!")
                self.robot.stop()
                break

            self._record_frame()
            rate.sleep()
            
        self.cleanup()

    def handle_intersection(self):
        """Handle intersection cho Problem A - chi navigation don gian"""
        rospy.loginfo("[PROBLEM A] Processing intersection...")
        self.robot.stop()
        rospy.sleep(0.5)

        # Problem A: Khong can YOLO detection, chi follow map plan
        rospy.loginfo("Following map navigation plan...")
        
        # Get next direction from planned path
        planned_direction_label = self.navigator.get_next_direction_label(self.current_node_id, self.planned_path)
        if not planned_direction_label:
            rospy.logerr("No next direction found in plan!")
            self._set_state(RobotState.DEAD_END)
            return
        
        # Convert to relative action
        current_direction = self.DIRECTIONS[self.current_direction_index]
        planned_action = self.map_absolute_to_relative(planned_direction_label, current_direction)
        rospy.loginfo(f"Plan: Go {planned_action} (direction {planned_direction_label})")

        # Execute the planned action
        if planned_action == 'straight':
            rospy.loginfo("[DECISION] GO STRAIGHT")
        elif planned_action == 'right':
            rospy.loginfo("[DECISION] TURN RIGHT")
            self.turn_robot(90, True)
        elif planned_action == 'left':
            rospy.loginfo("[DECISION] TURN LEFT")
            self.turn_robot(-90, True)
        else:
            rospy.logwarn("[DECISION] DEAD END - Invalid action")
            self._set_state(RobotState.DEAD_END)
            return
        
        # Update next target node
        next_node_id = self.planned_path[self.planned_path.index(self.current_node_id) + 1]
        self.target_node_id = next_node_id
        rospy.loginfo(f"Next target: node {self.target_node_id}")
        
        self._set_state(RobotState.LEAVING_INTERSECTION)

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
    rospy.init_node('problem_a_controller', anonymous=True)
    try:
        # Custom config cho Problem A neu can
        custom_config = {
            # 'map_type': 'map_a',  # Uncomment neu co map rieng cho Problem A
            # 'base_speed': 0.15,   # Uncomment de dieu chinh toc do
        }
        
        controller = ProblemAController(custom_config)
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Problem A node interrupted")
    except Exception as e:
        rospy.logerr(f"Problem A error: {e}", exc_info=True)

if __name__ == '__main__':
    main()