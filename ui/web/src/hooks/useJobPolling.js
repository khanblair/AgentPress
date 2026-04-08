import { useState, useEffect, useRef } from 'react'
import { getJobStatus } from '../api/client'

const TERMINAL = ['completed', 'failed']

export function useJobPolling(jobId, intervalMs = 2000) {
  const [job, setJob] = useState(null)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId)
        setJob(data)
        if (TERMINAL.includes(data.status)) {
          clearInterval(timerRef.current)
        }
      } catch (e) {
        setError(e.message)
        clearInterval(timerRef.current)
      }
    }

    poll()
    timerRef.current = setInterval(poll, intervalMs)
    return () => clearInterval(timerRef.current)
  }, [jobId, intervalMs])

  return { job, error }
}
