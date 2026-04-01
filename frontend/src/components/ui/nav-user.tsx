"use client";

import React, { useEffect, useState } from "react";
import { LogOut, User, Settings } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverBody,
  PopoverHeader,
  PopoverTitle,
  PopoverDescription,
  PopoverFooter,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface NavUserData {
  name?: string;
  email?: string;
  role?: string;
  avatar?: string;
  initials?: string;
  isOnline?: boolean;
}

export interface NavUserProps {
  /**
   * User data object containing profile information
   * If not provided, will automatically fetch from Supabase
   */
  user?: NavUserData;
  /**
   * Whether the sidebar is collapsed
   */
  collapsed?: boolean;
  /**
   * Callback when logout is clicked
   */
  onLogout?: () => void;
  /**
   * Callback when profile is clicked
   */
  onProfile?: () => void;
  /**
   * Callback when settings is clicked
   */
  onSettings?: () => void;
  /**
   * Additional class names
   */
  className?: string;
}

/**
 * Navigation user component - displays user profile with popover dropdown.
 * Uses shadcn/ui Popover, Avatar patterns.
 * Automatically syncs with Supabase auth state.
 */
export function NavUser({
  user: propUser,
  collapsed = false,
  onLogout,
  onProfile,
  onSettings,
  className,
}: NavUserProps) {
  const [sessionUser, setSessionUser] = useState<NavUserData | null>(null);
  const [loading, setLoading] = useState(true);

  // Sync with Supabase auth state
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setSessionUser({
          name: session.user.user_metadata?.full_name || session.user.user_metadata?.name,
          email: session.user.email,
          avatar: session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture,
          initials: session.user.user_metadata?.initials,
        });
      } else {
        setSessionUser(null);
      }
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setSessionUser({
          name: session.user.user_metadata?.full_name || session.user.user_metadata?.name,
          email: session.user.email,
          avatar: session.user.user_metadata?.avatar_url || session.user.user_metadata?.picture,
          initials: session.user.user_metadata?.initials,
        });
      } else {
        setSessionUser(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Use prop user if provided, otherwise use session user
  const user = propUser ?? sessionUser;

  // Generate initials from name or use provided initials
  const getInitials = () => {
    if (user?.initials) return user.initials;
    if (user?.name) {
      const parts = user.name.split(" ");
      if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      }
      return user.name.slice(0, 2).toUpperCase();
    }
    return "U";
  };

  const displayName = user?.name || "Guest";
  const displayRole = user?.role || user?.email || "User";

  // Handle logout - sign out from Supabase
  const handleLogout = async () => {
    await supabase.auth.signOut();
    onLogout?.();
  };

  // Show loading while checking auth
  if (loading) {
    return (
      <div className={cn("mt-auto p-3", className)}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-muted animate-pulse" />
          {!collapsed && (
            <div className="flex-1 space-y-2">
              <div className="h-3 w-20 bg-muted rounded animate-pulse" />
              <div className="h-2 w-28 bg-muted rounded animate-pulse" />
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show sign in prompt if not logged in
  if (!user) {
    return (
      <div className={cn("mt-auto", className)}>
        <Button
          asChild
          className="w-full"
          variant={collapsed ? "ghost" : "default"}
          size={collapsed ? "sm" : "default"}
        >
          <a href="/signin">Sign In</a>
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("mt-auto", className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            className={cn(
              "h-auto w-full rounded-none px-0 py-0 hover:bg-transparent",
              collapsed ? "w-10" : "w-full"
            )}
          >
            {!collapsed ? (
              // Expanded: Show full profile as trigger
              <div className="flex w-full items-center px-3 py-2 rounded-xl bg-[var(--glass-bg)] hover:bg-[var(--glass-bg-hover)] transition-colors duration-200 border border-[var(--glass-border-subtle)]">
                <Avatar size="default">
                  {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                  <AvatarFallback>{getInitials()}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0 ml-2.5">
                  <p className="text-sm font-medium text-foreground truncate">
                    {displayName}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {displayRole}
                  </p>
                </div>
                {user?.isOnline !== false && (
                  <div className="w-2 h-2 bg-green-500 rounded-full ml-2" />
                )}
              </div>
            ) : (
              // Collapsed: Show avatar only
              <div className="flex justify-center">
                <Avatar size="default">
                  {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                  <AvatarFallback>{getInitials()}</AvatarFallback>
                </Avatar>
              </div>
            )}
          </Button>
        </PopoverTrigger>

        <PopoverContent
          className="w-72 p-0 bg-[var(--glass-bg)] border border-[var(--glass-border-subtle)] shadow-[var(--glass-shadow)] backdrop-blur-xl"
          align="start"
          side="right"
          sideOffset={8}
          style={{ background: 'var(--glass-bg)', backdropFilter: 'blur(20px)' }}
        >
          <div className="p-4 border-b border-[var(--glass-border-subtle)]">
            <div className="flex items-center space-x-3">
              <Avatar className="h-10 w-10">
                {user?.avatar && <AvatarImage src={user.avatar} alt={displayName} />}
                <AvatarFallback className="bg-primary/10 text-primary">{getInitials()}</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium text-foreground">{displayName}</p>
                <p className="text-xs text-muted-foreground">
                  {user?.email || displayRole}
                </p>
              </div>
            </div>
          </div>
          <div className="p-2 space-y-1">
            <Button
              variant="ghost"
              className="w-full justify-start text-muted-foreground hover:text-foreground hover:bg-[var(--glass-bg-hover)]"
              size="sm"
              onClick={onProfile}
            >
              <User className="mr-2 h-4 w-4" />
              View Profile
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start text-muted-foreground hover:text-foreground hover:bg-[var(--glass-bg-hover)]"
              size="sm"
              onClick={onSettings}
            >
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Button>
          </div>
          <div className="p-2 pt-0">
            <Button
              variant="outline"
              className="w-full bg-transparent border-[var(--glass-border-subtle)] text-muted-foreground hover:text-destructive hover:border-destructive/50 hover:bg-destructive/10"
              size="sm"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}