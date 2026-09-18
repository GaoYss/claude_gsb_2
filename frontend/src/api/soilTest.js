import { createResourceApi } from './client'
import http from './client'

const soilTestBase = createResourceApi('soil-tests')

export const soilTestApi = {
  ...soilTestBase,
  summary: (params) => http.get('/soil-tests/summary', { params }),
  comparison: (greenSpaceId) =>
    http.get('/soil-tests/comparison', { params: { green_space_id: greenSpaceId } }),
  regeneratePlan: (id) => http.post(`/soil-tests/${id}/regenerate-plan`),
}

const fertilizationBase = createResourceApi('fertilizations')

export const fertilizationApi = {
  ...fertilizationBase,
  summary: (params) => http.get('/fertilizations/summary', { params }),
}
