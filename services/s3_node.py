import os
import sys
import hashlib
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

STORAGE_DIR = sys.argv[1] if len(sys.argv) > 1 else "./data"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 3900
NAME = sys.argv[3] if len(sys.argv) > 3 else "Garage S3 Archive Storage"

os.makedirs(STORAGE_DIR, exist_ok=True)
app = FastAPI(title=NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_file_path(bucket: str, key: str) -> str:
    b_dir = os.path.join(STORAGE_DIR, bucket)
    os.makedirs(b_dir, exist_ok=True)
    return os.path.join(b_dir, key)

@app.get("/")
def list_buckets():
    buckets = [d for d in os.listdir(STORAGE_DIR) if os.path.isdir(os.path.join(STORAGE_DIR, d))]
    default_bucket = "cloudvault-archive" if "archive" in NAME.lower() else "cloudvault-hot"
    if default_bucket not in buckets:
        buckets.append(default_bucket)
    b_xml = "".join([f"<Bucket><Name>{b}</Name><CreationDate>2026-01-01T00:00:00.000Z</CreationDate></Bucket>" for b in buckets])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Owner><ID>{NAME.lower().replace(' ', '-')}</ID><DisplayName>{NAME}</DisplayName></Owner>
  <Buckets>{b_xml}</Buckets>
</ListAllMyBucketsResult>"""
    return Response(content=xml, media_type="application/xml")

@app.head("/{bucket}")
def head_bucket(bucket: str):
    os.makedirs(os.path.join(STORAGE_DIR, bucket), exist_ok=True)
    return Response(status_code=200)

@app.put("/{bucket}")
def create_bucket(bucket: str):
    os.makedirs(os.path.join(STORAGE_DIR, bucket), exist_ok=True)
    return Response(status_code=200)

@app.head("/{bucket}/{key:path}")
def head_object(bucket: str, key: str):
    path = get_file_path(bucket, key)
    if not os.path.exists(path):
        return Response(status_code=404)
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        etag = hashlib.md5(f.read()).hexdigest()
    return Response(status_code=200, headers={"Content-Length": str(size), "ETag": f'"{etag}"', "Accept-Ranges": "bytes"})

@app.get("/{bucket}/{key:path}")
def get_object(bucket: str, key: str):
    path = get_file_path(bucket, key)
    if not os.path.exists(path):
        return Response(status_code=404)
    with open(path, "rb") as f:
        data = f.read()
    etag = hashlib.md5(data).hexdigest()
    return Response(content=data, media_type="application/octet-stream", headers={"ETag": f'"{etag}"', "Content-Length": str(len(data)), "Accept-Ranges": "bytes"})

@app.put("/{bucket}/{key:path}")
async def put_object(bucket: str, key: str, request: Request):
    data = await request.body()
    path = get_file_path(bucket, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    etag = hashlib.md5(data).hexdigest()
    print(f"[{NAME}] Stored object: /{bucket}/{key} ({len(data)} bytes)")
    return Response(status_code=200, headers={"ETag": f'"{etag}"'})

@app.delete("/{bucket}/{key:path}")
def delete_object(bucket: str, key: str):
    path = get_file_path(bucket, key)
    if os.path.exists(path):
        os.remove(path)
    print(f"[{NAME}] Deleted object: /{bucket}/{key}")
    return Response(status_code=204)

if __name__ == "__main__":
    banner = f"""
===================================================
      {NAME.upper()}
===================================================
 [STATUS]    Online (S3 API Active)
 [ENDPOINT]  http://127.0.0.1:{PORT}
 [STORAGE]   {os.path.abspath(STORAGE_DIR)}
===================================================
"""
    print(banner)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
