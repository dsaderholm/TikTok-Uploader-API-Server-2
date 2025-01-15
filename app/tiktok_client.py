import sys
import os
import subprocess
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class TikTokClient:
    def __init__(self, username):
        self.username = username
        self.tiktok_uploader_path = '/app/TiktokAutoUploader'
        self.videos_dir = os.path.join(self.tiktok_uploader_path, 'VideosDirPath')  
        self.cookies_dir = os.path.join(self.tiktok_uploader_path, 'CookiesDir')  # Updated to use TikTok uploader's CookiesDir
        
        # Ensure required directories exist
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.cookies_dir, exist_ok=True)

        # Log important paths
        logger.info(f"TikTok Uploader Path: {self.tiktok_uploader_path}")
        logger.info(f"Videos Directory: {self.videos_dir}")
        logger.info(f"Cookies Directory: {self.cookies_dir}")
        
        # Check and create config.txt in the correct location
        config_path = os.path.join(self.tiktok_uploader_path, 'config.txt')
        if not os.path.exists(config_path):
            logger.info("Creating config.txt")
            with open(config_path, 'w') as f:
                f.write('videos_dir=VideosDirPath\ncookies_dir=CookiesDir\n')

        # Copy cookie file from mounted volume to TikTok uploader's CookiesDir
        source_cookie = '/app/CookiesDir/tiktok_session-{}.cookie'.format(username)
        dest_cookie = os.path.join(self.cookies_dir, f'tiktok_session-{username}')
        
        if os.path.exists(source_cookie):
            logger.info(f"Copying cookie from {source_cookie} to {dest_cookie}")
            shutil.copy2(source_cookie, dest_cookie)
        else:
            logger.error(f"Cookie file not found: {source_cookie}")
            raise Exception(f"Cookie file not found for user {username}")

    def _run_tiktok_command(self, command):
        """Run a TikTok uploader CLI command"""
        try:
            logger.info(f"Running command: {' '.join(command)}")
            logger.info(f"Working directory: {self.tiktok_uploader_path}")
            
            # Log the contents of important directories
            logger.info(f"Contents of Videos directory: {os.listdir(self.videos_dir)}")
            logger.info(f"Contents of Cookies directory: {os.listdir(self.cookies_dir)}")
            
            result = subprocess.run(
                command,
                cwd=self.tiktok_uploader_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"Command output: {result.stdout}")
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}")
            logger.error(f"Standard error: {e.stderr}")
            logger.error(f"Standard output: {e.stdout}")
            raise Exception(f"TikTok upload failed: {e.stderr}\nOutput: {e.stdout}")
        except Exception as e:
            logger.error(f"Error running TikTok command: {str(e)}")
            raise

    def upload_video(self, video_path, caption):
        """
        Upload a video to TikTok
        Args:
            video_path (str): Path to the video file
            caption (str): Video caption/title
        Returns:
            dict: Upload result
        """
        try:
            # Copy video to TikTok uploader's videos directory
            video_filename = Path(video_path).name
            final_video_path = os.path.join(self.videos_dir, video_filename)
            
            logger.info(f"Copying video from {video_path} to {final_video_path}")
            with open(video_path, 'rb') as src, open(final_video_path, 'wb') as dst:
                dst.write(src.read())

            # Verify the video file exists and log its size
            if os.path.exists(final_video_path):
                logger.info(f"Video file size: {os.path.getsize(final_video_path)} bytes")
            else:
                raise Exception(f"Video file not found at {final_video_path}")

            command = [
                'python',
                'cli.py',
                'upload',
                '--users', self.username,
                '-v', video_filename,
                '-t', caption
            ]

            # Execute upload
            result = self._run_tiktok_command(command)
            
            return {
                'status': 'success',
                'output': result
            }

        except Exception as e:
            logger.error(f"Failed to upload video: {str(e)}")
            raise
        
        finally:
            # Cleanup the copied video
            try:
                if os.path.exists(final_video_path):
                    os.unlink(final_video_path)
            except Exception as e:
                logger.error(f"Failed to cleanup video file: {str(e)}")
