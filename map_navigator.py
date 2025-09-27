# map_navigator.py
import rospy

import json
import networkx as nx
import math
from api_utils import create_api_client

class MapNavigator:
    def __init__(self, map_file_path=None, api_url=None):
        """
        Khởi tạo bộ điều hướng bản đồ.
        - Tải bản đồ từ file JSON hoặc từ API.
        - Xây dựng một đồ thị có hướng (directed graph) bằng networkx.
        - Xác định điểm bắt đầu và kết thúc.
        
        Args:
            map_file_path (str): Đường dẫn đến file JSON map cục bộ
            api_url (str): URL API để tải map trực tuyến
        """
        self.graph = nx.DiGraph()
        self.nodes_data = {}
        self.start_node = None
        self.end_node = None
        self._opposite_direction = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        
        # Load map từ API hoặc file
        if api_url:
            self._load_map_from_api(api_url)
        elif map_file_path:
            self._load_map_from_file(map_file_path)
        else:
            rospy.logerr("Phải cung cấp map_file_path hoặc api_url!")

    def _load_map_from_api(self, api_url_or_token):
        """
        Tải bản đồ từ API server - sử dụng api_utils.
        
        Args:
            api_url_or_token (str): Token hoặc URL API
        """
        try:
            # Nếu là token (không chứa http), sử dụng api_utils
            if not api_url_or_token.startswith('http'):
                token = api_url_or_token
                rospy.loginfo(f"🌐 Loading map via API utils (token: {token[:8]}...)")
                
                api_client = create_api_client(token)
                data = api_client.get_map("map_z")  # Default to map_z
                
                if data:
                    rospy.loginfo("✅ Map loaded via API utils!")
                    self._parse_map_data(data)
                else:
                    rospy.logerr("❌ API utils failed to load map")
                    rospy.logwarn("⚠️ Fallback to map.json...")
                    self._load_map_from_file("map.json")
            else:
                # Legacy URL support - fallback to file
                rospy.logwarn("⚠️ URL format detected, falling back to file...")
                self._load_map_from_file("map.json")
                
        except Exception as e:
            rospy.logerr(f"❌ API loading error: {e}")
            rospy.logwarn("⚠️ Fallback to map.json...")
            self._load_map_from_file("map.json")

    def _load_map_from_file(self, map_file_path):
        """
        Tải bản đồ từ file JSON cục bộ.
        
        Args:
            map_file_path (str): Đường dẫn đến file JSON
        """
        try:
            rospy.loginfo(f"Đang tải map từ file: {map_file_path}")
            with open(map_file_path, 'r') as f:
                data = json.load(f)
            rospy.loginfo("✅ Tải map từ file thành công!")
            self._parse_map_data(data)
        except Exception as e:
            rospy.logerr(f"❌ Lỗi khi đọc file map: {e}")

    def _parse_map_data(self, data):
        """
        Phân tích và xử lý dữ liệu map từ JSON.
        
        Args:
            data (dict): Dữ liệu map đã được parse từ JSON
        """
        rospy.loginfo("Đang xử lý dữ liệu map...")
        
        # Xử lý nodes
        for node in data['nodes']:
            self.nodes_data[node['id']] = node
            self.graph.add_node(node['id'], **node)
            if node['type'] == 'start':
                self.start_node = node['id']
                rospy.loginfo(f"🚀 Start node: {node['id']}")
            elif node['type'] == 'end':
                self.end_node = node['id']
                rospy.loginfo(f"🎯 End node: {node['id']}")

        # Xử lý edges
        for edge in data['edges']:
            if not edge["label"]:
                edge["label"] = ""
            # Thêm cạnh xuôi và cạnh ngược để robot có thể đi hai chiều
            self.graph.add_edge(edge['source'], edge['target'], label=edge['label'])
            opposite_label = self._opposite_direction.get(edge['label'])
            if opposite_label:
                self.graph.add_edge(edge['target'], edge['source'], label=opposite_label)
        
        rospy.loginfo(f"✅ Map đã được load: {len(data['nodes'])} nodes, {len(data['edges'])} edges")

    def _load_map(self, map_file_path):
        """Legacy method - giữ lại để tương thích ngược"""
        self._load_map_from_file(map_file_path)
    
    def _heuristic(self, node1_id, node2_id):
        """Hàm heuristic (khoảng cách Euclid) cho thuật toán A*."""
        pos1 = self.nodes_data[node1_id]
        pos2 = self.nodes_data[node2_id]
        return math.sqrt((pos1['x'] - pos2['x'])**2 + (pos1['y'] - pos2['y'])**2)

    def find_path(self, start_node_id, end_node_id, banned_edges=None):
        """
        Tìm đường đi ngắn nhất từ điểm bắt đầu đến điểm kết thúc bằng thuật toán A*.
        :param start_node_id: ID của node bắt đầu.
        :param end_node_id: ID của node kết thúc.
        :param banned_edges: List các cạnh (u, v) bị cấm, dùng để tìm đường lại.
        :return: List các ID node trên đường đi, hoặc None nếu không có đường.
        """
        graph_to_search = self.graph.copy()
        if banned_edges:
            graph_to_search.remove_edges_from(banned_edges)

        try:
            path = nx.astar_path(
                graph_to_search, 
                start_node_id, 
                end_node_id, 
                heuristic=self._heuristic
            )
            rospy.loginfo(f"Path found: {path}")
            return path
        except nx.NetworkXNoPath:
            return None

    def get_next_direction_label(self, current_node_id, path):
        """
        Từ đường đi đã cho, xác định hướng đi tiếp theo (N, E, S, W) từ node hiện tại.
        """
        if not path or current_node_id not in path:
            return None
        
        current_index = path.index(current_node_id)
        if current_index + 1 >= len(path):
            return None # Đã đến đích

        next_node_id = path[current_index + 1]
        edge_data = self.graph.get_edge_data(current_node_id, next_node_id)
        rospy.loginfo(f"Next direction from {current_node_id} to {next_node_id}: {edge_data.get('label', None)}")
        return edge_data.get('label', None)
    
    def get_neighbor_by_direction(self, current_node_id, direction_label):
        """
        Tìm ID của node hàng xóm từ node hiện tại theo một hướng cho trước.
        :param current_node_id: ID của node hiện tại.
        :param direction_label: Hướng đi ('N', 'E', 'S', 'W').
        :return: ID của node hàng xóm, hoặc None nếu không có.
        """
        for neighbor in self.graph.neighbors(current_node_id):
            edge_data = self.graph.get_edge_data(current_node_id, neighbor)
            if edge_data and edge_data.get('label') == direction_label:
                rospy.loginfo(f"Neighbor of {current_node_id} in direction {direction_label}: {neighbor}")
                return neighbor
        return None

    @staticmethod
    def create_from_api(token, map_type="map_z"):
        """
        Factory method để tạo MapNavigator từ API - đơn giản.
        
        Args:
            token (str): Token xác thực
            map_type (str): Loại map cần tải (mặc định: "map_z")
            
        Returns:
            MapNavigator: Instance mới đã load map từ API
            
        Usage:
            navigator = MapNavigator.create_from_api("28b8940a37ed20635f0d72dd1a555520")
        """
        return MapNavigator(api_url=token)

    @staticmethod 
    def create_from_file(map_file_path="map_z.json"):
        """
        Factory method để tạo MapNavigator từ file cục bộ.
        
        Args:
            map_file_path (str): Đường dẫn file map
            
        Returns:
            MapNavigator: Instance mới đã load map từ file
        """
        return MapNavigator(map_file_path=map_file_path)