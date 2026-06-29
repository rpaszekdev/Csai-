import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Mirrors vercel.json's prod redirect so the pixel app is the default page in
// dev too. Only "/" redirects — every other path still serves the React SPA.
const redirectRootToPixel = () => {
  const mw = (req, res, next) => {
    if (req.url === "/" || req.url === "/index.html") {
      res.statusCode = 302;
      res.setHeader("Location", "/pixel/");
      res.end();
      return;
    }
    next();
  };
  return {
    name: "redirect-root-to-pixel",
    configureServer: (s) => {
      s.middlewares.use(mw);
    },
    configurePreviewServer: (s) => {
      s.middlewares.use(mw);
    },
  };
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), redirectRootToPixel()],
});
