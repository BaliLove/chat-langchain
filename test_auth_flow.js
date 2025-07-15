// Test auth flow locally
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://zgxvanaavvkttoohzwpo.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpneHZhbmFhdnZrdHRvb2h6d3BvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjA3OTQ2MzIsImV4cCI6MjAzNjM3MDYzMn0.tNDkY7bOI3f-QuTl1XMr9D_6jFEOHB8nVZEO6I_OAOI';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testAuth() {
  console.log('🔐 Testing Supabase connection...');
  
  try {
    // Test 1: Check if we can connect
    const { data: { session }, error } = await supabase.auth.getSession();
    
    if (error) {
      console.error('❌ Error getting session:', error);
      return;
    }
    
    console.log('✅ Successfully connected to Supabase');
    console.log('📊 Session status:', session ? 'Active session found' : 'No active session');
    
    if (session) {
      console.log('👤 User:', session.user.email);
      console.log('🆔 User ID:', session.user.id);
    }
    
    // Test 2: Check auth state
    supabase.auth.onAuthStateChange((event, session) => {
      console.log('🔄 Auth state changed:', event);
      if (session) {
        console.log('👤 Session user:', session.user.email);
      }
    });
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testAuth();