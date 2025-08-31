import "./globals.css";
import { Inter } from "next/font/google";
import { Figtree } from "next/font/google";
import TabClearClientEffect from "@/components/TabClearClientEffect";

const figtree = Figtree({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-figtree",
});

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Sustainability Report Generator",
  description: "Your description",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
          rel="stylesheet"
        />
        <link rel="icon" href="/truck-icon.svg" type="image/svg+xml" />
      </head>
      <body className={inter.className}>
        {children}
        </body>
    </html>
  );
}
