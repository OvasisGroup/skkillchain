import type { Metadata } from "next";
import { CookieConsentBanner } from "@/components/CookieConsentBanner";
import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth/AuthContext";
import { CartProvider } from "@/lib/cart/CartContext";
import {
  SITE_DESCRIPTION,
  SITE_KEYWORDS,
  SITE_NAME,
  SITE_URL,
  organizationJsonLd,
  safeJsonLd,
  websiteJsonLd,
} from "@/lib/seo";
import { ThemeProvider } from "@/lib/theme/ThemeContext";
import { WishlistProvider } from "@/lib/wishlist/WishlistContext";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} — Learn without limits`,
    template: `%s — ${SITE_NAME}`,
  },
  description: SITE_DESCRIPTION,
  keywords: SITE_KEYWORDS,
  alternates: {
    canonical: "/",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
    },
  },
  openGraph: {
    type: "website",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: `${SITE_NAME} — Learn without limits`,
    description: SITE_DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE_NAME} — Learn without limits`,
    description: SITE_DESCRIPTION,
  },
};

// Two separate script tags rather than one array — some third-party
// parsers (wallet-extension dapp detection, link-preview bots) assume a
// single JSON object per <script type="application/ld+json"> and break
// on an array root.
const JSON_LD_ENTRIES = [organizationJsonLd(), websiteJsonLd()];

const NO_FLASH_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("skillchain.theme");
    var theme = stored === "light" || stored === "dark" ? stored : "dark";
    document.documentElement.classList.toggle("dark", theme === "dark");
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: NO_FLASH_SCRIPT }} />
        {JSON_LD_ENTRIES.map((entry) => (
          <script
            key={entry["@type"]}
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: safeJsonLd(entry) }}
          />
        ))}
      </head>
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <ThemeProvider>
          <AuthProvider>
            <WishlistProvider>
              <CartProvider>
                <Navbar />
                <main className="flex-1">{children}</main>
                <Footer />
                <CookieConsentBanner />
              </CartProvider>
            </WishlistProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
