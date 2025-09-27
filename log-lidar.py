#!/usr/bin/env python3
import math
import rospy
from sensor_msgs.msg import LaserScan

def scan_cb(msg: LaserScan):
    # Lấy các giá trị range hợp lệ
    valid = [
        (i, r) for i, r in enumerate(msg.ranges)
        if math.isfinite(r) and msg.range_min <= r <= msg.range_max
    ]
    if not valid:
        rospy.logwarn("No valid LiDAR points")
        return

    # Tìm khoảng cách gần nhất và góc tương ứng
    i_min, r_min = min(valid, key=lambda t: t[1])
    angle_min = msg.angle_min + i_min * msg.angle_increment  # rad

    rospy.loginfo(f"Min dist = {r_min:.3f} m at angle = {angle_min:.3f} rad")

    # Chuyển toàn bộ scan -> XY (option: giảm mẫu để nhẹ CPU)
    points_xy = []
    for i, r in valid[::3]:  # lấy cách 3 điểm để nhẹ
        a = msg.angle_min + i * msg.angle_increment
        x = r * math.cos(a)
        y = r * math.sin(a)
        points_xy.append((x, y))
    # Ví dụ: in 5 điểm đầu
    rospy.loginfo(f"Sample XY: {points_xy[:5]}")

def main():
    rospy.init_node("lidar_listener")
    rospy.Subscriber("/scan", LaserScan, scan_cb, queue_size=1)
    rospy.loginfo("Listening /scan ...")
    rospy.spin()

if __name__ == "__main__":
    main()
