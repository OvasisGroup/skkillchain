"use client";

import { useEffect, useRef, type ComponentPropsWithoutRef } from "react";
import { gsap } from "@/lib/gsap";

type RevealProps = ComponentPropsWithoutRef<"div"> & {
  /** Distance (px) the element travels in from as it reveals. */
  y?: number;
  duration?: number;
  delay?: number;
  /** Set to animate direct children in sequence instead of the wrapper itself (e.g. a card grid). */
  stagger?: number;
  /** ScrollTrigger `start` position. */
  start?: string;
};

export function Reveal({
  y = 24,
  duration = 0.6,
  delay = 0,
  stagger,
  start = "top 85%",
  children,
  ...props
}: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const targets = stagger ? el.children : el;

    const ctx = gsap.context(() => {
      // Card components use Tailwind's `transition-all` for their hover
      // effects, which also covers opacity/transform — left alone, that CSS
      // transition fights GSAP's own per-frame writes to the same
      // properties and the reveal never visibly reaches its end state.
      // Suspending it for the reveal's duration and clearing every inline
      // style GSAP touched (including its own opacity/transform) once done
      // hands the element back to Tailwind's classes — otherwise the
      // leftover inline transform would permanently block hover effects
      // like `hover:-translate-y-0.5`.
      gsap.set(targets, { transition: "none" });
      gsap.from(targets, {
        opacity: 0,
        y,
        duration,
        delay,
        stagger,
        ease: "power2.out",
        clearProps: "transition,transform,opacity",
        scrollTrigger: { trigger: el, start, once: true },
      });
    }, el);

    return () => ctx.revert();
  }, [y, duration, delay, stagger, start]);

  return (
    <div ref={ref} {...props}>
      {children}
    </div>
  );
}
