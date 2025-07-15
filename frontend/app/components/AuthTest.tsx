'use client'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { useRouter } from 'next/navigation'
import { Button } from './ui/button'

export default function AuthTest() {
  const { user, userTeamData, loading, signOut } = useAuth()
  const router = useRouter()

  if (loading) {
    return (
      <div className="p-4 bg-primary/10 text-primary rounded-lg">
        Loading authentication...
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
        <p>Not authenticated</p>
        <Button 
          onClick={() => router.push('/login')}
          className="mt-2"
          variant="default"
        >
          Go to Login
        </Button>
      </div>
    )
  }

  return (
    <div className="p-4 bg-accent text-accent-foreground rounded-lg">
      <h3 className="font-bold text-lg">✅ Authentication Working!</h3>
      <p><strong>User ID:</strong> {user.id}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>Team:</strong> {userTeamData?.team_name || 'No team data'}</p>
      <p><strong>Role:</strong> {userTeamData?.role || 'No role assigned'}</p>
      
      <Button 
        onClick={signOut}
        className="mt-4"
        variant="destructive"
      >
        Sign Out
      </Button>
    </div>
  )
} 