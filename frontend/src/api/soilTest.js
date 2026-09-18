import { createResourceApi } from './client'
import http from './client'

export const soilTestApi = {
  ...createResourceApi('soil-tests'),
  summary: (params) => http.get('/soil-tests/summary', { params }),
  comparison: (greenSpaceId) =>
    http.get('/soil-tests/comparison', { params: { green_space_id: greenSpaceId } }),
  formulaOptions: (greenSpaceId) =>
    http.get('/soil-tests/formula-options', { params: { green_space_id: greenSpaceId } }),
}

export const fertilizationApi = {
  ...createResourceApi('fertilizations'),
  summary: (params) => http.get('/fertilizations/summary', { params }),
}
