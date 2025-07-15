const http = require('http');

console.log('🧪 Simple Auth Flow Test\n');
console.log('Testing http://localhost:3000...\n');

// First request - check main page
const req = http.get('http://localhost:3000', (res) => {
  console.log(`📊 Status: ${res.statusCode}`);
  console.log(`📍 Headers:`, {
    location: res.headers.location || 'No redirect',
    'set-cookie': res.headers['set-cookie'] || 'No cookies'
  });
  
  let body = '';
  res.on('data', chunk => body += chunk);
  
  res.on('end', () => {
    // Analyze the response
    console.log('\n📄 Page Analysis:');
    
    if (body.includes('Loading authentication')) {
      console.log('✅ Auth loading state detected');
    }
    
    if (body.includes('window.location.href = \'/login\'')) {
      console.log('✅ Client-side redirect to /login detected');
    }
    
    if (body.includes('ProtectedRoute')) {
      console.log('✅ ProtectedRoute component present');
    }
    
    if (body.includes('GraphProvider')) {
      console.log('✅ GraphProvider component present');
    }
    
    // Check for Supabase initialization
    if (body.includes('SUPABASE_URL')) {
      console.log('✅ Supabase configuration detected');
    }
    
    // Look for any error messages
    const errorMatch = body.match(/error[^>]*>([^<]+)</i);
    if (errorMatch) {
      console.log('❌ Error found:', errorMatch[1]);
    }
    
    console.log('\n📝 Auth Flow Summary:');
    console.log('1. Page loads with "Loading authentication" message');
    console.log('2. AuthContext initializes and checks Supabase session');
    console.log('3. If no session, ProtectedRoute redirects to /login');
    console.log('4. Console will show detailed logs with 🔐 markers');
    
    console.log('\n🔍 Next Steps:');
    console.log('1. Open http://localhost:3000 in browser');
    console.log('2. Open DevTools (F12) > Console tab');
    console.log('3. You should see logs like:');
    console.log('   🔐 Starting auth initialization...');
    console.log('   🔐 Session check: No session');
    console.log('   🛡️ ProtectedRoute state: {user: null, loading: false}');
    console.log('   🚫 Redirecting to login');
    
    // Now check the login page
    console.log('\n\nChecking /login page...');
    http.get('http://localhost:3000/login', (loginRes) => {
      let loginBody = '';
      loginRes.on('data', chunk => loginBody += chunk);
      loginRes.on('end', () => {
        if (loginBody.includes('Sign in to Bali Love Chat')) {
          console.log('✅ Login page is working correctly');
        }
        if (loginBody.includes('bali.love')) {
          console.log('✅ Domain restriction (bali.love) is configured');
        }
      });
    });
  });
});

req.on('error', (e) => {
  console.error('❌ Error:', e.message);
  console.log('\nMake sure the dev server is running:');
  console.log('  cd frontend && yarn dev');
});