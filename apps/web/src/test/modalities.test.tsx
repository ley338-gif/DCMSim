import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api,ModalityCheckResult,ModalityProfile,Target} from '../api/client'
import {Modalities} from '../pages/Modalities'

const target:Target={id:1,name:'JiveX Produktion',host:'127.0.0.1',mwl_enabled:true,mwl_port:11112,mwl_called_ae:'JIVEXWL',store_enabled:true,store_port:11113,store_called_ae:'JIVEX',default_calling_ae:'DCMSIM',created_at:'',updated_at:''}
const profile:ModalityProfile={id:4,name:'Aplio 300 – Sono 2',description:'Sono Raum 2',modality:'US',calling_ae:'APLIO02',mwl_enabled:true,mwl_target_id:1,store_enabled:true,store_target_id:1,created_at:'',updated_at:''}
const success:ModalityCheckResult={success:true,status:'PASS',duration_ms:42,overall:'success',profile_id:4,profile_name:profile.name,modality:'US',calling_ae:'APLIO02',run_id:10,worklist:{success:true,status:'0x0000',duration_ms:18,count:14,association:true,query:{station_ae:'APLIO02'}},store:{success:true,status:'0x0000',duration_ms:24,association:true,sop_class:'Ultrasound Image Storage',transfer_syntax:'Explicit VR Little Endian'}}

function setup(profiles:ModalityProfile[]=[profile]){vi.spyOn(api,'modalityProfiles').mockResolvedValue(profiles);vi.spyOn(api,'targets').mockResolvedValue([target]);const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter><Modalities/></MemoryRouter></QueryClientProvider>)}

afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()})

it('loads the modality list with referenced targets',async()=>{setup();expect(await screen.findByText(profile.name)).toBeVisible();expect(screen.getAllByText('JiveX Produktion')).toHaveLength(2);expect(screen.getByText('APLIO02')).toBeVisible()})

it('creates a modality and validates target selection and Calling AE input',async()=>{const create=vi.spyOn(api,'createModalityProfile').mockResolvedValue(profile);setup([]);await userEvent.click(await screen.findByRole('button',{name:'Neue Modalität'}));await userEvent.type(screen.getByLabelText('Name'),'Aplio 300 – Sono 2');const calling=screen.getByLabelText('Calling AE');await userEvent.clear(calling);await userEvent.type(calling,'aplio02');expect(calling).toHaveValue('APLIO02');expect(calling).toHaveAttribute('maxlength','16');expect(calling).toHaveAttribute('pattern');await userEvent.selectOptions(screen.getByLabelText('Worklist Target'),'1');await userEvent.selectOptions(screen.getByLabelText('Store Target'),'1');await userEvent.click(screen.getByRole('button',{name:'Speichern'}));await waitFor(()=>expect(create).toHaveBeenCalledWith(expect.objectContaining({calling_ae:'APLIO02',mwl_target_id:1,store_target_id:1})))})

it('edits and deletes an existing modality',async()=>{const update=vi.spyOn(api,'updateModalityProfile').mockResolvedValue({...profile,name:'Aplio 300 aktualisiert'});const remove=vi.spyOn(api,'deleteModalityProfile').mockResolvedValue();vi.stubGlobal('confirm',()=>true);setup();await userEvent.click(await screen.findByRole('button',{name:'Bearbeiten'}));const name=screen.getByLabelText('Name');await userEvent.clear(name);await userEvent.type(name,'Aplio 300 aktualisiert');await userEvent.click(screen.getByRole('button',{name:'Speichern'}));await waitFor(()=>expect(update).toHaveBeenCalledWith(4,expect.objectContaining({name:'Aplio 300 aktualisiert'})));await userEvent.click(screen.getByRole('button',{name:`${profile.name} löschen`}));await waitFor(()=>expect(remove.mock.calls[0][0]).toBe(4))})

it('shows loading, complete success and technical details for a modality check',async()=>{let resolve:(value:ModalityCheckResult)=>void=()=>{};const pending=new Promise<ModalityCheckResult>(done=>{resolve=done});vi.spyOn(api,'checkModalityProfile').mockReturnValue(pending);setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));expect(screen.getByText('Worklist und PACS Store werden nacheinander getestet …')).toBeVisible();resolve(success);expect(await screen.findByText('Overall PASS')).toBeVisible();expect(screen.getByText('14')).toBeVisible();expect(screen.getByText('Ultrasound Image Storage')).toBeVisible();await userEvent.click(screen.getByText('Technische Details'));expect(screen.getByText(/"profile_id": 4/)).toBeVisible()})

it.each([
 ['worklist',{...success,success:false,status:'FAIL',overall:'failure' as const,worklist:{success:false,code:'DICOM_C_FIND_FAILED',message:'C-FIND failed',duration_ms:12,association:true},store:success.store}],
 ['store',{...success,success:false,status:'FAIL',overall:'failure' as const,worklist:success.worklist,store:{success:false,code:'DICOM_STORE_FAILED',message:'C-STORE failed',duration_ms:12,association:true}}],
])('shows a partial %s failure separately from the successful service',async(_service,result)=>{vi.spyOn(api,'checkModalityProfile').mockResolvedValue(result as ModalityCheckResult);setup();await userEvent.click(await screen.findByRole('button',{name:'Modalität prüfen'}));expect(await screen.findByText('Overall FAIL')).toBeVisible();expect(screen.getAllByText((result as ModalityCheckResult).worklist.success?'DICOM_STORE_FAILED':'DICOM_C_FIND_FAILED').length).toBeGreaterThan(0);expect(screen.getAllByText('PASS').length).toBeGreaterThan(0);expect(screen.getAllByText('FAIL').length).toBeGreaterThan(0)})
