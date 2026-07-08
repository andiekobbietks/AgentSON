import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://andiekobbietks.github.io/AgentSON',
  base: '/',
  outDir: './dist',
  build: {
    format: 'directory',
  },
});
