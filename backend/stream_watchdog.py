import time
import os
import signal
import subprocess
import sys
from pathlib import Path

# Configuration
STREAM_URL = "rtsp://rtspstream:f2uiZuAIXMHTrvil_0I_l@zephyr.rtsp.stream/traffic" # RTSP source
OUTPUT_DIR = "../frontend/public/"
HLS_FILE = "stream.m3u8"
MAX_AGE_SECONDS = 5  # More strict for RTSP
CHECK_INTERVAL = 3   # Check more frequently
FFMPEG_CMD = [
    "ffmpeg",
    "-fflags", "nobuffer",   # Reduce input buffering for lower latency
    "-rtsp_transport", "tcp", # Use TCP for RTSP (more reliable than UDP)
    "-i", STREAM_URL,
    "-c:v", "libx264",
    "-preset", "ultrafast",  # Fastest encoding
    "-tune", "zerolatency",  # Optimize for low latency
    "-profile:v", "baseline", # Best for streaming
    "-sc_threshold", "0",    # Disable scene change detection
    "-g", "15",              # More frequent keyframes for RTSP
    "-keyint_min", "15",     # Min keyframe interval
    "-r", "30",              # 30fps output
    "-b:v", "1000k",         # Lower bitrate for more stability with RTSP
    "-maxrate", "1200k",     # Lower max rate
    "-bufsize", "600k",      # Smaller buffer for faster response
    "-hls_time", "1",        # 1-second segments for lower latency
    "-hls_list_size", "5",   # Smaller playlist (5 seconds)
    "-hls_flags", "delete_segments+append_list+omit_endlist+discont_start",
    "-hls_segment_type", "mpegts",
    "-start_number", "0",
    "-f", "hls",
    os.path.join(OUTPUT_DIR, HLS_FILE)
]

class StreamWatchdog:
    def __init__(self):
        self.process = None
        self.running = True
        self.last_restart = 0
    
    def start_ffmpeg(self):
        if self.process and self.process.poll() is None:
            # Process is still running
            print("FFmpeg process already running")
            return
            
        print(f"Starting FFmpeg: {' '.join(FFMPEG_CMD)}")
        self.process = subprocess.Popen(
            FFMPEG_CMD,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.last_restart = time.time()
    
    def check_stream_health(self):
        m3u8_path = os.path.join(OUTPUT_DIR, HLS_FILE)
        
        # Check if file exists
        if not os.path.exists(m3u8_path):
            print(f"Stream file {m3u8_path} not found!")
            return False
        
        # Check if file is recent
        mtime = os.path.getmtime(m3u8_path)
        age = time.time() - mtime
        if age > MAX_AGE_SECONDS:
            print(f"Stream file is too old ({age:.1f}s)")
            return False
            
        # Check if process is running
        if self.process and self.process.poll() is not None:
            print(f"FFmpeg process exited with code {self.process.returncode}")
            return False
            
        # All checks passed
        return True
    
    def run(self):
        print("Stream watchdog started")
        self.start_ffmpeg()
        
        try:
            while self.running:
                if not self.check_stream_health():
                    # Don't restart too frequently
                    if time.time() - self.last_restart > 5:
                        print("Stream is unhealthy, restarting FFmpeg")
                        if self.process:
                            try:
                                # Try to terminate gracefully first
                                self.process.terminate()
                                time.sleep(1)
                                if self.process.poll() is None:
                                    self.process.kill()
                            except Exception as e:
                                print(f"Error terminating process: {e}")
                        
                        self.start_ffmpeg()
                
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("Shutting down stream watchdog")
            if self.process:
                self.process.terminate()
        
        print("Stream watchdog stopped")

if __name__ == "__main__":
    watchdog = StreamWatchdog()
    watchdog.run()