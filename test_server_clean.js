// Test clean server startup
const http = require('http');

async function testCleanStartup() {
  console.log('🧪 Testing Clean Server Startup...\n');
  
  // Wait a moment for server to be ready
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Test main page
  try {
    const req = http.get('http://localhost:3000/', (res) => {
      console.log(`📊 Homepage Status: ${res.statusCode}`);
      
      if (res.statusCode === 200) {
        console.log('✅ Server is responding correctly');
        
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (data.includes('Loading authentication')) {
            console.log('✅ Auth loading screen detected');
          }
          if (data.includes('Bali Love Chat')) {
            console.log('✅ Page title correct');
          }
          
          console.log('\n🎉 Server appears to be working properly!');
          console.log('Open http://localhost:3000 in your browser to test the UI');
        });
      } else {
        console.log(`❌ Server returned status ${res.statusCode}`);
      }
    });
    
    req.on('error', (error) => {
      console.log('❌ Connection failed:', error.message);
      console.log('Make sure the dev server is running: cd frontend && yarn dev');
    });
    
    req.setTimeout(5000, () => {
      console.log('❌ Request timed out - server may not be ready yet');
    });
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

testCleanStartup();