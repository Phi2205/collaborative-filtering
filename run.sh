#!/bin/bash
# Script để chạy Recommend Server trên Linux/Mac
# Sử dụng: chmod +x run.sh && ./run.sh

echo "🚀 Starting Recommend Server..."
echo ""

uvicorn app.main:app --reload --port 3000

