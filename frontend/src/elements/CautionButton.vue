<script setup lang="ts">
// icons
import { IconCheck, IconCopy } from '@tabler/icons-vue';

// component properties
interface Props {
  label?: string; // button text
  icon?: 'copy'|'check'; // optional icon displayed before label
  waiting?: boolean; // if true, spinning animation is shown instead of label
}
defineProps<Props>();
</script>

<template>
  <button
    class="
      relative flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-lg
      bg-rose-600 px-6 text-base font-semibold text-white transition-all ease-in-out 
      hover:shadow-md enabled:hover:bg-rose-700 disabled:opacity-50 disabled:shadow-none
      dark:bg-rose-900
    "
    :class="{ '!text-transparent': waiting }"
  >
    <div
      v-if="waiting"
      class="absolute size-5 animate-spin rounded-full border-2 border-white border-t-transparent"
    ></div>
    <icon-copy v-if="icon === 'copy'" class="size-6 fill-transparent stroke-current stroke-2" />
    <icon-check v-if="icon === 'check'" class="size-6 fill-transparent stroke-current stroke-2" />
    <template v-if="label">
      {{ label }}
    </template>
    <template v-else>
      <slot></slot>
    </template>
  </button>
</template>
