const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch({headless: true});
    const page = await browser.newPage();
    const htmlPath = 'file:///' + path.resolve('handbuch.html').replace(/\\/g, '/');
    await page.goto(htmlPath, {waitUntil: 'networkidle0'});
    await page.pdf({
        path: 'handbuch.pdf',
        format: 'A4',
        printBackground: true,
        margin: {top: '20mm', right: '20mm', bottom: '20mm', left: '20mm'}
    });
    await browser.close();
    const fs = require('fs');
    const size = fs.statSync('handbuch.pdf').size;
    console.log(`PDF erstellt: handbuch.pdf (${(size/1024).toFixed(0)} KB)`);
})();
