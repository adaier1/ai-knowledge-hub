import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export default api

export const authApi = {
  login: (u: string, p: string) => api.post('/auth/login', { username: u, password: p }).then(r => r.data)
}

export const knowledgeApi = {
  list: (p?: any) => api.get('/knowledge', { params: p }).then(r => r.data),
  get: (id: number) => api.get('/knowledge/' + id).then(r => r.data),
  create: (d: any) => api.post('/knowledge', d).then(r => r.data),
  update: (id: number, d: any) => api.put('/knowledge/' + id, d).then(r => r.data),
  delete: (id: number) => api.delete('/knowledge/' + id).then(r => r.data),
  getChunks: (id: number) => api.get('/knowledge/' + id + '/chunks').then(r => r.data),
  getRelated: (id: number) => api.get('/knowledge/' + id + '/related').then(r => r.data),
  embed: (id: number) => api.post('/knowledge/' + id + '/embed').then(r => r.data),
}

export const searchApi = {
  search: (d: any) => api.post('/search', d).then(r => r.data),
  logs: (p?: any) => api.get('/search/logs', { params: p }).then(r => r.data),
}

export const graphApi = {
  get: (p?: any) => api.get('/graph', { params: p }).then(r => r.data),
  stats: () => api.get('/graph/statistics').then(r => r.data),
  entities: (p?: any) => api.get('/graph/entities', { params: p }).then(r => r.data),
  relations: (p?: any) => api.get('/graph/relations', { params: p }).then(r => r.data),
}

export const collectionApi = {
  list: () => api.get('/collections').then(r => r.data),
  create: (d: any) => api.post('/collections', d).then(r => r.data),
  update: (id: number, d: any) => api.put('/collections/' + id, d).then(r => r.data),
  delete: (id: number) => api.delete('/collections/' + id).then(r => r.data),
}

export const analyticsApi = {
  dashboard: () => api.get('/analytics/dashboard').then(r => r.data),
  trends: (days = 30) => api.get('/analytics/trends', { params: { days } }).then(r => r.data),
  topQueries: (l = 10) => api.get('/analytics/top-queries', { params: { limit: l } }).then(r => r.data),
  topKnowledge: (l = 10) => api.get('/analytics/top-knowledge', { params: { limit: l } }).then(r => r.data),
}

export const databaseApi = {
  files: () => api.get('/database/files').then(r => r.data),
  tables: (dbFile?: string) => api.get('/database/tables', { params: { db_file: dbFile } }).then(r => r.data),
  getTable: (n: string, p?: any) => api.get('/database/tables/' + n, { params: p }).then(r => r.data),
  query: (sql: string, dbFile?: string) => api.post('/database/query', { sql }, { params: { db_file: dbFile } }).then(r => r.data),
  exportDb: (dbFile: string) => api.get('/database/export', { params: { db_file: dbFile }, responseType: 'blob' }),
  importDb: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/database/import', fd).then(r => r.data)
  },
}

export const settingsApi = {
  get: (c: string) => api.get('/settings/' + c).then(r => r.data),
  update: (c: string, k: string, v: any) => api.put('/settings/' + c + '/' + k, { value: v }).then(r => r.data),
  test: (c: string, d: any) => api.post('/settings/' + c + '/test', d).then(r => r.data),
}

export const mcpApi = {
  config: () => api.get('/mcp/config').then(r => r.data),
  keys: () => api.get('/mcp/keys').then(r => r.data),
  createKey: (n: string, r = 'agent') => api.post('/mcp/keys', null, { params: { name: n, role: r } }).then(r => r.data),
  deleteKey: (id: number) => api.delete('/mcp/keys/' + id).then(r => r.data),
}

export const tagApi = {
  list: () => api.get('/tags').then(r => r.data),
  create: (d: any) => api.post('/tags', d).then(r => r.data),
  delete: (id: number) => api.delete('/tags/' + id).then(r => r.data),
}
export const webdavApi = {
  getConfig: () => api.get('/webdav/config').then(r => r.data),
  saveConfig: (d: any) => api.put('/webdav/config', d).then(r => r.data),
  test: (d: any) => api.post('/webdav/test', d).then(r => r.data),
  backup: () => api.post('/webdav/backup').then(r => r.data),
  listBackups: () => api.get('/webdav/backups').then(r => r.data),
  browse: (d: any) => api.post('/webdav/browse', d).then(r => r.data),
  importWebdav: (href: string) => api.post('/webdav/import', { href }).then(r => r.data),
  backupData: () => api.post("/webdav/backup-data").then(r => r.data),
  restoreData: (href: string) => api.post("/webdav/restore-data", { href }).then(r => r.data),
  importLocal: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/webdav/import/local', fd).then(r => r.data)
  },
}
