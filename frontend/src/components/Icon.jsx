import React from "react";

const icons = {
  home: "M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3V10.5Z",
  upload: "M12 3v12m0-12 5 5m-5-5-5 5M4 17v4h16v-4",
  video: "M4 6h11v12H4V6Zm11 4 5-3v10l-5-3v-4Z",
  chat: "M4 5h16v11H8l-4 4V5Z",
  history: "M4 12a8 8 0 1 0 2.35-5.65M4 4v6h6M12 8v5l4 2",
  file: "M6 3h8l4 4v14H6V3Zm8 0v5h4",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9a7 7 0 0 1 14 0",
  settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-5v3m0 12v3M4.6 4.6l2.1 2.1m10.6 10.6 2.1 2.1M3 12h3m12 0h3M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1",
  logout: "M10 17l5-5-5-5M15 12H3M21 3v18h-8",
  send: "M3 11l18-8-8 18-2-7-8-3Z",
  trash: "M4 7h16M9 7V4h6v3m-8 0 1 14h8l1-14",
  youtube: "M3 8s0-3 3-3h12s3 0 3 3v8s0 3-3 3H6s-3 0-3-3V8Zm8 1v6l5-3-5-3Z",
  link: "M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1M14 11a5 5 0 0 0-7.1 0l-2 2A5 5 0 0 0 12 20.1l1.1-1.1",
  spinner: "M12 3a9 9 0 1 0 9 9",
  cloud: "M7 18h10a4 4 0 0 0 0-8 6 6 0 0 0-11.6 2A3 3 0 0 0 7 18Zm5-9v7m0-7 3 3m-3-3-3 3"
};

export default function Icon({ name, size = 20, className = "" }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={icons[name] || icons.file} />
    </svg>
  );
}
