import React from "react";
const CustomDbIcon = ({ size = 22, ...props }) => (
  <svg width={size} height={size} viewBox="0 0 36 36" fill="none" {...props}>
    {/* Stacked DB layers */}
    <ellipse cx="23" cy="7" rx="11.3" ry="4.3" fill="#7dd3fc" stroke="#4b5563" strokeWidth=".9" />
    <ellipse cx="23" cy="14.2" rx="11.3" ry="4.3" fill="#fde68a" stroke="#4b5563" strokeWidth=".9" />
    <ellipse cx="23" cy="21.4" rx="11.3" ry="4.3" fill="#7dd3fc" stroke="#4b5563" strokeWidth=".9" />
    <ellipse cx="23" cy="28.6" rx="11.3" ry="4.3" fill="#fde68a" stroke="#4b5563" strokeWidth=".9" />
    {/* Connectors */}
    <rect x="8.4" y="6.3" width="6.8" height="1" fill="#555" />
    <rect x="8.4" y="13.5" width="6.8" height="1" fill="#555" />
    <rect x="8.4" y="20.7" width="6.8" height="1" fill="#555" />
    <rect x="8.4" y="27.9" width="6.8" height="1" fill="#555" />
    {/* Node circles */}
    {[7, 14.2, 21.4, 28.6].map((y, i) => (
      <ellipse key={i} cx="10.5" cy={y} rx="2.1" ry="2.1" fill="#dbeafe" stroke="#4b5563" strokeWidth=".7" />
    ))}
    {/* Stack dots */}
    <circle cx="29" cy="7.5" r=".7" fill="#222" />
    <circle cx="31.3" cy="7.5" r=".7" fill="#222" />
    <circle cx="29" cy="14.7" r=".7" fill="#444" />
    <circle cx="31.3" cy="14.7" r=".7" fill="#444" />
  </svg>
);
export default CustomDbIcon;
