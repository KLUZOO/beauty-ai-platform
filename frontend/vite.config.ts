import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
 
export default defineConfig({
  plugins: [react()],
 
  server: {
    allowedHosts: ["fool-creatable-ignition.ngrok-free.dev", "beautyaiservice.polandcentral.cloudapp.azure.com"],
    proxy: {
      "/api": {
        target: "https://beautyaiservice.polandcentral.cloudapp.azure.com",
        changeOrigin: true,
        // Бекенд поки на самопідписаному/недовіреному сертифікаті — вимикаємо перевірку
        // тільки для локального дев-проксі. На проді так робити не можна.
        secure: false,
      },
    },
  },
});