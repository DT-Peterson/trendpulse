Drop optional personal source clips into `user_clips/inbox`.

Quick ways to add clips:
- Windows Explorer: `\\wsl$\Ubuntu\home\daniel\.openclaw\skills\video-pipeline\scripts\user_clips\inbox`
- WSL helper: `~/.openclaw/skills/video-pipeline/scripts/add_user_clip.sh /path/to/clip.mp4`

Behavior:
- Option 1: standard generated-background format.
- Option 2: split layout with generated/random background on top, your uploaded clip on bottom, and text in the middle band.
- Automation only considers Option 2 when an unused clip exists in `user_clips/inbox`.
- If no unused clip exists, the run automatically uses Option 1.
- When Option 2 is selected and renders successfully, the chosen clip is moved to `user_clips/used` so it is not reused.
- If Option 2 fails for a clip, the pipeline falls back to Option 1 for that run.

Supported clip formats:
- `.mp4`
- `.mov`
- `.m4v`
- `.webm`