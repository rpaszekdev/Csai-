# CSAI Hub

A study companion for the Cognitive Science & AI programme at Tilburg University. Built with React + Vite, deployed on Vercel.

Courses covered: Cognitive Neuroscience, Autonomous Systems, Deep Learning, and more.

---

## Contributing

Everyone is welcome to contribute — whether you're a fellow CSAI student, alumni, or just someone who wants to help improve the materials.

### Getting started

```bash
cd csai-hub
npm install
npm run dev
```

### How to contribute

1. Fork the repo
2. Create a branch (`git checkout -b feature/your-thing`)
3. Make your changes
4. Open a pull request with a short description of what you did

---

## Style Guide

### Visual identity

- **Palette**: cream paper `#F2EDE0`, ink `#1A1A1A`, rust accent `#A84F2A`
- **Typography**: JetBrains Mono (primary), IBM Plex Mono (fallback) — monospace throughout
- **Aesthetic**: brutalist editorial — clean, dense, no rounded corners or gradients

### Lecture pages

Lecture content lives as static HTML in `public/`. Each course has its own subfolder (`public/cog-neuro/`, `public/auto-sys/`, etc.).

Every lecture page follows this structure:

- **Hero block** with outlined number, eyebrow, title, and tool buttons
- **Chip strip** linking sibling lectures
- **Sections** with numbered headings, body text left, slide thumbnails right
- **Hand-drawn ink dividers** between sections (SVG, stretched)
- **Callouts** with `[Prof]` or `[Exam]` badges for emphasis

### Code style

- No emojis in code or copy
- Small, focused files (under 400 lines)
- Functional components with hooks
- Immutable data patterns — never mutate state directly
- Meaningful variable names over comments

### Dos and Don'ts

| Do | Don't |
|---|---|
| Keep lecture pages as static HTML | Convert working static pages to React |
| Reuse shared assets (`lightbox.js`, `annotations.js`, SVGs) | Duplicate utilities per course |
| Follow the cog-neuro template for new courses | Invent new layout systems |
| Test locally before opening a PR | Push directly to main |

---

## Project structure

```
csai-hub/
├── public/          # Static lecture pages, assets, shared scripts
│   ├── auto-sys/    # Autonomous Systems lectures + quizzes
│   ├── cog-neuro/   # Cognitive Neuroscience lectures (canonical template)
│   ├── deep-learning/
│   └── shared/      # Lightbox, annotations, common JS/CSS
├── src/             # React app (landing page, quizzes, routing)
│   ├── components/
│   ├── courses/
│   ├── data/
│   └── routes/
└── _legacy/         # Archived Python study tools (not deployed)
```

---

## License

Open for educational use. If you use this as a base for your own programme's hub, a mention is appreciated.
