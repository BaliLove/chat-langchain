'use client'
import { useAuth } from '@/app/contexts/AuthContextStable'
import { useRouter } from 'next/navigation'

export default function AuthTest() {
  const { user, userTeamData, loading, signOut } = useAuth()
  const router = useRouter()

  if (loading) {
    return (
      <div className="p-4 bg-blue-100 text-blue-800 rounded-lg">
        Loading authentication...
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-4 bg-red-100 text-red-800 rounded-lg">
        <p>Not authenticated</p>
        <button 
          onClick={() => router.push('/login')}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Go to Login
        </button>
      </div>
    )
  }

  return (
    <div className="p-4 bg-green-100 text-green-800 rounded-lg">
      <h3 className="font-bold text-lg">✅ Authentication Working!</h3>
      <p><strong>User ID:</strong> {user.id}</p>
      <p><strong>Email:</strong> {user.email}</p>
      <p><strong>Team:</strong> {userTeamData?.team_name || 'No team data'}</p>
      <p><strong>Role:</strong> {userTeamData?.role || 'No role assigned'}</p>
      
      <button 
        onClick={signOut}
        className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
      >
        Sign Out
      </button>
    </div>
  )
} 