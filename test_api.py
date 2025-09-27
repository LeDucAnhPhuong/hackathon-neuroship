#!/usr/bin/env python3
"""
API Testing Script for Hackathon 2025
Test các endpoint server để kiểm tra phản hồi và validate integration
"""

import requests
import json
import time
from datetime import datetime

class HackathonAPITester:
    def __init__(self):
        self.SERVER_BASE_URL = "https://hackathon2025-dev.fpt.edu.vn"
        self.TEAM_TOKEN = "28b8940a37ed20635f0d72dd1a555520"
        
        # API Endpoints
        self.GET_MAP_ENDPOINT = "/api/maps/get_active_map"
        self.SUBMIT_SIGN_ENDPOINT = "/api/sign-submissions/submit"
        
        # Test results storage
        self.test_results = []
        
        print(f"🚀 Hackathon API Tester initialized")
        print(f"📡 Server: {self.SERVER_BASE_URL}")
        print(f"🔑 Token: {self.TEAM_TOKEN[:8]}...")
        print("="*60)

    def log_test_result(self, test_name, success, details, response_data=None):
        """Log test result for summary"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "details": details,
            "response": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")

    def test_server_connectivity(self):
        """Test 1: Kiểm tra server có online không"""
        print("\n🔍 TEST 1: Server Connectivity")
        try:
            response = requests.get(self.SERVER_BASE_URL, timeout=10)
            success = response.status_code in [200, 404, 403]  # Server responding
            
            self.log_test_result(
                "Server Connectivity", 
                success,
                f"Status: {response.status_code}, Response time: {response.elapsed.total_seconds():.2f}s"
            )
            return success
            
        except requests.exceptions.RequestException as e:
            self.log_test_result("Server Connectivity", False, f"Connection error: {e}")
            return False

    def test_get_active_map(self):
        """Test 2: Lấy map active từ server"""
        print("\n🗺️  TEST 2: Get Active Map")
        url = self.SERVER_BASE_URL + self.GET_MAP_ENDPOINT
        
        # Add token as query parameter
        params = {"token": self.TEAM_TOKEN}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    map_data = response.json()
                    
                    # Validate map structure
                    required_keys = ['nodes', 'edges']
                    has_required_keys = all(key in map_data for key in required_keys)
                    
                    node_count = len(map_data.get('nodes', []))
                    edge_count = len(map_data.get('edges', []))
                    
                    details = f"Nodes: {node_count}, Edges: {edge_count}, Valid structure: {has_required_keys}"
                    
                    self.log_test_result(
                        "Get Active Map",
                        has_required_keys and node_count > 0,
                        details,
                        map_data
                    )
                    
                    # Save map data for inspection
                    with open('downloaded_map.json', 'w') as f:
                        json.dump(map_data, f, indent=2)
                    print("📋 Map data saved to 'downloaded_map.json'")
                    
                    return map_data
                    
                except json.JSONDecodeError:
                    self.log_test_result("Get Active Map", False, "Invalid JSON response")
                    return None
            else:
                self.log_test_result("Get Active Map", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_test_result("Get Active Map", False, f"Request error: {e}")
            return None

    def test_sign_submission_valid(self):
        """Test 3: Submit sign detection (valid data)"""
        print("\n📝 TEST 3: Valid Sign Submission")
        url = self.SERVER_BASE_URL + self.SUBMIT_SIGN_ENDPOINT
        
        test_payload = {
            "text": "TEST_QR_CODE_123",
            "node_id": "1", 
            "token": self.TEAM_TOKEN
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            print(f"   Sending POST to: {url}")
            print(f"   Payload: {test_payload}")
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            success = response.status_code == 201
            details = f"Status: {response.status_code}"
            
            if success:
                details += " - Submission accepted"
            else:
                details += f" - Error: {response.text}"
            
            self.log_test_result("Valid Sign Submission", success, details, response.text)
            return success
            
        except requests.exceptions.RequestException as e:
            self.log_test_result("Valid Sign Submission", False, f"Request error: {e}")
            return False

    def test_sign_submission_invalid_token(self):
        """Test 4: Submit với token sai"""
        print("\n🔒 TEST 4: Invalid Token Submission")
        url = self.SERVER_BASE_URL + self.SUBMIT_SIGN_ENDPOINT
        
        test_payload = {
            "text": "TEST_INVALID_TOKEN",
            "node_id": "1", 
            "token": "invalid_token_12345"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            # Should fail with 401/403
            expected_failure = response.status_code in [401, 403]
            details = f"Status: {response.status_code} - {'Expected failure' if expected_failure else 'Unexpected'}"
            
            self.log_test_result("Invalid Token Test", expected_failure, details)
            return expected_failure
            
        except requests.exceptions.RequestException as e:
            self.log_test_result("Invalid Token Test", False, f"Request error: {e}")
            return False

    def test_sign_submission_missing_fields(self):
        """Test 5: Submit thiếu field required"""
        print("\n📋 TEST 5: Missing Required Fields")
        url = self.SERVER_BASE_URL + self.SUBMIT_SIGN_ENDPOINT
        
        # Test missing 'text' field
        test_payload = {
            "node_id": "1", 
            "token": self.TEAM_TOKEN
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            # Should fail with 400
            expected_failure = response.status_code == 400
            details = f"Status: {response.status_code} - {'Expected validation error' if expected_failure else 'Unexpected'}"
            
            self.log_test_result("Missing Fields Test", expected_failure, details)
            return expected_failure
            
        except requests.exceptions.RequestException as e:
            self.log_test_result("Missing Fields Test", False, f"Request error: {e}")
            return False

    def test_multiple_rapid_submissions(self):
        """Test 6: Test rate limiting và multiple submissions"""
        print("\n⚡ TEST 6: Rapid Multiple Submissions")
        url = self.SERVER_BASE_URL + self.SUBMIT_SIGN_ENDPOINT
        headers = {"Content-Type": "application/json"}
        
        success_count = 0
        total_requests = 5
        
        for i in range(total_requests):
            test_payload = {
                "text": f"RAPID_TEST_{i}_{int(time.time())}",
                "node_id": str(i), 
                "token": self.TEAM_TOKEN
            }
            
            try:
                response = requests.post(url, json=test_payload, headers=headers, timeout=5)
                if response.status_code == 201:
                    success_count += 1
                print(f"   Request {i+1}: Status {response.status_code}")
                time.sleep(0.5)  # Small delay
                
            except requests.exceptions.RequestException as e:
                print(f"   Request {i+1}: Error {e}")
        
        success_rate = success_count / total_requests
        details = f"{success_count}/{total_requests} successful ({success_rate*100:.1f}%)"
        
        self.log_test_result("Rapid Submissions", success_rate >= 0.8, details)
        return success_rate >= 0.8

    def test_response_time_benchmark(self):
        """Test 7: Đo response time trung bình"""
        print("\n⏱️  TEST 7: Response Time Benchmark")
        
        # Test GET map endpoint
        map_times = []
        for i in range(3):
            try:
                start_time = time.time()
                response = requests.get(self.SERVER_BASE_URL + self.GET_MAP_ENDPOINT, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    map_times.append(end_time - start_time)
                time.sleep(1)
            except:
                pass
        
        # Test POST submission endpoint  
        submit_times = []
        for i in range(3):
            try:
                start_time = time.time()
                response = requests.post(
                    self.SERVER_BASE_URL + self.SUBMIT_SIGN_ENDPOINT,
                    json={
                        "text": f"BENCHMARK_{i}",
                        "node_id": "0",
                        "token": self.TEAM_TOKEN
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                end_time = time.time()
                
                submit_times.append(end_time - start_time)
                time.sleep(1)
            except:
                pass
        
        avg_map_time = sum(map_times) / len(map_times) if map_times else 0
        avg_submit_time = sum(submit_times) / len(submit_times) if submit_times else 0
        
        details = f"GET Map: {avg_map_time:.2f}s, POST Submit: {avg_submit_time:.2f}s"
        good_performance = avg_map_time < 2.0 and avg_submit_time < 2.0
        
        self.log_test_result("Response Time", good_performance, details)
        return good_performance

    def run_all_tests(self):
        """Chạy tất cả tests"""
        print("🎯 HACKATHON API TEST SUITE")
        print("=" * 60)
        
        # Run all tests
        tests = [
            self.test_server_connectivity,
            self.test_get_active_map,
            self.test_sign_submission_valid,
            self.test_sign_submission_invalid_token,
            self.test_sign_submission_missing_fields,
            self.test_multiple_rapid_submissions,
            self.test_response_time_benchmark
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """In tổng kết test results"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} [{result['timestamp']}] {result['test']}: {result['details']}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("🎉 All tests passed! API integration looks good.")
        else:
            print("⚠️  Some tests failed. Check:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n🔧 NEXT STEPS:")
        print("1. Review downloaded_map.json để hiểu map structure")
        print("2. Test integration với robot code")
        print("3. Validate sign detection và submission logic")
        print("4. Test trong competition environment")


def main():
    """Main test execution"""
    tester = HackathonAPITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()