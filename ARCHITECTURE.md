# Phase 1: The Architectural Blueprint (Design System & DB)

## Frontend (HTML/Vanilla JS + Tailwind)
- **UI & Filters:** A clean, dark-themed dashboard. Top section contains the primary search input (keyword/query) and a mandatory platform toggle (YouTube vs. TikTok). A secondary filter bar allows sorting by "Most Views", "Most Likes", "Last 24h", "Last 30 days", and optionally "Specific Channels".
- **Video Preview & Hover State:** Each result is rendered as a card with a thumbnail. We attach `onmouseenter` and `onmouseleave` event listeners. On hover, the thumbnail is replaced by a silent, auto-playing YouTube iframe starting at `T - 0.5s` and lasting up to 10s (controlled via JS timeouts or YouTube Player API).
- **Clipping Controller (Slider UI):** Below the preview, two `input type="range"` elements control the exact start and end offset of the clip. JavaScript strictly enforces that `end_value - start_value <= 20s`. If the user drags a slider beyond this limit, the other slider adjusts automatically to maintain the 20s maximum range.
- **State Management (Download):** Each card has a selection checkbox. A global `selectedVideos` array tracks the selected clips and their respective slider timestamps. A floating/sticky "Download Clips" button remains `disabled` until `selectedVideos.length >= 1`, at which point it becomes active with a prominent CSS change.

## Backend (Python / FastAPI)
- **Scraper Orchestration:** A unified `MinerService` orchestrating `yt-dlp` for YouTube searches. We pass specific `yt-dlp` parameters (`--dateafter`, `--match-filter`) to implement the requested filters (Last 24h, Last 30 days, etc.). TikTok is mocked for v1.0.
- **Stream Slicing (Chunking):** To save bandwidth and CPU, we never download full videos. We utilize `yt-dlp`'s `--download-sections` feature (`*start-end`) which uses `ffmpeg` under the hood to stream and download exclusively the requested 20s chunk directly from the source server.
- **Transcription Alignment:** We use `youtube_transcript_api` to fetch the exact timestamps where the keyword is spoken, enabling the UI to center the preview and sliders around that exact moment.

## Database (SQLite / SQLAlchemy)
Structured to store metadata, keywords, and generated clips for future analysis:
- **`videos`:** `id`, `platform`, `external_id`, `url`, `title`, `duration`, `view_count`, `channel_name`, `created_at`.
- **`keyword_timestamps`:** `id`, `video_id` (FK), `keyword`, `start_time`, `end_time`, `context_text`.
- **`downloaded_clips`:** `id`, `video_id` (FK), `start_time`, `end_time`, `file_path`, `created_at`.

---

# Phase 2: Codebase Audit & Gap Analysis

## Current State vs. Ideal Architecture
- **Redundant Integrations:** The current repo contains `apify_service.py`, `scraper.py`, and a heavy `video_prospector_poc.py`. These are tightly coupled to "Kalodata" and "Apify" features which pollute the core Miner module.
- **Database Schema:** `domain.py` has legacy models (`Project`, `VideoAsset`, `Segment`) that don't fit the pure keyword/timestamp mining flow. They reflect an older "business intelligence" POC rather than a video clipper.
- **Search Capabilities:** `search_youtube_videos` in `miner_service.py` currently only performs a basic `ytsearch`. It lacks support for the required filters (Most Views, Most Likes, Last 24h, Last 30 days).
- **Stream Slicing Constraint:** The current chunking logic allows up to 30s. The new requirement strictly demands a 20s hard limit.
- **Language & Naming:** The codebase is heavily mixed with Portuguese comments, function names, and UI elements.

## Action Plan (Gap Resolution)
1. **Tree Shaking:** Delete the Kalodata/Apify POC files.
2. **Schema Redesign:** Replace the models in `domain.py` with the English-first `Video`, `KeywordTimestamp`, and `DownloadedClip` models.
3. **Backend Refactoring:** Upgrade `miner_service.py` to accept filtering parameters. Enforce the 20s download limit. Translate variables to English.
4. **Frontend Overhaul:** Replace `frontend_prototype.html` completely to implement the keyword search, slider constraints, hover previews, and download queue logic.