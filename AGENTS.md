# Flow Kit — Codex CLI Instructions

Base URL: `http://127.0.0.1:8100`

## Pre-flight

Before ANY workflow:
```bash
curl -s http://127.0.0.1:8100/health
# Must return: {"extension_connected": true}
```

## Pipeline Order

```
0. Research          /fk-research "topic" (fact-check via web search, save to .omc/research/)
1. Health check      GET  /health → extension_connected: true
2. Create project    POST /api/projects (with entities + material, story from research)
3. Create video      POST /api/videos
4. Create scenes     POST /api/scenes (with character_names, chain_type)
5. Gen ref images    POST /api/requests/batch → poll /batch-status?project_id=<PID>
                     Wait for done=true, verify all entities have media_id
6. Gen scene images  POST /api/requests/batch → poll /batch-status?video_id=<VID>
                     Wait for done=true, verify image_media_id = UUID
7. Gen videos        POST /api/requests/batch → poll /batch-status?video_id=<VID>
                     Wait for done=true (videos take 2-5 min each)
7.5 Review videos    POST /api/videos/{vid}/review?mode=light (AI vision quality check)
                     Pass: score >= 7.5 | Fail: update video_prompt → regen → re-review (max 2 cycles)
8. (Optional) 4K     POST /api/requests/batch (TIER_TWO only)
9. (Optional) TTS    Create voice template → POST /api/videos/{vid}/narrate
10. Concat           ffmpeg normalize + concat
```

## Batch API

Submit N requests at once (server throttles automatically — max 5 concurrent, 10s cooldown):

```bash
curl -X POST http://127.0.0.1:8100/api/requests/batch \
  -H "Content-Type: application/json" \
  -d '{"requests": [{"type": "...", "scene_id": "...", "project_id": "...", "video_id": "...", "orientation": "VERTICAL"}, ...]}'
```

Poll aggregate status:

```bash
curl -s "http://127.0.0.1:8100/api/requests/batch-status?video_id=<VID>&type=GENERATE_IMAGE"
# Returns: {"total": 40, "pending": 30, "processing": 5, "completed": 5, "failed": 0, "done": false}
# When "done": true → all requests have left the queue (completed or failed)
# When "all_succeeded": true → every request completed successfully
```

For full API reference, workflow recipes, and video prompt guidelines, see `CLAUDE.md`.

## Skills

This project has reusable skills in `skills/`. When the user says `/fk-<name>`, read `skills/fk-<name>.md` and follow the instructions inside.

| Skill | Purpose |
|-------|---------|
| `/fk-add-material` | fk-add-material — Image Material System |
| `/fk-brand-logo` | fk-brand-logo — Apply Channel Branding (Intro + Outro + Logo + 4K Badge) |
| `/fk-camera-guide` | Camera Guide — Cinematic Video Prompts (Veo 3) |
| `/fk-change-model` | fk-change-model — View & Change Video/Image Model Keys |
| `/fk-change-provider` | fk-change-provider — View & Switch the AI CLI for a Role |
| `/fk-concat-fit-narrator` | Trim each scene video to fit its TTS narrator duration, burn text overlays, then concatenate into a final video. |
| `/fk-concat` | Download and concatenate all scene videos into a single video with optional TTS narration. |
| `/fk-create-project` | Create a new Google Flow video project. Ask the user for: |
| `/fk-creative-mix` | Creative video mixing — combine techniques for cinematic results. |
| `/fk-dashboard` | Show live GLA status in Claude Code statusline. |
| `/fk-doctor` | Diagnose any FlowKit error and prescribe a fix. Knows the full error taxonomy across Google Flow, the Chrome extension, the FastAPI layer, the worker, and the YouTube upload pipeline. |
| `/fk-fix-uuids` | Find and fix any non-UUID media_ids (CAMS... format) across all scenes and entities. |
| `/fk-gen-chain-videos` | Generate videos with automatic scene chaining (start+end frame transitions). |
| `/fk-gen-images` | Generate scene images for all scenes in a video. |
| `/fk-gen-music` | fk-gen-music — Generate Music via Suno |
| `/fk-gen-narrator` | fk-gen-narrator — Generate Narrator Text + TTS for All Scenes |
| `/fk-gen-refs` | Generate reference images for all entities in a project. |
| `/fk-gen-text-overlays` | fk-gen-text-overlays — Generate Text Overlays from Narrator Text |
| `/fk-gen-tts-template` | fk-gen-tts-template — Generate Voice Template |
| `/fk-gen-videos` | Generate videos for all scenes in a video. |
| `/fk-import-voice` | fk-import-voice — Import Existing Voice as Template |
| `/fk-insert-scene` | Insert new scene(s) into an existing video chain — for multi-angle shots, cutaways, or close-ups. |
| `/fk-monitor` | fk-monitor — Full Pipeline Monitor |
| `/fk-pipeline` | fk-pipeline — Smart Full-Pipeline Orchestrator |
| `/fk-refresh-urls` | Re-sign expired media URLs for all scenes in a video (images, videos, upscale videos) and character reference images. |
| `/fk-research` | fk-research — Fact-Check & Research Before Scripting |
| `/fk-review-board` | Start the Scene Review Board web app for visual feedback on scene chains. |
| `/fk-review-video` | Review AI-generated scene videos for quality using Claude Vision. |
| `/fk-status` | Show full status dashboard for a project. |
| `/fk-switch-project` | fk-switch-project — Switch Active Project |
| `/fk-thumbnail-guide` | YouTube Thumbnail Guide — Hook-Worthy Design Rules |
| `/fk-thumbnail` | Generate 4 YouTube-optimized thumbnail variants for a project video. |
| `/fk-upload-image` | Upload a local image file to Google Flow and get a media_id (UUID). |
| `/fk-youtube-seo` | fk-youtube-seo — Generate YouTube Metadata (SEO-Optimized) |
| `/fk-youtube-upload` | fk-youtube-upload — Upload Video to YouTube (Shorts + Long-form) |
