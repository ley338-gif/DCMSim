import {expect,test} from '@playwright/test'

test('real worklist query reaches the local MWL SCP',async({page})=>{await page.goto('/worklist');await page.getByLabel('Host').fill('127.0.0.1');await page.getByLabel('Port').fill('11112');await page.getByLabel('Called AE').fill('TESTMWL');await page.getByRole('button',{name:'Worklist abfragen'}).click();await expect(page.getByText('DCMSIM-FULLSTACK-001')).toBeVisible();await expect(page.getByText('1 Worklist-Einträge gefunden')).toBeVisible();await page.getByText('Technische Details (DICOM)').click();await expect(page.getByText(/"status": "0x0000"/)).toBeVisible()})

test('real CT store reaches the local Storage SCP and returns generated UIDs',async({page})=>{await page.goto('/pacs-store');await page.getByLabel('Host').fill('127.0.0.1');await page.getByLabel('Port').fill('11113');await page.getByLabel('Called AE').fill('TESTPACS');await page.getByLabel('SOP Class').selectOption('ct');await page.getByRole('button',{name:'C-STORE senden'}).click();await expect(page.getByText('C-STORE erfolgreich')).toBeVisible();await expect(page.getByText('0x0000',{exact:true}).first()).toBeVisible();for(const label of ['Study Instance UID','Series Instance UID','SOP Instance UID'])await expect(page.getByText(label,{exact:true})).toBeVisible()})

test('real modality check covers the complete 0.2 workflow and history',async({page})=>{
  await page.goto('/targets')
  await page.getByRole('button',{name:'Neues Ziel'}).click()
  await page.getByLabel('Name').fill('Full Stack DICOM')
  await page.getByLabel('Host').fill('127.0.0.1')
  await page.locator('#mwl-port').fill('11112')
  await page.locator('#mwl-ae').fill('TESTMWL')
  await page.locator('#store-port').fill('11113')
  await page.locator('#store-ae').fill('TESTPACS')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByRole('cell',{name:'Full Stack DICOM',exact:true})).toBeVisible()

  await page.goto('/modalities')
  await page.getByRole('button',{name:'Neue Modalität'}).click()
  await page.getByLabel('Name').fill('Full Stack CT')
  await page.getByLabel('Modalität',{exact:true}).selectOption('CT')
  await page.getByLabel('Calling AE').fill('DCMSIM')
  await page.getByLabel('Worklist Target').selectOption({label:'Full Stack DICOM'})
  await page.getByLabel('Store Target').selectOption({label:'Full Stack DICOM'})
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByRole('heading',{name:'Full Stack CT'})).toBeVisible()

  await page.getByRole('button',{name:'Modalität prüfen'}).click()
  await expect(page.getByText('Overall PASS')).toBeVisible()
  await expect(page.getByText('CT Image Storage')).toBeVisible()
  await expect(page.getByText('1',{exact:true})).toBeVisible()

  await page.getByRole('link',{name:'Historieneintrag öffnen'}).click()
  await expect(page).toHaveURL(/\/history\/\d+$/)
  await expect(page.getByRole('heading',{name:/Modalitätsprüfung · Test #/})).toBeVisible()
  await expect(page.getByText('Overall PASS')).toBeVisible()
})
