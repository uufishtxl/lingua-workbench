# New Feature Proposals for Reader Module

This document captures brain-dumped ideas, UX enhancements, and structural features proposed for the Lingua Workbench Article Reader module.

## 1. Native Audio/TTS Support (Substack Audio Hijacking)
**Problem**: Substack articles often come with incredibly high-quality native AI voice/author readings, but users cannot listen to them synchronously while using our immersive ReaderView layout. Directly embedding the page via `<iframe>` is often blocked by `X-Frame-Options` headers and ruins the minimal reading experience.
**Proposal**:
- **Chrome Extension Update**: Modify `content.js` to scan the DOM for embedded `<audio>` tags or known Substack audio source patterns when grabbing the article text.
- **Backend update**: Add an `audio_url` field to the `Article` model.
- **Frontend update**: Embed a custom, minimalistic HTML5 `<audio controls>` player at the top of the ReaderView if `audio_url` exists.
- **Result**: Native Substack podcast listening experience overlaid on top of our isolated, translatable, AI-annotated text environment.

## 2. Gamification & Automation Dashboard (The "OpenClaw" Alternative)
**Problem**: The user currently has to manually initiate daily reviews via prompts. Review progress is visible, but there's no granular log or sense of a "daily learning session" bound by time.
**Proposal**:
- **Daily Heads-up Dashboard**: Create a central Vue dashboard that auto-calculates mature SRS boxes and presents a massive "Start Today's Review (N cards due)" button.
- **Review History Heatmap (ReviewLog)**: Create a lightweight `ReviewLog` table to record every annotation review (`timestamp, card_id, result`). Visualize this as a GitHub-style green contribution graph.
- **Integrated Pomodoro Engine**: Add an invisible or top-bar Pomodoro timer (25 mins). Tie completed Pomodoros to the `ReviewLog` or user stats, explicitly linking "Time Invested" with "Cards Processed / Articles Read".

## 3. Pronunciation & Phonetics for Annotations
**Problem**: Reading Jargon (Yellow marks) provides definitions, but the user often does not know how to pronounce the newly discovered word.
**Proposal**:
- **UI Action**: Add a new sub-action to the existing Yellow highlight. When selected, not only does it highlight yellow, but it affixes a small yellow 🔈 (speaker) icon next to the word.
- **AI Modification**: Update the backend AI prompt for Jargon. Instruct the LLM to *always* prepend the American English phonetic spelling (Merriam-Webster style, e.g., *\ˈjar-gən\*) at the very top of the response.
- **Bonus (Audio)**: Integrate a lightweight Web Speech API (or Edge TTS via backend) call into the frontend. Pressing the yellow speaker icon triggers a quick native browser TTS reading of the specific highlighted phrase to enforce auditory memory alongside visual reading.
