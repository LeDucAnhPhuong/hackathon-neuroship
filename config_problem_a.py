# Configuration for Problem A
# Override any base controller settings here

# Team token - centralized
TEAM_TOKEN = '28b8940a37ed20635f0d72dd1a555520'

PROBLEM_A_CONFIG = {
    'problem_type': 'PROBLEM_A',
    'base_speed': 0.18,          # Safety first for guaranteed points
    'turn_speed': 0.2,
    'map_type': 'map_a',         # Problem A specific map (available after 27h)
    'map_token': TEAM_TOKEN,
    'use_api_map': True,         # Set False to use local map.json
    'yolo_conf_threshold': 0.7,  # Higher for accuracy
    
    # Problem A specific
    'enable_yolo_detection': False,  # Problem A doesn't need YOLO
    'enable_sign_processing': False,
    'max_load_nodes': 0,            # No load nodes for Problem A
    
    # Speed optimization for Problem A
    'intersection_approach_duration': 0.4,
    'intersection_clearance_duration': 1.2,
    'line_reacquire_timeout': 2.5,
}

# Alternative map configurations
PROBLEM_A_CONFIGS = {
    'development': {
        **PROBLEM_A_CONFIG,
        'map_type': 'map_z',  # Use map_z for testing/development
        'base_speed': 0.15,   # Extra safe for development
    },
    
    'safe': {
        **PROBLEM_A_CONFIG,
        'base_speed': 0.15,
        'yolo_conf_threshold': 0.8,
    },
    
    'fast': {
        **PROBLEM_A_CONFIG, 
        'base_speed': 0.22,
        'intersection_clearance_duration': 1.0,
    },
    
    'custom_map': {
        **PROBLEM_A_CONFIG,
        'map_type': 'map_a',  # If you have specific map for Problem A
    }
}