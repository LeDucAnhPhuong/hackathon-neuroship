#!/usr/bin/env python3
"""
Hackathon API Utils - Centralized API handling
Handles map loading and sign submission to hackathon server
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional, Union

class HackathonAPI:
    """Centralized API handler for Hackathon 2025"""
    
    def __init__(self, token: str, base_url: str = "https://hackathon2025-dev.fpt.edu.vn"):
        """
        Initialize API handler
        
        Args:
            token (str): Team's authentication token
            base_url (str): Base URL of hackathon server
        """
        self.token = token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HackathonBot/1.0'
        })
    
    def get_map(self, map_type: str = "map_z", timeout: int = 10, save_to_file: bool = True) -> Optional[Dict]:
        """
        Get active map from server and optionally save to file
        
        Args:
            map_type (str): Map type - map_a, map_b, or map_z
            timeout (int): Request timeout in seconds
            save_to_file (bool): Whether to save map data to JSON file
            
        Returns:
            Dict: Map data if successful, None if failed
        """
        try:
            url = f"{self.base_url}/api/maps/get_active_map/"
            params = {
                'token': self.token,
                'map_type': map_type
            }
            
            print(f"🌐 Getting map from API...")
            print(f"   URL: {url}")
            print(f"   Token: {self.token[:8]}...")
            print(f"   Map type: {map_type}")
            
            response = self.session.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Map loaded successfully!")
                print(f"   Nodes: {len(data.get('nodes', []))}")
                print(f"   Edges: {len(data.get('edges', []))}")
                
                # Save to file if requested
                if save_to_file:
                    self._save_map_to_file(data, map_type)
                
                return data
            else:
                print(f"❌ Map API error {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Map API request failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Map API unexpected error: {e}")
            return None
    
    def _save_map_to_file(self, map_data: Dict, map_type: str) -> None:
        """
        Save map data to JSON file
        
        Args:
            map_data (Dict): Map data to save
            map_type (str): Map type for filename
        """
        try:
            # Always save as map_z.json for development/debugging
            filename = "map_z.json"
            
            # Add metadata to the saved file
            enhanced_data = {
                "metadata": {
                    "source": "hackathon_api",
                    "map_type": map_type,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "nodes_count": len(map_data.get('nodes', [])),
                    "edges_count": len(map_data.get('edges', []))
                },
                "map_data": map_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Map data saved to {filename}")
            print(f"   File size: {os.path.getsize(filename)} bytes")
            
        except Exception as e:
            print(f"❌ Failed to save map to file: {e}")
    
    def submit_sign(self, 
                   text: str, 
                   node_id: str, 
                   map_type: str = "map_z",
                   retry_attempts: int = 3,
                   timeout: int = 5) -> bool:
        """
        Submit sign detection to server
        
        Args:
            text (str): Content of detected symbol/sign
            node_id (str): ID of node/position where sign was detected  
            map_type (str): Current map type (map_a, map_b, map_z)
            retry_attempts (int): Number of retry attempts
            timeout (int): Request timeout in seconds
            
        Returns:
            bool: True if successful, False if failed
        """
        try:
            url = f"{self.base_url}/api/sign-submissions/submit/"
            payload = {
                'text': text,
                'node_id': str(node_id),
                'token': self.token,
                'map_type': map_type
            }
            
            print(f"📤 Submitting sign detection...")
            print(f"   Text: {text}")
            print(f"   Node: {node_id}")
            print(f"   Map: {map_type}")
            
            for attempt in range(retry_attempts):
                try:
                    response = self.session.post(
                        url, 
                        json=payload, 
                        timeout=timeout
                    )
                    
                    if response.status_code in [200, 201]:  # Accept both 200 and 201
                        result = response.json()
                        print(f"✅ Sign submitted successfully!")
                        print(f"   Response: {result}")
                        return True
                    else:
                        print(f"❌ Submit failed (attempt {attempt + 1}/{retry_attempts}): {response.status_code} - {response.text}")
                        
                except requests.RequestException as e:
                    print(f"❌ Submit request failed (attempt {attempt + 1}/{retry_attempts}): {e}")
                
                # Wait before retry (except last attempt)
                if attempt < retry_attempts - 1:
                    time.sleep(1)
            
            print(f"❌ Sign submission failed after {retry_attempts} attempts")
            return False
            
        except Exception as e:
            print(f"❌ Sign submission unexpected error: {e}")
            return False
    
    def submit_qr_code(self, qr_data: str, node_id: str, map_type: str = "map_z") -> bool:
        """Submit QR code detection"""
        return self.submit_sign(f"QR:{qr_data}", node_id, map_type)
    
    def submit_math_result(self, math_result: str, node_id: str, map_type: str = "map_z") -> bool:
        """Submit math problem result"""
        return self.submit_sign(f"MATH:{math_result}", node_id, map_type)
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            print("🧪 Testing API connection...")
            result = self.get_map("map_z", timeout=5)
            if result:
                print("✅ API connection test successful!")
                return True
            else:
                print("❌ API connection test failed!")
                return False
        except Exception as e:
            print(f"❌ API connection test error: {e}")
            return False
    
    @staticmethod
    def load_map_from_file(filename: str = "map_z.json") -> Optional[Dict]:
        """
        Load map data from saved JSON file
        
        Args:
            filename (str): JSON file to load from
            
        Returns:
            Dict: Map data if successful, None if failed
        """
        try:
            if not os.path.exists(filename):
                print(f"❌ Map file {filename} not found")
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both old format (direct map data) and new format (with metadata)
            if 'map_data' in data:
                # New format with metadata
                map_data = data['map_data']
                metadata = data.get('metadata', {})
                print(f"📁 Map loaded from {filename}")
                print(f"   Source: {metadata.get('source', 'unknown')}")
                print(f"   Map type: {metadata.get('map_type', 'unknown')}")
                print(f"   Timestamp: {metadata.get('timestamp', 'unknown')}")
                print(f"   Nodes: {metadata.get('nodes_count', len(map_data.get('nodes', [])))}")
                print(f"   Edges: {metadata.get('edges_count', len(map_data.get('edges', [])))}")
                return map_data
            else:
                # Old format (direct map data)
                print(f"📁 Map loaded from {filename} (legacy format)")
                print(f"   Nodes: {len(data.get('nodes', []))}")
                print(f"   Edges: {len(data.get('edges', []))}")
                return data
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {filename}: {e}")
            return None
        except Exception as e:
            print(f"❌ Failed to load map from {filename}: {e}")
            return None

# Factory function for easy usage
def create_api_client(token: str) -> HackathonAPI:
    """Create API client with team token"""
    return HackathonAPI(token)

# Convenience functions for backward compatibility
def get_map_data(token: str, map_type: str = "map_z", save_to_file: bool = True) -> Optional[Dict]:
    """Get map data - simple function with file saving option"""
    api = create_api_client(token)
    return api.get_map(map_type, save_to_file=save_to_file)

def submit_sign_data(token: str, text: str, node_id: str, map_type: str = "map_z") -> bool:
    """Submit sign data - simple function"""
    api = create_api_client(token)
    return api.submit_sign(text, node_id, map_type)

def load_cached_map(filename: str = "map_z.json") -> Optional[Dict]:
    """Load map data from cached JSON file"""
    return HackathonAPI.load_map_from_file(filename)

# Example usage and testing
if __name__ == "__main__":
    # Test with team token
    TOKEN = "28b8940a37ed20635f0d72dd1a555520"
    
    print("🚀 Testing Hackathon API Utils")
    print("=" * 50)
    
    # Create API client
    api = create_api_client(TOKEN)
    
    # Test connection
    if api.test_connection():
        print("\n🧪 Testing sign submission...")
        
        # Test sign submission
        success = api.submit_sign(
            text="Test QR Code Data",
            node_id="1",
            map_type="map_z"
        )
        
        if success:
            print("✅ All API tests passed!")
        else:
            print("⚠️ Sign submission test failed")
    else:
        print("❌ API connection failed - check network/server status")