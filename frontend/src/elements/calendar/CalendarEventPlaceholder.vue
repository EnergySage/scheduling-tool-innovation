<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// component properties
interface Props {
  isBusy: boolean; // flag showing this event as busy and non-selectable
  isSelected: boolean; // flag showing if the event is currently selected by user
  isMonthView: boolean; // flag, are we in month view?
  label: string; // event title
}
defineProps<Props>();

</script>

<template>
  <div
    class="m-auto size-[95%] shrink-0 text-sm text-gray-700 hover:shadow-md dark:text-gray-200"
    :class="{
      'group/event cursor-pointer rounded-md p-1 hover:bg-blue-300 hover:shadow-lg': !isBusy,
      'bg-blue-50 hover:bg-blue-500 hover:!text-white dark:bg-blue-600 dark:hover:bg-blue-800': !isBusy,
      'bg-blue-500 text-white dark:bg-blue-800 shadow-lg': isSelected,
      'h-full rounded': !isMonthView,
      '!cursor-not-allowed rounded-md bg-gray-100 p-1 dark:bg-gray-600': isBusy,
    }"
  >
    <div class="grid">
      <div
        class="
          h-full truncate rounded border-2 border-dashed border-blue-400 p-1
          font-semibold group-hover/event:border-white"
        :class="{
          '!border-none': isBusy,
          'border-white': isSelected,
        }"
      >
        <template v-if="isBusy">{{ t('label.busy') }}</template>
        <template v-else>{{ label }}</template>
      </div>
    </div>
  </div>
</template>
