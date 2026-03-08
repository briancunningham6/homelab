import { useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMissions } from '../api/client'
import '../styles/QuickCapture.css'

interface CaptureResult {
  mission_id: string
  mission_name: string
  file_count: number
  message_id: string
}

function fileIcon(mime: string) {
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.startsWith('video/')) return '🎬'
  if (mime === 'application/pdf') return '📄'
  return '📎'
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}

export const QuickCapture: React.FC = () => {
  const [missionId, setMissionId] = useState('')
  const [note, setNote] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result, setResult] = useState<CaptureResult | null>(null)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: missions } = useQuery({ queryKey: ['missions'], queryFn: getMissions })
  const activeMissions = (missions ?? []).filter((m) => m.status === 'active')

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name + f.size))
      return [...prev, ...Array.from(incoming).filter((f) => !existing.has(f.name + f.size))]
    })
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      addFiles(e.dataTransfer.files)
    },
    [addFiles],
  )

  const handleSubmit = async () => {
    if (!missionId) { setError('Select a mission first.'); return }
    if (!note.trim() && files.length === 0) { setError('Add a note or at least one file.'); return }

    setIsSubmitting(true)
    setError('')

    try {
      const form = new FormData()
      form.append('mission_id', missionId)
      form.append('note', note)
      files.forEach((f) => form.append('files', f))

      const res = await fetch('/api/capture', { method: 'POST', body: form })
      if (!res.ok) {
        const body = await res.json()
        throw new Error(body.detail ?? 'Capture failed')
      }
      setResult(await res.json())
    } catch (e: any) {
      setError(e.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const reset = () => {
    setResult(null)
    setNote('')
    setFiles([])
    setMissionId('')
    setError('')
  }

  // ── Success state ────────────────────────────────────────────────────────
  if (result) {
    return (
      <div className="capture-success">
        <div className="capture-success-icon">✓</div>
        <h2>Sent to "{result.mission_name}"</h2>
        <p>
          {result.file_count > 0
            ? `${result.file_count} file${result.file_count !== 1 ? 's' : ''} analysed and added to context.`
            : 'Note added to mission context.'}
        </p>
        <p className="capture-success-hint">
          Your agent will use this context the next time you chat.
        </p>
        <div className="capture-success-actions">
          <Link to={`/missions/${result.mission_id}`} className="btn-primary">
            Open Mission →
          </Link>
          <button onClick={reset} className="btn-secondary">
            Capture More
          </button>
        </div>
      </div>
    )
  }

  // ── Main form ────────────────────────────────────────────────────────────
  return (
    <div className="capture-page">
      <div className="capture-header">
        <h1>Quick Capture</h1>
        <p>Drop a photo, file, or note into a mission so your agent has more context to work with.</p>
      </div>

      <div className="capture-form">
        {/* Mission selector */}
        <div className="capture-field">
          <label className="capture-label">Mission</label>
          <select
            className="capture-select"
            value={missionId}
            onChange={(e) => setMissionId(e.target.value)}
          >
            <option value="">Select a mission…</option>
            {activeMissions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* Drop zone */}
        <div className="capture-field">
          <label className="capture-label">
            Files <span className="capture-label-hint">photos, videos, PDFs, documents</span>
          </label>
          <div
            className={`capture-dropzone ${isDragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,video/*,.pdf,.doc,.docx,.txt,.csv,.xlsx"
              style={{ display: 'none' }}
              onChange={(e) => addFiles(e.target.files)}
            />
            <span className="capture-dropzone-icon">📁</span>
            <p>Drop files here or <span className="capture-dropzone-link">browse</span></p>
            <p className="capture-dropzone-hint">Images are automatically analysed</p>
          </div>

          {files.length > 0 && (
            <ul className="capture-file-list">
              {files.map((f, i) => (
                <li key={i} className="capture-file-item">
                  <span className="capture-file-icon">{fileIcon(f.type)}</span>
                  <span className="capture-file-name">{f.name}</span>
                  <span className="capture-file-size">{formatSize(f.size)}</span>
                  <button
                    className="capture-file-remove"
                    onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                    title="Remove"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Note */}
        <div className="capture-field">
          <label className="capture-label">
            Note <span className="capture-label-hint">optional — what should your agent know?</span>
          </label>
          <textarea
            className="capture-textarea"
            rows={4}
            placeholder={`e.g. "This is the dentist receipt from March — log it against the health budget mission"`}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </div>

        {error && <div className="capture-error">{error}</div>}

        <button
          className="capture-submit"
          onClick={handleSubmit}
          disabled={isSubmitting || !missionId}
        >
          {isSubmitting ? 'Sending…' : 'Send to Mission'}
        </button>
      </div>
    </div>
  )
}
