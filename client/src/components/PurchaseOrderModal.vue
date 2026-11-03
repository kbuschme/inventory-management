<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container po-modal-container" role="dialog" aria-modal="true" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="btn btn-ghost close-button" :aria-label="t('purchaseOrder.close')" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item summary (shown in both modes) -->
            <div class="item-summary">
              <div class="summary-title">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">{{ t('purchaseOrder.sku') }}: {{ backlogItem.item_sku }}</div>
              </div>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.orderId') }}</div>
                  <div class="info-value">{{ backlogItem.order_id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.shortage') }}</div>
                  <div class="info-value shortage-value">{{ shortage }} {{ t('purchaseOrder.units') }}</div>
                </div>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="viewLoading" class="state-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="viewError" class="error-message" role="alert">{{ viewError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid po-details">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                  <div class="info-value">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="badge info status-badge">{{ purchaseOrder.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ money(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value">{{ money(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value notes-value">{{ purchaseOrder.notes || '-' }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" required :disabled="submitting" />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" required :disabled="submitting" />
                </div>
                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input id="po-unit-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" required :disabled="submitting" />
                </div>
              </div>

              <div class="form-group">
                <label for="po-delivery">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-delivery" v-model="form.expected_delivery_date" type="date" required :disabled="submitting" />
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notesOptional') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" :disabled="submitting"></textarea>
              </div>

              <div class="total-row">
                <span class="total-label">{{ t('purchaseOrder.total') }}</span>
                <span class="total-value">{{ money(total) }}</span>
              </div>

              <div v-if="submitError" class="error-message" role="alert">{{ submitError }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('purchaseOrder.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn btn-primary"
              :disabled="!isValid || submitting"
            >
              {{ submitting ? t('purchaseOrder.creating') : t('purchaseOrder.create') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const emptyForm = () => ({
  supplier_name: '',
  quantity: 1,
  unit_cost: '',
  expected_delivery_date: '',
  notes: ''
})

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentCurrency, translateProductName, currentLocale } = useI18n()

    const form = ref(emptyForm())
    const submitting = ref(false)
    const submitError = ref(null)

    const purchaseOrder = ref(null)
    const viewLoading = ref(false)
    const viewError = ref(null)
    // Guards against a slow response for a previous item overwriting the current one
    let loadToken = 0

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    // v-model on number inputs yields '' when empty, so coerce explicitly
    const quantityNum = computed(() => (form.value.quantity === '' ? NaN : Number(form.value.quantity)))
    const unitCostNum = computed(() => (form.value.unit_cost === '' ? NaN : Number(form.value.unit_cost)))

    const total = computed(() => {
      const q = quantityNum.value
      const c = unitCostNum.value
      return Number.isFinite(q) && Number.isFinite(c) ? q * c : 0
    })

    const isValid = computed(() => {
      const date = new Date(form.value.expected_delivery_date)
      return (
        form.value.supplier_name.trim().length > 0 &&
        Number.isFinite(quantityNum.value) && quantityNum.value > 0 &&
        Number.isFinite(unitCostNum.value) && unitCostNum.value >= 0 &&
        form.value.expected_delivery_date !== '' && !isNaN(date.getTime())
      )
    })

    const money = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    const close = () => {
      emit('close')
    }

    const submit = async () => {
      if (!isValid.value || submitting.value) return
      submitting.value = true
      submitError.value = null
      try {
        const po = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name.trim(),
          quantity: quantityNum.value,
          unit_cost: unitCostNum.value,
          expected_delivery_date: form.value.expected_delivery_date,
          // Omit empty notes so the backend stores null rather than ''
          ...(form.value.notes.trim() ? { notes: form.value.notes.trim() } : {})
        })
        emit('po-created', po)
      } catch (err) {
        // Backend returns detail for 400/404/409 (e.g. duplicate PO)
        const detail = err.response?.data?.detail
        submitError.value = typeof detail === 'string' ? detail : t('purchaseOrder.createFailed')
        console.error('Failed to create purchase order:', err)
      } finally {
        submitting.value = false
      }
    }

    const loadPurchaseOrder = async () => {
      const token = ++loadToken
      purchaseOrder.value = null
      viewError.value = null
      // Use the PO already attached to the backlog item to avoid a request
      if (props.backlogItem.purchase_order) {
        purchaseOrder.value = props.backlogItem.purchase_order
        viewLoading.value = false
        return
      }
      viewLoading.value = true
      try {
        const po = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
        if (token === loadToken) purchaseOrder.value = po
      } catch (err) {
        if (token === loadToken) {
          const detail = err.response?.data?.detail
          viewError.value = typeof detail === 'string' ? detail : t('purchaseOrder.loadFailed')
        }
        console.error('Failed to load purchase order:', err)
      } finally {
        if (token === loadToken) viewLoading.value = false
      }
    }

    // Reset/load every time the modal opens or targets a different item
    watch(
      () => [props.isOpen, props.backlogItem, props.mode],
      () => {
        if (!props.isOpen || !props.backlogItem) return
        submitError.value = null
        submitting.value = false
        if (props.mode === 'view') {
          loadPurchaseOrder()
        } else {
          form.value = { ...emptyForm(), quantity: shortage.value || 1 }
        }
      },
      { immediate: true }
    )

    const onKeydown = (event) => {
      if (event.key === 'Escape') close()
    }

    // Only listen for Escape while open
    watch(
      () => props.isOpen,
      (open) => {
        if (open) document.addEventListener('keydown', onKeydown)
        else document.removeEventListener('keydown', onKeydown)
      },
      { immediate: true }
    )

    onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

    return {
      t,
      translateProductName,
      form,
      submitting,
      submitError,
      purchaseOrder,
      viewLoading,
      viewError,
      shortage,
      total,
      isValid,
      money,
      formatDate,
      close,
      submit
    }
  }
}
</script>

<style scoped>
.po-modal-container {
  max-width: 640px;
}

.close-button {
  padding: var(--space-2);
}

.item-summary {
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}

.item-name {
  font-size: var(--text-20);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 var(--space-1) 0;
}

.item-sku {
  font-size: var(--text-13);
  color: var(--color-text-muted);
  margin-bottom: var(--space-3);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
  gap: var(--space-4);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: var(--text-13);
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--text-14);
  font-weight: 500;
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.shortage-value {
  color: var(--color-danger);
}

.notes-value {
  white-space: pre-wrap;
  font-weight: 400;
}

.status-badge {
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

label {
  font-size: var(--text-13);
  font-weight: 500;
  color: var(--color-text);
}

textarea {
  resize: vertical;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.total-label {
  font-size: var(--text-13);
  font-weight: 500;
  color: var(--color-text-muted);
}

.total-value {
  font-size: var(--text-20);
  font-weight: 600;
  color: var(--color-ink);
  font-variant-numeric: tabular-nums;
}

.state-message {
  color: var(--color-text-muted);
  font-size: var(--text-14);
}

.error-message {
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger-border);
  border-radius: var(--radius-lg);
  color: var(--color-danger);
  font-size: var(--text-14);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
