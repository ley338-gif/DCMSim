import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor,within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach} from 'vitest'
import {api,ConfigurationV1,ConfigurationV2} from '../api/client'
import {SettingsPage} from '../pages/Settings'

function setup(){return render(<QueryClientProvider client={new QueryClient()}><SettingsPage/></QueryClientProvider>)}

afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();localStorage.clear();document.documentElement.classList.remove('compact-tables')})

it('purges history using the configured retention without a scheduler',async()=>{vi.stubGlobal('confirm',()=>true);const purge=vi.spyOn(api,'purgeHistory').mockResolvedValue({deleted_count:3,cutoff:''});setup();await userEvent.click(screen.getByRole('button',{name:'Retention'}));await userEvent.click(screen.getByRole('button',{name:'Alte Historie bereinigen'}));await waitFor(()=>expect(purge).toHaveBeenCalledWith(90));expect(await screen.findByText('3 alte Historieneinträge wurden gelöscht.')).toBeVisible()})

it('offers configuration export, import and SQLite backup',async()=>{vi.stubGlobal('URL',{...URL,createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}});vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});const exported=vi.spyOn(api,'exportConfiguration').mockResolvedValue({format_version:1,targets:[],modality_profiles:[]});vi.spyOn(api,'databaseBackup').mockResolvedValue(new Blob(['db']));setup();await userEvent.click(screen.getByRole('button',{name:'Datensicherung'}));await userEvent.click(screen.getByRole('button',{name:'Konfiguration exportieren'}));await waitFor(()=>expect(exported).toHaveBeenCalled());expect(screen.getByLabelText('Konfigurationsdatei auswählen')).toBeInTheDocument();expect(screen.getByRole('button',{name:'SQLite-Backup erstellen'})).toBeVisible()})

it('previews legacy v1 configuration changes and imports only after confirmation',async()=>{
 const target:ConfigurationV1['targets'][number]={name:'JiveX',host:'pacs.local',mwl_enabled:true,mwl_port:104,mwl_called_ae:'JIVEXWL',store_enabled:false,store_port:null,store_called_ae:null,qr_enabled:false,qr_port:null,qr_called_ae:null,default_calling_ae:'DCMSIM'}
 const configuration:ConfigurationV1={format_version:1,targets:[target,{...target,name:'Test PACS'}],modality_profiles:[]}
 vi.spyOn(api,'exportConfiguration').mockResolvedValue({format_version:2,sites:[],areas:[],dicom_systems:[],worklist_channels:[],modality_profiles:[]})
 const targets=vi.spyOn(api,'targets').mockResolvedValue([{...target,id:1,created_at:'',updated_at:''}])
 const imported=vi.spyOn(api,'importConfiguration').mockResolvedValue({created_targets:1,updated_targets:1,created_profiles:0,updated_profiles:0})
 setup()
 await userEvent.click(screen.getByRole('button',{name:'Datensicherung'}))
 const file=new File([JSON.stringify(configuration)],'config.json',{type:'application/json'})
 Object.defineProperty(file,'text',{value:()=>Promise.resolve(JSON.stringify(configuration))})
 await userEvent.upload(screen.getByLabelText('Konfigurationsdatei auswählen'),file)
 const dialog=await screen.findByRole('dialog',{name:'Konfigurationsimport prüfen'})
 expect(within(dialog).getByText('JiveX',{exact:false})).toBeVisible()
 expect(within(dialog).getByText(/1 neue Ziele, 1 bestehende Ziele/)).toBeVisible()
 expect(targets).toHaveBeenCalled()
 expect(imported).not.toHaveBeenCalled()
 await userEvent.click(within(dialog).getByRole('button',{name:'Abbrechen'}))
 expect(imported).not.toHaveBeenCalled()
 await userEvent.upload(screen.getByLabelText('Konfigurationsdatei auswählen'),file)
 await userEvent.click(within(await screen.findByRole('dialog',{name:'Konfigurationsimport prüfen'})).getByRole('button',{name:'Import bestätigen'}))
 await waitFor(()=>expect(imported).toHaveBeenCalledWith(configuration))
 expect(await screen.findByText(/1 Einträge neu; 1 Einträge aktualisiert/)).toBeVisible()
})

