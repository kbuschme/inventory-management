<template>
  <div class="language-switcher" :class="{ compact }">
    <button
      class="language-button"
      :aria-label="compact ? localeName : null"
      :title="compact ? localeName : null"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span v-if="!compact" class="language-label">{{ localeName }}</span>
      <svg
        v-if="!compact"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

defineProps({
  compact: { type: Boolean, default: false }
})

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  display: flex;
  align-items: center;
  width: 100%;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--sidebar-control-bg);
  border: 1px solid var(--sidebar-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition);
  color: var(--sidebar-text);
  text-align: left;
  font-size: var(--text-14);
}

.language-button:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.globe-icon,
.chevron {
  flex-shrink: 0;
  color: var(--sidebar-text-muted);
}

.compact .language-button {
  justify-content: center;
  padding-inline: 0;
}

/* Open to the right of the 72px rail, bottom aligned with the trigger */
.compact .dropdown-menu {
  bottom: 0;
  left: calc(100% + var(--space-4) + var(--space-2));
  right: auto;
  min-width: 180px;
}

.language-label {
  flex: 1;
  font-weight: 500;
}

.chevron {
  transition: transform var(--transition);
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + var(--space-2));
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-float);
  z-index: var(--z-dropdown);
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--transition);
  font-size: var(--text-14);
  font-weight: 500;
  color: var(--color-text);
}

.dropdown-item:hover {
  background: var(--color-surface-muted);
}

.dropdown-item.active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}
</style>
