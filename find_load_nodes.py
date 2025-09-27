#!/usr/bin/env python3

from api_utils import create_api_client

def find_load_nodes():
    """
    Call API and find all LOAD nodes in map_z.
    Returns list of LOAD node IDs.
    """
    try:
        # Create API client
        api_token = "28b8940a37ed20635f0d72dd1a555520"
        api_client = create_api_client(api_token)

        # Get map data
        print("Calling API to get map_z...")
        map_data = api_client.get_map("map_z")

        if not map_data:
            print("Failed to get map data from API")
            return []

        # Extract nodes
        nodes = map_data.get('nodes', [])
        print(f"Found {len(nodes)} nodes in map")

        # Find LOAD nodes
        load_nodes = []
        for node in nodes:
            if node.get('type', '').upper() == 'LOAD':
                load_nodes.append(node['id'])
                print(f"LOAD node found: ID={node['id']}, name={node.get('name')}")

        print(f"Total LOAD nodes found: {len(load_nodes)}")
        print(f"LOAD node IDs: {load_nodes}")

        return load_nodes

    except Exception as e:
        print(f"Error finding LOAD nodes: {e}")
        return []

if __name__ == "__main__":
    find_load_nodes()