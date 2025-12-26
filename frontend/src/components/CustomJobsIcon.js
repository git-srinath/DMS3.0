import React from "react";

const CustomJobsIcon = ({ size = 18, ...props }) => {
  // The icon represents: Document -> Gear (Process) -> Database
  // Based on the flat-design icon: document with purple fill, golden gear, purple database stack
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 36 36" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      {...props}
    >
      {/* Document (left side) */}
      <path
        d="M6 4h10v16H6V4z"
        fill="#e9d5ff"
        stroke="#1f2937"
        strokeWidth="0.9"
      />
      {/* Document fold corner */}
      <path
        d="M14 4l2 2h-2V4z"
        fill="#ddd6fe"
        stroke="#1f2937"
        strokeWidth="0.9"
      />
      {/* Document lines (text) */}
      <line x1="8" y1="7" x2="12" y2="7" stroke="#1f2937" strokeWidth="0.8" />
      <line x1="8" y1="9.5" x2="12" y2="9.5" stroke="#1f2937" strokeWidth="0.8" />
      <line x1="8" y1="12" x2="12" y2="12" stroke="#1f2937" strokeWidth="0.8" />
      <line x1="8" y1="14.5" x2="11" y2="14.5" stroke="#1f2937" strokeWidth="0.8" />

      {/* Gear/Cogwheel (center) */}
      <g transform="translate(18, 12)">
        {/* Outer gear teeth */}
        <circle cx="0" cy="0" r="7" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.9" />
        {/* Center circle */}
        <circle cx="0" cy="0" r="3.5" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.7" />
        {/* Gear teeth (top, bottom, left, right) */}
        <rect x="-1" y="-9" width="2" height="3" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" />
        <rect x="-1" y="6" width="2" height="3" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" />
        <rect x="-9" y="-1" width="3" height="2" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" />
        <rect x="6" y="-1" width="3" height="2" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" />
        {/* Diagonal teeth */}
        <rect x="5" y="-5" width="2" height="2.5" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" transform="rotate(45 6 -3.75)" />
        <rect x="-7" y="-5" width="2" height="2.5" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" transform="rotate(-45 -6 -3.75)" />
        <rect x="5" y="3" width="2" height="2.5" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" transform="rotate(-45 6 4.25)" />
        <rect x="-7" y="3" width="2" height="2.5" fill="#fbbf24" stroke="#1f2937" strokeWidth="0.5" transform="rotate(45 -6 4.25)" />
      </g>

      {/* Database stack (right side) */}
      <g transform="translate(26, 12)">
        {/* Top cylinder */}
        <ellipse cx="0" cy="0" rx="4.5" ry="2" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <rect x="-4.5" y="0" width="9" height="4" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <ellipse cx="0" cy="4" rx="4.5" ry="2" fill="#c084fc" stroke="#1f2937" strokeWidth="0.9" />
        {/* Middle cylinder */}
        <ellipse cx="0" cy="6" rx="4.5" ry="2" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <rect x="-4.5" y="6" width="9" height="4" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <ellipse cx="0" cy="10" rx="4.5" ry="2" fill="#c084fc" stroke="#1f2937" strokeWidth="0.9" />
        {/* Bottom cylinder */}
        <ellipse cx="0" cy="12" rx="4.5" ry="2" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <rect x="-4.5" y="12" width="9" height="4" fill="#e9d5ff" stroke="#1f2937" strokeWidth="0.9" />
        <ellipse cx="0" cy="16" rx="4.5" ry="2" fill="#c084fc" stroke="#1f2937" strokeWidth="0.9" />
        {/* Horizontal lines on cylinders */}
        <line x1="-3" y1="2" x2="3" y2="2" stroke="#c084fc" strokeWidth="0.6" />
        <line x1="-3" y1="8" x2="3" y2="8" stroke="#c084fc" strokeWidth="0.6" />
        <line x1="-3" y1="14" x2="3" y2="14" stroke="#c084fc" strokeWidth="0.6" />
      </g>
    </svg>
  );
};

export default CustomJobsIcon;

