#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from map_navigator import MapNavigator
from api_utils import create_api_client

def test_load_nodes_in_map():
    """
    Test function to check for LOAD nodes in map_z and debug the issue.
    """
    print("🔍 Testing LOAD nodes detection in map_z...")

    # Test with API
    try:
        print("\n1. Testing with API...")
        api_token = "28b8940a37ed20635f0d72dd1a555520"
        navigator = MapNavigator.create_from_api(api_token, "map_z")

        if navigator.nodes_data:
            print(f"✅ Successfully loaded {len(navigator.nodes_data)} nodes from API")
            check_load_nodes(navigator, "API")
        else:
            print("❌ No nodes loaded from API")

    except Exception as e:
        print(f"❌ API test failed: {e}")

    # Test with local file (fallback)
    try:
        print("\n2. Testing with local file fallback...")
        navigator = MapNavigator.create_from_file("map_z.json")

        if navigator.nodes_data:
            print(f"✅ Successfully loaded {len(navigator.nodes_data)} nodes from file")
            check_load_nodes(navigator, "File")
        else:
            print("❌ No nodes loaded from file")

    except Exception as e:
        print(f"❌ File test failed: {e}")

def check_load_nodes(navigator, source):
    """
    Check for LOAD nodes in the navigator and print detailed information.
    """
    print(f"\n📊 Analyzing nodes from {source}:")

    # Count node types
    node_types = {}
    load_nodes = []

    for node_id, node_data in navigator.nodes_data.items():
        node_type = node_data.get('type', 'UNKNOWN')

        if node_type not in node_types:
            node_types[node_type] = 0
        node_types[node_type] += 1

        # Check for LOAD nodes (case-insensitive)
        if node_type.upper() == 'LOAD':
            load_nodes.append(node_id)
            print(f"🏗️ Found LOAD node: {node_id} - {node_data}")

    print(f"\n📈 Node type summary:")
    for node_type, count in node_types.items():
        print(f"  - {node_type}: {count}")

    if load_nodes:
        print(f"\n✅ Found {len(load_nodes)} LOAD nodes: {load_nodes}")
        return load_nodes
    else:
        print("\n❌ No LOAD nodes found!")
        print("\n🔍 Sample node data (first 3 nodes):")
        for i, (node_id, node_data) in enumerate(navigator.nodes_data.items()):
            if i >= 3:
                break
            print(f"  Node {node_id}: {node_data}")
        return []

def find_load_nodes(navigator):
    """
    Function to find all LOAD nodes in the map.
    Returns list of LOAD node IDs.
    """
    load_nodes = []

    if not navigator or not navigator.nodes_data:
        print("❌ Navigator or nodes_data is None/empty")
        return load_nodes

    for node_id, node_data in navigator.nodes_data.items():
        node_type = node_data.get('type', '').upper()

        # Check for various LOAD node representations
        if node_type in ['LOAD', 'LOAD_NODE', 'PICKUP', 'CARGO']:
            load_nodes.append(node_id)
            print(f"🏗️ LOAD node found: {node_id} (type: {node_data.get('type')})")

    return load_nodes

def test_api_direct():
    """
    Test API connection directly to understand the data structure.
    """
    print("\n🌐 Testing direct API connection...")

    try:
        api_token = "28b8940a37ed20635f0d72dd1a555520"
        api_client = create_api_client(api_token)

        print("📡 Fetching map_z data...")
        map_data = api_client.get_map("map_z")

        if map_data:
            print("✅ API response received")
            print(f"📊 Data keys: {list(map_data.keys())}")

            # Check if nodes exist and their structure
            nodes = map_data.get('nodes', [])
            if not nodes and 'map_data' in map_data:
                nodes = map_data['map_data'].get('nodes', [])

            print(f"📈 Found {len(nodes)} nodes")

            if nodes:
                print("\n🔍 Sample node structure:")
                for i, node in enumerate(nodes[:3]):
                    print(f"  Node {i+1}: {node}")

                # Check for LOAD nodes
                load_count = 0
                for node in nodes:
                    if node.get('type', '').upper() == 'LOAD':
                        load_count += 1
                        print(f"🏗️ LOAD node in API data: {node}")

                print(f"\n📊 Total LOAD nodes in API data: {load_count}")
        else:
            print("❌ No data received from API")

    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 LOAD Node Detection Test")
    print("=" * 50)

    # Run all tests
    test_api_direct()
    test_load_nodes_in_map()

    print("\n✅ Test completed!")