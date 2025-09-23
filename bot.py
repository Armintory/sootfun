import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultVoice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, InlineQueryHandler, CallbackQueryHandler
from database import User, Voice, VoiceRequest, get_db
from search_utils import fuzzy_search, get_popular_voices, get_recent_voices, increment_usage
from admin_handlers import admin_add_voice_handler, admin_view_voices_handler, admin_requests_handler, save_voice_to_db
from media_utils import download_video, convert_video_to_voice, parse_time_range, get_video_info, cleanup_temp_files

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "5955245262:AAEPyh31nfQB3lRx8LuUyTFM2OFxYicZytM"
ADMIN_ID = 542290480

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    
    # Check if user exists in database
    db = get_db()
    existing_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not existing_user:
        # Request phone number
        keyboard = [[InlineKeyboardButton("📱 اشتراک شماره تماس", request_contact=True)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🎵 به ربات صوت فان خوش آمدید! 🎵

برای استفاده از ربات، لطفاً شماره تماس خود را با ما به اشتراک بگذارید.

🔹 جستجوی آسان ویس‌ها با @sootfun_bot
🔹 تبدیل ویدیو به ویس
🔹 دسترسی به محبوب‌ترین ویس‌ها
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await show_main_menu(update, context)
    
    db.close()

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact sharing"""
    contact = update.message.contact
    user = update.effective_user
    
    db = get_db()
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.telegram_id == user.id).first()
    
    if not existing_user:
        # Create new user
        new_user = User(
            telegram_id=user.id,
            phone_number=contact.phone_number,
            first_name=user.first_name,
            username=user.username,
            is_admin=(user.id == ADMIN_ID)
        )
        db.add(new_user)
        db.commit()
        
        await update.message.reply_text("✅ ثبت نام شما با موفقیت انجام شد!")
        await show_main_menu(update, context)
    
    db.close()

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("🔥 محبوب‌ترین‌ها", callback_data="popular")],
        [InlineKeyboardButton("🆕 جدیدترین‌ها", callback_data="recent")],
        [InlineKeyboardButton("🎬 تبدیل ویدیو به ویس", callback_data="video_to_voice")],
        [InlineKeyboardButton("📝 درخواست صدای جدید", callback_data="request_voice")],
        [InlineKeyboardButton("❓ راهنما", callback_data="help")]
    ]
    
    # Add admin panel for admin user
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ پنل مدیریت", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """
🎵 منوی اصلی ربات صوت فان 🎵

برای جستجوی ویس در هر چت:
@sootfun_bot + کلمه کلیدی

یا از گزینه‌های زیر استفاده کنید:
    """
    
    if update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline queries"""
    query = update.inline_query.query
    
    if not query:
        # Show popular voices if no query
        voices = get_popular_voices(10)
    else:
        # Search for voices
        voices = fuzzy_search(query, threshold=0.4)
    
    results = []
    for voice in voices[:10]:  # Limit to 10 results
        result = InlineQueryResultVoice(
            id=str(voice.id),
            voice_url=f"https://api.telegram.org/file/bot{BOT_TOKEN}/{voice.file_path}",
            title=voice.title or "ویس بدون عنوان",
            voice_duration=voice.duration or 0
        )
        results.append(result)
    
    await update.inline_query.answer(results)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "popular":
        await show_popular_voices(update, context)
    elif query.data == "recent":
        await show_recent_voices(update, context)
    elif query.data == "video_to_voice":
        await query.edit_message_text("🎬 لطفاً ویدیوی خود را ارسال کنید تا آن را به ویس تبدیل کنم.")
        context.user_data['waiting_for_video'] = True
    elif query.data == "request_voice":
        await query.edit_message_text("📝 لطفاً توضیحی از ویس مورد نظرتان بنویسید:")
        context.user_data['waiting_for_voice_request'] = True
    elif query.data == "help":
        await show_help(update, context)
    elif query.data == "back_to_menu":
        await show_main_menu(update, context)
    elif query.data == "admin_panel" and query.from_user.id == ADMIN_ID:
        await show_admin_panel(update, context)
    elif query.data == "admin_add_voice" and query.from_user.id == ADMIN_ID:
        await admin_add_voice_handler(update, context)
    elif query.data == "admin_view_voices" and query.from_user.id == ADMIN_ID:
        await admin_view_voices_handler(update, context)
    elif query.data == "admin_requests" and query.from_user.id == ADMIN_ID:
        await admin_requests_handler(update, context)

async def show_popular_voices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show popular voices"""
    voices = get_popular_voices(10)
    
    if not voices:
        text = "هنوز ویسی اضافه نشده است."
    else:
        text = "🔥 محبوب‌ترین ویس‌ها:\n\n"
        for i, voice in enumerate(voices, 1):
            text += f"{i}. {voice.title or 'بدون عنوان'} ({voice.usage_count} بار استفاده)\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_recent_voices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent voices"""
    voices = get_recent_voices(10)
    
    if not voices:
        text = "هنوز ویسی اضافه نشده است."
    else:
        text = "🆕 جدیدترین ویس‌ها:\n\n"
        for i, voice in enumerate(voices, 1):
            text += f"{i}. {voice.title or 'بدون عنوان'}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    help_text = """
📖 راهنمای استفاده از ربات صوت فان

🔍 جستجوی ویس:
در هر چت @sootfun_bot و سپس کلمه کلیدی را تایپ کنید

🎬 تبدیل ویدیو به ویس:
ویدیو را ارسال کنید و ربات آن را به ویس تبدیل می‌کند

📝 درخواست ویس جدید:
می‌توانید از ادمین درخواست اضافه کردن ویس جدید کنید

🔥 محبوب‌ترین‌ها:
مشاهده پرکاربردترین ویس‌ها

🆕 جدیدترین‌ها:
مشاهده آخرین ویس‌های اضافه شده
    """
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (only for admin)"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    db = get_db()
    voice_count = db.query(Voice).count()
    user_count = db.query(User).count()
    pending_requests = db.query(VoiceRequest).filter(VoiceRequest.status == 'pending').count()
    db.close()
    
    admin_text = f"""
⚙️ پنل مدیریت ربات صوت فان

📊 آمار:
👥 تعداد کاربران: {user_count}
🎵 تعداد ویس‌ها: {voice_count}
📝 درخواست‌های در انتظار: {pending_requests}
    """
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن ویس", callback_data="admin_add_voice")],
        [InlineKeyboardButton("📋 مشاهده ویس‌ها", callback_data="admin_view_voices")],
        [InlineKeyboardButton("📝 درخواست‌ها", callback_data="admin_requests")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(admin_text, reply_markup=reply_markup)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    # This would be used for adding voices by admin
    if update.effective_user.id == ADMIN_ID:
        voice = update.message.voice
        # Here you would save the voice to database
        await update.message.reply_text("✅ ویس دریافت شد. لطفاً عنوان و تگ‌های آن را ارسال کنید.")

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video messages"""
    if context.user_data.get('waiting_for_video'):
        video = update.message.video
        if video:
            # Download video
            await update.message.reply_text("⏳ در حال دانلود ویدیو...")
            video_path, duration = await download_video(update, context)
            
            if video_path:
                # Show video info and options
                minutes = duration // 60
                seconds = duration % 60
                
                text = f"""
🎬 ویدیو دریافت شد!
⏱️ مدت زمان: {minutes:02d}:{seconds:02d}

برای برش ویدیو، فرمت زمانی را ارسال کنید:
مثال: 10:30 (از ثانیه 10 تا 30)

یا "تمام" برای تبدیل کل ویدیو
                """
                
                await update.message.reply_text(text)
                context.user_data['video_path'] = video_path
                context.user_data['video_duration'] = duration
                context.user_data['waiting_for_time_range'] = True
                context.user_data['waiting_for_video'] = False
        else:
            await update.message.reply_text("❌ لطفاً یک ویدیو ارسال کنید.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text
    
    if context.user_data.get('waiting_for_time_range'):
        # Handle time range for video conversion
        video_path = context.user_data.get('video_path')
        
        if text.lower() == "تمام":
            # Convert entire video
            await update.message.reply_text("⏳ در حال تبدیل ویدیو به ویس...")
            voice_path = await convert_video_to_voice(video_path)
        else:
            # Parse time range
            start_time, end_time = parse_time_range(text)
            if start_time and end_time:
                await update.message.reply_text("⏳ در حال برش و تبدیل ویدیو...")
                voice_path = await convert_video_to_voice(video_path, start_time, end_time)
            else:
                await update.message.reply_text("❌ فرمت زمانی نادرست. مثال: 10:30")
                return
        
        if voice_path:
            # Send voice file
            with open(voice_path, 'rb') as voice_file:
                await update.message.reply_voice(voice_file)
            
            # Cleanup
            cleanup_temp_files(video_path)
            cleanup_temp_files(voice_path)
            
            await update.message.reply_text("✅ تبدیل با موفقیت انجام شد!")
        else:
            await update.message.reply_text("❌ خطا در تبدیل ویدیو.")
        
        # Reset user data
        context.user_data.clear()
    
    elif context.user_data.get('waiting_for_voice_request'):
        # Handle voice request
        db = get_db()
        request = VoiceRequest(
            user_id=update.effective_user.id,
            description=text
        )
        db.add(request)
        db.commit()
        db.close()
        
        await update.message.reply_text("✅ درخواست شما ثبت شد و به ادمین ارسال خواهد شد.")
        context.user_data['waiting_for_voice_request'] = False

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    application.add_handler(MessageHandler(filters.VIDEO, video_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start the bot
    print("🤖 ربات صوت فان شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()

