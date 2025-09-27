# Robot Changelog System 📝

Hệ thống ghi nhật ký tự động cho robot navigation, ghi lại state changes và LIDAR intersection detection.

## ✨ Features

- 🔄 **State Changes**: Tự động log khi robot chuyển state
- 🚦 **Intersection Detection**: Ghi lại khi LIDAR phát hiện giao lộ  
- 📋 **Navigation Events**: Log các quyết định navigation quan trọng
- 📡 **LIDAR Events**: Theo dõi obstacle detection và sensor data
- ⏰ **Timestamp**: Tất cả events đều có timestamp và elapsed time
- 📊 **Session Summary**: Tổng kết session với statistics

## 📁 Generated Files

- `robot_problem_a.md` - Navigation log cho Problem A
- `robot_problem_b.md` - Navigation log cho Problem B  
- `robot_base.md` - Base controller events
- `state_machine_test.md` - Test session logs

## 🔧 Integration

### 1. Automatic Integration (Đã tích hợp sẵn)

```python
# base_controller.py đã tích hợp sẵn:
from robot_changelog import get_logger

class BaseJetBotController:
    def __init__(self, config=None):
        # Changelog đã được khởi tạo tự động
        self.changelog = get_logger(f"robot_{problem_type}.md")
        
    def _set_state(self, new_state, initial=False):
        # State changes được log tự động
        if self.current_state != new_state:
            self.changelog.log_state_change(old_state, new_state, context)
```

### 2. Manual Logging Methods

```python
# Log intersection detection
self.log_intersection_detection("T_INTERSECTION")

# Log navigation decisions  
self.log_navigation_decision("TURN", "Turning left at intersection",
                           degrees=-90, reason="shortest_path")

# Log LIDAR obstacles
self.log_lidar_obstacle("Wall detected", min_distance=0.18)

# Log general navigation events
self.changelog.log_navigation_event("GOAL_REACHED", "Target reached successfully")
```

### 3. Usage in Problem Controllers

```python
class ProblemAController(BaseJetBotController):
    def handle_driving_straight(self):
        # Check for intersection
        if self.detector.process_detection():
            # Automatically logs intersection with LIDAR data
            self.log_intersection_detection("LIDAR_DETECTED") 
            self._set_state(RobotState.APPROACHING_INTERSECTION)
            
    def handle_intersection(self):
        # Log navigation decision
        self.log_navigation_decision("TURN", "Turning based on path planning",
                                   degrees=turn_angle, target_node=next_node)
        self.turn_robot(turn_angle)
```

## 📋 Log Entry Types

### 🔄 State Changes
```markdown
### 🔄 State Change #1
**Time:** 2025-09-27 17:21:36 (+00:00)  
**Transition:** `WAITING_FOR_LINE` → `DRIVING_STRAIGHT`
**Context:** `speed=0.16, node_id=G, elapsed_time=2.5s`
```

### 🚦 Intersection Detection
```markdown
### 🚦 Intersection #1
**Time:** 2025-09-27 17:21:37 (+00:01)  
**Type:** `T_INTERSECTION`  
**LIDAR:** `front_distance=0.25m, left_open=True, right_blocked=False`  
**Navigation:** `current_node=G, target_node=F`
```

### 🔄 Navigation Events
```markdown
### 🔄 TURN
**Time:** 2025-09-27 17:21:38 (+00:02)  
**Event:** Turning left at intersection  
**Data:** `degrees=-90, duration=0.80, reason=path_planning`
```

### 📋 LIDAR Events
```markdown
### 📋 LIDAR
**Time:** 2025-09-27 17:21:38 (+00:02)  
**Event:** Obstacle detected ahead  
**Data:** `min_distance=0.15, obstacle_angle=0, scan_points=360`
```

## 🎯 Use Cases

### Debugging State Machine
- Track unexpected state transitions
- Monitor state timing and duration  
- Identify stuck states or loops

### Intersection Analysis
- Verify LIDAR intersection detection accuracy
- Analyze intersection approach timing
- Debug navigation decisions at intersections

### Performance Monitoring
- Track navigation success rate
- Monitor average intersection handling time
- Identify problematic areas in map

### Competition Analysis
- Review complete navigation sessions
- Analyze failure points and recovery
- Generate performance reports

## 📊 Session Summary Example

```markdown
## Session Summary
**Duration:** 02:34  
**State Changes:** 15  
**Intersections:** 4  
**Final Status:** `GOAL_REACHED`  
**End Time:** 2025-09-27 17:25:30
```

## 🧪 Testing

```bash
# Test basic functionality
python robot_changelog.py

# Test integration patterns  
python test_changelog_integration.py

# Check generated files
ls *.md
```

## 🔍 Advanced Features

### Thread-Safe Logging
- Sử dụng threading.Lock cho concurrent access
- Safe cho multi-threaded ROS applications

### Context-Aware Logging
- Automatically include LIDAR data when available
- Add navigation context (current/target nodes)
- Include timing information

### Structured Markdown Output
- Easy to read and parse
- Compatible with Markdown viewers
- Clear section organization

## 📈 Benefits

- ✅ **Automated**: No manual logging required for basic events
- ✅ **Comprehensive**: Covers all major robot events  
- ✅ **Readable**: Clean Markdown format
- ✅ **Debugging**: Easy to identify issues
- ✅ **Performance**: Track improvements over time
- ✅ **Competition**: Review and analyze runs

## 🚀 Quick Start

1. Changelog đã được tích hợp vào `base_controller.py`
2. Tất cả state changes được log tự động
3. Thêm manual logging cho events quan trọng:
   ```python
   self.log_intersection_detection("T_INTERSECTION")
   self.log_navigation_decision("TURN", "Turning left", degrees=-90)
   ```
4. Check generated `.md` files để review navigation behavior

## 🎉 Ready to Use!

Hệ thống changelog đã sẵn sàng để debug và monitor robot navigation trong hackathon!