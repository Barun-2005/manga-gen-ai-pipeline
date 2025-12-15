import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MangaGen.AI - Create Professional Manga with AI",
  description: "The world's fastest AI manga generator. Transform text prompts into professional manga pages.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link href="https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-[#0a110e] text-white font-[Spline_Sans] antialiased selection:bg-[#38e07b] selection:text-black" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
