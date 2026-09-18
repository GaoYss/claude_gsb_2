import http from './client'

export const metaApi = {
  getEnums: () => http.get('/meta/enums'),
  getSoilIndicators: () => http.get('/meta/soil-indicators'),
  health: () => http.get('/meta/health'),
}
