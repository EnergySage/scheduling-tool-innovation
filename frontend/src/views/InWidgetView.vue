<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import GenericModal from '@/components/GenericModal.vue';
import PrimaryButton from '@/tbpro/elements/PrimaryButton.vue';

// component constants
const { t } = useI18n();
const router = useRouter();
</script>

<template>
  <div>
    <generic-modal>
      <template v-slot:header>
        <h2 id="title">Appointment Widget</h2>
      </template>
      <div class="widget-container">
        <iframe class="widget" src="http://localhost:8080/widget/user/dejan.stokic%40energysage.com/31e87e3e/" />
      </div>
      <template v-slot:actions>
        <primary-button
          class="btn-close"
          :title="t('label.close')"
          @click="router.push({name: 'home'})"
        >
          {{ t('label.close') }}
        </primary-button>
      </template>
      <template v-slot:footer>
      <router-link :to="{name: 'home'}">{{ t('app.tagline') }}</router-link>
      </template>
    </generic-modal>
  </div>
</template>

<style scoped>
.widget-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
  height: inherit;
}

.widget {
  height: inherit;
}
</style>
