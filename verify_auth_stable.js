// Verify stable auth flow
const http = require('http');

console.log('🧪 Testing Stable Auth Flow...\n');

// Test 1: Check main page
console.log('1️⃣ Testing main page...');
http.get('http://localhost:3003/', (res) => {
  console.log(`   Status: ${res.statusCode}`);
  console.log(`   Location: ${res.headers.location || 'No redirect'}`);
  
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    if (data.includes('Loading authentication')) {
      console.log('   ✅ Auth loading screen present');
    }
    if (res.statusCode === 200) {
      console.log('   ✅ Page loaded successfully');
    }
  });
});

// Test 2: Check API health
setTimeout(() => {
  console.log('\n2️⃣ Testing API health endpoint...');
  http.get('http://localhost:3003/api/health', (res) => {
    console.log(`   Status: ${res.statusCode}`);
    
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        const json = JSON.parse(data);
        console.log('   ✅ API is responding');
        console.log(`   Environment: ${JSON.stringify(json.env, null, 2)}`);
      } catch (e) {
        console.log('   ❌ API response error:', data);
      }
    });
  });
}, 1000);

console.log('\n📋 Expected Behavior:');
console.log('- No auth timeout clearing user state');
console.log('- Stable authentication state');
console.log('- No redirect loops');
console.log('- Black screen should be resolved');
console.log('\n🔍 Check browser console for:');
console.log('- 🔐 Initializing auth...');
console.log('- ✅ Found existing session (if logged in)');
console.log('- No duplicate auth initializations');