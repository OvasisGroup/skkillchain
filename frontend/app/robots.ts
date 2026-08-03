import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Auth-gated, per-user pages — nothing here is reachable without a
      // session anyway, so let crawlers skip them rather than burn budget.
      disallow: ["/dashboard", "/cart", "/wishlist", "/notifications", "/settings", "/profile"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
