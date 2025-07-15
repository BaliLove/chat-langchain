// Test the frontend auth flow by making requests like a browser would
const http = require('http');

// Test 1: Check if the server is responding
console.log('🧪 Testing frontend server at http://localhost:3000...\n');

const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/',
  method: 'GET',
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  }
};

const req = http.request(options, (res) => {
  console.log(`📊 Status Code: ${res.statusCode}`);
  console.log(`📋 Headers:`, res.headers);
  
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('\n📄 Response Preview (first 500 chars):');
    console.log(data.substring(0, 500) + '...\n');
    
    // Check for important indicators
    if (data.includes('Loading authentication')) {
      console.log('✅ Found: Loading authentication message');
    }
    
    if (data.includes('window.location.href = \'/login\'')) {
      console.log('✅ Found: Redirect to login logic');
    }
    
    if (data.includes('NEXT_PUBLIC_SUPABASE_URL')) {
      console.log('❌ Warning: Environment variables might be exposed');
    }
    
    // Check for any inline scripts that might show auth state
    const scriptMatch = data.match(/<script[^>]*>([^<]+)<\/script>/g);
    if (scriptMatch) {
      console.log('\n📜 Inline scripts found:');
      scriptMatch.forEach((script, i) => {
        if (script.includes('console.log') || script.includes('auth')) {
          console.log(`Script ${i + 1}: ${script.substring(0, 200)}...`);
        }
      });
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Error connecting to server:', error.message);
  console.log('\n🔧 Make sure the dev server is running with: cd frontend && yarn dev');
});

req.end();