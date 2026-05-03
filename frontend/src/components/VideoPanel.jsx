/**
 * VideoPanel
 *
 * Renders two side-by-side panels:
 *   Left  — Live webcam feed (raw, via <video> element).
 *   Right — Processed stream with bounding boxes (via <img> updated each frame).
 *
 * A hidden <canvas> sits alongside the video; useWebcamStream draws into it
 * to capture JPEG frames for upload.
 */

import React from 'react'
import { useWebcamStream } from '../hooks/useWebcamStream'
import { useViewerStream } from '../hooks/useViewerStream'

export default function VideoPanel({ onSessionId }) {
  const { videoRef, canvasRef, sessionId, streaming, error } =
    useWebcamStream()

  const { frameUrl, connected } = useViewerStream(sessionId)

  // Propagate sessionId up to App so the ROI table can filter by it
  React.useEffect(() => {
    if (sessionId) onSessionId(sessionId)
  }, [sessionId, onSessionId])

  return (
    <>
      {error && (
        <div
          id="error-banner"
          role="alert"
          style={{
            background: 'rgba(255,79,106,0.1)',
            border: '1px solid rgba(255,79,106,0.3)',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            color: '#ff4f6a',
            fontSize: '0.85rem',
          }}
        >
          ⚠ {error}
        </div>
      )}

      <div className="video-grid">
        {/* ---- Left: Webcam feed ---- */}
        <div className="video-panel" id="webcam-panel">
          <div className="panel-header">
            <div className="panel-label">
              <span className="icon">📷</span>
              Webcam Feed
            </div>
            <span className={`panel-badge ${streaming ? 'live' : ''}`}>
              {streaming ? '● LIVE' : 'OFFLINE'}
            </span>
          </div>

          <div className="video-wrapper">
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video
              id="webcam-video"
              ref={videoRef}
              className="video-el"
              autoPlay
              playsInline
              muted
            />
            {/* Hidden canvas used by the capture hook */}
            <canvas ref={canvasRef} />

            {!streaming && (
              <div className="video-overlay">
                <span className="overlay-icon">🎥</span>
                <p>Requesting camera access…</p>
              </div>
            )}
          </div>

          <div className="session-bar">
            session:&nbsp;
            <span id="session-id-display">
              {sessionId ?? 'awaiting backend…'}
            </span>
          </div>
        </div>

        {/* ---- Right: Processed stream ---- */}
        <div className="video-panel" id="processed-panel">
          <div className="panel-header">
            <div className="panel-label">
              <span className="icon">🤖</span>
              Processed Stream
            </div>
            <span className={`panel-badge ${connected ? 'live' : ''}`}>
              {connected ? '● LIVE' : 'WAITING'}
            </span>
          </div>

          <div className="video-wrapper">
            {frameUrl ? (
              <img
                id="processed-img"
                className="processed-img"
                src={frameUrl}
                alt="Processed video frame with face bounding boxes"
              />
            ) : (
              <div className="video-overlay">
                {sessionId ? (
                  <>
                    <div className="spinner" />
                    <p>Waiting for first frame…</p>
                  </>
                ) : (
                  <>
                    <span className="overlay-icon">⏳</span>
                    <p>Waiting for session…</p>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="session-bar">
            viewer:&nbsp;
            <span>{connected ? 'connected' : 'disconnected'}</span>
          </div>
        </div>
      </div>
    </>
  )
}
