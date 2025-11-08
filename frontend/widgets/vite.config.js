import { defineConfig } from 'vite'

// Explicit multi-entry for clarity (expand as you add widgets)
const inputs = {
  orchidOfTheDay: 'src/widgets/orchidOfTheDay/index.ts',
  themedGalleries: 'src/widgets/themedGalleries/index.ts',
  myCollection: 'src/widgets/myCollection/index.ts',
  hollywoodBlooms: 'src/widgets/hollywoodBlooms/index.ts',
  philosophyQuiz: 'src/widgets/philosophyQuiz/index.ts',
}

export default defineConfig({
  build: {
    rollupOptions: {
      input: inputs,
      output: {
        // One file per widget with stable names
        entryFileNames: 'widgets/[name].js',
        chunkFileNames: 'widgets/[name]-[hash].js',
        assetFileNames: 'widgets/[name]-[hash][extname]',
        inlineDynamicImports: false
      }
    },
    sourcemap: false,
    minify: true,
    outDir: 'dist',
    emptyOutDir: true
  }
})
