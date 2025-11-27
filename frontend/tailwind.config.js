/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0d1117", // GitHub dark bg
                surface: "#161b22", // GitHub surface
                border: "#30363d", // GitHub border
                primary: "#2f81f7", // GitHub blue
                secondary: "#238636", // GitHub green
                text: "#c9d1d9", // GitHub text
                muted: "#8b949e", // GitHub muted text
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
