<template>
  <div class="reports">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ t('reports.title') }}</h1>
        <p class="page-subtitle">{{ t('reports.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="isEmpty" class="card">
        <div class="empty-state">{{ t('reports.empty') }}</div>
      </div>

      <template v-else>
        <!-- Quarterly Performance -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
          </div>
          <div class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.quarterly.quarter') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalOrders') }}</th>
                  <th class="num">{{ t('reports.quarterly.totalRevenue') }}</th>
                  <th class="num">{{ t('reports.quarterly.avgOrderValue') }}</th>
                  <th class="num">{{ t('reports.quarterly.fulfillmentRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in quarterlyData" :key="q.quarter">
                  <td><strong>{{ q.quarter }}</strong></td>
                  <td class="num">{{ q.total_orders.toLocaleString(numberLocale) }}</td>
                  <td class="num">{{ formatMoney(q.total_revenue) }}</td>
                  <td class="num">{{ formatMoney(q.avg_order_value) }}</td>
                  <td class="num">
                    <span :class="getFulfillmentClass(q.fulfillment_rate)">
                      {{ q.fulfillment_rate }}%
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Monthly Trends Chart -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.chart.title') }}</h3>
          </div>
          <div class="chart-container">
            <div class="bar-chart" role="group" :aria-label="t('reports.chart.ariaLabel')">
              <div v-for="row in monthlyRows" :key="row.month" class="bar-wrapper">
                <div class="bar-container">
                  <div
                    class="bar"
                    role="img"
                    :style="{ height: getBarHeight(row.revenue) + 'px' }"
                    :title="row.tooltip"
                    :aria-label="row.tooltip"
                  ></div>
                </div>
                <div class="bar-label">{{ row.label }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Month-over-Month Comparison -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.monthly.title') }}</h3>
          </div>
          <div class="table-container">
            <table class="reports-table">
              <thead>
                <tr>
                  <th>{{ t('reports.monthly.month') }}</th>
                  <th class="num">{{ t('reports.monthly.orders') }}</th>
                  <th class="num">{{ t('reports.monthly.revenue') }}</th>
                  <th class="num">{{ t('reports.monthly.change') }}</th>
                  <th class="num">{{ t('reports.monthly.growthRate') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in monthlyRows" :key="row.month">
                  <td><strong>{{ row.label }}</strong></td>
                  <td class="num">{{ row.order_count.toLocaleString(numberLocale) }}</td>
                  <td class="num">{{ formatMoney(row.revenue) }}</td>
                  <td class="num">
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.changeText }}</span>
                    <span v-else>-</span>
                  </td>
                  <td class="num">
                    <span v-if="row.hasPrevious" :class="row.changeClass">{{ row.growthText }}</span>
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Summary Stats -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatMoney(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
          <div class="stat-value">{{ totalOrders.toLocaleString(numberLocale) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter || '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

// Max bar height in px (matches .bar-container height)
const MAX_BAR_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    // Incremented per load; only the latest request may write state, so a slow
    // earlier response cannot overwrite the result of a newer filter change
    let latestRequestId = 0

    const loadData = async () => {
      const requestId = ++latestRequestId
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        if (requestId !== latestRequestId) return
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        if (requestId !== latestRequestId) return
        error.value = t('reports.loadError') + ': ' + err.message
      } finally {
        if (requestId === latestRequestId) {
          loading.value = false
        }
      }
    }

    const numberLocale = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    // Report amounts are stored in USD; the helper converts for the active currency
    const formatMoney = (value) => formatCurrency(value, currentCurrency.value)

    // Convert YYYY-MM to a localized "Jan 2025" / "2025年1月" label.
    // Falls back to the raw string when the input is not a valid year-month.
    const formatMonth = (monthStr) => {
      const match = /^(\d{4})-(\d{2})$/.exec(monthStr || '')
      if (!match) return monthStr || ''
      const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, 1))
      if (isNaN(date.getTime()) || Number(match[2]) < 1 || Number(match[2]) > 12) return monthStr
      // timeZone UTC so the first of the month never rolls into the previous month
      return date.toLocaleDateString(numberLocale.value, {
        year: 'numeric',
        month: 'short',
        timeZone: 'UTC'
      })
    }

    // Highest monthly revenue, computed once instead of per bar
    const maxRevenue = computed(() => {
      return monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
    })

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * MAX_BAR_HEIGHT
    }

    // Monthly rows with labels and month-over-month change precomputed
    const monthlyRows = computed(() => {
      return monthlyData.value.map((m, index) => {
        const label = formatMonth(m.month)
        const row = {
          ...m,
          label,
          tooltip: `${label}: ${formatMoney(m.revenue)}`,
          hasPrevious: index > 0
        }
        if (index > 0) {
          const previous = monthlyData.value[index - 1].revenue
          const change = m.revenue - previous
          // Sign is added here and the absolute value formatted, so negatives
          // render as -$12,345 / -¥1,851,675
          const sign = change > 0 ? '+' : change < 0 ? '-' : ''
          row.changeText = sign + formatMoney(Math.abs(change))
          row.changeClass = change > 0 ? 'positive-change' : change < 0 ? 'negative-change' : ''
          if (previous === 0) {
            row.growthText = t('reports.notAvailable')
          } else {
            const rate = (change / previous) * 100
            row.growthText = (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
          }
        }
        return row
      })
    })

    const totalRevenue = computed(() => {
      return monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    })

    const avgMonthlyRevenue = computed(() => {
      return monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    })

    const totalOrders = computed(() => {
      return monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    })

    // Quarter with the highest revenue; empty string when there is no data
    const bestQuarter = computed(() => {
      let best = ''
      let bestRevenue = 0
      for (const q of quarterlyData.value) {
        if (q.total_revenue > bestRevenue) {
          bestRevenue = q.total_revenue
          best = q.quarter
        }
      }
      return best
    })

    const isEmpty = computed(() => quarterlyData.value.length === 0 && monthlyData.value.length === 0)

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(() => {
      loadData()
    })

    return {
      t,
      loading,
      error,
      quarterlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      isEmpty,
      numberLocale,
      formatMoney,
      getBarHeight,
      getFulfillmentClass
    }
  }
}
</script>

<style scoped>
.chart-container {
  padding: var(--space-5) var(--space-4);
  min-height: 300px;
  overflow-x: auto;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  min-width: 480px;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--color-accent);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: background-color var(--transition);
  cursor: pointer;
}

.bar:hover {
  background: var(--color-accent-hover);
}

.bar-label {
  font-size: var(--text-12);
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-5);
}

.positive-change {
  color: var(--color-success);
  font-weight: 600;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
