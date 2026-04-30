export const PROGRAM = [
  {
    year: 1,
    semesters: [
      { number: 1, courses: [] },
      { number: 2, courses: [] },
    ],
  },
  {
    year: 2,
    semesters: [
      { number: 3, courses: [] },
      {
        number: 4,
        courses: [
          {
            id: "cog-neuro",
            name: "Cognitive Neuroscience",
            icon: "\u{1F9E0}",
            color: "#FF5BAA",
            shape: "neuron",
            exams: [
              {
                type: "Midterm",
                format: "Digital",
                weight: "40%",
                min: "None",
                date: "31 Mar",
              },
              {
                type: "Final",
                format: "Digital",
                weight: "40%",
                min: "None",
                date: "28 May",
              },
              {
                type: "Resit",
                format: "Digital",
                weight: "80%",
                min: "None",
                date: "23 Jun",
              },
            ],
            resources: [
              { label: "Roadmap", href: "/courses/cog-neuro/roadmap" },
              { label: "Lessons", href: "/courses/cog-neuro/notes" },
              { label: "Quizzes", href: "/courses/cog-neuro/quiz" },
              { label: "Brain Quiz", href: "/courses/cog-neuro/brain-quiz" },
            ],
          },
          {
            id: "auto-sys",
            name: "Autonomous Systems",
            icon: "\u{1F916}",
            color: "#2D5BFF",
            shape: "orbit",
            exams: [
              {
                type: "Final",
                format: "Digital",
                weight: "60%",
                min: "5.5",
                date: "5 Jun",
              },
            ],
            resources: [
              {
                label: "L01 — Intro & Logistics",
                href: "/auto-sys/lecture-01.html",
              },
              {
                label: "L02 — Sensors & Braitenberg",
                href: "/auto-sys/lecture-02.html",
              },
              {
                label: "L03 — Controllers (Brains)",
                href: "/auto-sys/lecture-03.html",
              },
              { label: "L04 — Embodiment", href: "/auto-sys/lecture-04.html" },
              {
                label: "L05 — Reinforcement Learning",
                href: "/auto-sys/lecture-05.html",
              },
              {
                label: "L06 — Unsupervised Learning",
                href: "/auto-sys/lecture-06.html",
              },
              { label: "L07 — Multimodal", href: "/auto-sys/lecture-07.html" },
              {
                label: "L08 — Affective & Social HRI",
                href: "/auto-sys/lecture-08.html",
              },
              {
                label: "L09 — Cognitive Robotics",
                href: "/auto-sys/lecture-09.html",
              },
              {
                label: "L10 — Simulation Environments",
                href: "/auto-sys/lecture-10.html",
              },
              { label: "L11 — Exam Review", href: "/auto-sys/lecture-11.html" },
            ],
          },
          {
            id: "research",
            name: "Research Workshop",
            icon: "\u{1F52C}",
            color: "#F5C518",
            shape: "burst",
            exams: [],
            resources: [{ label: "Project", href: "#" }],
          },
          {
            id: "deep-learn",
            name: "Introduction to Deep Learning",
            icon: "\u{1F525}",
            color: "#FF4521",
            shape: "stack",
            exams: [
              {
                type: "Final",
                format: "Digital",
                weight: "70%",
                min: "5.5",
                date: "3 Jun",
              },
            ],
            resources: [
              { label: "Lesson 1: MLPs", href: "/lesson.html" },
              { label: "Lesson 2: Backprop", href: "/lesson2.html" },
              { label: "Lesson 3: Optimizers", href: "/lesson3.html" },
              { label: "Lesson 4: CNNs", href: "/lesson4.html" },
              { label: "Lesson 5: Regularization", href: "/lesson5.html" },
              { label: "Lesson 6: Recurrence", href: "/lesson6.html" },
              { label: "Lesson 7: Transformers", href: "/lesson7.html" },
              { label: "Lesson 8: Computer Vision", href: "/lesson8.html" },
            ],
          },
          {
            id: "adv-prog",
            name: "Advanced Programming for CSAI",
            icon: "\u{26A1}",
            color: "#7C3AED",
            shape: "bolt",
            exams: [
              {
                type: "Final",
                format: "Digital",
                weight: "80%",
                min: "5.5",
                date: "28 May",
              },
            ],
            resources: [
              { label: "Lessons", href: "#" },
              { label: "Q&A (RAG)", href: "#" },
            ],
          },
        ],
      },
    ],
  },
  {
    year: 3,
    semesters: [
      { number: 5, courses: [] },
      { number: 6, courses: [] },
    ],
  },
];

export const ALL_EXAMS = PROGRAM.flatMap((y) =>
  y.semesters.flatMap((s) =>
    s.courses.flatMap((c) => c.exams.map((e) => ({ course: c.name, ...e }))),
  ),
);
