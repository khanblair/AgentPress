import axios from 'axios'

const api = axios.create({ baseURL: '/api/v1' })

export const generateDocument = (prompt, sessionId, outputFormat) =>
  api.post('/generate', { prompt, session_id: sessionId, output_format: outputFormat }).then(r => r.data)

export const getJobStatus = (jobId) =>
  api.get(`/status/${jobId}`).then(r => r.data)

export const listJobs = () =>
  api.get('/jobs').then(r => r.data)

export const getJobMessages = (jobId) =>
  api.get(`/jobs/${jobId}/messages`).then(r => r.data)

export const getChatMessages = (sinceId = 0) =>
  api.get(`/chat/messages?since_id=${sinceId}`).then(r => r.data)

export const sendChatMessage = (message, sinceId = 0) =>
  api.post('/chat/message', { message, since_id: sinceId }).then(r => r.data)

export const submitCorrection = (original, corrected, sessionId) =>
  api.post('/submit-correction', { original, corrected, session_id: sessionId }).then(r => r.data)

export const listOutputs = () =>
  api.get('/outputs').then(r => r.data)

export const getDownloadUrl = (filename) => `/api/v1/outputs/download/${filename}`

export const previewDocument = (filename) =>
  api.get(`/outputs/preview/${filename}`).then(r => r.data)

export const chatWithDoc = (filename, message, history) =>
  api.post('/outputs/chat', { filename, message, history }).then(r => r.data)

export const listSkills = () =>
  api.get('/skills').then(r => r.data)

export const getKnowledge = () =>
  api.get('/knowledge').then(r => r.data)

export const updateKnowledge = (file, content) =>
  api.post('/knowledge', { file, content }).then(r => r.data)

export const getAnalytics = () =>
  api.get('/analytics').then(r => r.data)

export default api
