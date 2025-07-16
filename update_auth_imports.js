const fs = require('fs');
const path = require('path');

// Files to update
const filesToUpdate = [
  'frontend/app/components/AdminRoute.tsx',
  'frontend/app/components/AuthTest.tsx',
  'frontend/app/components/Header.tsx',
  'frontend/app/components/PermissionStatus.tsx',
  'frontend/app/hooks/usePermissions.tsx',
  'frontend/app/settings/page.tsx'
];

filesToUpdate.forEach(filePath => {
  try {
    const fullPath = path.join(__dirname, filePath);
    let content = fs.readFileSync(fullPath, 'utf8');
    
    // Replace the import
    const oldImport = "import { useAuth } from '@/app/contexts/AuthContext'";
    const newImport = "import { useAuth } from '@/app/contexts/AuthContextStable'";
    
    if (content.includes(oldImport)) {
      content = content.replace(oldImport, newImport);
      fs.writeFileSync(fullPath, content, 'utf8');
      console.log(`✅ Updated: ${filePath}`);
    } else {
      console.log(`⏭️  Skipped: ${filePath} (already updated or not found)`);
    }
  } catch (error) {
    console.error(`❌ Error updating ${filePath}:`, error.message);
  }
});

console.log('\n✨ Import updates complete!');