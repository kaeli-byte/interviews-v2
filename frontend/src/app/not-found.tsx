"use client";

import Link from "next/link";
import { Home, ArrowLeft, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div
        className="w-full max-w-lg rounded-2xl border border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-xl backdrop-saturate-150 shadow-[var(--glass-shadow),var(--glass-shadow-inset)] p-8 text-center"
      >
        {/* 404 Number */}
        <div className="mb-6">
          <span className="text-8xl font-bold text-primary/20">404</span>
        </div>

        {/* Icon */}
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-primary/10 flex items-center justify-center">
          <Search className="w-8 h-8 text-primary" />
        </div>

        {/* Text */}
        <h1 className="text-2xl font-semibold text-foreground mb-2">
          Page Not Found
        </h1>
        <p className="text-muted-foreground mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild variant="default">
            <Link href="/">
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="javascript:history.back()">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
