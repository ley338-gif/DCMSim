import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor,within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api,Area,DicomEndpoint,ModalityCheckResult,ModalityProfile,Site,WorklistChannel} from '../api/client'
import {Modalities} from '../pages/Modalities'

const site:Site={id:1,name:'Klinikum Nord',created_at:'',updated_at:''}
const area:Area={id:2,site_id:1,name:'Radiologie',created_at:'',updated_at:''}
const channel:WorklistChannel={id:5,name:'US Worklist',area_id:2,modality_code:'US',mwl_endpoint_id:7,station_ae_mode:'profile',station_ae_fixed_value:null,modality_filter_mode:'profile',modality_filter_fixed_value:null,created_at:'',updated_at:''}
const store:DicomEndpoint={id:6,system_id:3,name:'PACS Store',service:'STORE',host:'pacs.local',port:11112,called_ae:'PACS',created_at:'',updated_at:''}
const profile:ModalityProfile={id:4,name:'Aplio 300 – Sono 2',description:'Sono Raum 2',modality:'US',calling_ae:'APLIO02',mwl_enabled:true,mwl_target_id:null,store_enabled:true,store_target_id:null,area_id:2,worklist_channel_id:5,store_endpoint_id:6,created_at:'',updated_at:''}
const success:ModalityCheckResult={success:true,status:'PASS',duration_ms:42,overall:'success',profile_id:4,profile_name:profile.name,modality:'US',calling_ae:'APLIO02',run_id:10,worklist:{success:true,status:'0x0000',duration_ms:18,count:14,association:true,query:{station_ae:'APLIO02'}},store:{success:true,status:'0x0000',duration_ms:24,association:true,sop_class:'Ultrasound Image Storage',transfer_syntax:'Explicit VR Little Endian'}}

function setup(profiles:ModalityProfile[]=[profile],options:{areas?:Area[];channels?:WorklistChannel[];endpoints?:DicomEndpoint[]}={}){vi.spyOn(api,'modalityProfiles').mockResolvedValue(profiles);vi.spyOn(api,'sites').mockResolvedValue([site]);vi.spyOn(api,'areas').mockResolvedValue(options.areas??[area]);vi.spyOn(api,'worklistChannels').mockResolvedValue(options.channels??[channel]);vi.spyOn(api,'dicomEndpoints').mockResolvedValue(options.endpoints??[store]);const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><Modalities/></MemoryRouter></QueryClientProvider>)}

afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()})

it('allows an MWL-only profile to be checked and edited without a STORE endpoint',async()=>{
 const mwlOnly={...profile,mwl_enabled:true,store_enabled:false,store_endpoint_id:null}
 setup([mwlOnly])
 expect(await screen.findByRole('button',{name:'Modalität prüfen'})).toBeEnabled()
 expect(screen.getByText('Deaktiviert')).toBeVisible()
 await userEvent.click(screen.getByRole('button',{name:'Bearbeiten'}))
 expect(screen.getByLabelText('MWL aktiviert')).toBeChecked()
 expect(screen.getByLabelText('STORE aktiviert')).not.toBeChecked()
 expect(screen.getByLabelText('Worklist-Kanal')).toBeRequired()
 expect(screen.getByLabelText('Worklist-Kanal')).toBeEnabled()
 expect(screen.getByLabelText('STORE-Endpoint')).not.toBeRequired()
 expect(screen.getByLabelText('STORE-Endpoint')).toBeDisabled()
})

it('allows a STORE-only profile to be checked and edited without a worklist channel',async()=>{
 const storeOnly={...profile,mwl_enabled:false,worklist_channel_id:null,store_enabled:true}
 setup([storeOnly])
 expect(await screen.findByRole('button',{name:'Modalität prüfen'})).toBeEnabled()
 await userEvent.click(screen.getByRole('button',{name:'Bearbeiten'}))
 expect(screen.getByLabelText('MWL aktiviert')).not.toBeChecked()
 expect(screen.getByLabelText('Worklist-Kanal')).toBeDisabled()
 expect(screen.getByLabelText('Worklist-Kanal')).not.toBeRequired()
 expect(screen.getByLabelText('STORE aktiviert')).toBeChecked()
 expect(screen.getByLabelText('STORE-Endpoint')).toBeEnabled()
 expect(screen.getByLabelText('STORE-Endpoint')).toBeRequired()
})

it('keeps an active legacy target fallback checkable and editable',async()=>{
 const legacy={...profile,mwl_enabled:true,mwl_target_id:12,worklist_channel_id:null,store_enabled:false,store_endpoint_id:null}
 const update=vi.spyOn(api,'updateModalityProfile').mockResolvedValue(legacy)
 setup([legacy])
 expect(await screen.findByText('Legacy-Ziel')).toBeVisible()
 expect(screen.getByRole('button',{name:'Modalität prüfen'})).toBeEnabled()
 await userEvent.click(screen.getByRole('button',{name:'Bearbeiten'}))
 expect(screen.getByLabelText('Worklist-Kanal')).not.toBeRequired()
 await userEvent.click(screen.getByRole('button',{name:'Speichern'}))
 await waitFor(()=>expect(update).toHaveBeenCalledWith(4,expect.objectContaining({mwl_target_id:12,worklist_channel_id:null})))
})

