<template>
    <div class="app">
        <NavBar />
        <HeroSection @open-analyzer="showAnalyzer = true" />
        <AnalyzerModal v-if="showAnalyzer" @close="showAnalyzer = false" />
        <ChatWidget />
        <HowItWork />
    </div>
</template>

<script setup>
import { ref } from "vue";
import NavBar from "./components/NavBar.vue";
import HeroSection from "./components/HeroSection.vue";
import AnalyzerModal from "./components/AnalyzerModal.vue";
import ChatWidget from "./components/ChatWidget.vue";
import HowItWork from "./components/HowItWork.vue";

const showAnalyzer = ref(false);
</script>

<style scoped>
.app {
    min-height: 100vh;
}
</style>
