<template>
  <div class="restocking">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ t('restocking.title') }}</h1>
        <p class="page-subtitle">{{ t('restocking.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-row">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
          <span class="budget-value">{{ formatMoney(budget) }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="0"
          max="500000"
          step="5000"
          class="budget-slider"
        />
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatMoney(budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ formatMoney(totalSpent) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: orderLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header header-with-action">
          <h2 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h2>
          <button
            type="button"
            class="btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="submittedOrder" class="notice success-notice">
          <span>
            {{ t('restocking.success', {
              orderNumber: submittedOrder.order_number,
              days: submittedOrder.lead_time_days,
              date: formatDate(submittedOrder.expected_delivery)
            }) }}
          </span>
          <router-link to="/orders" class="notice-link">{{ t('restocking.viewOrder') }}</router-link>
        </div>
        <div v-if="submitError" class="notice error-notice">{{ submitError }}</div>

        <div v-if="recommendations.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.currentDemand') }}</th>
                <th class="num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.id">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.current_demand }}</td>
                <td class="num">{{ item.forecasted_demand }}</td>
                <td class="num"><strong>{{ item.quantity }}</strong></td>
                <td class="num">{{ formatMoney(item.unit_cost, 2) }}</td>
                <td class="num"><strong>{{ formatMoney(item.lineCost) }}</strong></td>
                <td class="num">{{ item.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(100000)

    // Order submission state is kept separate so the table is not reloaded
    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrder = ref(null)

    // Amounts from the API are in USD; convert for the active currency
    const formatMoney = (value, decimals = 0) => {
      return decimals > 0
        ? formatCurrencyWithDecimals(value, currentCurrency.value, decimals)
        : formatCurrency(value, currentCurrency.value)
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    // Greedy selection: rank items with a positive demand gap by gap size (largest first),
    // then walk the list adding each item in full if it fits in the remaining budget.
    // An item that does not fit is skipped (not partially ordered) and the walk continues,
    // so smaller, cheaper items further down the list can still use the leftover budget.
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .filter(f => f.forecasted_demand > f.current_demand)
        .map(f => ({ ...f, quantity: f.forecasted_demand - f.current_demand }))
        .sort((a, b) => b.quantity - a.quantity)

      let remaining = budget.value
      const selected = []
      for (const item of candidates) {
        const lineCost = item.quantity * item.unit_cost
        if (lineCost <= remaining) {
          selected.push({ ...item, lineCost })
          remaining -= lineCost
        }
      }
      return selected
    })

    const totalSpent = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.lineCost, 0)
    })

    const remainingBudget = computed(() => budget.value - totalSpent.value)

    // The order is complete only when the slowest item arrives, so use the max lead time
    const orderLeadTime = computed(() => {
      return recommendations.value.reduce((max, item) => Math.max(max, item.lead_time_days), 0)
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = t('restocking.loadError') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (submitting.value || recommendations.value.length === 0) return
      try {
        submitting.value = true
        submitError.value = null
        submittedOrder.value = null
        submittedOrder.value = await api.createRestockOrder({
          items: recommendations.value.map(item => ({
            sku: item.item_sku,
            name: item.item_name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
            lead_time_days: item.lead_time_days
          })),
          budget: budget.value
        })
      } catch (err) {
        submitError.value = err.response?.data?.detail || (t('restocking.error') + ': ' + err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      recommendations,
      totalSpent,
      remainingBudget,
      orderLeadTime,
      submitting,
      submitError,
      submittedOrder,
      formatMoney,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.budget-label {
  font-size: var(--text-14);
  font-weight: 600;
  color: var(--color-text-muted);
}

.budget-value {
  font-size: var(--text-24);
  font-weight: 600;
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
}

.budget-hint {
  margin: var(--space-3) 0 0;
  font-size: var(--text-13);
  color: var(--color-text-muted);
}

.budget-slider {
  display: block;
  width: 100%;
}

.header-with-action {
  flex-wrap: wrap;
}

.notice {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin: 0 0 var(--space-4);
  padding: var(--space-3) var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: var(--text-14);
}

.success-notice {
  background: var(--color-success-soft);
  border-color: var(--color-success-border);
  color: var(--color-success);
}

.error-notice {
  background: var(--color-danger-soft);
  border-color: var(--color-danger-border);
  color: var(--color-danger);
}

.notice-link {
  color: var(--color-accent);
  font-weight: 600;
  white-space: nowrap;
}
</style>
