'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { Label } from '@/app/components/ui/label'
import { Switch } from '@/app/components/ui/switch'
import ProtectedRoute from '@/app/components/ProtectedRoute'
import { useAuth } from '@/app/contexts/AuthContextStable'

export default function SettingsPage() {
  const { user, userTeamData } = useAuth()

  return (
    <ProtectedRoute>
      <div className="flex-1 p-8 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-foreground mb-8">
          Settings
        </h1>

        {/* Profile Settings */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>
              Manage your profile information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={user?.email || ''}
                disabled
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="team">Team</Label>
              <Input
                id="team"
                value={userTeamData?.team_name || ''}
                disabled
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={userTeamData?.role || ''}
                disabled
                className="mt-1"
              />
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
            <CardDescription>
              Customize your chat experience
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="notifications">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">Receive email updates about important messages</p>
              </div>
              <Switch id="notifications" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="sound">Sound Effects</Label>
                <p className="text-sm text-muted-foreground">Play sounds for new messages</p>
              </div>
              <Switch id="sound" />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="theme">Dark Mode</Label>
                <p className="text-sm text-muted-foreground">Use dark theme</p>
              </div>
              <Switch id="theme" />
            </div>
          </CardContent>
        </Card>

        {/* API Access */}
        <Card>
          <CardHeader>
            <CardTitle>API Access</CardTitle>
            <CardDescription>
              Manage your API keys for programmatic access
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              API keys allow you to access the chat system programmatically.
            </p>
            <Button variant="outline">
              Generate API Key
            </Button>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <Button>
            Save Changes
          </Button>
        </div>
      </div>
    </ProtectedRoute>
  )
}