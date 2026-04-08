import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export const generateDocument = (prompt, sessionId, outputFormat) =>
  api.post('/generate', { prompt, session_id: sessionId, output_format: outputFormat }).then(r => r.data)

export const getJobStatus = (jobId) =>
  api.get(`/status/${jobId}`).then(r => r.data)

export const listJobs = () =>
  api.get('/jobs').then(r => r.data)

export const submitCorrection = (original, corrected, sessionId) =>
  api.post('/submit-correction', { original, corrected, session_id: sessionId }).then(r => r.data)

export const listOutputs = () =>
  api.get('/outputs').then(r => r.data)

export const getDownloadUrl = (filename) => `/api/v1/outputs/download/${filename}`

export const listSkills = () =>
  api.get('/skills').then(r => r.data)

export const getKnowledge = () =>
  api.get('/knowledge').then(r => r.data)

export const updateKnowledge = (file, content) =>
  api.post('/knowledge', { file, content }).then(r => r.data)

export const getAnalytics = () =>
  api.get('/analytics').then(r => r.data)

export default api
