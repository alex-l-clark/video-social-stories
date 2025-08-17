#!/usr/bin/env python3
"""
Integration test script for the Social Story application.
Tests the full workflow: frontend serving + backend API integration.
"""

import requests
import time
import json
import sys

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running at", FRONTEND_URL)
            if "Social Story Creator" in response.text:
                print("✅ Frontend title found - looks good!")
                return True
            else:
                print("⚠️  Frontend content may not be loading correctly")
                return False
        else:
            print("❌ Frontend not accessible")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running at", BACKEND_URL)
            print(f"✅ API keys configured: {data.get('has_keys', False)}")
            return data.get('has_keys', False)
        else:
            print("❌ Backend health check failed")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_backend_workflow():
    """Test the complete backend workflow"""
    print("\n🧪 Testing complete backend workflow...")
    
    # Test story request
    story_request = {
        "age": 6,
        "reading_level": "early_reader", 
        "diagnosis_summary": "autism; sound sensitivity; prefers routine",
        "situation": "saying hello to new classmates",
        "setting": "elementary classroom",
        "words_to_avoid": ["scary", "bad"],
        "voice_preset": "calm_childlike_female"
    }
    
    try:
        # Start job
        print("📝 Starting story generation job...")
        response = requests.post(f"{BACKEND_URL}/v1/social-story:start", 
                               json=story_request, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Job creation failed: {response.status_code}")
            return False
            
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"✅ Job created with ID: {job_id}")
        
        # Monitor job status
        print("⏳ Monitoring job progress...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{BACKEND_URL}/v1/jobs/{job_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data["status"]
                print(f"   Status: {status}")
                
                if status == "succeeded":
                    print("✅ Job completed successfully!")
                    print("🎬 Video is ready for download")
                    return True
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    print(f"❌ Job failed: {error}")
                    return False
                    
            time.sleep(5)  # Check every 5 seconds
            
        print("⏰ Job timeout - taking longer than expected")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend workflow test failed: {e}")
        return False

def main():
    print("🚀 Testing Social Story Integration")
    print("=" * 50)
    
    # Test components
    frontend_ok = test_frontend()
    backend_ok = test_backend_health()
    
    if not frontend_ok:
        print("\n❌ Frontend is not accessible!")
        print("Make sure to run: python3 proxy_server.py")
        return 1
        
    if not backend_ok:
        print("\n❌ Backend is not properly configured!")
        print("Make sure to run: uvicorn social_story.app:app --reload --host 0.0.0.0 --port 8000")
        return 1
    
    print("\n✅ Both frontend and backend are running!")
    print("\n🌐 Access your application at:")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend API: {BACKEND_URL}")
    
    # Ask user if they want to test the full workflow
    print("\n" + "=" * 50)
    test_full = input("Do you want to test the full story generation workflow? (y/N): ").lower().strip()
    
    if test_full == 'y':
        if test_backend_workflow():
            print("\n🎉 FULL INTEGRATION TEST PASSED!")
            print("Your Social Story application is fully functional!")
        else:
            print("\n⚠️  Backend workflow test had issues")
            print("Check the backend logs for more details")
            return 1
    else:
        print("\n✅ Basic integration test completed")
        print("You can now use the web interface to create social stories!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
