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
      <PageHeader
        title="Dashboard"
        description="Welcome back, John Doe"
        actions={
          <>
            <Button variant="outline">
              <FileText className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button>
              <TrendingUp className="mr-2 h-4 w-4" />
              View Analytics
            </Button>
          </>
        }
      />

      {/* Stats Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        {[
          { title: "Total Revenue", value: "$45,231", change: "+20.1%", icon: TrendingUp, positive: true },
          { title: "Active Users", value: "2,345", change: "+12.5%", icon: User, positive: true },
          { title: "New Signups", value: "156", change: "+8.2%", icon: Zap, positive: true },
          { title: "Pending Tasks", value: "23", change: "-3.1%", icon: Clock, positive: false },
        ].map((stat) => (
          <ContentCard key={stat.title}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{stat.title}</p>
                <p className="text-2xl font-semibold mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-xl ${stat.positive ? 'bg-primary/10' : 'bg-destructive/10'}`}>
                <stat.icon className={`h-5 w-5 ${stat.positive ? 'text-primary' : 'text-destructive'}`} />
              </div>
            </div>
            <div className="mt-3 flex items-center gap-1">
              <span className={`text-sm font-medium ${stat.positive ? 'text-green-500' : 'text-red-500'}`}>
                {stat.change}
              </span>
              <span className="text-sm text-muted-foreground">from last month</span>
            </div>
          </ContentCard>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Recent Activity */}
          <ContentCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Recent Activity</h3>
              <Button variant="ghost" size="sm">View All</Button>
            </div>
            <div className="space-y-4">
              {[
                { title: "New user registered", desc: "John Smith signed up for Pro plan", time: "2 min ago", icon: User },
                { title: "Payment received", desc: "$1,299 from Enterprise client", time: "1 hour ago", icon: CheckCircle },
                { title: "Document uploaded", desc: "Q4 Financial Report.pdf", time: "3 hours ago", icon: FileText },
                { title: "Meeting scheduled", desc: "Product review with design team", time: "5 hours ago", icon: Calendar },
              ].map((activity, i) => (
                <div key={i} className="flex items-start gap-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <activity.icon className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{activity.title}</p>
                    <p className="text-sm text-muted-foreground">{activity.desc}</p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{activity.time}</span>
                </div>
              ))}
            </div>
          </ContentCard>

          {/* Quick Actions */}
          <div className="grid gap-4 md:grid-cols-2">
            <ContentCard>
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "New Project", icon: FileText },
                  { label: "Add User", icon: User },
                  { label: "Create Report", icon: Calendar },
                  { label: "Settings", icon: Settings },
                ].map((action) => (
                  <Button key={action.label} variant="outline" className="h-20 flex-col gap-2">
                    <action.icon className="h-5 w-5" />
                    <span className="text-xs">{action.label}</span>
                  </Button>
                ))}
              </div>
            </ContentCard>

            <ContentCard>
              <h3 className="text-lg font-semibold mb-4">System Status</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm">API Server</span>
                  </div>
                  <Badge variant="secondary">Operational</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm">Database</span>
                  </div>
                  <Badge variant="secondary">Operational</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-yellow-500" />
                    <span className="text-sm">Cache Layer</span>
                  </div>
                  <Badge>Degraded</Badge>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm">CDN</span>
                  </div>
                  <Badge variant="secondary">Operational</Badge>
                </div>
              </div>
            </ContentCard>
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <ContentCard>
            <h3 className="text-lg font-semibold mb-4">Analytics Overview</h3>
            <p className="text-muted-foreground">Analytics data visualization would go here.</p>
          </ContentCard>
        </TabsContent>

        <TabsContent value="reports">
          <ContentCard>
            <h3 className="text-lg font-semibold mb-4">Reports</h3>
            <p className="text-muted-foreground">Reports and exports would go here.</p>
          </ContentCard>
        </TabsContent>

        <TabsContent value="settings">
          <ContentCard>
            <h3 className="text-lg font-semibold mb-4">Settings</h3>
            <p className="text-muted-foreground">Configuration options would go here.</p>
          </ContentCard>
        </TabsContent>
      </Tabs>

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