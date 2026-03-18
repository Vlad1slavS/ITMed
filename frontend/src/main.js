import { createApp } from "vue"
import Root from "./Root.vue"        // ← было App, стало Root
import { router } from "./router"
import "./style.css"

createApp(Root).use(router).mount("#app")