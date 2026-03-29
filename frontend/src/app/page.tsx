import { BaseLayout, PageHeader, ContentCard } from "@/components/layouts/base-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { LiquidGlassVoiceAssistant } from "@/components/ui/lg-voice-assistant";
import {
  Home,
  User,
  Search,
  Settings,
  Bell,
  TrendingUp,
  Droplets,
  Zap,
  CheckCircle,
  Clock,
  FileText,
  Calendar
} from "lucide-react";

/**
 * Example Page using BaseLayout
 *
 * Child pages simply wrap content in <BaseLayout> and use
 * helper components like <PageHeader> and <ContentCard>
 */
export default function HomePage() {
  return (
    <BaseLayout>
      {/* Page Header - title, description, and action buttons */}
      

      {/* Voice Assistant Section */}
      <div className="mt-6">
        <ContentCard>
          <div className="flex flex-col items-center">
            <h3 className="text-lg font-semibold mb-4">Voice Assistant</h3>
            <LiquidGlassVoiceAssistant />
          </div>
        </ContentCard>
      </div>
    </BaseLayout>
  );
}