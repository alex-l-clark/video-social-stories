#!/usr/bin/env python3
"""
Test the production endpoint to verify the deployment and environment
"""
import requests
import time
import json

BACKEND_URL = "https://social-story-backend.vercel.app"

def test_production_endpoint():
    """Test the production endpoint comprehensively"""
    
    print("🧪 Testing production endpoint...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        health_resp = requests.get(f"{BACKEND_URL}/health", timeout=10)
        health_data = health_resp.json()
        print(f"✅ Health: {health_data}")
        
        if not health_data.get('has_keys'):
            print("❌ API keys not configured in production!")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test start endpoint
    print("\n2. Testing start endpoint...")
    payload = {
        "situation": "test situation",
        "setting": "test setting", 
        "diagnosis_summary": "test"
    }
    
    try:
        print("📤 Sending start request...")
        start_time = time.time()
        
        start_resp = requests.post(
            f"{BACKEND_URL}/v1/social-story:start",
            json=payload,
            timeout=300  # 5 minutes
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request took {duration:.2f} seconds")
        
        if start_resp.status_code != 200:
            print(f"❌ Start request failed: {start_resp.status_code}")
            print(f"Response: {start_resp.text}")
            return False
            
        start_data = start_resp.json()
        print(f"📋 Start response: {start_data}")
        
        job_id = start_data.get('job_id')
        status = start_data.get('status')
        error = start_data.get('error')
        
        if duration < 5:
            print("⚠️  Request completed very quickly - likely still using background tasks")
            print("🔍 Let's check the job status...")
            
            # Poll job status
            for i in range(12):  # Check for 1 minute
                time.sleep(5)
                try:
                    status_resp = requests.get(f"{BACKEND_URL}/v1/jobs/{job_id}")
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        current_status = status_data.get('status')
                        print(f"📊 Job {job_id} status: {current_status}")
                        
                        if current_status == 'succeeded':
                            print("✅ Job completed successfully!")
                            return True
                        elif current_status == 'failed':
                            print(f"❌ Job failed: {status_data.get('error')}")
                            return False
                    else:
                        print(f"⚠️  Status check failed: {status_resp.status_code}")
                except Exception as e:
                    print(f"⚠️  Status check error: {e}")
                    
            print("⏰ Job didn't complete within 1 minute")
            return False
            
        elif status == 'succeeded':
            print("✅ Request completed synchronously and succeeded!")
            return True
        elif status == 'failed':
            print(f"❌ Request completed synchronously but failed: {error}")
            return False
        else:
            print(f"⚠️  Unexpected status after long request: {status}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate synchronous execution is working")
        print("   but the process is taking longer than expected")
        return False
    except Exception as e:
        print(f"❌ Start request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_production_endpoint()
    if success:
        print("\n🎉 PRODUCTION TEST PASSED!")
    else:
        print("\n💥 PRODUCTION TEST FAILED!")
        print("\n🔧 Next steps:")
        print("1. Ensure RENDER_WORKER_URL is set in Vercel environment variables")
        print("2. Verify all API keys are configured in Vercel")
        print("3. Check that the latest deployment includes the synchronous fix")
