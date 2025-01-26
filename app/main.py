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

# Configuration
UPLOAD_FOLDER = '/app/VideosDirPath'
ALLOWED_EXTENSIONS = {'mp4', 'mov'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_video():
    temp_files = []  # Keep track of temporary files to clean up

    try:
        # Check if video file is provided
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        if not video or not allowed_file(video.filename):
            return jsonify({'error': 'Invalid video file'}), 400

        # Get parameters
        description = request.form.get('description', '')
        accountname = request.form.get('accountname')
        hashtags = request.form.get('hashtags', '').split(',') if request.form.get('hashtags') else []
        sound_name = request.form.get('sound_name')
        sound_aud_vol = request.form.get('sound_aud_vol', 'mix')

        if not accountname:
            return jsonify({'error': 'Account name is required'}), 400

        # Save video temporarily
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_files.append(temp_video.name)
        video.save(temp_video.name)

        # Process audio if sound is specified
        final_video_path = temp_video.name
        if sound_name:
            processor = AudioProcessor()
            sound_path = f'/app/sounds/{sound_name}.mp3'
            if not os.path.exists(sound_path):
                return jsonify({'error': 'Sound file not found'}), 404
            
            final_video_path = processor.mix_audio(
                temp_video.name,
                sound_path,
                sound_aud_vol
            )
            temp_files.append(final_video_path)

        # Prepare caption with hashtags
        caption = description
        if hashtags and hashtags[0]:  # Only add hashtags if the list is not empty and first element is not empty
            caption += ' ' + ' '.join(f'#{tag.strip()}' for tag in hashtags if tag.strip())

        # Upload to TikTok
        client = TikTokClient(accountname)
        result = client.upload_video(final_video_path, caption)
        
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
    app.run(host='0.0.0.0', port=8000)