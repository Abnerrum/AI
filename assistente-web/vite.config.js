import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

const raiz = fileURLToPath(new URL('./painel_web', import.meta.url));

export default defineConfig({
  configFile: false,
  root: raiz,
  publicDir: false,
  build: {
    outDir: fileURLToPath(new URL('./painel_web/estatico/build', import.meta.url)),
    emptyOutDir: true,
    rollupOptions: {
      input: fileURLToPath(new URL('./painel_web/src/main.jsx', import.meta.url)),
      output: {
        entryFileNames: 'painel-react.js',
        chunkFileNames: 'chunk-[name].js',
        assetFileNames: 'asset-[name][extname]',
      },
    },
  },
});
