"use client";

import Script from "next/script";
import { useEffect, useRef, useState } from "react";
import { useTheme } from "@/lib/theme/ThemeContext";

interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleIdentityServices {
  accounts: {
    id: {
      initialize(config: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
      }): void;
      renderButton(
        parent: HTMLElement,
        options: {
          type: "standard";
          theme: "outline" | "filled_black";
          size: "large";
          text: "continue_with";
          shape: "pill";
          width: string;
        }
      ): void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentityServices;
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export function GoogleSignInButton({
  onToken,
  onError,
}: {
  onToken: (idToken: string) => void;
  onError: (message: string) => void;
}) {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [width, setWidth] = useState(384);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) {
        setWidth(Math.min(384, Math.floor(entry.contentRect.width)));
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!scriptReady || !containerRef.current) return;
    if (!window.google) return;
    if (!CLIENT_ID) {
      onError("Google sign-in is not configured.");
      return;
    }

    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: (response) => onToken(response.credential),
    });
    containerRef.current.innerHTML = "";
    window.google.accounts.id.renderButton(containerRef.current, {
      type: "standard",
      theme: theme === "dark" ? "filled_black" : "outline",
      size: "large",
      text: "continue_with",
      shape: "pill",
      width: String(width),
    });
    // onToken/onError are recreated every render by the caller; re-running
    // this on their identity change would just re-render an identical
    // button, so only script readiness, theme, and measured width (which
    // change the button's actual appearance) are real dependencies.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptReady, theme, width]);

  if (!CLIENT_ID) return null;

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={() => setScriptReady(true)}
      />
      <div ref={containerRef} className="flex justify-center" />
    </>
  );
}
