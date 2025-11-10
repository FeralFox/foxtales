import { nodeResolve } from '@rollup/plugin-node-resolve'
import terser from '@rollup/plugin-terser'
import { copy } from 'fs-extra'

const copyPDFJS = () => ({
    name: 'copy-pdfjs',
    async writeBundle() {
        await copy('node_modules/pdfjs-dist/build/pdf.mjs', 'public/pdfjs/pdf.mjs')
        await copy('node_modules/pdfjs-dist/build/pdf.mjs.map', 'public/pdfjs/pdf.mjs.map')
        await copy('node_modules/pdfjs-dist/build/pdf.worker.mjs', 'public/pdfjs/pdf.worker.mjs')
        await copy('node_modules/pdfjs-dist/build/pdf.worker.mjs.map', 'public/pdfjs/pdf.worker.mjs.map')
        await copy('node_modules/pdfjs-dist/cmaps', 'public/pdfjs/cmaps')
        await copy('node_modules/pdfjs-dist/standard_fonts', 'public/pdfjs/standard_fonts')
    },
})

export default [{
    input: 'rollup/fflate.js',
    output: {
        dir: 'vendor/',
        format: 'esm',
    },
    plugins: [nodeResolve(), terser()],
},
{
    input: 'rollup/zip.js',
    output: {
        dir: 'vendor/',
        format: 'esm',
    },
    plugins: [nodeResolve(), terser(), copyPDFJS()],
}]
