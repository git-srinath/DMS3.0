import React from "react";
const CustomParameterIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" {...props}>
    {/* Horizontal sliders */}
    <line x1="5" y1="8" x2="23" y2="8" stroke="#2563eb" strokeWidth="1.6" strokeLinecap="round" />
    <line x1="5" y1="14.7" x2="23" y2="14.7" stroke="#2563eb" strokeWidth="1.6" strokeLinecap="round" />
    <line x1="5" y1="21.4" x2="23" y2="21.4" stroke="#2563eb" strokeWidth="1.6" strokeLinecap="round" />
    {/* Slider knobs */}
    <circle cx="10" cy="8" r="2" fill="#2563eb" stroke="#224e7b" strokeWidth=".7" />
    <circle cx="19" cy="14.7" r="2" fill="#2563eb" stroke="#224e7b" strokeWidth=".7" />
    <circle cx="12.8" cy="21.4" r="2" fill="#2563eb" stroke="#224e7b" strokeWidth=".7" />
    {/* Gear at the end */}
    <g transform="translate(24,13)">
      <circle cx="4.5" cy="5.5" r="2.8" fill="#fff" stroke="#2563eb" strokeWidth="1.3" />
      <circle cx="4.5" cy="5.5" r="1.0" fill="#2563eb" />
      {/* simple notches */}
      <rect x="4.4" y="1.5" width="0.35" height="1.1" fill="#2563eb" rx="0.13" />
      <rect x="4.4" y="8.0" width="0.35" height="1.1" fill="#2563eb" rx="0.13" />
      <rect x="1.7" y="5.35" width="1.1" height="0.35" fill="#2563eb" rx="0.13" />
      <rect x="7.3" y="5.35" width="1.1" height="0.35" fill="#2563eb" rx="0.13" />
    </g>
  </svg>
);
export default CustomParameterIcon;
