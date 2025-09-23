import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Voice, VoiceRequest, get_db

ADMIN_ID = 542290480

async def admin_add_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding new voice by admin"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    text = """
➕ افزودن ویس جدید

لطفاً ویس مورد نظر را ارسال کنید.
سپس عنوان و تگ‌های آن را وارد کنید.

فرمت تگ‌ها: تگ1,تگ2,تگ3
    """
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def admin_view_voices_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all voices to admin"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    db = get_db()
    voices = db.query(Voice).order_by(Voice.usage_count.desc()).limit(20).all()
    
    if not voices:
        text = "هیچ ویسی در دیتابیس موجود نیست."
    else:
        text = "📋 لیست ویس‌ها (20 مورد اول):\n\n"
        for i, voice in enumerate(voices, 1):
            text += f"{i}. {voice.title or 'بدون عنوان'}\n"
            text += f"   📊 {voice.usage_count} بار استفاده\n"
            if voice.tags:
                try:
                    tags = json.loads(voice.tags)
                    text += f"   🏷️ {', '.join(tags[:3])}\n"
                except:
                    pass
            text += "\n"
    
    keyboard = [
        [InlineKeyboardButton("🗑️ حذف ویس", callback_data="admin_delete_voice")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    db.close()

async def admin_requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending voice requests to admin"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    db = get_db()
    requests = db.query(VoiceRequest).filter(VoiceRequest.status == 'pending').limit(10).all()
    
    if not requests:
        text = "هیچ درخواست در انتظاری وجود ندارد."
    else:
        text = "📝 درخواست‌های در انتظار:\n\n"
        for i, req in enumerate(requests, 1):
            text += f"{i}. کاربر {req.user_id}\n"
            text += f"   📄 {req.description[:100]}...\n"
            text += f"   📅 {req.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("✅ تایید درخواست", callback_data="admin_approve_request")],
        [InlineKeyboardButton("❌ رد درخواست", callback_data="admin_reject_request")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    db.close()

async def save_voice_to_db(file_id, file_path, title, tags_str, created_by):
    """Save voice to database"""
    db = get_db()
    
    # Parse tags
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    tags_json = json.dumps(tags, ensure_ascii=False)
    
    # Create voice record
    voice = Voice(
        file_id=file_id,
        file_path=file_path,
        title=title,
        tags=tags_json,
        created_by=created_by
    )
    
    db.add(voice)
    db.commit()
    db.close()
    
    return voice.id

async def delete_voice_from_db(voice_id):
    """Delete voice from database"""
    db = get_db()
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if voice:
        db.delete(voice)
        db.commit()
        db.close()
        return True
    db.close()
    return False

async def approve_voice_request(request_id):
    """Approve a voice request"""
    db = get_db()
    request = db.query(VoiceRequest).filter(VoiceRequest.id == request_id).first()
    if request:
        request.status = 'approved'
        db.commit()
        db.close()
        return True
    db.close()
    return False

async def reject_voice_request(request_id):
    """Reject a voice request"""
    db = get_db()
    request = db.query(VoiceRequest).filter(VoiceRequest.id == request_id).first()
    if request:
        request.status = 'rejected'
        db.commit()
        db.close()
        return True
    db.close()
    return False

