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
      width: "384",
    });
    // onToken/onError are recreated every render by the caller; re-running
    // this on their identity change would just re-render an identical
    // button, so only script readiness and theme (which changes the
    // button's actual appearance) are real dependencies.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptReady, theme]);

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
