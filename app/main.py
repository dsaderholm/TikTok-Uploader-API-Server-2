from flask import Flask, request, jsonify
import os
import sys
from tiktok_client import TikTokClient
import tempfile
import logging
import traceback

# Add TikTok Uploader to path
sys.path.append('/app/TiktokAutoUploader')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Add CORS support
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Configuration
ALLOWED_EXTENSIONS = {'mp4', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/ping', methods=['GET'])
def ping():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "message": "Server is running"})

@app.route('/upload', methods=['POST'])
def upload_video():
    logger.info("Received upload request")
    temp_files = []  # Keep track of temporary files to clean up

    try:
        # Check if video file is provided
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        if not video or not video.filename:
            return jsonify({'error': 'Invalid video file'}), 400

        if not allowed_file(video.filename):
            return jsonify({'error': 'Invalid file type. Allowed types: mp4, mov'}), 400

        # Get parameters
        description = request.form.get('description', '')
        accountname = request.form.get('accountname')

        logger.info(f"Processing upload for account: {accountname}")

        if not accountname:
            return jsonify({'error': 'Account name is required'}), 400

        # Save video with proper error handling
        try:
            temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_files.append(temp_video.name)
            video.save(temp_video.name)
            logger.info(f"Video saved temporarily to {temp_video.name}")

            # Verify file was saved and is not empty
            if not os.path.exists(temp_video.name):
                raise Exception("Failed to save video file")
            
            file_size = os.path.getsize(temp_video.name)
            if file_size == 0:
                raise Exception("Saved video file is empty")
                
            logger.info(f"Saved video file size: {file_size} bytes")
            
        except Exception as e:
            logger.error(f"Error saving video: {str(e)}")
            return jsonify({'error': f'Error saving video: {str(e)}'}), 500

        # Use the original video without processing
        final_video_path = temp_video.name

        # Use description as caption
        caption = description

        # Upload to TikTok with proper error handling
        try:
            client = TikTokClient(accountname)
            result = client.upload_video(final_video_path, caption)
            logger.info(f"Upload result: {result}")
            
            return jsonify({
                'success': True,
                'message': 'Video uploaded successfully',
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Error in TikTok upload: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'TikTok upload error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Unexpected error in upload_video: {str(e)}")
        logger.error(traceback.format_exc())
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
    app.run(host='0.0.0.0', port=8048)
