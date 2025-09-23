import re
from difflib import SequenceMatcher
from database import Voice, get_db
import json

def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fuzzy_search(query, threshold=0.6):
    """Perform fuzzy search on voice tags and titles"""
    db = get_db()
    voices = db.query(Voice).all()
    results = []
    
    query = query.lower().strip()
    
    for voice in voices:
        # Check title similarity
        title_similarity = similarity(query, voice.title.lower()) if voice.title else 0
        
        # Check tags similarity
        max_tag_similarity = 0
        if voice.tags:
            try:
                tags = json.loads(voice.tags)
                for tag in tags:
                    tag_similarity = similarity(query, tag.lower())
                    max_tag_similarity = max(max_tag_similarity, tag_similarity)
            except:
                pass
        
        # Use the highest similarity score
        best_similarity = max(title_similarity, max_tag_similarity)
        
        if best_similarity >= threshold:
            results.append((voice, best_similarity))
    
    # Sort by similarity score (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    db.close()
    return [voice for voice, score in results]

def get_popular_voices(limit=10):
    """Get most popular voices by usage count"""
    db = get_db()
    voices = db.query(Voice).order_by(Voice.usage_count.desc()).limit(limit).all()
    db.close()
    return voices

def get_recent_voices(limit=10):
    """Get recently added voices"""
    db = get_db()
    voices = db.query(Voice).order_by(Voice.created_at.desc()).limit(limit).all()
    db.close()
    return voices

def increment_usage(voice_id):
    """Increment usage count for a voice"""
    db = get_db()
    voice = db.query(Voice).filter(Voice.id == voice_id).first()
    if voice:
        voice.usage_count += 1
        db.commit()
    db.close()

