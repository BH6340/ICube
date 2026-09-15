/**
 * 从 SVG 生成 Android 应用图标各尺寸 PNG
 * 用法: node scripts/generate-app-icons.js
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const svgPath = path.resolve(__dirname, '../../cube_front/src/assets/cube.svg');
const resDir = path.resolve(__dirname, '../android/app/src/main/res');

const sizes = {
  'mipmap-mdpi': 48,
  'mipmap-hdpi': 72,
  'mipmap-xhdpi': 96,
  'mipmap-xxhdpi': 144,
  'mipmap-xxxhdpi': 192,
};

async function main() {
  const svgContent = fs.readFileSync(svgPath, 'utf-8');
  const browser = await chromium.launch();
  const page = await browser.newPage();

  for (const [folder, size] of Object.entries(sizes)) {
    const folderPath = path.join(resDir, folder);
    if (!fs.existsSync(folderPath)) fs.mkdirSync(folderPath, { recursive: true });

    // 生成带背景的方形图标
    const html = `
      <div style="width:${size}px;height:${size}px;background:#ffffff;display:flex;align-items:center;justify-content:center;">
        ${svgContent.replace('width="200"', `width="${Math.floor(size * 0.75)}"`).replace('height="200"', `height="${Math.floor(size * 0.75)}"`)}
      </div>`;
    await page.setContent(html, { waitUntil: 'networkidle' });
    const el = await page.$('div');
    await el.screenshot({ path: path.join(folderPath, 'ic_launcher.png'), type: 'png' });

    // 生成圆形图标
    const htmlRound = `
      <div style="width:${size}px;height:${size}px;background:#ffffff;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;">
        ${svgContent.replace('width="200"', `width="${Math.floor(size * 0.65)}"`).replace('height="200"', `height="${Math.floor(size * 0.65)}"`)}
      </div>`;
    await page.setContent(htmlRound, { waitUntil: 'networkidle' });
    const elRound = await page.$('div');
    await elRound.screenshot({ path: path.join(folderPath, 'ic_launcher_round.png'), type: 'png' });

    // 生成前景图（adaptive icon）
    const htmlFg = `
      <div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center;">
        ${svgContent.replace('width="200"', `width="${Math.floor(size * 0.7)}"`).replace('height="200"', `height="${Math.floor(size * 0.7)}"`)}
      </div>`;
    await page.setContent(htmlFg, { waitUntil: 'networkidle' });
    const elFg = await page.$('div');
    await elFg.screenshot({ path: path.join(folderPath, 'ic_launcher_foreground.png'), type: 'png', omitBackground: true });

    console.log(`✓ ${folder} (${size}px)`);
  }

  await browser.close();
  console.log('\n全部图标生成完成');
}

main().catch(e => { console.error(e); process.exit(1); });
