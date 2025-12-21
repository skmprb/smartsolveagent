/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#135bec",
                "background-light": "#f6f7f8",
                "background-dark": "#101a22",
                "surface-dark": "#1c2932",
                "surface-light": "#ffffff",
                "card-dark": "#1c2b36",
                "card-light": "#ffffff",
            },
            fontFamily: {
                "display": ["Inter", "sans-serif"]
            },
            borderRadius: {
                "lg": "0.5rem",
                "xl": "0.75rem",
                "2xl": "1rem",
                // Default and full are usually included by default but we can keep them if needed to match specific override logic
            },
        },
    },
    plugins: [],
}