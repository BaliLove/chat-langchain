import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: './vitest.setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'test-utils/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData.ts',
        '**/__tests__/**',
        '**/types/**',
        '.next/**',
        'coverage/**',
      ],
      thresholds: {
        branches: 60,
        functions: 60,
        lines: 70,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
})