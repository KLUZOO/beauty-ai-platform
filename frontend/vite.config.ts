import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
 
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");

  return {
    plugins: [react()],

    server: {
      host: "0.0.0.0",
      allowedHosts: true,
      proxy: {
        "/api": {
          target: "https://beautyaiservice.polandcentral.cloudapp.azure.com",
          changeOrigin: true,
          secure: false,
        },
        "/ai-chat": {
          target: env.VITE_AI_CHAT_PROXY_TARGET || "http://localhost:8001",
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/ai-chat/, ""),
        },
      },
    },
  };
});
  