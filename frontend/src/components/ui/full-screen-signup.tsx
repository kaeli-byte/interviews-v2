"use client";

import { Sun } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

export const FullScreenSignup = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState("");

  const validateEmail = (value: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  };

  const validatePassword = (value: string) => {
    return value.length >= 8;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError("");
    let valid = true;

    if (!validateEmail(email)) {
      setEmailError("Please enter a valid email address.");
      valid = false;
    } else {
      setEmailError("");
    }

    if (!validatePassword(password)) {
      setPasswordError("Password must be at least 8 characters.");
      valid = false;
    } else {
      setPasswordError("");
    }

    if (!valid) return;

    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Signup failed");
      }

      // Store token
      localStorage.setItem("auth_token", data.token);
      localStorage.setItem("user_email", data.user.email);
      localStorage.setItem("user_id", data.user.id);

      // Redirect to home
      router.push("/");
      router.refresh();
    } catch (err: unknown) {
      setServerError(err instanceof Error ? err.message : "Signup failed");
    } finally {
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

        {/* Right side - Form */}
        <div className="p-8 md:p-12 md:w-1/2 flex flex-col bg-[var(--glass-bg)] backdrop-blur-xl border-t md:border-t-0 md:border-l border-[var(--glass-border-subtle)]">
          <div className="flex flex-col items-left mb-8">
            <div className="text-orange-500 mb-4">
              <Sun className="h-10 w-10" />
            </div>
            <h2 className="text-3xl font-medium mb-2 tracking-tight text-foreground">
              Get Started
            </h2>
            <p className="text-left opacity-80 text-muted-foreground">
              Welcome — Let's get started
            </p>
          </div>

          <form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit}
            noValidate
          >
            <div>
              <label htmlFor="email" className="block text-sm mb-2 text-foreground">
                Your email
              </label>
              <input
                type="email"
                id="email"
                placeholder="hi@example.com"
                className={cn(
                  "text-sm w-full py-2.5 px-4 border rounded-xl focus:outline-none focus:ring-2 bg-[var(--glass-bg)] text-foreground placeholder:text-muted-foreground focus:ring-primary",
                  emailError ? "border-destructive" : "border-[var(--glass-border-subtle)]"
                )}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={!!emailError}
                aria-describedby="email-error"
              />
              {emailError && (
                <p id="email-error" className="text-destructive text-xs mt-1">
                  {emailError}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm mb-2 text-foreground">
                Create new password
              </label>
              <input
                type="password"
                id="password"
                className={cn(
                  "text-sm w-full py-2.5 px-4 border rounded-xl focus:outline-none focus:ring-2 bg-[var(--glass-bg)] text-foreground placeholder:text-muted-foreground focus:ring-primary",
                  passwordError ? "border-destructive" : "border-[var(--glass-border-subtle)]"
                )}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!passwordError}
                aria-describedby="password-error"
              />
              {passwordError && (
                <p id="password-error" className="text-destructive text-xs mt-1">
                  {passwordError}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-orange-300 text-white font-medium py-3 px-4 rounded-xl transition-all hover:scale-[1.02] active:scale-[0.98] disabled:hover:scale-100"
            >
              {isLoading ? "Creating account..." : "Create a new account"}
            </button>

            {serverError && (
              <p className="text-destructive text-sm text-center">{serverError}</p>
            )}

            <div className="text-center text-muted-foreground text-sm">
              Already have account?{" "}
              <a href="/signin" className="text-foreground font-medium underline">
                Login
              </a>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};