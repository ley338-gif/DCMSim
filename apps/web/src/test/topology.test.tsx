import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor,within} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api,Area,DicomEndpoint,DicomSystem,Site,WorklistChannel} from '../api/client'
import {Topology} from '../pages/Topology'

const site:Site={id:1,name:'Klinikum Nord',created_at:'',updated_at:''}
const area:Area={id:2,site_id:1,name:'Radiologie',created_at:'',updated_at:''}
const system:DicomSystem={id:3,name:'RIS/PACS',created_at:'',updated_at:''}
const mwl:DicomEndpoint={id:4,system_id:3,name:'RIS MWL',service:'MWL',host:'ris.local',port:104,called_ae:'RIS_MWL',created_at:'',updated_at:''}
const channel:WorklistChannel={id:5,name:'CT Worklist',area_id:2,modality_code:'CT',mwl_endpoint_id:4,station_ae_mode:'profile',station_ae_fixed_value:null,modality_filter_mode:'fixed',modality_filter_fixed_value:'CT',created_at:'',updated_at:''}

function setup(){
 vi.spyOn(api,'sites').mockResolvedValue([site])
 vi.spyOn(api,'areas').mockResolvedValue([area])
 vi.spyOn(api,'dicomSystems').mockResolvedValue([system])
 vi.spyOn(api,'dicomEndpoints').mockResolvedValue([mwl])
 vi.spyOn(api,'worklistChannels').mockResolvedValue([channel])
 const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}})
 return render(<QueryClientProvider client={client}><MemoryRouter><Topology/></MemoryRouter></QueryClientProvider>)
}

afterEach(()=>vi.restoreAllMocks())

it('shows organizational and technical topology with understandable endpoint details',async()=>{
 setup()
 expect(await screen.findByRole('heading',{name:'Standorte und DICOM-Systeme'})).toBeVisible()
 expect(await screen.findByText('Klinikum Nord')).toBeVisible()
 expect(screen.getByText('Radiologie')).toBeVisible()
 expect(screen.getByText(/CT Worklist/)).toBeVisible()
 expect(screen.getByText('RIS/PACS')).toBeVisible()
 const technicalSection=screen.getByRole('heading',{name:'Technische DICOM-Systeme'}).closest('section')
 expect(technicalSection).not.toBeNull()
 expect(within(technicalSection!).getByText(/ris\.local:104/)).toBeVisible()
 expect(within(technicalSection!).getByText(/RIS_MWL/)).toBeVisible()
})

it('creates a site through an accessible modal and refreshes topology',async()=>{
 const create=vi.spyOn(api,'createSite').mockResolvedValue(site)
 setup()
 await userEvent.click(await screen.findByRole('button',{name:'Standort hinzufügen'}))
 await userEvent.type(screen.getByLabelText('Standortname'),'Klinikum Süd')
 await userEvent.click(screen.getByRole('button',{name:'Speichern'}))
 await waitFor(()=>expect(create).toHaveBeenCalledWith({name:'Klinikum Süd'}))
})

it('shows a useful error state when topology cannot be loaded',async()=>{
 vi.spyOn(api,'sites').mockRejectedValue(new Error('API nicht erreichbar'))
 vi.spyOn(api,'areas').mockResolvedValue([])
 vi.spyOn(api,'dicomSystems').mockResolvedValue([])
 vi.spyOn(api,'dicomEndpoints').mockResolvedValue([])
 vi.spyOn(api,'worklistChannels').mockResolvedValue([])
 const client=new QueryClient({defaultOptions:{queries:{retry:false}}})
 render(<QueryClientProvider client={client}><MemoryRouter><Topology/></MemoryRouter></QueryClientProvider>)
 expect(await screen.findByText('Topologie konnte nicht geladen werden')).toBeVisible()
 expect(screen.getByText('API nicht erreichbar')).toBeVisible()
})
