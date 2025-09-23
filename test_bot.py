#!/usr/bin/env python3
"""
Test script for SootFun Bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import User, Voice, VoiceRequest, get_db, engine, Base
from search_utils import fuzzy_search, get_popular_voices, get_recent_voices
import json

def test_database():
    """Test database functionality"""
    print("🔍 Testing database...")
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Test database connection
    db = get_db()
    
    # Add test user
    test_user = User(
        telegram_id=123456789,
        phone_number="+989123456789",
        first_name="Test User",
        username="testuser",
        is_admin=False
    )
    
    db.add(test_user)
    db.commit()
    
    # Add test voice
    test_voice = Voice(
        file_id="test_file_id",
        file_path="voices/test.ogg",
        title="تست صدا",
        tags=json.dumps(["تست", "صدا", "نمونه"], ensure_ascii=False),
        created_by=123456789
    )
    
    db.add(test_voice)
    db.commit()
    
    # Test queries
    users = db.query(User).all()
    voices = db.query(Voice).all()
    
    print(f"✅ Users in database: {len(users)}")
    print(f"✅ Voices in database: {len(voices)}")
    
    db.close()
    return True

def test_search():
    """Test search functionality"""
    print("🔍 Testing search...")
    
    # Test fuzzy search
    results = fuzzy_search("تست")
    print(f"✅ Search results for 'تست': {len(results)}")
    
    # Test popular voices
    popular = get_popular_voices(5)
    print(f"✅ Popular voices: {len(popular)}")
    
    # Test recent voices
    recent = get_recent_voices(5)
    print(f"✅ Recent voices: {len(recent)}")
    
    return True

def test_imports():
    """Test all imports"""
    print("🔍 Testing imports...")
    
    try:
        import telegram
        print("✅ python-telegram-bot imported successfully")
        
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
        
        from bot import main
        print("✅ Bot main function imported successfully")
        
        from admin_handlers import admin_add_voice_handler
        print("✅ Admin handlers imported successfully")
        
        from media_utils import convert_video_to_voice
        print("✅ Media utils imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 Starting SootFun Bot Tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Search", test_search)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} test passed\n")
                passed += 1
            else:
                print(f"❌ {test_name} test failed\n")
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready to run.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    main()

