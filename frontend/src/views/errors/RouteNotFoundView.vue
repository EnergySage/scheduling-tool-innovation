<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import ArtInvalidLink from '@/elements/arts/ArtInvalidLink.vue';
import PrimaryButton from '@/elements/PrimaryButton.vue';

const { t } = useI18n();
</script>

<template>
  <div class="flex-center h-full flex-col gap-12 p-4">
    <div class="flex-center flex-col gap-8 px-4">
      <div class="text-xl font-semibold text-gray-700">
        {{ t('error.routeNotFound') }}
      </div>
      <primary-button class="btn-back" @click="$router.go(-1)" :title="t('label.goBack')">
        {{ t('label.goBack') }}
      </primary-button>
    </div>
  </div>

</template>
