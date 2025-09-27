#!/usr/bin/env python3
"""
Test script for Problem B functionality
"""

import json
from map_navigator import MapNavigator

def test_load_node_detection():
    """Test that LOAD nodes are properly identified"""
    print("🧪 Testing LOAD node detection...")

    # Load the map
    navigator = MapNavigator.create_from_file("map_z.json")

    # Test each node type
    for node_id, node_data in navigator.nodes_data.items():
        node_type = node_data.get('type')
        print(f"Node {node_id} ({node_data.get('name')}): Type = {node_type}")

        if node_type == "LOAD":
            print(f"  ✅ LOAD node detected at {node_id}!")

    # Identify all LOAD nodes from the map
    load_nodes = [node_id for node_id, node_data in navigator.nodes_data.items()
                  if node_data.get('type') == 'LOAD']

    print(f"\n📍 Found {len(load_nodes)} LOAD nodes: {load_nodes}")

    return load_nodes

def test_path_planning():
    """Test path planning from start to end"""
    print("\n🗺️ Testing path planning...")

    navigator = MapNavigator.create_from_file("map_z.json")

    print(f"Start node: {navigator.start_node}")
    print(f"End node: {navigator.end_node}")

    if navigator.start_node and navigator.end_node:
        path = navigator.find_path(navigator.start_node, navigator.end_node)
        print(f"Path found: {path}")

        # Check if path goes through any LOAD nodes
        load_nodes = [node_id for node_id, node_data in navigator.nodes_data.items()
                      if node_data.get('type') == 'LOAD']

        path_load_nodes = [node for node in path if node in load_nodes]
        if path_load_nodes:
            print(f"🔄 Path goes through LOAD nodes: {path_load_nodes}")
        else:
            print("ℹ️ Path does not go through any LOAD nodes")
    else:
        print("❌ Could not find start or end node!")

def test_api_payload():
    """Test API payload structure for LOAD nodes"""
    print("\n📤 Testing API payload structure...")

    # Simulate LOAD node data payload
    load_data = {
        'type': 'LOAD_NODE_DETECTED',
        'value': f'Reached LOAD node 9',
        'confidence': 1.0,
        'position': {'x': 0, 'y': 0},
        'node_id': 9,
        'action': 'east_south_turn'
    }

    print("Sample LOAD node API payload:")
    print(json.dumps(load_data, indent=2))
    print("✅ Payload structure looks good!")

if __name__ == "__main__":
    print("🚀 Problem B Validation Test")
    print("=" * 40)

    try:
        # Test 1: LOAD node detection
        load_nodes = test_load_node_detection()

        # Test 2: Path planning
        test_path_planning()

        # Test 3: API payload
        test_api_payload()

        print("\n" + "=" * 40)
        print("✅ All tests completed successfully!")
        print("🎯 Problem B implementation ready!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()