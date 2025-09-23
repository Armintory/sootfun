#!/usr/bin/env python3
"""
Production runner for SootFun Bot
"""

import os
import sys
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sootfun_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot"""
    try:
        logger.info("🚀 Starting SootFun Bot...")
        logger.info(f"📅 Start time: {datetime.now()}")
        
        # Import and run bot
        from bot import main as bot_main
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed with error: {e}")
        raise

if __name__ == "__main__":
    main()

