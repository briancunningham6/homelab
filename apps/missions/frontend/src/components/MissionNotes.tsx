import { useState, useEffect, useRef } from 'react'
import { marked } from 'marked'
import { useUpdateMission } from '../hooks/useMissions'
import '../styles/MissionNotes.css'

interface Props {
  missionId: string
  initialNotes: string | undefined
}

type Mode = 'edit' | 'preview'

const AUTOSAVE_DELAY = 1500

export const MissionNotes: React.FC<Props> = ({ missionId, initialNotes }) => {
  const [content, setContent] = useState(initialNotes ?? '')
  const [mode, setMode] = useState<Mode>('edit')
  const [saveState, setSaveState] = useState<'saved' | 'saving' | 'unsaved'>('saved')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const updateMission = useUpdateMission()

  // Sync if parent reloads the mission
  useEffect(() => {
    setContent(initialNotes ?? '')
  }, [initialNotes])

  const save = async (text: string) => {
    setSaveState('saving')
    try {
      await updateMission.mutateAsync({ id: missionId, data: { notes: text } })
      setSaveState('saved')
    } catch {
      setSaveState('unsaved')
    }
  }

  const handleChange = (value: string) => {
    setContent(value)
    setSaveState('unsaved')
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => save(value), AUTOSAVE_DELAY)
  }

  // Flush on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const previewHtml = marked.parse(content || '_No notes yet._') as string

  const saveIndicator =
    saveState === 'saving' ? 'Saving…'
    : saveState === 'unsaved' ? 'Unsaved'
    : 'Saved'

  const saveIndicatorClass =
    saveState === 'saving' ? 'notes-save-state saving'
    : saveState === 'unsaved' ? 'notes-save-state unsaved'
    : 'notes-save-state saved'

  return (
    <div className="mission-notes">
      <div className="notes-toolbar">
        <div className="notes-tabs">
          <button
            className={`notes-tab ${mode === 'edit' ? 'active' : ''}`}
            onClick={() => setMode('edit')}
          >
            Edit
          </button>
          <button
            className={`notes-tab ${mode === 'preview' ? 'active' : ''}`}
            onClick={() => setMode('preview')}
          >
            Preview
          </button>
        </div>
        <span className={saveIndicatorClass}>{saveIndicator}</span>
      </div>

      {mode === 'edit' ? (
        <textarea
          className="notes-editor"
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={`Add notes in Markdown…\n\n# Heading\n**bold**, *italic*, \`code\`\n- list item`}
          spellCheck
        />
      ) : (
        <div
          className="notes-preview"
          dangerouslySetInnerHTML={{ __html: previewHtml }}
        />
      )}

      <p className="notes-hint">
        Notes are included in the agent's context every time you chat. Use them to record
        standing instructions, preferences, or background the agent should always know.
      </p>
    </div>
  )
}
