import {defineConfig} from 'vite'
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js'
import vue from '@vitejs/plugin-vue'
import svgLoader from 'vite-svg-loader'
import {VitePWA} from 'vite-plugin-pwa'


// https://cn.vitejs.dev/config/
export default defineConfig({
    plugins: [vue(),
        cssInjectedByJsPlugin(),
        svgLoader({
            defaultImport: "component"
        }),
        VitePWA({
            registerType: 'autoUpdate',
            includeAssets: ['favicon.ico', 'logo.svg', 'logo192.png', 'logo512.png'],
            manifest: {
                name: 'Foxtales Ebook Library',
                short_name: 'Foxtales',
                description: 'An ebook library and reader',
                theme_color: '#fff',
                background_color: '#fff',
                display: 'standalone',
                scope: '/',
                start_url: '/',
                orientation: 'any',
                icons: [
                    {
                        src: '/logo192.png',
                        sizes: '192x192',
                        type: 'image/png',
                        purpose: 'any maskable'
                    },
                    {
                        src: '/logo512.png',
                        sizes: '512x512',
                        type: 'image/png',
                        purpose: 'any maskable'
                    }
                ]
            }
        })
    ],
    build: {
        target: 'esnext' //browsers can handle the latest ES features
    },
})