it('previews a v2 topology configuration',async()=>{
 const configuration:ConfigurationV2={format_version:2,sites:[{name:'Nord'}],areas:[{name:'Radiologie',site_name:'Nord'}],dicom_systems:[],worklist_channels:[],modality_profiles:[]}
 vi.spyOn(api,'exportConfiguration').mockResolvedValue({format_version:2,sites:[],areas:[],dicom_systems:[],worklist_channels:[],modality_profiles:[]})
 setup();await userEvent.click(screen.getByRole('button',{name:'Datensicherung'}))
 const file=new File([JSON.stringify(configuration)],'topology.json',{type:'application/json'});Object.defineProperty(file,'text',{value:()=>Promise.resolve(JSON.stringify(configuration))})
 await userEvent.upload(screen.getByLabelText('Konfigurationsdatei auswählen'),file)
 const dialog=await screen.findByRole('dialog',{name:'Konfigurationsimport prüfen'})
 expect(within(dialog).getByText(/1 neue Standorte/)).toBeVisible()
 expect(within(dialog).getByText(/1 neue Bereiche/)).toBeVisible()
})

it('previews new and technically changed v2 endpoints by system and endpoint key before confirmation',async()=>{
 const base={service:'STORE' as const,host:'pacs.local',port:104,called_ae:'PACS'}
 const current:ConfigurationV2={format_version:2,sites:[],areas:[],dicom_systems:[{name:'PACS',endpoints:[
  {...base,name:'Host'},
  {...base,name:'Port'},
  {...base,name:'Called AE'},
  {...base,name:'Dienst'},
 ]}],worklist_channels:[],modality_profiles:[]}
 const configuration:ConfigurationV2={...current,dicom_systems:[{name:'PACS',endpoints:[
  {...base,name:'Host',host:'archive.local'},
  {...base,name:'Port',port:11112},
  {...base,name:'Called AE',called_ae:'ARCHIVE'},
  {...base,name:'Dienst',service:'QR'},
  {...base,name:'Neu'},
 ]}]}
 vi.spyOn(api,'exportConfiguration').mockResolvedValue(current)
 const imported=vi.spyOn(api,'importConfiguration').mockResolvedValue({created_sites:0,updated_sites:0,created_areas:0,updated_areas:0,created_systems:0,updated_systems:1,created_endpoints:1,updated_endpoints:4,created_channels:0,updated_channels:0,created_profiles:0,updated_profiles:0})
 setup();await userEvent.click(screen.getByRole('button',{name:'Datensicherung'}))
 const file=new File([JSON.stringify(configuration)],'endpoints.json',{type:'application/json'});Object.defineProperty(file,'text',{value:()=>Promise.resolve(JSON.stringify(configuration))})
 await userEvent.upload(screen.getByLabelText('Konfigurationsdatei auswählen'),file)
 const dialog=await screen.findByRole('dialog',{name:'Konfigurationsimport prüfen'})
 expect(within(dialog).getByText(/1 neue Endpoints, 4 zu aktualisierende Endpoints/)).toBeVisible()
 expect(within(dialog).getByText(/PACS \/ Neu/)).toBeVisible()
 expect(within(dialog).getByText(/PACS \/ Host/)).toBeVisible()
 expect(within(dialog).getByText(/PACS \/ Port/)).toBeVisible()
 expect(within(dialog).getByText(/PACS \/ Called AE/)).toBeVisible()
 expect(within(dialog).getByText(/PACS \/ Dienst/)).toBeVisible()
 expect(imported).not.toHaveBeenCalled()
 await userEvent.click(within(dialog).getByRole('button',{name:'Import bestätigen'}))
 await waitFor(()=>expect(imported).toHaveBeenCalledWith(configuration))
})

it('saves a validated default Calling AE and applies compact tables immediately',async()=>{setup();const ae=screen.getByLabelText('Default Calling AE');await userEvent.clear(ae);await userEvent.type(ae,'local_aet');await userEvent.click(screen.getByRole('button',{name:'Einstellungen speichern'}));expect(JSON.parse(localStorage.getItem('dcmsim-settings')??'{}').callingAe).toBe('LOCAL_AET');await userEvent.click(screen.getByRole('button',{name:'UI'}));await userEvent.click(screen.getByLabelText('Kompakte Tabellenansicht'));await userEvent.click(screen.getByRole('button',{name:'Einstellungen speichern'}));expect(document.documentElement).toHaveClass('compact-tables')})

it('shows effective server settings without fake editable controls',async()=>{vi.spyOn(api,'runtimeSettings').mockResolvedValue({connect_timeout:7.5,association_timeout:12,dimse_timeout:30,log_level:'WARNING'});setup();expect(await screen.findByText('7.5 s')).toBeVisible();expect(screen.getByText('12 s')).toBeVisible();expect(screen.getByText('30 s')).toBeVisible();expect(screen.queryByLabelText('Connect Timeout (Sekunden)')).not.toBeInTheDocument();await userEvent.click(screen.getByRole('button',{name:'Logging'}));expect(screen.getByText('WARNING')).toBeVisible();expect(screen.queryByRole('button',{name:'Einstellungen speichern'})).not.toBeInTheDocument()})
