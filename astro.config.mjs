// @ts-check
import { defineConfig } from 'astro/config';

// GitHub Pages project site: https://<user>.github.io/<repo>/
// IMPORTANT: `base` MUST match the GitHub repository name exactly
// (currently "ResumeGenerator"). If the repo is renamed, update it here.
// `site` should be your GitHub Pages origin (https://<github-user>.github.io).
export default defineConfig({
  site: 'https://oscared08.github.io',
  base: '/ResumeGenerator',
  output: 'static',
});
