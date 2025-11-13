/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true, // Allows to use test() and expect() globally
    environment: 'jsdom', // Use jsdom for a browser-like environment
    setupFiles: './src/test/setup.js', // A file to run before each test
  },
})