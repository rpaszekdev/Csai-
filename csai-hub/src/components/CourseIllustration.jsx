const SHAPES = {
  brain: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <path
        d="M22 68 C 22 38 42 22 56 32 C 60 26 70 26 74 32 C 88 22 108 38 108 68 C 108 90 90 102 75 98 C 70 102 60 102 55 98 C 40 102 22 90 22 68 Z"
        fill={color}
        stroke="#1A1A1A"
        strokeWidth="4"
        strokeLinejoin="round"
      />
      <path d="M65 32 L65 98" stroke="#1A1A1A" strokeWidth="3.5" fill="none" />
      <path
        d="M34 52 Q 42 46 50 52"
        stroke="#1A1A1A"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M34 72 Q 42 66 50 72"
        stroke="#1A1A1A"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M80 52 Q 88 46 96 52"
        stroke="#1A1A1A"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M80 72 Q 88 66 96 72"
        stroke="#1A1A1A"
        strokeWidth="3"
        fill="none"
      />
      <rect x="58" y="98" width="14" height="14" fill="#1A1A1A" />
    </g>
  ),
  robot: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <line x1="65" y1="14" x2="65" y2="30" stroke="#1A1A1A" strokeWidth="4" />
      <circle
        cx="65"
        cy="14"
        r="6"
        fill={color}
        stroke="#1A1A1A"
        strokeWidth="3"
      />
      <rect
        x="32"
        y="30"
        width="66"
        height="54"
        rx="8"
        fill={color}
        stroke="#1A1A1A"
        strokeWidth="4"
      />
      <rect x="40" y="44" width="50" height="18" rx="3" fill="#1A1A1A" />
      <circle cx="52" cy="53" r="4" fill={color} />
      <circle cx="78" cy="53" r="4" fill={color} />
      <rect x="48" y="70" width="34" height="5" fill="#1A1A1A" />
      <rect x="44" y="88" width="42" height="20" fill="#1A1A1A" />
      <rect x="22" y="94" width="20" height="8" fill="#1A1A1A" />
      <rect x="88" y="94" width="20" height="8" fill="#1A1A1A" />
    </g>
  ),
  burst: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <circle cx="65" cy="65" r="30" fill={color} />
      <path
        d="M65 20 L65 110 M20 65 L110 65 M30 30 L100 100 M100 30 L30 100"
        stroke="#1A1A1A"
        strokeWidth="4"
      />
      <circle cx="65" cy="65" r="10" fill="#1A1A1A" />
    </g>
  ),
  stack: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <rect x="20" y="30" width="80" height="14" fill={color} />
      <rect x="30" y="54" width="80" height="14" fill="#1A1A1A" />
      <rect x="20" y="78" width="80" height="14" fill={color} />
      <rect x="30" y="102" width="50" height="14" fill="#1A1A1A" />
    </g>
  ),
  bolt: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <path d="M70 15 L35 70 L60 70 L45 115 L95 55 L70 55 Z" fill={color} />
      <circle cx="25" cy="100" r="10" fill="#1A1A1A" />
      <rect
        x="95"
        y="20"
        width="18"
        height="18"
        fill="#1A1A1A"
        transform="rotate(20 104 29)"
      />
    </g>
  ),
};

export default function CourseIllustration({ shape, color, id }) {
  const Shape = SHAPES[shape] ?? SHAPES.burst;
  const filterId = `grain-${id}`;

  return (
    <svg
      className="course-illustration"
      viewBox="0 0 130 130"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <filter id={filterId}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.9"
            numOctaves="2"
            seed="3"
          />
          <feColorMatrix
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0.55 0"
          />
          <feComposite in2="SourceGraphic" operator="in" />
          <feComposite in="SourceGraphic" operator="over" />
        </filter>
      </defs>
      <Shape color={color} id={id} />
    </svg>
  );
}
