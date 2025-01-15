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
        self.cookies_dir = os.path.join(self.tiktok_uploader_path, 'CookiesDir')  
        
        # Ensure required directories exist
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.cookies_dir, exist_ok=True)

        # Log important paths
        logger.info(f"TikTok Uploader Path: {self.tiktok_uploader_path}")
        logger.info(f"Videos Directory: {self.videos_dir}")
        logger.info(f"Cookies Directory: {self.cookies_dir}")

        # Setup proper config.txt
        config_path = os.path.join(self.tiktok_uploader_path, 'config.txt')
        logger.info("Creating config.txt")
        with open(config_path, 'w') as f:
            f.write(f'videos_dir={os.path.join(self.tiktok_uploader_path, "VideosDirPath")}\n')
            f.write(f'cookies_dir={os.path.join(self.tiktok_uploader_path, "CookiesDir")}\n')
        
        logger.info(f"Config contents:")
        with open(config_path, 'r') as f:
            logger.info(f.read())

        # Copy and rename cookie file from mounted volume to TikTok uploader's CookiesDir
        source_cookie = f'/app/CookiesDir/tiktok_session-{username}.cookie'
        dest_cookie = os.path.join(self.cookies_dir, f'tiktok_session-{username}')
        
        if os.path.exists(source_cookie):
            logger.info(f"Copying cookie from {source_cookie} to {dest_cookie}")
            shutil.copy2(source_cookie, dest_cookie)
            # Read and log first few bytes of cookie file to verify content
            with open(dest_cookie, 'rb') as f:
                content = f.read(100)
                logger.info(f"First 100 bytes of cookie file: {content}")
        else:
            logger.error(f"Cookie file not found: {source_cookie}")
            raise Exception(f"Cookie file not found for user {username}")

    def _run_tiktok_command(self, command):
        """Run a TikTok uploader CLI command"""
        try:
            logger.info(f"Running command: {' '.join(command)}")
            logger.info(f"Working directory: {self.tiktok_uploader_path}")
            
            # Log contents of important directories
            logger.info(f"Contents of Videos directory: {os.listdir(self.videos_dir)}")
            logger.info(f"Contents of Cookies directory: {os.listdir(self.cookies_dir)}")
            
            # Log specific cookie file info
            cookie_path = os.path.join(self.cookies_dir, f'tiktok_session-{self.username}')
            if os.path.exists(cookie_path):
                logger.info(f"Cookie file exists at {cookie_path}, size: {os.path.getsize(cookie_path)} bytes")
                with open(cookie_path, 'rb') as f:
                    content = f.read(100)
                    logger.info(f"First 100 bytes of cookie file: {content}")
            else:
                logger.error(f"Cookie file not found at {cookie_path}")

            # Get absolute path to python3
            python_path = subprocess.check_output(['which', 'python3']).decode().strip()
            logger.info(f"Using Python path: {python_path}")
            
            command[0] = python_path  # Replace 'python' with full path
            
            result = subprocess.run(
                command,
                cwd=self.tiktok_uploader_path,
                check=True,
                capture_output=True,
                text=True,
                env={
                    "PYTHONPATH": self.tiktok_uploader_path,
                    "PATH": os.environ.get("PATH", ""),
                    "DISPLAY": os.environ.get("DISPLAY", ":99")
                }
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
                'python3',  # Changed from 'python' to 'python3'
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
