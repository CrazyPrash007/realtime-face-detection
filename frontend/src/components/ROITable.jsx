/**
 * ROITable
 *
 * Polls GET /api/v1/roi?session_id=<id>&limit=50 every 2 seconds and
 * renders a table of the latest bounding-box detection events.
 *
 * Audit fix #4 — Memory leak prevention:
 *   - The polling interval is cleared in the useEffect cleanup function,
 *     so it stops when the component unmounts or session_id changes.
 */

import { useEffect, useState, useCallback } from 'react'

const POLL_INTERVAL_MS = 2000
const LIMIT = 50

export default function ROITable({ sessionId }) {
  const [events, setEvents]   = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(false)
  const [lastFetch, setLastFetch] = useState(null)

  const fetchROI = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const url = `/api/v1/roi?session_id=${encodeURIComponent(sessionId)}&limit=${LIMIT}`
      const res  = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setEvents(data.items ?? [])
      setTotal(data.total ?? 0)
      setLastFetch(new Date())
    } catch (err) {
      console.error('ROI fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  // Audit fix #4: clear interval on unmount / sessionId change
  useEffect(() => {
    fetchROI()
    const id = setInterval(fetchROI, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [fetchROI])

  const fmt = (dt) =>
    new Date(dt).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 1,
    })

  return (
    <div className="roi-section" id="roi-section">
      <div className="roi-header">
        <p className="section-title">Detection History</p>
        <span className="roi-count">
          <strong>{total}</strong> total events
          {lastFetch && (
            <> · updated {fmt(lastFetch)}</>
          )}
        </span>
      </div>

      <div className="table-wrapper">
        <table id="roi-table" aria-label="ROI detection events">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>X</th>
              <th>Y</th>
              <th>Width</th>
              <th>Height</th>
              <th>Session</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state">
                    <span className="empty-icon">📭</span>
                    <p>
                      {sessionId
                        ? loading
                          ? 'Loading…'
                          : 'No detections yet. Show your face to the camera!'
                        : 'Start streaming to see detections here.'}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              events.map((ev) => (
                <tr key={ev.id} id={`roi-row-${ev.id}`}>
                  <td>{fmt(ev.timestamp)}</td>
                  <td><span className="coord">{ev.x}</span></td>
                  <td><span className="coord">{ev.y}</span></td>
                  <td><span className="coord">{ev.width}</span></td>
                  <td><span className="coord">{ev.height}</span></td>
                  <td title={ev.session_id}>
                    {ev.session_id.slice(0, 8)}…
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
