#!/usr/bin/env python
"""
Script để chạy Recommend Server
Sử dụng: python start.py
"""
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Lấy port từ environment variable hoặc dùng mặc định 3000
    port = int(os.getenv("PORT", 3000))
    
    print(f"🚀 Starting Recommend Server on port {port}...")
    print(f"📖 API Documentation: http://localhost:{port}/docs")
    print(f"🔍 ReDoc: http://localhost:{port}/redoc")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["app"]
    )

