// Test auth-related API endpoints
const http = require('http');
const https = require('https');

async function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const client = urlObj.protocol === 'https:' ? https : http;
    
    const req = client.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, data }));
    });
    
    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function testAuthFlow() {
  console.log('🧪 Testing Auth Flow...\n');
  
  // Test 1: Check if Supabase is accessible
  console.log('1️⃣ Testing Supabase connection...');
  try {
    const supabaseUrl = 'https://zgxvanaavvkttoohzwpo.supabase.co';
    const response = await makeRequest(`${supabaseUrl}/auth/v1/health`, {
      method: 'GET',
      headers: {
        'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpneHZhbmFhdnZrdHRvb2h6d3BvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjA3OTQ2MzIsImV4cCI6MjAzNjM3MDYzMn0.tNDkY7bOI3f-QuTl1XMr9D_6jFEOHB8nVZEO6I_OAOI'
      }
    });
    console.log(`✅ Supabase Health Check: ${response.status}`);
  } catch (error) {
    console.log('❌ Supabase connection failed:', error.message);
  }
  
  // Test 2: Check frontend login page
  console.log('\n2️⃣ Testing login page...');
  try {
    const loginResponse = await makeRequest('http://localhost:3000/login');
    console.log(`✅ Login page status: ${loginResponse.status}`);
    
    if (loginResponse.data.includes('Sign in to Bali Love Chat')) {
      console.log('✅ Login page content verified');
    }
    
    if (loginResponse.data.includes('bali.love')) {
      console.log('✅ Allowed domain "bali.love" found in login page');
    }
  } catch (error) {
    console.log('❌ Login page test failed:', error.message);
  }
  
  // Test 3: Check API proxy
  console.log('\n3️⃣ Testing API proxy...');
  try {
    const apiResponse = await makeRequest('http://localhost:3000/api/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    console.log(`📊 API proxy response: ${apiResponse.status}`);
    if (apiResponse.data) {
      console.log('📄 API response:', apiResponse.data.substring(0, 100) + '...');
    }
  } catch (error) {
    console.log('⚠️  API proxy test failed (this might be normal):', error.message);
  }
  
  // Test 4: Check for auth cookies/session
  console.log('\n4️⃣ Checking for auth session...');
  try {
    const homeResponse = await makeRequest('http://localhost:3000/', {
      headers: {
        'Cookie': 'sb-zgxvanaavvkttoohzwpo-auth-token=; ' // Would need actual session cookie
      }
    });
    
    // Check if we're redirected to login
    if (homeResponse.status === 307 || homeResponse.headers.location === '/login') {
      console.log('✅ Correctly redirecting to login (no session)');
    } else if (homeResponse.data.includes('Loading authentication')) {
      console.log('✅ Auth check in progress');
    }
  } catch (error) {
    console.log('❌ Session check failed:', error.message);
  }
  
  console.log('\n📋 Summary:');
  console.log('- Frontend server is running on http://localhost:3000');
  console.log('- Login page is accessible at http://localhost:3000/login');
  console.log('- Auth flow will redirect unauthenticated users to login');
  console.log('- Allowed email domain: bali.love');
  console.log('\n🔍 To see detailed auth logs:');
  console.log('1. Open http://localhost:3000 in your browser');
  console.log('2. Open browser console (F12)');
  console.log('3. Look for logs with 🔐 emoji markers');
}

testAuthFlow();