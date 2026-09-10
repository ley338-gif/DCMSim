import {defineConfig,devices} from '@playwright/test'
export default defineConfig({testDir:'./e2e',fullyParallel:true,reporter:'html',use:{baseURL:'http://127.0.0.1:41737',trace:'on-first-retry'},webServer:{command:'npm run dev -- --host 127.0.0.1 --port 41737 --strictPort',url:'http://127.0.0.1:41737',reuseExistingServer:false},projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}]})
