const SHAPES = {
  neuron: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <circle cx="60" cy="50" r="28" fill={color} />
      <circle cx="100" cy="80" r="14" fill="#1A1A1A" />
      <path d="M40 90 Q70 110 100 90" stroke={color} strokeWidth="6" fill="none" />
      <rect x="20" y="30" width="14" height="14" fill="#1A1A1A" transform="rotate(15 27 37)" />
    </g>
  ),
  orbit: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <rect x="30" y="40" width="60" height="60" fill={color} />
      <circle cx="100" cy="40" r="22" fill="#1A1A1A" />
      <circle cx="100" cy="40" r="8" fill={color} />
      <path d="M20 110 L60 70" stroke="#1A1A1A" strokeWidth="6" />
    </g>
  ),
  burst: ({ color, id }) => (
    <g filter={`url(#grain-${id})`}>
      <circle cx="65" cy="65" r="30" fill={color} />
      <path d="M65 20 L65 110 M20 65 L110 65 M30 30 L100 100 M100 30 L30 100"
        stroke="#1A1A1A" strokeWidth="4" />
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
      <rect x="95" y="20" width="18" height="18" fill="#1A1A1A" transform="rotate(20 104 29)" />
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
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" />
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
