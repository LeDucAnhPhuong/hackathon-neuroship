#!/usr/bin/env python3

import json
import sys
import os

# Mock rospy for testing
class MockRospy:
    def loginfo(self, msg):
        print(f"[INFO] {msg}")

    def logwarn(self, msg):
        print(f"[WARN] {msg}")

    def logerr(self, msg):
        print(f"[ERROR] {msg}")

# Add mock rospy to sys.modules
sys.modules['rospy'] = MockRospy()

# Now import our modules
from api_utils import create_api_client

def test_api_direct():
    """
    Test API connection directly to understand the data structure.
    """
    print("\nTesting direct API connection...")

    try:
        api_token = "28b8940a37ed20635f0d72dd1a555520"
        api_client = create_api_client(api_token)

        print("Fetching map_z data...")
        map_data = api_client.get_map("map_z")

        if map_data:
            print("API response received")
            print(f"Data keys: {list(map_data.keys())}")

            # Check if nodes exist and their structure
            nodes = map_data.get('nodes', [])
            if not nodes and 'map_data' in map_data:
                nodes = map_data['map_data'].get('nodes', [])

            print(f"Found {len(nodes)} nodes")

            if nodes:
                print("\nSample node structure:")
                for i, node in enumerate(nodes[:3]):
                    print(f"  Node {i+1}: {node}")

                # Check for LOAD nodes
                load_count = 0
                load_nodes = []
                for node in nodes:
                    node_type = node.get('type', '').upper()
                    if node_type in ['LOAD', 'LOAD_NODE', 'PICKUP', 'CARGO']:
                        load_count += 1
                        load_nodes.append(node['id'])
                        print(f"LOAD node in API data: {node}")

                print(f"\nTotal LOAD nodes in API data: {load_count}")
                print(f"LOAD node IDs: {load_nodes}")

                # Show all node types
                node_types = {}
                for node in nodes:
                    node_type = node.get('type', 'UNKNOWN')
                    if node_type not in node_types:
                        node_types[node_type] = []
                    node_types[node_type].append(node['id'])

                print(f"\nAll node types in map_z:")
                for node_type, node_ids in node_types.items():
                    print(f"  - {node_type}: {node_ids}")

            else:
                print("No nodes found in API response")
        else:
            print("No data received from API")

    except Exception as e:
        print(f"Direct API test failed: {e}")
        import traceback
        traceback.print_exc()

def find_load_nodes_test(map_data):
    """
    Test function to find load nodes from map data.
    """
    load_nodes = []

    if not map_data:
        print("❌ No map data provided")
        return load_nodes

    # Check if nodes exist and their structure
    nodes = map_data.get('nodes', [])
    if not nodes and 'map_data' in map_data:
        nodes = map_data['map_data'].get('nodes', [])

    for node in nodes:
        node_type = node.get('type', '').upper()

        # Check for various LOAD node representations
        if node_type in ['LOAD', 'LOAD_NODE', 'PICKUP', 'CARGO']:
            load_nodes.append(node['id'])
            print(f"LOAD node found: {node['id']} (type: {node.get('type')})")

    return load_nodes

if __name__ == "__main__":
    print("Simple LOAD Node Detection Test")
    print("=" * 50)

    # Run API test
    test_api_direct()

    print("\nTest completed!")