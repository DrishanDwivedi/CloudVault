import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.adapters.seaweedfs import SeaweedFSAdapter

def test_upload_download():
    adapter = SeaweedFSAdapter()
    test_content = b"Hello, SeaweedFS! This is a test upload."
    file_name = "test_upload.txt"
    bucket_name = "test-bucket"
    
    result = adapter.upload(test_content, file_name, bucket_name)
    assert result is True
    
    downloaded_content = adapter.download(file_name, bucket_name)
    assert downloaded_content == test_content
    
    print("✓ Upload/download test passed")

def test_delete():
    adapter = SeaweedFSAdapter()
    file_name = "test_delete.txt"
    bucket_name = "test-bucket"
    
    result = adapter.delete(file_name, bucket_name)
    assert result is True
    
    exists = adapter.exists(file_name, bucket_name)
    assert exists is False
    
    print("✓ Delete test passed")

if __name__ == "__main__":
    test_upload_download()
    test_delete()
    print("\n✅ All SeaweedFS adapter tests passed!")