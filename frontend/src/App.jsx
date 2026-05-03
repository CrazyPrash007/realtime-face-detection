import { useState, useCallback } from 'react'
import VideoPanel from './components/VideoPanel'
import ROITable from './components/ROITable'

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [streaming, setStreaming] = useState(false)

  const handleSessionId = useCallback((id) => {
    setSessionId(id)
    setStreaming(true)
  }, [])

  return (
    <div className="app">
      {/* ---- Header ---- */}
      <header className="header" role="banner">
        <div className="header-logo">
          <div className="logo-icon" aria-hidden="true">👁</div>
          <div className="logo-text">Face<span>Stream</span></div>
        </div>

        <div
          id="stream-status"
          className={`status-pill ${streaming ? 'active' : ''}`}
          aria-live="polite"
          aria-label={streaming ? 'Streaming active' : 'Not streaming'}
        >
          <div className="status-dot" />
          {streaming ? 'Streaming' : 'Not streaming'}
        </div>
      </header>

      {/* ---- Main Content ---- */}
      <main className="main" role="main" id="main-content">
        <h1 className="section-title" style={{ fontSize: '0.75rem' }}>
          Real-Time Face Detection Pipeline
        </h1>

        {/* Stat strip */}
        <div className="info-strip" aria-label="Session statistics">
          <div className="info-card">
            <span className="info-card-label">Status</span>
            <span
              id="stat-status"
              className={`info-card-value ${streaming ? 'green' : ''}`}
            >
              {streaming ? 'Live' : 'Idle'}
            </span>
          </div>
          <div className="info-card">
            <span className="info-card-label">Frame Rate</span>
            <span id="stat-fps" className="info-card-value blue">10 fps</span>
          </div>
          <div className="info-card">
            <span className="info-card-label">Detection</span>
            <span className="info-card-value green">MediaPipe</span>
          </div>
          <div className="info-card">
            <span className="info-card-label">Drawing</span>
            <span className="info-card-value blue">Pillow</span>
          </div>
        </div>

        {/* Video panels */}
        <VideoPanel onSessionId={handleSessionId} />

        {/* ROI history table */}
        <ROITable sessionId={sessionId} />
      </main>

      {/* ---- Footer ---- */}
      <footer
        style={{
          textAlign: 'center',
          padding: '1rem',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
          borderTop: '1px solid var(--border)',
        }}
        role="contentinfo"
      >
        FaceStream · FastAPI + MediaPipe + Pillow + PostgreSQL · No OpenCV
      </footer>
    </div>
  )
}
