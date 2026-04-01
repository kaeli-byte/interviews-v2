"use client";

import { useEffect, ReactNode } from "react";
import { supabase } from "@/lib/supabase";

/**
 * Auth provider that syncs Supabase session with localStorage for UI components.
 * This is used by the layout - only needs to run once.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const syncAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (session?.user) {
        const user = session.user;
        localStorage.setItem("user_id", user.id);
        localStorage.setItem("user_email", user.email || "");
        localStorage.setItem("user_name", user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'User');
        localStorage.setItem("user_avatar", user.user_metadata?.avatar_url || user.user_metadata?.picture || "");
      }
    };

    syncAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === "SIGNED_IN" && session?.user) {
        const user = session.user;
        localStorage.setItem("user_id", user.id);
        localStorage.setItem("user_email", user.email || "");
        localStorage.setItem("user_name", user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'User');
        localStorage.setItem("user_avatar", user.user_metadata?.avatar_url || user.user_metadata?.picture || "");
      } else if (event === "SIGNED_OUT") {
        localStorage.removeItem("user_id");
        localStorage.removeItem("user_email");
        localStorage.removeItem("user_name");
        localStorage.removeItem("user_avatar");
        localStorage.removeItem("auth_token");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return <>{children}</>;
}