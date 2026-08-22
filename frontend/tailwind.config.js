/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "trust-green": "#16a34a",
        "trust-red": "#dc2626",
        "trust-navy": "#1a1a2e",
      },
    },
  },
  plugins: [],
};
