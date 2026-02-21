import { useState, useRef } from 'react'
import { useUploadFile, useDeleteFile } from '../hooks/useMissions'
import '../styles/FileUpload.css'

interface FileUploadProps {
  missionId: string
}

export const FileUpload: React.FC<FileUploadProps> = ({ missionId }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const uploadFile = useUploadFile()
  const deleteFile = useDeleteFile()

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    for (const file of files) {
      await handleFileUpload(file)
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    for (const file of files) {
      await handleFileUpload(file)
    }
    // Reset input so the same file can be uploaded again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleFileUpload = async (file: File) => {
    try {
      setUploadProgress(`Uploading ${file.name}...`)
      await uploadFile.mutateAsync({ missionId, file })
      setUploadProgress(null)
    } catch (error) {
      console.error('Upload failed:', error)
      alert(`Failed to upload ${file.name}`)
      setUploadProgress(null)
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="file-upload">
      <div
        className={`upload-area ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          multiple
          style={{ display: 'none' }}
        />

        {uploadProgress ? (
          <div className="upload-progress">
            <div className="spinner small"></div>
            <p>{uploadProgress}</p>
          </div>
        ) : (
          <>
            <div className="upload-icon">📁</div>
            <p className="upload-text">
              <strong>Click to upload</strong> or drag and drop
            </p>
            <p className="upload-hint">
              PDFs, images, text files, and more
            </p>
          </>
        )}
      </div>
    </div>
  )
}
