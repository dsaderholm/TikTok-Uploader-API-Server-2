from flask import Flask, request, jsonify
import os
import sys
from tiktok_client import TikTokClient
from audio_processor import AudioProcessor
import tempfile
import logging

# Add TikTok Uploader to path
sys.path.append('/app/TiktokAutoUploader')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Add a test route
@app.route('/')
def test():
    return jsonify({"status": "server is running"})

# Configuration
UPLOAD_FOLDER = '/app/VideosDirPath'
ALLOWED_EXTENSIONS = {'mp4', 'mov'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_string(s):
    """Remove surrounding quotes from string"""
    if isinstance(s, str):
        return s.strip("'\"")
    return s

@app.route('/upload', methods=['POST'])
def upload_video():
    logger.info("Received upload request")
    temp_files = []  # Keep track of temporary files to clean up

    try:
        # Log request details
        logger.info(f"Files in request: {request.files}")
        logger.info(f"Form data in request: {request.form}")
        
        # Check if video file is provided
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        if not video or not allowed_file(video.filename):
            logger.error(f"Invalid video file: {video.filename if video else 'None'}")
            return jsonify({'error': 'Invalid video file'}), 400

        # Get parameters and clean them
        description = clean_string(request.form.get('description', ''))
        accountname = clean_string(request.form.get('accountname'))
        hashtags = [clean_string(tag) for tag in request.form.get('hashtags', '').split(',') if tag.strip()]
        sound_name = clean_string(request.form.get('sound_name'))
        sound_aud_vol = clean_string(request.form.get('sound_aud_vol', 'mix'))

        if not accountname:
            logger.error("No account name provided")
            return jsonify({'error': 'Account name is required'}), 400

        # Save video temporarily
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_files.append(temp_video.name)
        video.save(temp_video.name)
        logger.info(f"Video saved temporarily to {temp_video.name}")

        # Process audio if sound is specified
        final_video_path = temp_video.name
        if sound_name:
            processor = AudioProcessor()
            sound_path = f'/app/sounds/{sound_name}.mp3'
            logger.info(f"Looking for sound file at: {sound_path}")
            
            # List available sound files
            sound_dir = '/app/sounds'
            if os.path.exists(sound_dir):
                logger.info(f"Available sound files: {os.listdir(sound_dir)}")
            else:
                logger.error(f"Sound directory does not exist: {sound_dir}")
            
            if not os.path.exists(sound_path):
                logger.error(f"Sound file not found: {sound_path}")
                return jsonify({'error': f'Sound file not found: {sound_name}'}), 404
            
            final_video_path = processor.mix_audio(
                temp_video.name,
                sound_path,
                sound_aud_vol
            )
            temp_files.append(final_video_path)
            logger.info(f"Audio processed, new video path: {final_video_path}")

        # Prepare caption with hashtags
        caption = description
        if hashtags:  # Only add hashtags if the list is not empty
            caption += ' ' + ' '.join(f'#{tag.strip()}' for tag in hashtags if tag.strip())
        logger.info(f"Prepared caption: {caption}")

        # Upload to TikTok
        client = TikTokClient(accountname)
        result = client.upload_video(final_video_path, caption)
        logger.info(f"Upload result: {result}")
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'result': result
        })

    except Exception as e:
        logger.error(f"Error in upload_video: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error cleaning up {temp_file}: {str(e)}")

if __name__ == '__main__':
    # Add startup logging
    logger.info("Starting Flask server...")
    logger.info("Registered routes:")
    logger.info(app.url_map)
    
    app.run(host='0.0.0.0', port=8048)