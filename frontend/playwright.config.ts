import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { defineConfig, devices } from '@playwright/test';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendNodeModules = path.resolve(__dirname, 'node_modules');
const rootNodeModules = path.resolve(__dirname, '..', 'node_modules');

// Symlink frontend/node_modules to root node_modules so tests in tests/e2e/ resolve packages
if (!fs.existsSync(rootNodeModules) && fs.existsSync(frontendNodeModules)) {
  try {
    fs.symlinkSync(frontendNodeModules, rootNodeModules, 'junction');
  } catch {
    // Ignore symlink errors
  }
}

process.env.NODE_PATH = process.env.NODE_PATH
  ? `${frontendNodeModules}:${process.env.NODE_PATH}`
  : frontendNodeModules;

export default defineConfig({
  testDir: '../tests/e2e',
  snapshotDir: '../tests/e2e/snapshots',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'python -m src',
    cwd: '..',
    url: 'http://localhost:8000/health',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
