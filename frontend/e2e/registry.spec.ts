import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
const sample=resolve('../docs/reference/received/0936a617-4998-43d9-8020-97b5606c3f69.xlsx');

test('real Excel import, card, group, persistence and export',async({page})=>{
  await page.goto('/');
  await page.locator('input[type=file]').setInputFiles(sample);
  await page.getByRole('button',{name:'Проверить и импортировать'}).click();
  await expect(page.getByRole('heading',{name:'Общий реестр дефектов'})).toBeVisible();
  const search=page.getByPlaceholder('Поиск по ID');
  await search.fill('91199328');
  await page.locator('tr[data-row-key="91199328@31"]').click();
  const drawer=page.getByRole('dialog');
  await expect(drawer).toContainText('anom, строка 31');
  await drawer.getByRole('tab',{name:'Результат',exact:true}).click();
  await expect(drawer).toContainText('13.595063');
  await drawer.getByRole('button',{name:'Закрыть',exact:true}).click();
  await expect(search).toHaveValue('91199328');
  await search.fill('91198158');
  await page.locator('.ant-table-row-expand-icon').first().click();
  await expect(page.locator('.ant-table-expanded-row')).toContainText('91198158');
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Экспорт Excel'}).click();
  expect((await download).suggestedFilename()).toBe('vtd-results.xlsx');
  await page.reload();
  await page.locator('.topbar .ant-select').click();
  await expect(page.locator('.ant-select-dropdown')).toContainText('0936a617');
});

test('malformed workbook shows an error',async({page})=>{
  await page.goto('/');
  await page.locator('input[type=file]').setInputFiles({name:'bad.xlsx',mimeType:'application/octet-stream',buffer:Buffer.from('bad zip')});
  await page.getByRole('button',{name:'Проверить и импортировать'}).click();
  await expect(page.getByText('Ошибка импорта', {exact:true})).toBeVisible();
});

