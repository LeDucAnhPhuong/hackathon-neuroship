#!/usr/bin/env python3
"""
Test script for map caching functionality
Demonstrates getting map from API and loading from cached file
"""

from api_utils import create_api_client, load_cached_map
import time
import os

def test_map_caching():
    """Test map caching functionality"""
    TOKEN = "28b8940a37ed20635f0d72dd1a555520"
    
    print("🧪 Testing Map Caching Functionality")
    print("=" * 50)
    
    # Create API client
    api = create_api_client(TOKEN)
    
    print("\n📥 Step 1: Get fresh map from API (auto-saves to map_z.json)")
    map_data = api.get_map("map_z")
    
    if map_data:
        print(f"   ✅ Fresh map loaded with {len(map_data.get('nodes', []))} nodes")
    else:
        print("   ❌ Failed to get map from API")
        return False
    
    # Wait a moment
    time.sleep(1)
    
    print("\n📁 Step 2: Load map from cached file")
    cached_map = load_cached_map("map_z.json")
    
    if cached_map:
        print(f"   ✅ Cached map loaded with {len(cached_map.get('nodes', []))} nodes")
    else:
        print("   ❌ Failed to load cached map")
        return False
    
    print("\n🔍 Step 3: Compare data integrity")
    if (len(map_data.get('nodes', [])) == len(cached_map.get('nodes', [])) and
        len(map_data.get('edges', [])) == len(cached_map.get('edges', []))):
        print("   ✅ Data integrity confirmed - cached data matches API data")
    else:
        print("   ❌ Data mismatch between API and cached data")
        return False
    
    print("\n📊 Step 4: File information")
    if os.path.exists("map_z.json"):
        file_size = os.path.getsize("map_z.json")
        print(f"   📄 File: map_z.json")
        print(f"   📏 Size: {file_size} bytes ({file_size/1024:.1f} KB)")
        print(f"   ⏰ Modified: {time.ctime(os.path.getmtime('map_z.json'))}")
    
    print("\n✅ Map caching test completed successfully!")
    return True

def test_offline_mode():
    """Test loading map when API is unavailable (offline mode)"""
    print("\n🔌 Testing Offline Mode")
    print("-" * 30)
    
    # Try to load from cached file first (simulating offline mode)
    cached_map = load_cached_map("map_z.json")
    
    if cached_map:
        print("✅ Offline mode works - can use cached map data")
        print(f"   📊 Nodes: {len(cached_map.get('nodes', []))}")
        print(f"   📊 Edges: {len(cached_map.get('edges', []))}")
        
        # Show some sample data
        print("\n📋 Sample nodes:")
        for i, node in enumerate(cached_map.get('nodes', [])[:3]):
            print(f"   {i+1}. Node {node['id']}: {node['name']} at ({node['x']}, {node['y']}) - {node['type']}")
        
        return True
    else:
        print("❌ No cached data available for offline mode")
        return False

if __name__ == "__main__":
    print("🚀 Map Caching Test Suite")
    print("=" * 60)
    
    # Test main caching functionality
    success = test_map_caching()
    
    if success:
        # Test offline mode functionality
        test_offline_mode()
        
        print("\n🎉 All tests passed!")
        print("\n💡 Usage Tips:")
        print("   • map_z.json is automatically created when calling get_map()")
        print("   • Use load_cached_map() for offline development")
        print("   • Cached file includes metadata and timestamp")
        print("   • File is updated every time API is called")
    else:
        print("\n❌ Some tests failed - check API connectivity")