it('clears target references when a service is switched off',async()=>{
 const update=vi.spyOn(api,'updateModalityProfile').mockResolvedValue({...profile,store_enabled:false,store_endpoint_id:null})
 setup()
 await userEvent.click(await screen.findByRole('button',{name:'Bearbeiten'}))
 await userEvent.click(screen.getByLabelText('STORE aktiviert'))
 await userEvent.click(screen.getByRole('button',{name:'Speichern'}))
 await waitFor(()=>expect(update).toHaveBeenCalledWith(4,expect.objectContaining({store_enabled:false,store_target_id:null,store_endpoint_id:null})))
})

it('filters worklist channels by area and modality and clears incompatible selections',async()=>{
 const secondArea:Area={id:9,site_id:1,name:'MRT',created_at:'',updated_at:''}
 const ctChannel:WorklistChannel={...channel,name:'CT Worklist',modality_code:'CT'}
 const mrChannel:WorklistChannel={...channel,id:8,name:'MR Worklist',modality_code:'MR'}
 const otherAreaMr:WorklistChannel={...mrChannel,id:9,name:'MR Worklist anderer Bereich',area_id:9}
 setup([{...profile,modality:'CT'}],{areas:[area,secondArea],channels:[ctChannel,mrChannel,otherAreaMr]})
 await userEvent.click(await screen.findByRole('button',{name:'Bearbeiten'}))
 const channelSelect=screen.getByLabelText('Worklist-Kanal')
 expect(within(channelSelect).getByRole('option',{name:'CT Worklist · CT'})).toBeVisible()
 expect(within(channelSelect).queryByRole('option',{name:'MR Worklist · MR'})).not.toBeInTheDocument()
 expect(within(channelSelect).queryByRole('option',{name:/anderer Bereich/})).not.toBeInTheDocument()
 await userEvent.selectOptions(screen.getByLabelText('Modalität'),'MR')
 expect(channelSelect).toHaveValue('')
 expect(within(channelSelect).getByRole('option',{name:'MR Worklist · MR'})).toBeVisible()
 await userEvent.selectOptions(channelSelect,'8')
 await userEvent.selectOptions(screen.getByLabelText('Standort / Bereich'),'9')
 expect(channelSelect).toHaveValue('')
 expect(within(channelSelect).getByRole('option',{name:'MR Worklist anderer Bereich · MR'})).toBeVisible()
})

it('loads the modality list with referenced channel and endpoint',async()=>{setup();expect(await screen.findByText(profile.name)).toBeVisible();expect(screen.getByText('US Worklist')).toBeVisible();expect(screen.getByText('PACS Store')).toBeVisible();expect(screen.getByText('APLIO02')).toBeVisible()})

it('creates a modality and validates channel, endpoint and Calling AE input',async()=>{const create=vi.spyOn(api,'createModalityProfile').mockResolvedValue(profile);setup([]);await userEvent.click(await screen.findByRole('button',{name:'Neue Modalität'}));await userEvent.type(screen.getByLabelText('Name'),'Aplio 300 – Sono 2');const calling=screen.getByLabelText('Calling AE');await userEvent.clear(calling);await userEvent.type(calling,'aplio02');expect(calling).toHaveValue('APLIO02');expect(calling).toHaveAttribute('maxlength','16');expect(calling).toHaveAttribute('pattern');await userEvent.selectOptions(screen.getByLabelText('Modalität'),'US');await userEvent.selectOptions(screen.getByLabelText('Standort / Bereich'),'2');await userEvent.selectOptions(screen.getByLabelText('Worklist-Kanal'),'5');await userEvent.selectOptions(screen.getByLabelText('STORE-Endpoint'),'6');await userEvent.click(screen.getByRole('button',{name:'Speichern'}));await waitFor(()=>expect(create).toHaveBeenCalledWith(expect.objectContaining({calling_ae:'APLIO02',area_id:2,worklist_channel_id:5,store_endpoint_id:6})))})

it('edits and deletes an existing modality',async()=>{const update=vi.spyOn(api,'updateModalityProfile').mockResolvedValue({...profile,name:'Aplio 300 aktualisiert'});const remove=vi.spyOn(api,'deleteModalityProfile').mockResolvedValue();vi.stubGlobal('confirm',()=>true);setup();await userEvent.click(await screen.findByRole('button',{name:'Bearbeiten'}));const name=screen.getByLabelText('Name');await userEvent.clear(name);await userEvent.type(name,'Aplio 300 aktualisiert');await userEvent.click(screen.getByRole('button',{name:'Speichern'}));await waitFor(()=>expect(update).toHaveBeenCalledWith(4,expect.objectContaining({name:'Aplio 300 aktualisiert'})));await userEvent.click(screen.getByRole('button',{name:`${profile.name} löschen`}));await waitFor(()=>expect(remove.mock.calls[0][0]).toBe(4))})

