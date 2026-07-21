import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 정적 호스팅(서브경로 포함) 어디서든 동작하도록 상대 경로 빌드
export default defineConfig({
  base: "./",
  plugins: [react()],
});
