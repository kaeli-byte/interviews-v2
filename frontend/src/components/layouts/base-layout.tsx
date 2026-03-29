"use client";

import React, { useState, useEffect } from 'react';
import { cn } from "@/lib/utils";
import { Sidebar } from "@/components/ui/modern-side-bar";
import { Menu, X, Bell, Search, User } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/**
 * BaseLayout - Production-ready master template for all pages
 *
 * Responsive Breakpoints:
 * - Mobile: < 768px (sidebar hidden, hamburger toggle)
 * - Tablet: 768px - 1199px (collapsible sidebar)
 * - Desktop: 1200px+ (persistent sidebar)
 *
 * Layout Zones:
 * - Header: Top navigation bar (full width)
 * - Sidebar: Left navigation (collapsible)
 * - Main: Content area (fluid width)
 * - Footer: Optional bottom section
 *
 * Child pages extend via props or by wrapping this component
 */

interface BaseLayoutProps {
  /** Main content area - pass page content here */
  children: React.ReactNode;
  /** Optional header content - defaults to search + user profile */
  headerContent?: React.ReactNode;
  /** Sidebar content - uses default if not provided */
  sidebarContent?: React.ReactNode;
  /** Hide default header */
  hideHeader?: boolean;
  /** Hide default sidebar */
  hideSidebar?: boolean;
  /** Additional wrapper classes */
  className?: string;
}

/**
 * Default header content - customizable via headerContent prop
 */
function DefaultHeader({ onMenuToggle }: { onMenuToggle: () => void }) {
  return (
    <header className="h-16 flex items-center justify-between px-4 md:px-6 border-b border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] backdrop-blur-xl">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onMenuToggle}
        aria-label="Toggle navigation menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Logo / Brand - visible on mobile */}
      <div className="flex items-center gap-3 md:hidden">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-primary-foreground font-bold">A</span>
        </div>
        <span className="font-semibold text-foreground">Acme Corp</span>
      </div>

      
    </header>
  );
}

/**
 * Main Layout Component
 *
 * Usage:
 * ```tsx
 * <BaseLayout>
 *   <YourPageContent />
 * </BaseLayout>
 * ```
 *
 * Or with custom header:
 * ```tsx
 * <BaseLayout headerContent={<CustomHeader />}>
 *   <YourPageContent />
 * </BaseLayout>
 * ```
 */
export function BaseLayout({
  children,
  headerContent,
  sidebarContent,
  hideHeader = true,
  hideSidebar = false,
  className
}: BaseLayoutProps) {
  // Sidebar state - managed internally but can be controlled externally
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Track viewport size for responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      const tablet = window.innerWidth >= 768 && window.innerWidth < 1200;

      setIsMobile(mobile);

      // Auto-collapse sidebar on tablet, hide on mobile
      if (tablet) {
        setIsSidebarCollapsed(true);
      } else if (!mobile) {
        setIsSidebarCollapsed(false);
      }

      // Close mobile sidebar on resize to desktop
      if (!mobile && isSidebarOpen) {
        setIsSidebarOpen(false);
      }
    };

    // Initial check
    handleResize();

    // Listen for changes
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isSidebarOpen]);

  // Toggle sidebar (mobile: slide in/out, tablet/desktop: collapse)
  const toggleSidebar = () => {
    if (isMobile) {
      setIsSidebarOpen(!isSidebarOpen);
    } else {
      setIsSidebarCollapsed(!isSidebarCollapsed);
    }
  };

  // Close mobile sidebar
  const closeMobileSidebar = () => {
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  };

  return (
    <div className={cn("min-h-screen flex flex-col", className)}>
      {/* Header Zone - spans full width above sidebar and content */}
      {!hideHeader && (
        headerContent || <DefaultHeader onMenuToggle={toggleSidebar} />
      )}

      {/* Main Container - flex row for desktop */}
      <div className="flex flex-1 relative">
        {/* Sidebar Zone */}
        {!hideSidebar && (
          <>
            {/* Mobile overlay backdrop */}
            {isMobile && isSidebarOpen && (
              <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
                onClick={closeMobileSidebar}
                aria-hidden="true"
              />
            )}

            {/* Sidebar wrapper - positioned fixed on mobile, static on desktop */}
            <div
              className={cn(
                // Mobile: fixed overlay
                "md:relative md:translate-x-0 z-50",
                isMobile && isSidebarOpen ? "fixed inset-y-0 left-0" : isMobile ? "fixed -translate-x-full" : "",
                // Transition for smooth animations
                "transition-all duration-300 ease-in-out"
              )}
            >
              {sidebarContent || (
                <Sidebar
                  collapsed={isSidebarCollapsed}
                  onCollapsedChange={setIsSidebarCollapsed}
                  className={cn(
                    // Adjust margin based on collapsed state (desktop only)
                    !isMobile && (isSidebarCollapsed ? "md:w-28" : "md:w-72")
                  )}
                />
              )}
            </div>
          </>
        )}

        {/* Main Content Zone - fluid width, adjusts for sidebar */}
        <main
          className={cn(
            "flex-1 min-h-0 transition-all duration-300",
            // Content margin/padding based on sidebar state
            !hideSidebar && !isMobile && (isSidebarCollapsed ? "md:ml-28" : "md:ml-0"),
            // Full width on mobile when sidebar is hidden
            isMobile && "w-full"
          )}
        >
          {/* Content wrapper with padding */}
          <div className="p-4 md:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>

      {/* Footer Zone - optional, uncomment if needed */}
      {/* <footer className="border-t border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] p-4"> */}
      {/*   Footer content */}
      {/* </footer> */}
    </div>
  );
}

/**
 * PageHeader - Helper component for page titles
 *
 * Usage:
 * ```tsx
 * <BaseLayout>
 *   <PageHeader
 *     title="Dashboard"
 *     description="Welcome back, John"
 *     actions={<Button>New Action</Button>}
 *   />
 * </BaseLayout>
 * ```
 */
interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6", className)}>
      <div>
        <h1 className="text-2xl md:text-3xl font-semibold text-foreground tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}

/**
 * ContentCard - Helper for consistent card styling in content areas
 */
interface ContentCardProps {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export function ContentCard({ children, className, noPadding = false }: ContentCardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-[var(--glass-border-subtle)] bg-[var(--glass-bg)] backdrop-blur-xl",
        "shadow-[var(--glass-shadow),var(--glass-shadow-inset)]",
        !noPadding && "p-6",
        className
      )}
    >
      {children}
    </div>
  );
}

// Re-export Sidebar for direct access if needed
export { Sidebar };