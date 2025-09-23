import os
import subprocess
from telegram import Update
from telegram.ext import ContextTypes

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download video from Telegram"""
    video = update.message.video
    if not video:
        return None
    
    # Create downloads directory if not exists
    os.makedirs('downloads', exist_ok=True)
    
    # Download video
    file = await context.bot.get_file(video.file_id)
    file_path = f"downloads/{video.file_id}.mp4"
    await file.download_to_drive(file_path)
    
    return file_path, video.duration

async def convert_video_to_voice(video_path, start_time=None, end_time=None):
    """Convert video to voice using ffmpeg"""
    try:
        # Create voices directory if not exists
        os.makedirs('voices', exist_ok=True)
        
        # Generate output filename
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = f"voices/{base_name}.ogg"
        
        # Build ffmpeg command
        cmd = ['ffmpeg', '-i', video_path]
        
        # Add time range if specified
        if start_time and end_time:
            cmd.extend(['-ss', start_time, '-to', end_time])
        
        # Add audio conversion parameters
        cmd.extend([
            '-vn',  # No video
            '-acodec', 'libopus',  # Opus codec for Telegram
            '-b:a', '64k',  # Audio bitrate
            '-ac', '1',  # Mono
            '-ar', '48000',  # Sample rate
            output_path,
            '-y'  # Overwrite output file
        ])
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return output_path
        else:
            print(f"FFmpeg error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error converting video: {e}")
        return None

def parse_time_range(time_str):
    """Parse time range string (e.g., '09:67' -> start:end)"""
    try:
        if ':' in time_str:
            start, end = time_str.split(':')
            # Convert to seconds
            start_sec = int(start)
            end_sec = int(end)
            
            # Format for ffmpeg (MM:SS)
            start_formatted = f"{start_sec//60:02d}:{start_sec%60:02d}"
            end_formatted = f"{end_sec//60:02d}:{end_sec%60:02d}"
            
            return start_formatted, end_formatted
        else:
            return None, None
    except:
        return None, None

async def get_video_info(video_path):
    """Get video information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            return duration
        else:
            return None
            
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def cleanup_temp_files(file_path):
    """Clean up temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

