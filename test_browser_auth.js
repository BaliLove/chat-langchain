// Browser automation test for auth flow
const puppeteer = require('puppeteer-core');
const path = require('path');

async function testAuthInBrowser() {
  console.log('🧪 Testing auth flow in headless browser...\n');
  
  let browser;
  try {
    // Try to find Chrome/Edge executable
    const possiblePaths = [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
      'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
    ];
    
    let executablePath;
    for (const p of possiblePaths) {
      try {
        if (require('fs').existsSync(p)) {
          executablePath = p;
          break;
        }
      } catch (e) {}
    }
    
    if (!executablePath) {
      console.log('❌ Could not find Chrome or Edge browser');
      console.log('Please install Chrome or Edge to run browser tests');
      return;
    }
    
    browser = await puppeteer.launch({
      headless: true,
      executablePath,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Capture console logs
    const consoleLogs = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleLogs.push({ type: msg.type(), text });
      
      // Print auth-related logs immediately
      if (text.includes('🔐') || text.includes('🛡️') || text.includes('Auth')) {
        console.log(`[${msg.type()}] ${text}`);
      }
    });
    
    // Capture network requests
    const authRequests = [];
    page.on('request', request => {
      const url = request.url();
      if (url.includes('supabase') || url.includes('/api/') || url.includes('auth')) {
        authRequests.push({
          method: request.method(),
          url: url.substring(0, 100) + (url.length > 100 ? '...' : '')
        });
      }
    });
    
    console.log('📍 Navigating to http://localhost:3000...\n');
    
    try {
      await page.goto('http://localhost:3000', {
        waitUntil: 'networkidle2',
        timeout: 30000
      });
      
      // Wait a bit for auth to initialize
      await page.waitForTimeout(2000);
      
      // Get current URL
      const currentUrl = page.url();
      console.log(`\n📍 Current URL: ${currentUrl}`);
      
      // Check page content
      const pageContent = await page.content();
      
      if (currentUrl.includes('/login')) {
        console.log('✅ Redirected to login page (no active session)');
        
        // Check login page elements
        const hasLoginForm = pageContent.includes('Sign in to Bali Love Chat');
        const hasAllowedDomain = pageContent.includes('bali.love');
        
        console.log(`✅ Login form present: ${hasLoginForm}`);
        console.log(`✅ Allowed domain shown: ${hasAllowedDomain}`);
      } else if (pageContent.includes('Loading authentication')) {
        console.log('⏳ Still loading authentication...');
      } else {
        console.log('📄 Page loaded, checking content...');
      }
      
      // Print auth-related network requests
      if (authRequests.length > 0) {
        console.log('\n🌐 Auth-related network requests:');
        authRequests.forEach(req => {
          console.log(`  ${req.method} ${req.url}`);
        });
      }
      
      // Print all console logs at the end
      console.log('\n📋 All console logs:');
      consoleLogs.forEach(log => {
        if (!log.text.includes('Download the React DevTools')) {
          console.log(`  [${log.type}] ${log.text}`);
        }
      });
      
    } catch (error) {
      console.log('❌ Page load error:', error.message);
    }
    
  } catch (error) {
    console.log('❌ Browser test failed:', error.message);
    console.log('\nTo run browser tests, you need to install puppeteer:');
    console.log('  cd frontend && yarn add -D puppeteer');
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Check if puppeteer is available
try {
  require.resolve('puppeteer-core');
  testAuthInBrowser();
} catch (e) {
  console.log('📦 Puppeteer not installed. Testing with basic HTTP requests instead.\n');
  
  // Fallback to basic test
  const http = require('http');
  
  const req = http.get('http://localhost:3000', (res) => {
    console.log(`📊 Homepage Status: ${res.statusCode}`);
    console.log(`📍 Location Header: ${res.headers.location || 'Not redirecting'}`);
    
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      if (data.includes('Loading authentication')) {
        console.log('✅ Auth loading screen detected');
      }
      if (data.includes('/login')) {
        console.log('✅ Login redirect logic detected');
      }
      
      console.log('\n🔍 To see detailed auth logs:');
      console.log('1. Open http://localhost:3000 in your browser');
      console.log('2. Open DevTools Console (F12)');
      console.log('3. Look for these log patterns:');
      console.log('   - 🔐 Auth initialization steps');
      console.log('   - 🛡️ ProtectedRoute decisions');
      console.log('   - Auth state changes');
      console.log('4. You should see the auth flow and any errors');
    });
  });
  
  req.on('error', (e) => {
    console.log('❌ Could not connect to localhost:3000');
    console.log('Make sure the dev server is running: cd frontend && yarn dev');
  });
}