const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const userDataDir = path.join(__dirname, 'playwright/user-data');
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: true // Run in headless mode to not disturb
  });

  const cookies = await context.cookies('https://jimeng.jianying.com');
  console.log(JSON.stringify(cookies, null, 2));

  await context.close();
})();
