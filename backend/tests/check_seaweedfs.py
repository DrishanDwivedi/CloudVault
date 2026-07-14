# Test script to verify SeaweedFS server is running
import requests
import sys

def test_seaweedfs_server():
    base_url = "http://localhost:8333"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ SeaweedFS server is running at http://localhost:8333")
            return True
        else:
            print(f"❌ SeaweedFS server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed: SeaweedFS server is not running at http://localhost:8333")
        print("💡 Start SeaweedFS with: weed.exe server -dir=data-warm -filer -s3 -s3.port=8333")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing SeaweedFS server connection...")
    if test_seaweedfs_server():
        print("\n🎉 SeaweedFS server is ready!")
        sys.exit(0)
    else:
        print("\n⚠️  SeaweedFS server is not running.")
        sys.exit(1)