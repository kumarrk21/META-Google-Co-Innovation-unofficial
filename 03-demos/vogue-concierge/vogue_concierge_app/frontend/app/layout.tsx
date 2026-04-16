import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: 'Vogue Concierge — AI Boutique | META × Google Better Together',
  description: 'Your elite AI fashion advisor. Powered by Meta Llama 4 Scout, Google ADK, MCP Toolbox, and Vertex AI.',
  
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/* <body className="min-h-full flex flex-col">{children}</body> */}
      <body>{children}</body>
    </html>
  );
}
