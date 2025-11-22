# Sample Videos

Please place your test video files in this directory.

## Recommended Video Specs
- Format: MP4 or AVI
- Resolution: 1280x720 (The lane detection perspective transform is tuned for this resolution)
- Content: Road driving footage with visible lane lines.

## How to Run
Once you have a video here (e.g., `test_drive.mp4`), run:

```bash
python main.py --input data/sample_videos/test_drive.mp4 --debug
```
