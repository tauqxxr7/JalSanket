const {chromium}=require('playwright');
const assert=require('node:assert/strict');const fs=require('node:fs/promises');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
 try{
  const page=await browser.newPage();const base=process.env.JALSANKET_BASE_URL||'http://127.0.0.1:8769';
  await page.goto(base);await page.getByText('5 of 5 stations shown',{exact:true}).waitFor();
  await page.getByLabel('Find a station').fill('group-540acb3b92fe6e39');
  assert.equal(await page.locator('.queue-row').count(),1);
  await page.locator('#state-filter').selectOption('UNCERTAIN');
  await page.locator('#anomaly-filter').selectOption('SPIKE');
  await page.getByText('No stations match this filter.',{exact:true}).waitFor();
  await page.reload();assert.equal(await page.locator('#anomaly-filter').inputValue(),'SPIKE');
  await page.getByRole('button',{name:'Clear filters',exact:true}).click();
  assert.equal(await page.locator('.queue-row').count(),5);
  await page.getByRole('button',{name:'Explore an Evidence Trail',exact:true}).click();
  await page.locator('#observation-picker').waitFor();
  const point=page.locator('.history-chart circle').nth(0);const id=await point.getAttribute('data-observation');
  await point.press('Enter');await page.getByRole('link',{name:'INSPECT SELECTED EVIDENCE →',exact:true}).waitFor();
  await page.waitForFunction(id=>document.querySelector('#selection-panel a')?.href.includes(encodeURIComponent(id)),id);
  assert.match(await page.locator('#selection-panel').innerText(),/INSUFFICIENT EVIDENCE/);
  await page.getByRole('link',{name:'INSPECT SELECTED EVIDENCE →',exact:true}).click();
  await page.locator('.next-check').waitFor();
  await page.getByText('Source provenance & original evidence rows',{exact:true}).click();
  assert.match(await page.locator('#evidence-body').innerText(),/datum unverified/);
  const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Download evidence JSON',exact:true}).click();
  const download=await downloadPromise;const report=JSON.parse(await fs.readFile(await download.path(),'utf8'));
  assert.equal(report.observation.observation_id,id);assert.equal(report.assessment,'INSUFFICIENT_EVIDENCE');
  assert.ok((await page.locator('.next-check').innerText()).includes(report.next_check.action));
  await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await fs.mkdir('artifacts',{recursive:true});await page.screenshot({path:'artifacts/investigation-mobile.png',fullPage:true});
  console.log('PASS: search, filters, URL persistence, reset, guided entry, keyboard selection, exact evidence/export, provenance, mobile.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
