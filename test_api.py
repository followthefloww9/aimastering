#!/usr/bin/env python3
"""
Simple test script for the AI Mastering API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("\nTesting root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_docs():
    """Test docs endpoint"""
    print("\nTesting docs endpoint...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    return response.status_code == 200

def test_chat_examples():
    """Test chat examples endpoint"""
    print("\nTesting chat examples endpoint...")
    response = requests.get(f"{BASE_URL}/api/chat/examples")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Examples found: {len(data.get('examples', []))}")
        for category in data.get('examples', []):
            print(f"  - {category['category']}: {len(category['commands'])} commands")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("🎵 AI Mastering Service - API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("API Documentation", test_docs),
        ("Chat Examples", test_chat_examples),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        print("\n🌐 Access the application at:")
        print(f"   - Local: http://localhost:80")
        print(f"   - API Docs: http://localhost:8000/docs")
        print(f"   - Public URL: https://aimastering.loca.lt")
    else:
        print("⚠️  Some tests failed. Please check the logs.")

if __name__ == "__main__":
    main()
