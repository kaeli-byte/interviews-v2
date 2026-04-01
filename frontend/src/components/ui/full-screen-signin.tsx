"use client";

import { Sun } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export const FullScreenSignin = () => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState("");

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    setServerError("");
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) throw error;
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "Google sign-in failed");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center overflow-hidden p-4">
      <div className="w-full relative max-w-5xl overflow-hidden flex flex-col md:flex-row shadow-xl rounded-2xl">
        {/* Gradient overlay */}
        <div className="w-full h-full z-10 absolute bg-gradient-to-t from-transparent to-black/60 pointer-events-none"></div>

        {/* Animated bars */}
        <div className="absolute z-10 flex overflow-hidden opacity-30">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-[40rem] w-4 bg-gradient-to-r from-transparent via-foreground to-transparent"
              style={{
                animation: `slide 3s ease-in-out infinite`,
                animationDelay: `${i * 0.5}s`,
              }}
            />
          ))}
        </div>

        {/* Decorative circles */}
        <div className="w-[15rem] h-[15rem] bg-orange-500 absolute z-0 rounded-full bottom-0 blur-3xl opacity-50" />
        <div className="w-[8rem] h-[5rem] bg-white absolute z-0 rounded-full bottom-0 blur-xl opacity-20" />
        <div className="w-[8rem] h-[5rem] bg-white absolute z-0 rounded-full bottom-0 blur-xl opacity-20 right-20" />

        {/* Left side - Marketing */}
        <div className="bg-black/80 text-white p-8 md:p-12 md:w-1/2 relative rounded-t-2xl md:rounded-tr-none md:rounded-bl-2xl overflow-hidden backdrop-blur-sm">
          <h1 className="text-2xl md:text-3xl font-medium leading-tight z-10 tracking-tight relative">
            Design and dev partner for startups and founders.
          </h1>
        </div>

        {/* Right side - Sign in with Google only */}
        <div className="p-8 md:p-12 md:w-1/2 flex flex-col bg-[var(--glass-bg)] backdrop-blur-xl border-t md:border-t-0 md:border-l border-[var(--glass-border-subtle)]">
          <div className="flex flex-col items-left mb-8">
            <div className="text-orange-500 mb-4">
              <Sun className="h-10 w-10" />
            </div>
            <h2 className="text-3xl font-medium mb-2 tracking-tight text-foreground">
              Welcome Back
            </h2>
            <p className="text-left opacity-80 text-muted-foreground">
              Sign in to continue with Google
            </p>
          </div>

          <div className="flex flex-col gap-4">
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] hover:bg-[var(--glass-bg-hover)] text-foreground font-medium py-3 px-4 rounded-xl transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" className="h-5 w-5">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Continue with Google
                </>
              )}
            </button>

            {serverError && (
              <p className="text-destructive text-sm text-center">{serverError}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};