it('shows loading, complete success and technical details for a modality check',async()=>{let resolve:(value:ModalityCheckResult)=>void=()=>{};const pending=new Promise<ModalityCheckResult>(done=>{resolve=done});vi.spyOn(api,'checkModalityProfile').mockReturnValue(pending);setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));expect(screen.getByText('Worklist und PACS Store werden nacheinander getestet …')).toBeVisible();resolve(success);expect(await screen.findByText('Overall PASS')).toBeVisible();expect(screen.getByText('14')).toBeVisible();expect(screen.getByText('Ultrasound Image Storage')).toBeVisible();await userEvent.click(screen.getByText('Technische Details'));expect(screen.getByText(/"profile_id": 4/)).toBeVisible()})

it('cancels the browser wait and can retry the last check',async()=>{const check=vi.spyOn(api,'checkModalityProfile').mockImplementation((_id,_syntax,signal)=>new Promise((resolve,reject)=>{signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')));if(check.mock.calls.length>1)resolve(success)}));setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));await userEvent.click(screen.getByRole('button',{name:'Anzeige abbrechen'}));expect(await screen.findByText('Anzeige abgebrochen')).toBeVisible();await userEvent.click(screen.getByRole('button',{name:'Modalität prüfen'}));expect(await screen.findByText('Overall PASS')).toBeVisible();await userEvent.click(screen.getByRole('button',{name:'Erneut prüfen'}));await waitFor(()=>expect(check).toHaveBeenCalledTimes(3))})

it('blocks checks for profiles with a deleted channel',async()=>{setup([{...profile,worklist_channel_id:null}]);expect(await screen.findByText('Konfiguration unvollständig')).toBeVisible();expect(screen.getByRole('button',{name:'Modalität prüfen'})).toBeDisabled()})

it('runs a broad zero-result diagnosis only after explicit confirmation',async()=>{const zero={...success,worklist:{...success.worklist,count:0}};const check=vi.spyOn(api,'checkModalityProfile').mockResolvedValue(zero);setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));expect(await screen.findByRole('button',{name:'Breite Worklist-Diagnose starten'})).toBeVisible();expect(check).toHaveBeenLastCalledWith(4,'explicit_vr_little_endian',expect.any(AbortSignal),false);await userEvent.click(screen.getByRole('button',{name:'Breite Worklist-Diagnose starten'}));await waitFor(()=>expect(check).toHaveBeenLastCalledWith(4,'explicit_vr_little_endian',expect.any(AbortSignal),true))})

it.each([
 ['worklist',{...success,success:false,status:'FAIL',overall:'failure' as const,worklist:{success:false,code:'DICOM_C_FIND_FAILED',message:'C-FIND failed',duration_ms:12,association:true},store:success.store}],
 ['store',{...success,success:false,status:'FAIL',overall:'failure' as const,worklist:success.worklist,store:{success:false,code:'DICOM_STORE_FAILED',message:'C-STORE failed',recommendation:'PACS-Importlog prüfen.',duration_ms:12,association:true}}],
])('shows a partial %s failure separately from the successful service',async(_service,result)=>{vi.spyOn(api,'checkModalityProfile').mockResolvedValue(result as ModalityCheckResult);setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));expect(await screen.findByText('Overall FAIL')).toBeVisible();expect(screen.getAllByText((result as ModalityCheckResult).worklist.success?'DICOM_STORE_FAILED':'DICOM_C_FIND_FAILED').length).toBeGreaterThan(0);expect(screen.getAllByText('PASS').length).toBeGreaterThan(0);expect(screen.getAllByText('FAIL').length).toBeGreaterThan(0)})

it('groups profiles by site and area and offers channel and STORE endpoint selection',async()=>{
 setup([profile])
 expect(await screen.findByRole('heading',{name:'Klinikum Nord'})).toBeVisible()
 expect(screen.getByRole('heading',{name:'Radiologie'})).toBeVisible()
 expect(screen.getByText('US Worklist')).toBeVisible()
 expect(screen.getByText('PACS Store')).toBeVisible()
 await userEvent.click(screen.getByRole('button',{name:'Bearbeiten'}))
 expect(screen.getByLabelText('Worklist-Kanal')).toHaveValue('5')
 expect(screen.getByLabelText('STORE-Endpoint')).toHaveValue('6')
})

it('keeps profiles with a missing area visible as not assigned',async()=>{
 setup([{...profile,area_id:null}])
 expect(await screen.findByRole('heading',{name:'Nicht zugeordnet'})).toBeVisible()
 expect(screen.getByText(profile.name)).toBeVisible()
})
