import { ImageResponse } from "next/og";

export const alt = "SkillChain — Learn without limits";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#050f0c",
          backgroundImage: "linear-gradient(135deg, #050f0c 0%, #0b1f19 55%, #0d2a22 100%)",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            height: 96,
            width: 96,
            alignItems: "center",
            justifyContent: "center",
            borderRadius: 24,
            backgroundColor: "#2dd4bf",
            marginBottom: 40,
          }}
        >
          <span style={{ fontSize: 48, fontWeight: 700, color: "#022c22" }}>{"</>"}</span>
        </div>
        <div style={{ display: "flex", fontSize: 88, fontWeight: 700, color: "#f2fbf7", letterSpacing: -2 }}>
          SkillChain
        </div>
        <div style={{ display: "flex", marginTop: 20, fontSize: 32, color: "#9db8ab" }}>
          Learn without limits — blockchain & AI education
        </div>
      </div>
    ),
    { ...size }
  );
}
