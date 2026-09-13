import {expect,test} from '@playwright/test'

test('real worklist query reaches the local MWL SCP',async({page})=>{await page.goto('/worklist');await page.getByLabel('Host').fill('127.0.0.1');await page.getByLabel('Port').fill('11112');await page.getByLabel('Called AE').fill('TESTMWL');await page.getByRole('button',{name:'Worklist abfragen'}).click();await expect(page.getByText('DCMSIM-FULLSTACK-001')).toBeVisible();await expect(page.getByText('1 Worklist-Einträge gefunden')).toBeVisible();await page.getByText('Technische Details (DICOM)').click();await expect(page.getByText(/"status": "0x0000"/)).toBeVisible()})

test('real CT store reaches the local Storage SCP and returns generated UIDs',async({page})=>{await page.goto('/pacs-store');await page.getByLabel('Host').fill('127.0.0.1');await page.getByLabel('Port').fill('11113');await page.getByLabel('Called AE').fill('TESTPACS');await page.getByLabel('SOP Class').selectOption('ct');await page.getByRole('button',{name:'C-STORE senden'}).click();await expect(page.getByText('C-STORE erfolgreich')).toBeVisible();await expect(page.getByText('0x0000',{exact:true}).first()).toBeVisible();for(const label of ['Study Instance UID','Series Instance UID','SOP Instance UID'])await expect(page.getByText(label,{exact:true})).toBeVisible()})

test('real PACS query reaches the local Study Root SCP',async({page})=>{await page.goto('/pacs-query');await page.getByLabel('Host').fill('127.0.0.1');await page.getByLabel('Port').fill('11114');await page.getByLabel('Called AE').fill('TESTQR');await page.getByRole('button',{name:'Studien suchen'}).click();await expect(page.getByText('FULL STACK PACS QUERY')).toBeVisible();await expect(page.getByText('DCMSIM-QR-001')).toBeVisible();await page.getByText('FULL STACK PACS QUERY').click();await expect(page.getByRole('dialog',{name:'DICOM-Studienantwort'})).toContainText('1.2.826.0.1.3680043.10.543.300')})

test('real modality check covers the complete structured 0.4 workflow and history',async({page})=>{
  await page.goto('/systems')
  await page.getByRole('button',{name:'Standort hinzufügen'}).click()
  await page.getByLabel('Standortname').fill('Full Stack Standort')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByRole('heading',{name:'Full Stack Standort'})).toBeVisible()

  await page.getByRole('button',{name:'Bereich'}).click()
  await page.getByLabel('Bereichsname').fill('Radiologie')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByText('Radiologie',{exact:true})).toBeVisible()

  await page.getByRole('button',{name:'DICOM-System hinzufügen'}).click()
  await page.getByLabel('Systemname').fill('Full Stack DICOM')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByRole('heading',{name:'Full Stack DICOM'})).toBeVisible()

  await page.getByRole('button',{name:'Endpoint'}).click()
  await page.getByLabel('Endpointname').fill('Full Stack MWL')
  await page.getByLabel('Dienst').selectOption('MWL')
  await page.getByLabel('Host').fill('127.0.0.1')
  await page.getByLabel('Port').fill('11112')
  await page.getByLabel('Called AE').fill('TESTMWL')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByText(/Full Stack MWL · MWL/)).toBeVisible()

  await page.getByRole('button',{name:'Endpoint'}).click()
  await page.getByLabel('Endpointname').fill('Full Stack Store')
  await page.getByLabel('Dienst').selectOption('STORE')
  await page.getByLabel('Host').fill('127.0.0.1')
  await page.getByLabel('Port').fill('11113')
  await page.getByLabel('Called AE').fill('TESTPACS')
  await page.getByRole('button',{name:'Speichern'}).click()
  await expect(page.getByText(/Full Stack Store · STORE/)).toBeVisible()

  await page.goto('/modalities')
  await page.getByRole('button',{name:'Neue Modalität'}).click()
  await page.getByLabel('Name').fill('Full Stack CT')
  await page.getByLabel('Modalität',{exact:true}).selectOption('CT')
  await page.getByLabel('Calling AE').fill('DCMSIM')
  await page.getByLabel('Standort / Bereich').selectOption({label:'Full Stack Standort · Radiologie'})
  await page.getByLabel('MWL-Endpoint').selectOption({label:'Full Stack DICOM · Full Stack MWL · 127.0.0.1:11112 · Called AE TESTMWL'})
  await page.getByLabel('STORE-Endpoint').selectOption({label:'Full Stack DICOM · Full Stack Store · 127.0.0.1:11113 · Called AE TESTPACS'})
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
