// Test the API proxy
const http = require('http');

const testApiProxy = async () => {
  console.log('🧪 Testing API Proxy...\n');
  
  const options = {
    hostname: 'localhost',
    port: 3003,
    path: '/api/threads/search',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
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
      console.log('\n📄 Response:');
      try {
        const parsed = JSON.parse(data);
        console.log(JSON.stringify(parsed, null, 2));
      } catch (e) {
        console.log(data);
      }
      
      if (res.statusCode === 500) {
        console.log('\n❌ Internal Server Error - Check server logs for details');
        console.log('Common causes:');
        console.log('- Missing LANGGRAPH_API_KEY in environment');
        console.log('- Incorrect API_BASE_URL');
        console.log('- LangGraph service authentication issues');
      }
    });
  });
  
  req.on('error', (error) => {
    console.error('❌ Request error:', error);
  });
  
  // Send empty search request
  req.write(JSON.stringify({
    limit: 10
  }));
  
  req.end();
};

testApiProxy();