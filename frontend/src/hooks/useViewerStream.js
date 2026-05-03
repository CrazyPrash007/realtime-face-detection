/**
 * useViewerStream
 *
 * Manages the viewer WebSocket lifecycle:
 *   1. Waits until sessionId is available (provided by useWebcamStream).
 *   2. Opens /stream/view?session_id=<id> and receives processed JPEG frames
 *      as binary WebSocket messages.
 *   3. Converts each binary frame to a Blob URL for the <img> element.
 *
 * Audit fix #4 — Memory leak prevention:
 *   - Each incoming frame replaces the previous Blob URL.
 *   - The old URL is revoked before creating the new one to free memory.
 *   - On unmount, the WebSocket is closed and any pending URL is revoked.
 */

import { useEffect, useRef, useState } from 'react'

export function useViewerStream(sessionId) {
  const [frameUrl, setFrameUrl] = useState(null)
  const [connected, setConnected] = useState(false)
  const prevUrlRef = useRef(null)   // tracks last blob URL for revocation
  const wsRef      = useRef(null)

  useEffect(() => {
    // Don't open until the uploader has received a session_id from the server
    if (!sessionId) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(
      `${protocol}://${window.location.host}/stream/view?session_id=${sessionId}`,
    )
    wsRef.current = ws
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => setConnected(true)

    ws.onmessage = (event) => {
      // Audit fix #4: revoke the previous blob URL before creating a new one
      if (prevUrlRef.current) {
        URL.revokeObjectURL(prevUrlRef.current)
      }

      const blob = new Blob([event.data], { type: 'image/jpeg' })
      const url  = URL.createObjectURL(blob)
      prevUrlRef.current = url
      setFrameUrl(url)
    }

    ws.onclose = () => {
      setConnected(false)
    }

    return () => {
      ws.close()
      // Revoke any remaining blob URL on unmount
      if (prevUrlRef.current) {
        URL.revokeObjectURL(prevUrlRef.current)
        prevUrlRef.current = null
      }
    }
  }, [sessionId])

  return { frameUrl, connected }
}
