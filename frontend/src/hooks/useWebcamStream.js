/**
 * useWebcamStream
 *
 * Manages the uploader WebSocket lifecycle:
 *   1. Requests webcam access via getUserMedia.
 *   2. Opens /stream/upload — receives the server-generated session_id
 *      as the very first JSON message (Audit fix #1).
 *   3. Captures frames from a hidden <canvas> at ~10 fps and sends them
 *      as JPEG binary over the WebSocket.
 *   4. Returns refs for the video element, the canvas, and state signals.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

const FPS = 10
const FRAME_INTERVAL_MS = 1000 / FPS
const JPEG_QUALITY = 0.7

export function useWebcamStream() {
  const videoRef    = useRef(null)
  const canvasRef   = useRef(null)
  const wsRef       = useRef(null)
  const timerRef    = useRef(null)

  const [sessionId, setSessionId]   = useState(null)
  const [streaming, setStreaming]   = useState(false)
  const [error, setError]           = useState(null)

  // ------------------------------------------------------------------
  // Frame capture loop
  // ------------------------------------------------------------------
  const startCapture = useCallback((ws) => {
    const video  = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    const ctx = canvas.getContext('2d')

    timerRef.current = setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) return
      canvas.width  = video.videoWidth  || 640
      canvas.height = video.videoHeight || 480
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      canvas.toBlob(
        (blob) => {
          if (blob && ws.readyState === WebSocket.OPEN) {
            blob.arrayBuffer().then((buf) => ws.send(buf))
          }
        },
        'image/jpeg',
        JPEG_QUALITY,
      )
    }, FRAME_INTERVAL_MS)
  }, [])

  // ------------------------------------------------------------------
  // Effect: open webcam + WebSocket
  // ------------------------------------------------------------------
  useEffect(() => {
    let stream = null
    let ws = null

    async function init() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        setError('Camera access denied. Please allow camera permissions.')
        return
      }

      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${protocol}://${window.location.host}/stream/upload`)
      wsRef.current = ws
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => {
        setStreaming(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        // First message from server contains the backend-generated session_id
        try {
          const data = JSON.parse(event.data)
          if (data.session_id) {
            setSessionId(data.session_id)
            startCapture(ws)
          }
        } catch {
          // not JSON — ignore
        }
      }

      ws.onerror = () => {
        setError('WebSocket connection error. Is the backend running?')
      }

      ws.onclose = () => {
        setStreaming(false)
        clearInterval(timerRef.current)
      }
    }

    init()

    return () => {
      clearInterval(timerRef.current)
      if (ws) ws.close()
      if (stream) stream.getTracks().forEach((t) => t.stop())
    }
  }, [startCapture])

  return { videoRef, canvasRef, sessionId, streaming, error }
}
