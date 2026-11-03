<template>
  <div class="app-shell" :class="{ 'is-rail': isRail, 'is-animated': animated }">
    <button
      class="menu-button"
      type="button"
      :aria-label="navOpen ? t('nav.closeMenu') : t('nav.openMenu')"
      :aria-expanded="navOpen"
      aria-controls="app-sidebar"
      @click="navOpen = !navOpen"
    >
      <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>

    <div v-if="navOpen" class="sidebar-backdrop" aria-hidden="true" @click="navOpen = false"></div>

    <aside id="app-sidebar" class="sidebar" :class="{ open: navOpen }">
      <div class="sidebar-brand">
        <span class="brand-monogram" aria-hidden="true">{{ brandInitial }}</span>
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav" :aria-label="t('nav.mainNav')">
        <div v-for="group in navGroups" :key="group.key" class="nav-group">
          <div class="nav-group-label">{{ t(group.labelKey) }}</div>
          <router-link
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            :title="isRail ? t(item.labelKey) : null"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="(d, i) in item.icon" :key="i" :d="d" />
            </svg>
            <span class="nav-label">{{ t(item.labelKey) }}</span>
          </router-link>
        </div>
      </nav>

      <button
        v-if="!isMobile"
        class="sidebar-toggle"
        type="button"
        :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')"
        :title="collapsed ? t('nav.expand') : t('nav.collapse')"
        :aria-expanded="!collapsed"
        aria-controls="app-sidebar"
        @click="toggleCollapsed"
      >
        <svg class="nav-icon toggle-chevron" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 6l-6 6 6 6" />
        </svg>
      </button>

      <div class="sidebar-footer">
        <LanguageSwitcher :compact="isRail" />
        <ProfileMenu
          :compact="isRail"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-column">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()

    const navGroups = [
      {
        key: 'operations',
        labelKey: 'nav.groupOperations',
        items: [
          { to: '/', labelKey: 'nav.overview', icon: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'] },
          { to: '/inventory', labelKey: 'nav.inventory', icon: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
          { to: '/orders', labelKey: 'nav.orders', icon: ['M9 4h6a1 1 0 011 1v1H8V5a1 1 0 011-1z', 'M8 6H6a2 2 0 00-2 2v11a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-2', 'M9 12h6M9 16h4'] },
          { to: '/restocking', labelKey: 'nav.restocking', icon: ['M21 12a9 9 0 01-15.5 6.2L3 16', 'M3 12a9 9 0 0115.5-6.2L21 8', 'M21 3v5h-5', 'M3 21v-5h5'] }
        ]
      },
      {
        key: 'planning',
        labelKey: 'nav.groupPlanning',
        items: [
          { to: '/demand', labelKey: 'nav.demandForecast', icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
          { to: '/spending', labelKey: 'nav.finance', icon: ['M12 2v20', 'M17 6H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6'] },
          { to: '/reports', labelKey: 'nav.reports', icon: ['M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z', 'M14 3v5h5', 'M9 13h6M9 17h6'] }
        ]
      }
    ]

    // Sidebar collapse state. Computed in setup so the first paint is already correct.
    const COLLAPSE_KEY = 'inventory.sidebarCollapsed'
    const mqMobile = window.matchMedia ? window.matchMedia('(max-width: 768px)') : null
    const mqNarrow = window.matchMedia ? window.matchMedia('(max-width: 1100px)') : null

    const readStored = () => {
      try {
        const v = window.localStorage.getItem(COLLAPSE_KEY)
        return v === 'true' ? true : v === 'false' ? false : null
      } catch (e) {
        return null
      }
    }
    const stored = readStored()
    const userChose = ref(stored !== null)
    const collapsed = ref(stored !== null ? stored : !!(mqNarrow && mqNarrow.matches))
    const isMobile = ref(!!(mqMobile && mqMobile.matches))
    // Rail only applies on desktop; the mobile drawer always shows labels.
    const isRail = computed(() => collapsed.value && !isMobile.value)
    const brandInitial = computed(() => Array.from(t('nav.companyName'))[0] || '')

    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value
      userChose.value = true
      try {
        window.localStorage.setItem(COLLAPSE_KEY, String(collapsed.value))
      } catch (e) { /* storage blocked: choice lasts for this session only */ }
    }
    const onMobileChange = (e) => { isMobile.value = e.matches }
    const onNarrowChange = (e) => { if (!userChose.value) collapsed.value = e.matches }

    // Enable width/margin transitions only after the first paint.
    const animated = ref(false)
    onMounted(() => {
      if (mqMobile) mqMobile.addEventListener('change', onMobileChange)
      if (mqNarrow) mqNarrow.addEventListener('change', onNarrowChange)
      requestAnimationFrame(() => requestAnimationFrame(() => { animated.value = true }))
    })
    onUnmounted(() => {
      if (mqMobile) mqMobile.removeEventListener('change', onMobileChange)
      if (mqNarrow) mqNarrow.removeEventListener('change', onNarrowChange)
    })

    const navOpen = ref(false)
    const closeNav = () => { navOpen.value = false }
    const onKeydown = (e) => {
      if (e.key === 'Escape') closeNav()
    }
    watch(() => route.path, closeNav)
    onMounted(() => window.addEventListener('keydown', onKeydown))
    onUnmounted(() => window.removeEventListener('keydown', onKeydown))
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navGroups,
      navOpen,
      collapsed,
      isRail,
      isMobile,
      animated,
      brandInitial,
      toggleCollapsed,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
.app-shell {
  --sidebar-current: var(--sidebar-width);
  min-height: 100vh;
}

.app-shell.is-rail {
  --sidebar-current: var(--sidebar-width-collapsed);
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-current);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  z-index: var(--z-sidebar);
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3) var(--space-3);
  border-bottom: 1px solid var(--sidebar-border);
}

