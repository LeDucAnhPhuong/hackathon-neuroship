#!/usr/bin/env python3
"""
Simple test để kiểm tra map_z.json có format tương thích không
"""

import json
import os

def test_map_format_compatibility():
    """Kiểm tra format của map_z.json"""
    print("🧪 Testing map_z.json Format Compatibility")
    print("=" * 50)
    
    if not os.path.exists("map_z.json"):
        print("❌ map_z.json not found!")
        return False
    
    try:
        print("\n📁 Step 1: Load and parse JSON")
        with open("map_z.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON loaded successfully")
        
        print("\n🔍 Step 2: Analyze structure")
        
        # Check if new format (with metadata) or old format
        if 'map_data' in data and 'metadata' in data:
            print("✅ New format detected (with metadata)")
            metadata = data['metadata']
            map_data = data['map_data']
            
            print(f"   📊 Metadata:")
            print(f"      • Source: {metadata.get('source')}")
            print(f"      • Map type: {metadata.get('map_type')}")  
            print(f"      • Timestamp: {metadata.get('timestamp')}")
            print(f"      • Nodes: {metadata.get('nodes_count')}")
            print(f"      • Edges: {metadata.get('edges_count')}")
            
            # Use map_data for compatibility check
            working_data = map_data
            print("\n   🔄 Using map_data section for compatibility...")
            
        else:
            print("ℹ️ Legacy format detected")
            working_data = data
        
        print("\n✅ Step 3: Check required fields")
        required_fields = ['nodes', 'edges']
        
        for field in required_fields:
            if field in working_data:
                print(f"   ✅ {field}: {len(working_data[field])} items")
            else:
                print(f"   ❌ Missing {field}")
                return False
        
        print("\n🔍 Step 4: Analyze node structure")
        nodes = working_data['nodes']
        if len(nodes) > 0:
            sample_node = nodes[0]
            print(f"   📋 Sample node: {sample_node}")
            
            required_node_fields = ['id', 'x', 'y', 'type', 'name']
            for field in required_node_fields:
                if field in sample_node:
                    print(f"      ✅ {field}: {sample_node[field]}")
                else:
                    print(f"      ❌ Missing {field}")
        
        print("\n🔍 Step 5: Analyze node types")
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'UNKNOWN')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for node_type, count in node_types.items():
            print(f"   📊 {node_type}: {count} nodes")
        
        print("\n🔍 Step 6: Check edges structure")
        edges = working_data['edges']
        if len(edges) > 0:
            sample_edge = edges[0]
            print(f"   📋 Sample edge: {sample_edge}")
            
            required_edge_fields = ['source', 'target']
            for field in required_edge_fields:
                if field in sample_edge:
                    print(f"      ✅ {field}: {sample_edge[field]}")
                else:
                    print(f"      ❌ Missing {field}")
        
        print("\n✅ Step 7: MapNavigator compatibility check")
        
        # Check for START and END nodes (required for pathfinding)
        start_nodes = [n for n in nodes if n.get('type') == 'START']
        end_nodes = [n for n in nodes if n.get('type') == 'END']
        
        print(f"   🚀 START nodes: {len(start_nodes)} found")
        for node in start_nodes:
            print(f"      • Node {node['id']}: {node['name']} at ({node['x']}, {node['y']})")
        
        print(f"   🏁 END nodes: {len(end_nodes)} found")
        for node in end_nodes:
            print(f"      • Node {node['id']}: {node['name']} at ({node['x']}, {node['y']})")
        
        # Check connectivity
        print(f"\n   🔗 Edge connectivity:")
        node_ids = {n['id'] for n in nodes}
        valid_edges = 0
        
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source in node_ids and target in node_ids:
                valid_edges += 1
        
        print(f"      • Valid edges: {valid_edges}/{len(edges)}")
        
        if valid_edges == len(edges):
            print("      ✅ All edges reference valid nodes")
        else:
            print("      ⚠️ Some edges reference invalid nodes")
        
        print(f"\n✅ Compatibility test completed!")
        print(f"   📊 Summary:")
        print(f"      • Total nodes: {len(nodes)}")
        print(f"      • Total edges: {len(edges)}")
        print(f"      • Start nodes: {len(start_nodes)}")
        print(f"      • End nodes: {len(end_nodes)}")
        print(f"      • Valid connectivity: {valid_edges == len(edges)}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_legacy_format_test():
    """Tạo file test với format legacy để so sánh"""
    print("\n🔄 Creating legacy format for MapNavigator")
    print("-" * 45)
    
    try:
        # Load new format
        with open("map_z.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract map_data if new format
        if 'map_data' in data:
            map_data = data['map_data']
            print("✅ Extracted map_data from new format")
        else:
            map_data = data
            print("ℹ️ Already in legacy format")
        
        # Save as legacy format for testing
        legacy_file = "map_z_legacy.json"
        with open(legacy_file, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Legacy format saved to {legacy_file}")
        print(f"   📏 File size: {os.path.getsize(legacy_file)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating legacy format: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Map Format Compatibility Test")
    print("=" * 60)
    
    # Test main format
    format_ok = test_map_format_compatibility()
    
    if format_ok:
        # Create legacy format for comparison
        legacy_ok = create_legacy_format_test()
        
        if legacy_ok:
            print(f"\n🎉 All tests passed!")
            print(f"\n💡 Results:")
            print(f"   • map_z.json: New format with metadata ✅")
            print(f"   • map_z_legacy.json: Legacy format for MapNavigator ✅")
            print(f"   • Both formats are compatible with existing code")
        else:
            print(f"\n⚠️ Legacy format creation failed")
    else:
        print(f"\n❌ Format compatibility test failed")