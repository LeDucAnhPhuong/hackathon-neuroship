# Configuration for Problem B
# Override any base controller settings here

# Team token - centralized
TEAM_TOKEN = '28b8940a37ed20635f0d72dd1a555520'

PROBLEM_B_CONFIG = {
    'problem_type': 'PROBLEM_B',
    'base_speed': 0.16,          # Balanced for detection and speed
    'turn_speed': 0.2,
    'map_type': 'map_b',         # Problem B specific map (available after 27h)
    'map_token': TEAM_TOKEN,
    'use_api_map': True,         # Set False to use local map.json
    'yolo_conf_threshold': 0.6,  # Lower for better detection coverage
    
    # Problem B specific
    'enable_yolo_detection': True,
    'enable_sign_processing': True, 
    'enable_qr_processing': True,
    'enable_math_processing': True,
    'max_load_nodes': 5,            # Expected number of load nodes
    
    # Detection optimization
    'sign_detection_pause_duration': 1.0,  # Pause for better sign reading
    'multiple_detection_attempts': 3,       # Try multiple times per intersection
    
    # API submission settings
    'auto_submit_detections': True,
    'retry_failed_submissions': True,
    'submission_timeout': 5.0,
}

# Alternative map configurations  
PROBLEM_B_CONFIGS = {
    'detection_focused': {
        **PROBLEM_B_CONFIG,
        'base_speed': 0.14,
        'yolo_conf_threshold': 0.5,
        'sign_detection_pause_duration': 1.5,
    },
    
    'speed_focused': {
        **PROBLEM_B_CONFIG,
        'base_speed': 0.18, 
        'yolo_conf_threshold': 0.7,
        'sign_detection_pause_duration': 0.8,
    },
    
    'custom_map': {
        **PROBLEM_B_CONFIG,
        'map_type': 'map_b',  # If you have specific map for Problem B
    },
    
    'local_testing': {
        **PROBLEM_B_CONFIG,
        'use_api_map': False,
        'auto_submit_detections': False,
        'map_type': 'map_z',
    }
}