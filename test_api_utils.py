#!/usr/bin/env python3
"""
Test script for api_utils
Tests both map loading and sign submission
"""

from api_utils import create_api_client, get_map_data, submit_sign_data

def main():
    print("🧪 Testing Hackathon API Utils")
    print("=" * 50)
    
    TOKEN = "28b8940a37ed20635f0d72dd1a555520"
    
    # Test 1: Simple functions
    print("\n1️⃣ Testing simple functions:")
    print("-" * 30)
    
    print("📡 Testing get_map_data...")
    map_data = get_map_data(TOKEN, "map_z")
    if map_data:
        print(f"✅ Map loaded: {len(map_data.get('nodes', []))} nodes, {len(map_data.get('edges', []))} edges")
    else:
        print("❌ Map loading failed")
    
    print("\n📤 Testing submit_sign_data...")
    success = submit_sign_data(TOKEN, "TEST:Hello World", "1", "map_z")
    print(f"{'✅' if success else '❌'} Sign submission: {'Success' if success else 'Failed'}")
    
    # Test 2: API Client class
    print("\n\n2️⃣ Testing API Client class:")
    print("-" * 30)
    
    api = create_api_client(TOKEN)
    
    # Connection test
    if api.test_connection():
        print("✅ API connection working")
        
        # Test different map types
        for map_type in ["map_z"]:  # Only map_z is available during development
            print(f"\n📡 Testing map type: {map_type}")
            data = api.get_map(map_type)
            if data:
                print(f"✅ {map_type}: {len(data.get('nodes', []))} nodes")
            else:
                print(f"❌ {map_type}: Failed to load")
        
        # Test sign submissions
        print(f"\n📤 Testing different sign types:")
        test_cases = [
            ("QR Code", "QR:ABC123", "1"),
            ("Math Result", "MATH:42", "2"), 
            ("Custom Sign", "CUSTOM:Test Data", "3")
        ]
        
        for desc, text, node in test_cases:
            print(f"   {desc}: ", end="")
            success = api.submit_sign(text, node, "map_z")
            print(f"{'✅' if success else '❌'}")
    
    else:
        print("❌ API connection failed")
    
    print(f"\n{'='*50}")
    print("🏁 API Utils testing completed!")

if __name__ == "__main__":
    main()