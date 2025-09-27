#!/usr/bin/env python3
"""
Test script để kiểm tra map_navigator với map_z.json
"""

import os
import sys
import json

# Mock rospy để tránh lỗi ROS
class MockRospy:
    def loginfo(self, msg):
        print(f"[INFO] {msg}")
    
    def logwarn(self, msg):
        print(f"[WARN] {msg}")
    
    def logerr(self, msg):
        print(f"[ERROR] {msg}")

# Inject mock rospy
sys.modules['rospy'] = MockRospy()

# Import sau khi đã mock
from map_navigator import MapNavigator

def test_map_navigator_with_cached_file():
    """Test map_navigator với file map_z.json đã cache"""
    print("🧪 Testing MapNavigator with cached map_z.json")
    print("=" * 50)
    
    # Check if map_z.json exists
    if not os.path.exists("map_z.json"):
        print("❌ map_z.json not found! Run API test first.")
        return False
    
    print("\n📁 Step 1: Load map_z.json with MapNavigator")
    try:
        navigator = MapNavigator(map_file_path="map_z.json")
        
        print(f"✅ MapNavigator loaded successfully!")
        print(f"   📊 Total nodes: {len(navigator.nodes_data)}")
        print(f"   📊 Graph nodes: {navigator.graph.number_of_nodes()}")
        print(f"   📊 Graph edges: {navigator.graph.number_of_edges()}")
        
    except Exception as e:
        print(f"❌ Failed to load with MapNavigator: {e}")
        return False
    
    print("\n🔍 Step 2: Analyze map structure")
    
    # Check node types
    node_types = {}
    for node_id, node_data in navigator.nodes_data.items():
        node_type = node_data['type']
        if node_type not in node_types:
            node_types[node_type] = 0
        node_types[node_type] += 1
    
    print("   📋 Node types:")
    for node_type, count in node_types.items():
        print(f"      • {node_type}: {count} nodes")
    
    # Show start and end nodes
    start_nodes = [n for n in navigator.nodes_data.values() if n['type'] == 'START']
    end_nodes = [n for n in navigator.nodes_data.values() if n['type'] == 'END']
    load_nodes = [n for n in navigator.nodes_data.values() if n['type'] == 'LOAD']
    
    print(f"\n   🚀 Start nodes: {[n['name'] for n in start_nodes]}")
    print(f"   🏁 End nodes: {[n['name'] for n in end_nodes]}")
    print(f"   📦 Load nodes: {[n['name'] for n in load_nodes]}")
    
    print("\n🧭 Step 3: Test pathfinding capability")
    
    if start_nodes and end_nodes:
        start_id = start_nodes[0]['id']
        end_id = end_nodes[0]['id']
        
        try:
            path = navigator.find_path(start_id, end_id)
            if path:
                print(f"   ✅ Path found from {start_nodes[0]['name']} to {end_nodes[0]['name']}")
                print(f"   📍 Path: {' → '.join([navigator.nodes_data[n]['name'] for n in path])}")
                print(f"   📏 Path length: {len(path)} nodes")
            else:
                print(f"   ❌ No path found from {start_nodes[0]['name']} to {end_nodes[0]['name']}")
        except Exception as e:
            print(f"   ❌ Pathfinding error: {e}")
    
    print("\n✅ MapNavigator test with map_z.json completed!")
    return True

def test_direct_json_structure():
    """Test structure của file map_z.json trực tiếp"""
    print("\n🔍 Direct JSON Structure Analysis")
    print("-" * 40)
    
    try:
        with open("map_z.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's the new format with metadata
        if 'map_data' in data and 'metadata' in data:
            print("✅ New format detected (with metadata)")
            metadata = data['metadata']
            map_data = data['map_data']
            
            print(f"   📊 Metadata:")
            print(f"      • Source: {metadata.get('source')}")
            print(f"      • Map type: {metadata.get('map_type')}")
            print(f"      • Timestamp: {metadata.get('timestamp')}")
            print(f"      • Nodes count: {metadata.get('nodes_count')}")
            print(f"      • Edges count: {metadata.get('edges_count')}")
            
            print(f"\n   🗺️ Map data structure:")
            print(f"      • Map ID: {map_data.get('id')}")
            print(f"      • Map name: {map_data.get('name')}")
            print(f"      • Dimensions: {map_data.get('dimensions')}")
            print(f"      • Starting positions: {map_data.get('startingPositions')}")
            
        else:
            print("ℹ️ Legacy format detected (direct map data)")
            map_data = data
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing JSON structure: {e}")
        return False

def check_compatibility():
    """Kiểm tra compatibility giữa format mới và MapNavigator"""
    print("\n🔄 Checking Format Compatibility")
    print("-" * 35)
    
    try:
        with open("map_z.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract map_data if it's new format
        if 'map_data' in data:
            actual_map_data = data['map_data']
            print("ℹ️ Extracting map_data from new format...")
        else:
            actual_map_data = data
            print("ℹ️ Using legacy format directly...")
        
        # Check required fields for MapNavigator
        required_fields = ['nodes', 'edges']
        missing_fields = []
        
        for field in required_fields:
            if field not in actual_map_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields present")
            
            # Check nodes structure
            nodes = actual_map_data['nodes']
            if nodes and len(nodes) > 0:
                sample_node = nodes[0]
                node_fields = ['id', 'x', 'y', 'type', 'name']
                node_missing = [f for f in node_fields if f not in sample_node]
                
                if node_missing:
                    print(f"⚠️ Node missing fields: {node_missing}")
                else:
                    print("✅ Node structure compatible")
            
            # Check edges structure  
            edges = actual_map_data['edges']
            if edges and len(edges) > 0:
                sample_edge = edges[0]
                edge_fields = ['source', 'target']
                edge_missing = [f for f in edge_fields if f not in sample_edge]
                
                if edge_missing:
                    print(f"⚠️ Edge missing fields: {edge_missing}")
                else:
                    print("✅ Edge structure compatible")
            
            return True
            
    except Exception as e:
        print(f"❌ Compatibility check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Map Navigator Compatibility Test")
    print("=" * 60)
    
    # Test JSON structure first
    json_ok = test_direct_json_structure()
    
    if json_ok:
        # Check compatibility
        compat_ok = check_compatibility()
        
        if compat_ok:
            # Test with MapNavigator
            nav_ok = test_map_navigator_with_cached_file()
            
            if nav_ok:
                print("\n🎉 All tests passed!")
                print("✅ map_z.json is compatible with MapNavigator")
            else:
                print("\n⚠️ MapNavigator test failed")
        else:
            print("\n❌ Compatibility issues detected")
    else:
        print("\n❌ JSON structure issues detected")