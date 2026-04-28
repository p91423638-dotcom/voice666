from flask import Flask, render_template, request, send_file, jsonify
from gtts import gTTS
import io
import os
from functools import wraps
import time
from collections import defaultdict

app = Flask(__name__)

# Rate limiting: 10 requests per minute per IP
rate_limits = defaultdict(list)
MAX_REQUESTS = 10
TIME_WINDOW = 60  # seconds

def rate_limit():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            now = time.time()
            
            # Clean old requests
            rate_limits[client_ip] = [
                req_time for req_time in rate_limits[client_ip] 
                if now - req_time < TIME_WINDOW
            ]
            
            if len(rate_limits[client_ip]) >= MAX_REQUESTS:
                return jsonify({
                    'error': 'Rate limit exceeded. Please wait a moment.',
                    'remaining': MAX_REQUESTS - len(rate_limits[client_ip])
                }), 429
            
            rate_limits[client_ip].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Voices and languages config
VOICES = {
    'en': {
        'name': 'English (US)',
        'voices': ['male', 'female']
    },
    'es': {
        'name': 'Spanish',
        'voices': ['male', 'female']
    },
    'fr': {
        'name': 'French',
        'voices': ['male', 'female']
    },
    'de': {
        'name': 'German',
        'voices': ['male', 'female']
    },
    'it': {
        'name': 'Italian',
        'voices': ['male', 'female']
    },
    'pt': {
        'name': 'Portuguese',
        'voices': ['male', 'female']
    },
    'hi': {
        'name': 'Hindi',
        'voices': ['male', 'female']
    },
    'ar': {
        'name': 'Arabic',
        'voices': ['male', 'female']
    }
}

@app.route('/')
def index():
    return render_template('index.html', voices=VOICES)

@app.route('/generate', methods=['POST'])
@rate_limit()
def generate_speech():
    data = request.json
    text = data.get('text', '').strip()
    lang = data.get('lang', 'en')
    voice = data.get('voice', 'male')
    
    # Validation
    if len(text) > 500:  # Max 500 chars
        return jsonify({'error': 'Text too long (max 500 characters)'}), 400
    
    if not text:
        return jsonify({'error': 'Please enter some text'}), 400
    
    if lang not in VOICES:
        return jsonify({'error': 'Invalid language'}), 400
    
    try:
        # gTTS tld for better quality (US English)
        tld = 'com' if lang == 'en' else 'co.uk'
        
        tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        
        # Create in-memory MP3 file
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return send_file(
            mp3_fp,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='voice.mp3',
            cache_timeout=0
        )
        
    except Exception as e:
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
