import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'CharanBot',
  description: 'CharanBot – Personal AI Assistant by Sri Charan',

  // VERY IMPORTANT for Cloudflare Pages
  base: '/',

  themeConfig: {
    nav: [
      { text: 'Home', link: '/' }
    ],
    footer: {
      message: 'Built with ❤️ by Sri Charan',
      copyright: '© 2026 CharanBot'
    }
  }
})
