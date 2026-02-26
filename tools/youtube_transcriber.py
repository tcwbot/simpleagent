import logging
from typing import Optional

# Silence noisy logs
logging.getLogger("youtube_transcript_api").setLevel(logging.ERROR)

SCHEMA = {
    'type': 'function',
    'function': {
        'name': 'youtube_transcriber',
        'description': 'Extracts text transcripts from YouTube videos or Shorts. Handles modern 2026 API formats.',
        'parameters': {
            'type': 'object',
            'properties': {
                'video_url': {'type': 'string', 'description': 'The YouTube URL'}
            },
            'required': ['video_url'],
        },
    },
}

def extract_video_id(url: str) -> Optional[str]:
    import re
    match = re.search(r'(?:v=|shorts\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def execute(video_url: str):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        video_id = extract_video_id(video_url)
        if not video_id:
            return "ERROR: Invalid YouTube URL format."

        # Initialize API
        api = YouTubeTranscriptApi()
        
        # Fetch transcript (tries English by default)
        try:
            transcript_list = api.list(video_id)
            transcript = transcript_list.find_transcript(['en'])
            raw_data = transcript.fetch()
        except:
            # Fallback for some versions/environments
            raw_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

        # UNIVERSAL PARSER: Handles both old dicts and new 2026 Objects
        text_segments = []
        for entry in raw_data:
            if hasattr(entry, 'text'):
                # New 2026 Object format: entry.text
                text_segments.append(entry.text)
            elif isinstance(entry, dict) and 'text' in entry:
                # Legacy Dictionary format: entry['text']
                text_segments.append(entry['text'])
        
        full_text = " ".join(text_segments)
        
        if not full_text:
            return "ERROR: Transcript was found but no text content could be parsed."

        return f"SUCCESS [ID: {video_id}]: {full_text[:3000]}"

    except Exception as e:
        # Returns the EXACT technical error to the LLM (NameError, TypeError, etc)
        return f"TOOL_ERROR: {type(e).__name__} - {str(e)}"
