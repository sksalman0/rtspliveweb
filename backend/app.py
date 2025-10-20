from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__, static_folder='static')
CORS(app)

HLS_OUTPUT = os.path.join(app.static_folder, 'hls')
os.makedirs(HLS_OUTPUT, exist_ok=True)

RTSP_URL = "rtsp://rtspstream:f2uiZuAIXMHTrvil_0I_l@zephyr.rtsp.stream/movie"

# Start FFmpeg process if not already running
ffmpeg_command = [
    'ffmpeg',
    '-rtsp_transport', 'tcp',
    '-i', RTSP_URL,
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-tune', 'zerolatency',
    '-f', 'hls',
    '-hls_time', '2',
    '-hls_list_size', '5',
    '-hls_flags', 'delete_segments',
    '-hls_segment_filename', os.path.join(HLS_OUTPUT, 'segment_%03d.ts'),
    os.path.join(HLS_OUTPUT, 'index.m3u8')
]

# Start ffmpeg only once
if not any('ffmpeg' in p.name() for p in __import__('psutil').process_iter()):
    subprocess.Popen(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.route('/video')
def video():
    return send_from_directory(HLS_OUTPUT, 'index.m3u8')

@app.route('/hls/<path:filename>')
def hls(filename):
    return send_from_directory(HLS_OUTPUT, filename)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
