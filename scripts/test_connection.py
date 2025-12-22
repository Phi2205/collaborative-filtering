"""
Script để test kết nối database
Chạy: python scripts/test_connection.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Kiểm tra cấu hình database...")
print()

# Kiểm tra các biến môi trường
DATABASE_URL = os.getenv('DATABASE_URL')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

print("📋 Thông tin cấu hình:")
print(f"  DATABASE_URL: {'✅ Có' if DATABASE_URL else '❌ Không có'}")
print(f"  POSTGRES_HOST: {POSTGRES_HOST if POSTGRES_HOST else '❌ Không có'}")
print(f"  POSTGRES_USER: {POSTGRES_USER if POSTGRES_USER else '❌ Không có'}")
print(f"  POSTGRES_PASSWORD: {'✅ Có (ẩn)' if POSTGRES_PASSWORD else '❌ Không có'}")
print(f"  POSTGRES_DB: {POSTGRES_DB if POSTGRES_DB else '❌ Không có'}")
print(f"  POSTGRES_PORT: {POSTGRES_PORT}")
print()

if not DATABASE_URL and not all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    print("❌ Thiếu thông tin database trong .env")
    print("💡 Vui lòng kiểm tra file .env")
    sys.exit(1)

# Test connection
print("🔌 Đang test kết nối database...")
try:
    from app.utils.database import engine
    
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        version = result.fetchone()[0]
        print("✅ Kết nối database thành công!")
        print(f"📊 PostgreSQL Version: {version}")
        print()
        
        # Kiểm tra các bảng
        print("📋 Kiểm tra các bảng:")
        tables = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        table_list = [row[0] for row in tables]
        required_tables = ['user_profile', 'tour', 'user_tour_interaction']
        
        for table in required_tables:
            if table in table_list:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (chưa có)")
        
        print()
        
        # Đếm số lượng records
        if 'user_profile' in table_list:
            count = conn.execute("SELECT COUNT(*) FROM user_profile;").fetchone()[0]
            print(f"👥 Số users: {count}")
        
        if 'tour' in table_list:
            count = conn.execute("SELECT COUNT(*) FROM tour WHERE is_active = true AND is_approved = true AND is_banned = false;").fetchone()[0]
            print(f"🎯 Số tours active: {count}")
        
        if 'user_tour_interaction' in table_list:
            count = conn.execute("SELECT COUNT(*) FROM user_tour_interaction;").fetchone()[0]
            print(f"📊 Số interactions: {count}")
        
except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")
    print()
    print("💡 Hướng dẫn sửa lỗi:")
    print("1. Kiểm tra lại password trong file .env")
    print("2. Copy lại External Database URL từ Render dashboard")
    print("3. Đảm bảo đã enable 'Allow connections from outside Render'")
    print("4. Kiểm tra IP của bạn đã được whitelist chưa")
    print()
    print("📖 Xem thêm: docs/TROUBLESHOOTING.md")
    sys.exit(1)

print()
print("✅ Tất cả đều OK!")

