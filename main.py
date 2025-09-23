#!/usr/bin/env python3
"""
Flask wrapper for SootFun Bot deployment
"""

from flask import Flask, jsonify, request
import threading
import logging
import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Bot instance
bot_thread = None
bot_running = False

@app.route('/')
def index():
    """Main page"""
    return jsonify({
        "name": "SootFun Bot",
        "status": "running" if bot_running else "stopped",
        "description": "ربات تلگرام برای جستجو و اشتراک‌گذاری ویس‌های کوتاه",
        "features": [
            "جستجوی فازی ویس‌ها",
            "حالت Inline Bot",
            "تبدیل ویدیو به ویس",
            "پنل مدیریت ادمین",
            "رابط کاربری شیشه‌ای"
        ],
        "admin": "@Armintory",
        "bot_username": "@sootfun_bot"
    })

@app.route('/status')
def status():
    """Bot status"""
    return jsonify({
        "bot_running": bot_running,
        "thread_alive": bot_thread.is_alive() if bot_thread else False
    })

@app.route('/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    global bot_thread, bot_running
    
    if not bot_running:
        try:
            from bot import main as bot_main
            bot_thread = threading.Thread(target=bot_main, daemon=True)
            bot_thread.start()
            bot_running = True
            return jsonify({"message": "Bot started successfully", "status": "running"})
        except Exception as e:
            return jsonify({"error": str(e), "status": "error"}), 500
    else:
        return jsonify({"message": "Bot is already running", "status": "running"})

@app.route('/logs')
def get_logs():
    """Get bot logs"""
    try:
        if os.path.exists('sootfun_bot.log'):
            with open('sootfun_bot.log', 'r', encoding='utf-8') as f:
                logs = f.readlines()
                return jsonify({"logs": logs[-50:]})  # Last 50 lines
        else:
            return jsonify({"logs": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats')
def get_stats():
    """Get bot statistics"""
    try:
        from database import User, Voice, VoiceRequest, get_db
        
        db = get_db()
        user_count = db.query(User).count()
        voice_count = db.query(Voice).count()
        pending_requests = db.query(VoiceRequest).filter(VoiceRequest.status == 'pending').count()
        db.close()
        
        return jsonify({
            "users": user_count,
            "voices": voice_count,
            "pending_requests": pending_requests
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Auto-start bot
    try:
        from bot import main as bot_main
        bot_thread = threading.Thread(target=bot_main, daemon=True)
        bot_thread.start()
        bot_running = True
        print("🤖 SootFun Bot started automatically")
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

