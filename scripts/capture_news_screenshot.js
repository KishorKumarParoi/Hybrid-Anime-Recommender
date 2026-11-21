const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle0', timeout: 30000 });
  
  // Find and click on the 2027 Live Newsroom tab
  const buttons = await page.$$('button');
  for (const b of buttons) {
    const text = await page.evaluate(el => el.innerText, b);
    if (text.includes('Studio News') || text.includes('Newsroom') || text.includes('MAL 2027')) {
      await b.click();
      console.log('Clicked newsroom button:', text);
      break;
    }
  }
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: '/Users/kishorkumarparoi/.gemini/antigravity/brain/cf7d33bf-91aa-43e8-8289-301de0cb7453/reddit_news_live_verified.png' });
  console.log('[✓] Screenshot saved to reddit_news_live_verified.png');

  // Also test clicking "Discuss & Reviews" to open Reddit modal
  const discussBtns = await page.$$('button');
  for (const b of discussBtns) {
    const text = await page.evaluate(el => el.innerText, b);
    if (text.includes('Discuss & Reviews')) {
      await b.click();
      console.log('Clicked Discuss & Reviews button');
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: '/Users/kishorkumarparoi/.gemini/antigravity/brain/cf7d33bf-91aa-43e8-8289-301de0cb7453/reddit_discussion_modal_verified.png' });
  console.log('[✓] Modal screenshot saved to reddit_discussion_modal_verified.png');

  await browser.close();
})();
