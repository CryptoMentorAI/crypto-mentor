import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0d1117",
          secondary: "#161b22",
          tertiary: "#1c2128",
        },
        border: {
          DEFAULT: "#30363d",
        },
        accent: {
          green: "#3fb950",
          red: "#f85149",
          blue: "#58a6ff",
          yellow: "#d29922",
          purple: "#bc8cff",
        },
      },
    },
  },
  plugins: [],
};

export default config;
