import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach,vi} from 'vitest'
import {api,Result,WorklistEntry} from '../api/client'
import {Worklist} from '../pages/Worklist'

const entry:WorklistEntry={patient_name:'TEST^PATIENT',patient_id:'P1',birth_date:'',accession_number:'A1',modality:'CT',station_ae:'CT01',start_date:'20260912',start_time:'120000',sps_description:'',requested_procedure_description:'',dataset:[{tag:'(0010,0010)',name:'Patient Name',vr:'PN',value:'TEST^PATIENT'}]}
const found:Result={success:true,status:'0x0000',duration_ms:15,count:1,entries:[entry]}
const empty:Result={success:true,status:'0x0000',duration_ms:10,count:0,entries:[],active_filters:{station_ae:'CT01'}}

function setup(){vi.spyOn(api,'targets').mockResolvedValue([]);return render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Worklist/></MemoryRouter></QueryClientProvider>)}

async function configure(){await userEvent.type(screen.getByLabelText('Host'),'127.0.0.1');await userEvent.type(screen.getByLabelText('Called AE'),'TESTMWL')}

afterEach(()=>vi.restoreAllMocks())

it('clears Worklist patient data when filters or target change',async()=>{
 vi.spyOn(api,'mwl').mockResolvedValue(found)
 setup()
 await configure()
 await userEvent.click(screen.getByRole('button',{name:'Worklist abfragen'}))
 await screen.findByText('TEST^PATIENT')
 await userEvent.type(screen.getByLabelText('Patient ID'),'P2')
 expect(screen.queryByText('TEST^PATIENT')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Worklist abfragen'}))
 await screen.findByText('TEST^PATIENT')
 await userEvent.type(screen.getByLabelText('Host'),'2')
 expect(screen.queryByText('TEST^PATIENT')).not.toBeInTheDocument()
})

it('ignores a late Worklist response after the input changes',async()=>{
 let resolveFirst!: (value:Result)=>void
 const first=new Promise<Result>(resolve=>{resolveFirst=resolve})
 const mwl=vi.spyOn(api,'mwl').mockReturnValueOnce(first).mockResolvedValueOnce(found)
 setup()
 await configure()
 await userEvent.click(screen.getByRole('button',{name:'Worklist abfragen'}))
 await waitFor(()=>expect(mwl).toHaveBeenCalledTimes(1))
 await userEvent.type(screen.getByLabelText('Patient ID'),'P2')
 resolveFirst({...found,entries:[{...entry,patient_name:'OLD^PATIENT'}]})
 await waitFor(()=>expect(screen.getByRole('button',{name:'Worklist abfragen'})).toBeEnabled())
 expect(screen.queryByText('OLD^PATIENT')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Worklist abfragen'}))
 expect(await screen.findByText('TEST^PATIENT')).toBeVisible()
 expect(mwl).toHaveBeenLastCalledWith(expect.objectContaining({filters:expect.objectContaining({patient_id:'P2'})}))
})

it('uses the updated filter snapshot for a zero-result diagnostic retry',async()=>{
 const mwl=vi.spyOn(api,'mwl').mockResolvedValueOnce(empty).mockResolvedValueOnce(found)
 setup()
 await configure()
 await userEvent.type(screen.getByLabelText('Station AE'),'CT01')
 await userEvent.click(screen.getByRole('button',{name:'Worklist abfragen'}))
 await screen.findByText('Keine Worklist-Einträge gefunden')
 await userEvent.click(screen.getByRole('button',{name:'Ohne Station AE testen'}))
 expect(await screen.findByText('TEST^PATIENT')).toBeVisible()
 expect(screen.getByLabelText('Station AE')).toHaveValue('')
 expect(mwl).toHaveBeenLastCalledWith(expect.objectContaining({broad:false,filters:expect.objectContaining({station_ae:''})}))
})
