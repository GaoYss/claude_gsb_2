import { defineStore } from 'pinia'

import { metaApi } from '@/api'

/** 业务字典缓存：后端 /meta/enums 是唯一数据源，前端不重复维护枚举。 */
export const useMetaStore = defineStore('meta', {
  state: () => ({
    enums: {},
    indicators: [],
    loaded: false,
    indicatorsLoaded: false,
    pending: null,
    indicatorsPending: null,
  }),
  getters: {
    options: (state) => (group) => state.enums[group] || [],
  },
  actions: {
    async ensureLoaded() {
      if (this.loaded) return this.enums
      if (!this.pending) {
        this.pending = metaApi
          .getEnums()
          .then((data) => {
            this.enums = data?.enums || {}
            this.loaded = true
            return this.enums
          })
          .finally(() => {
            this.pending = null
          })
      }
      return this.pending
    },
    async ensureIndicators() {
      if (this.indicatorsLoaded) return this.indicators
      if (!this.indicatorsPending) {
        this.indicatorsPending = metaApi
          .getSoilIndicators()
          .then((data) => {
            this.indicators = data?.indicators || []
            this.indicatorsLoaded = true
            return this.indicators
          })
          .finally(() => {
            this.indicatorsPending = null
          })
      }
      return this.indicatorsPending
    },
    label(group, value) {
      if (value === null || value === undefined || value === '') return '-'
      const option = (this.enums[group] || []).find((item) => item.value === value)
      return option ? option.label : value
    },
    /** 按后端下发的分界值对土壤指标做五档评级，与入库口径保持一致。 */
    gradeOf(indicatorKey, value) {
      if (value === null || value === undefined || value === '') return null
      const indicator = this.indicators.find((item) => item.key === indicatorKey)
      if (!indicator) return null
      const number = Number(value)
      if (!Number.isFinite(number)) return null
      const grades = ['very_low', 'low', 'medium', 'high', 'very_high']
      const index = indicator.breakpoints.findIndex((bound) => number < bound)
      return grades[index === -1 ? grades.length - 1 : index]
    },
  },
})