.brand-name {
  font-size: var(--text-16);
  font-weight: 600;
  color: var(--sidebar-text-active);
}

.brand-subtitle {
  font-size: var(--text-12);
  color: var(--sidebar-text-muted);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  overflow-y: auto;
  min-height: 0;
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-group-label {
  padding: 0 var(--space-3) var(--space-1);
  font-size: var(--text-12);
  font-weight: 500;
  color: var(--sidebar-text-muted);
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: var(--text-14);
  font-weight: 500;
  transition: background-color var(--transition), color var(--transition);
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.nav-item.router-link-exact-active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-text-active);
}

.nav-item.router-link-exact-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-1);
  bottom: var(--space-1);
  width: 3px;
  border-radius: 0 var(--space-1) var(--space-1) 0;
  background: var(--sidebar-accent);
}

.sidebar :focus-visible {
  outline-color: var(--sidebar-accent);
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: flex-end;
  width: 32px;
  height: 32px;
  padding: 0;
  background: none;
  border: 1px solid var(--sidebar-border);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  cursor: pointer;
  transition: background-color var(--transition), color var(--transition);
}

.sidebar-toggle:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.toggle-chevron {
  transition: transform var(--transition);
}

.brand-monogram {
  display: none;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid var(--sidebar-border);
}

/* ---------- Collapsed rail (desktop only) ---------- */
.app-shell.is-animated .sidebar {
  transition: width var(--transition), transform var(--transition), visibility var(--transition);
}

.app-shell.is-animated .content-column {
  transition: margin-left var(--transition);
}

.is-rail .sidebar-brand {
  position: relative;
  align-items: center;
  padding-inline: 0;
}

.is-rail .brand-monogram {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-text-active);
  font-size: var(--text-16);
  font-weight: 600;
}

/* Visually hidden but still exposed to assistive tech */
.is-rail .brand-name,
.is-rail .brand-subtitle,
.is-rail .nav-label,
.is-rail .nav-group-label {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

.is-rail .sidebar-nav {
  gap: var(--space-3);
}

.is-rail .nav-group + .nav-group {
  padding-top: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
}

.is-rail .nav-item {
  justify-content: center;
  padding-inline: 0;
}

.is-rail .sidebar-toggle {
  align-self: center;
}

.is-rail .toggle-chevron {
  transform: rotate(180deg);
}

/* ---------- Content column ---------- */
.content-column {
  margin-left: var(--sidebar-current);
  min-width: 0;
  min-height: 100vh;
}

.main-content {
  max-width: var(--content-max-width);
  padding: var(--space-6);
}

.menu-button,
.sidebar-backdrop {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .app-shell.is-animated .sidebar,
  .app-shell.is-animated .content-column {
    transition: none;
  }
}

@media (max-width: 768px) {
  .sidebar-toggle {
    display: none;
  }

  .sidebar {
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform var(--transition), visibility var(--transition);
  }

  .sidebar.open {
    transform: translateX(0);
    visibility: visible;
    box-shadow: var(--shadow-float);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    z-index: var(--z-backdrop);
  }

  .menu-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: var(--space-2);
    left: var(--space-3);
    width: 40px;
    height: 40px;
    z-index: calc(var(--z-sticky) + 1);
    background: var(--color-surface);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-sm);
    color: var(--color-ink);
    cursor: pointer;
  }

  .content-column {
    margin-left: 0;
  }

  .main-content {
    padding: var(--space-4);
  }
}
</style>
