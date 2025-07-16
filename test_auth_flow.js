// Test auth flow locally
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

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