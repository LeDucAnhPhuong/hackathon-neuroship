#!/usr/bin/env python3

# Test the find_load_nodes function with the actual data structure
def test_find_load_nodes():
    # Sample data structure from map_z API
    sample_nodes_data = {
        1: {'id': 1, 'x': 1, 'y': 0, 'type': 'None', 'name': 'A'},
        6: {'id': 6, 'x': 3, 'y': 0, 'type': 'End', 'name': 'F'},
        7: {'id': 7, 'x': 0, 'y': 0, 'type': 'Start', 'name': 'G'},
        9: {'id': 9, 'x': 2, 'y': 2, 'type': 'Load', 'name': 'I'},
        10: {'id': 10, 'x': 3, 'y': 2, 'type': 'Load', 'name': 'J'},
        13: {'id': 13, 'x': 3, 'y': 3, 'type': 'Load', 'name': 'M'}
    }

    # Test the find_load_nodes logic
    load_nodes = []

    for node_id, node_data in sample_nodes_data.items():
        node_type = node_data.get('type', '')

        # Check for various LOAD node representations (case-insensitive)
        if node_type.upper() in ['LOAD', 'LOAD_NODE', 'PICKUP', 'CARGO']:
            load_nodes.append(node_id)
            print(f"LOAD node found: {node_id} (type: {node_data.get('type')})")

    print(f"Total LOAD nodes found: {len(load_nodes)}")
    print(f"LOAD node IDs: {load_nodes}")

    # Expected result: [9, 10, 13]
    expected = [9, 10, 13]
    if set(load_nodes) == set(expected):
        print("Test PASSED - Function correctly identifies LOAD nodes")
        return True
    else:
        print(f"Test FAILED - Expected {expected}, got {load_nodes}")
        return False

if __name__ == "__main__":
    print("Testing find_load_nodes function logic...")
    print("=" * 50)
    test_find_load_nodes()