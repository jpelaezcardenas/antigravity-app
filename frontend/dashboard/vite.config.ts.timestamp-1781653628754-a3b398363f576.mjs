// vite.config.ts
import { defineConfig } from "file:///C:/Users/contexia/Projects/antigravity-app/frontend/dashboard/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/contexia/Projects/antigravity-app/frontend/dashboard/node_modules/@vitejs/plugin-react/dist/index.js";
import tailwindcss from "file:///C:/Users/contexia/Projects/antigravity-app/frontend/dashboard/node_modules/@tailwindcss/vite/dist/index.mjs";
var vite_config_default = defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api/v1": {
        target: "http://localhost:8080",
        changeOrigin: true
      },
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "/api/v1")
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxjb250ZXhpYVxcXFxQcm9qZWN0c1xcXFxhbnRpZ3Jhdml0eS1hcHBcXFxcZnJvbnRlbmRcXFxcZGFzaGJvYXJkXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxjb250ZXhpYVxcXFxQcm9qZWN0c1xcXFxhbnRpZ3Jhdml0eS1hcHBcXFxcZnJvbnRlbmRcXFxcZGFzaGJvYXJkXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9jb250ZXhpYS9Qcm9qZWN0cy9hbnRpZ3Jhdml0eS1hcHAvZnJvbnRlbmQvZGFzaGJvYXJkL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xyXG5pbXBvcnQgdGFpbHdpbmRjc3MgZnJvbSAnQHRhaWx3aW5kY3NzL3ZpdGUnXHJcblxyXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xyXG4gIGJhc2U6ICcvJyxcclxuICBwbHVnaW5zOiBbcmVhY3QoKSwgdGFpbHdpbmRjc3MoKV0sXHJcbiAgc2VydmVyOiB7XHJcbiAgICBwb3J0OiA1MTczLFxyXG4gICAgaG9zdDogdHJ1ZSxcclxuICAgIHByb3h5OiB7XHJcbiAgICAgICcvYXBpL3YxJzoge1xyXG4gICAgICAgIHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA4MCcsXHJcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlXHJcbiAgICAgIH0sXHJcbiAgICAgICcvYXBpJzoge1xyXG4gICAgICAgIHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA4MCcsXHJcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxyXG4gICAgICAgIHJld3JpdGU6IChwYXRoKSA9PiBwYXRoLnJlcGxhY2UoL15cXC9hcGkvLCAnL2FwaS92MScpXHJcbiAgICAgIH1cclxuICAgIH1cclxuICB9XHJcbn0pXHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBdVgsU0FBUyxvQkFBb0I7QUFDcFosT0FBTyxXQUFXO0FBQ2xCLE9BQU8saUJBQWlCO0FBRXhCLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLE1BQU07QUFBQSxFQUNOLFNBQVMsQ0FBQyxNQUFNLEdBQUcsWUFBWSxDQUFDO0FBQUEsRUFDaEMsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sT0FBTztBQUFBLE1BQ0wsV0FBVztBQUFBLFFBQ1QsUUFBUTtBQUFBLFFBQ1IsY0FBYztBQUFBLE1BQ2hCO0FBQUEsTUFDQSxRQUFRO0FBQUEsUUFDTixRQUFRO0FBQUEsUUFDUixjQUFjO0FBQUEsUUFDZCxTQUFTLENBQUMsU0FBUyxLQUFLLFFBQVEsVUFBVSxTQUFTO0FBQUEsTUFDckQ7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
