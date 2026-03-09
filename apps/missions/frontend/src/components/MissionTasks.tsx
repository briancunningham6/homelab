import { useState, useRef } from 'react'
import { useTasks, useCreateTask, useUpdateTask, useDeleteTask, useReorderTasks } from '../hooks/useMissions'
import type { MissionTask, TaskStatus } from '../types'
import '../styles/MissionTasks.css'

interface Props {
  missionId: string
}

const STATUS_LABELS: Record<TaskStatus, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  done: 'Done',
}

const NEXT_STATUS: Record<TaskStatus, TaskStatus> = {
  open: 'in_progress',
  in_progress: 'done',
  done: 'open',
}

export const MissionTasks: React.FC<Props> = ({ missionId }) => {
  const { data: tasks = [], isLoading } = useTasks(missionId)
  const createTask = useCreateTask()
  const updateTask = useUpdateTask()
  const deleteTask = useDeleteTask()
  const reorderTasks = useReorderTasks()

  const [newTitle, setNewTitle] = useState('')
  const [newDueDate, setNewDueDate] = useState('')
  const [adding, setAdding] = useState(false)

  // Drag state
  const dragItem = useRef<number | null>(null)
  const dragOver = useRef<number | null>(null)

  const activeTasks = tasks.filter((t) => t.status !== 'done')
  const doneTasks = tasks.filter((t) => t.status === 'done')

  const handleAdd = async () => {
    if (!newTitle.trim()) return
    await createTask.mutateAsync({
      missionId,
      data: { title: newTitle.trim(), due_date: newDueDate || undefined },
    })
    setNewTitle('')
    setNewDueDate('')
    setAdding(false)
  }

  const handleStatusCycle = async (task: MissionTask) => {
    await updateTask.mutateAsync({
      missionId,
      taskId: task.id,
      data: { status: NEXT_STATUS[task.status] },
    })
  }

  const handleDelete = async (taskId: string) => {
    await deleteTask.mutateAsync({ missionId, taskId })
  }

  // Drag handlers (only for active tasks)
  const handleDragStart = (index: number) => {
    dragItem.current = index
  }

  const handleDragEnter = (index: number) => {
    dragOver.current = index
  }

  const handleDragEnd = async () => {
    if (dragItem.current === null || dragOver.current === null) return
    if (dragItem.current === dragOver.current) {
      dragItem.current = null
      dragOver.current = null
      return
    }

    const reordered = [...activeTasks]
    const [moved] = reordered.splice(dragItem.current, 1)
    reordered.splice(dragOver.current, 0, moved)

    dragItem.current = null
    dragOver.current = null

    await reorderTasks.mutateAsync({
      missionId,
      items: reordered.map((t, i) => ({ id: t.id, sort_order: i + 1 })),
    })
  }

  if (isLoading) {
    return <div className="tasks-loading">Loading tasks…</div>
  }

  return (
    <div className="mission-tasks">
      {/* Add task form */}
      {adding ? (
        <div className="task-add-form">
          <input
            className="task-add-input"
            type="text"
            placeholder="Task description…"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            autoFocus
          />
          <input
            className="task-add-date"
            type="date"
            value={newDueDate}
            onChange={(e) => setNewDueDate(e.target.value)}
            title="Due date (optional)"
          />
          <button className="task-btn-primary" onClick={handleAdd} disabled={createTask.isPending || !newTitle.trim()}>
            Add
          </button>
          <button className="task-btn-ghost" onClick={() => { setAdding(false); setNewTitle(''); setNewDueDate('') }}>
            Cancel
          </button>
        </div>
      ) : (
        <button className="task-add-trigger" onClick={() => setAdding(true)}>
          + Add task
        </button>
      )}

      {/* Active tasks */}
      {activeTasks.length > 0 && (
        <div className="task-section">
          <ul className="task-list">
            {activeTasks.map((task, index) => (
              <li
                key={task.id}
                className={`task-item task-item--${task.status}`}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragEnter={() => handleDragEnter(index)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => e.preventDefault()}
              >
                <span className="task-drag-handle" title="Drag to reorder">⠿</span>
                <button
                  className={`task-status-pill task-status--${task.status}`}
                  onClick={() => handleStatusCycle(task)}
                  title="Click to advance status"
                >
                  {STATUS_LABELS[task.status]}
                </button>
                <span className="task-title">{task.title}</span>
                {task.due_date && (
                  <span className={`task-due ${isDueOrPast(task.due_date) ? 'task-due--overdue' : ''}`}>
                    {formatDate(task.due_date)}
                  </span>
                )}
                <button
                  className="task-delete"
                  onClick={() => handleDelete(task.id)}
                  title="Delete task"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Done tasks */}
      {doneTasks.length > 0 && (
        <div className="task-section task-section--done">
          <h4 className="task-section-label">Done ({doneTasks.length})</h4>
          <ul className="task-list">
            {doneTasks.map((task) => (
              <li key={task.id} className="task-item task-item--done">
                <span className="task-drag-handle task-drag-handle--hidden">⠿</span>
                <button
                  className="task-status-pill task-status--done"
                  onClick={() => handleStatusCycle(task)}
                  title="Click to reopen"
                >
                  Done
                </button>
                <span className="task-title task-title--done">{task.title}</span>
                {task.completed_at && (
                  <span className="task-due task-due--completed">
                    {formatDate(task.completed_at.split('T')[0])}
                  </span>
                )}
                <button
                  className="task-delete"
                  onClick={() => handleDelete(task.id)}
                  title="Delete task"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tasks.length === 0 && !adding && (
        <p className="tasks-empty">No tasks yet. Add one to track work for this mission.</p>
      )}
    </div>
  )
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: new Date().getFullYear() !== year ? 'numeric' : undefined,
  })
}

function isDueOrPast(dateStr: string): boolean {
  const [year, month, day] = dateStr.split('-').map(Number)
  const due = new Date(year, month - 1, day)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return due <= today
}
