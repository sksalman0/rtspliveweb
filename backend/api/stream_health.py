from flask import Blueprint, jsonify
import os
import time
from pathlib import Path

# Create a blueprint for stream health endpoints
stream_health_bp = Blueprint('stream_health', __name__)

@stream_health_bp.route('/health', methods=['GET'])
def check_stream_health():
    """Check the health of the HLS stream with RTSP-specific optimizations"""
    
    # Path to the m3u8 and ts files
    m3u8_path = Path('../frontend/public/stream.m3u8')
    
    # Add timestamp for tracking latency
    server_time = time.time()
    
    # Check if the m3u8 file exists
    if not m3u8_path.exists():
        return jsonify({
            'status': 'error',
            'message': 'Stream file not found',
            'code': 404,
            'server_time': server_time
        }), 404
    
    # Check if the m3u8 file is recent (updated in the last 5 seconds - stricter for RTSP streams)
    m3u8_modified = m3u8_path.stat().st_mtime
    if time.time() - m3u8_modified > 5:  # Stricter timing for RTSP
        return jsonify({
            'status': 'warning',
            'message': f'Stream manifest not updated recently (last update: {int(time.time() - m3u8_modified)}s ago)',
            'code': 200
        })
    
    # Read the m3u8 file to check its content
    try:
        with open(m3u8_path, 'r') as f:
            content = f.read()
            
        # Check if there are segments listed
        segment_count = content.count('.ts')
        if segment_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'No segments found in playlist',
                'code': 200
            })
            
        # Get the current segments
        segments = [line.strip() for line in content.split('\n') if line.strip().endswith('.ts')]
        
        # Check if the segments exist
        missing_segments = []
        for segment in segments:
            segment_path = Path(f'../frontend/public/{segment}')
            if not segment_path.exists():
                missing_segments.append(segment)
        
        if missing_segments:
            return jsonify({
                'status': 'warning',
                'message': f'Missing {len(missing_segments)} segments',
                'missing': missing_segments,
                'code': 200
            })
        
        # All checks passed
        return jsonify({
            'status': 'healthy',
            'message': 'Stream is healthy',
            'segments': segment_count,
            'last_updated': int(time.time() - m3u8_modified),
            'server_time': time.time(),
            'segment_info': [{
                'name': s,
                'age': int(time.time() - Path(f'../frontend/public/{s}').stat().st_mtime) if Path(f'../frontend/public/{s}').exists() else -1
            } for s in segments[:3]],  # Include age info for newest 3 segments
            'code': 200
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking stream: {str(e)}',
            'code': 500
        }), 500