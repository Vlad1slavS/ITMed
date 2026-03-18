import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import AdminPanel from "./components/AdminPanel.vue";

const routes = [
    { path: "/", name: "home", component: App },
    { path: "/admin", name: "admin", component: AdminPanel },
];

export const router = createRouter({
    history: createWebHistory(),
    routes,
});

