import subprocess
import tempfile
import os

class AudioProcessor:
    def __init__(self):
        self.volume_presets = {
            'mix': ('0.5', '0.5'),
            'background': ('0.8', '0.2'),
            'main': ('0.2', '0.8')
        }

    def mix_audio(self, video_path, sound_path, volume_type='mix'):
        if volume_type not in self.volume_presets:
            volume_type = 'mix'

        video_vol, sound_vol = self.volume_presets[volume_type]
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name

        cmd = [
            'ffmpeg', '-y',  # Added -y flag to force overwrite
            '-i', video_path,
            '-i', sound_path,
            '-filter_complex',
            f'[0:a]volume={video_vol}[a1];[1:a]volume={sound_vol}[a2];[a1][a2]amix=inputs=2:duration=first[aout]',
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy', '-c:a', 'aac',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg Error: {e.stderr}")
            raise