import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach} from 'vitest'
import {api} from '../api/client'
import {StudyQuery} from '../pages/StudyQuery'

function setup(){return render(<QueryClientProvider client={new QueryClient()}><StudyQuery/></QueryClientProvider>)}

afterEach(()=>vi.restoreAllMocks())

it('runs a safe study query and opens the DICOM response',async()=>{
 vi.spyOn(api,'targets').mockResolvedValue([{id:1,name:'PACS Query',host:'127.0.0.1',mwl_enabled:false,mwl_port:null,mwl_called_ae:null,store_enabled:false,store_port:null,store_called_ae:null,qr_enabled:true,qr_port:11114,qr_called_ae:'PACSQR',default_calling_ae:'DCMSIM',created_at:'',updated_at:''}])
 const studies=vi.spyOn(api,'studies').mockResolvedValue({success:true,status:'0x0000',duration_ms:21,count:1,entries:[{patient_name:'DCMSIM^QUERY',patient_id:'DCMSIM-Q1',accession_number:'QR-1',study_date:'20260911',study_time:'101500',study_description:'SYNTHETIC STUDY',study_instance_uid:'1.2.826.1',modalities:'CT',series_count:2,instance_count:42,dataset:[{tag:'(0020,000D)',name:'Study Instance UID',vr:'UI',value:'1.2.826.1'}]}]})
 setup()
 await screen.findByRole('option',{name:'PACS Query'})
 await userEvent.selectOptions(screen.getByLabelText('Ziel'),'1')
 await userEvent.click(screen.getByRole('button',{name:'Studien suchen'}))
 await waitFor(()=>expect(studies).toHaveBeenCalledWith(expect.objectContaining({host:'127.0.0.1',port:11114,called_ae:'PACSQR',filters:expect.objectContaining({study_date:expect.any(String)})})))
 expect(await screen.findByText('SYNTHETIC STUDY')).toBeVisible()
 await userEvent.click(screen.getByText('SYNTHETIC STUDY'))
 expect(screen.getByRole('dialog',{name:'DICOM-Studienantwort'})).toBeVisible()
 expect(screen.getByText('Study Instance UID')).toBeVisible()
})

const study=(description:string)=>({patient_name:'TEST^PATIENT',patient_id:'P1',accession_number:'A1',study_date:'20260912',study_time:'120000',study_description:description,study_instance_uid:`1.2.3.${description.length}`,modalities:'CT',series_count:1,instance_count:1,dataset:[{tag:'(0020,000D)',name:'Study Instance UID',vr:'UI',value:'1.2.3'}]})

it('clears studies and closes details when the target or filters change',async()=>{
 vi.spyOn(api,'targets').mockResolvedValue([])
 vi.spyOn(api,'studies').mockResolvedValue({success:true,status:'0x0000',duration_ms:10,count:1,entries:[study('OLD STUDY')]})
 setup()
 await userEvent.type(screen.getByLabelText('Host'),'127.0.0.1')
 await userEvent.type(screen.getByLabelText('Called AE'),'PACSQR')
 await userEvent.click(screen.getByRole('button',{name:'Studien suchen'}))
 await userEvent.click(await screen.findByText('OLD STUDY'))
 expect(screen.getByRole('dialog',{name:'DICOM-Studienantwort'})).toBeVisible()
 await userEvent.type(screen.getByLabelText('Patient ID'),'P2')
 expect(screen.queryByRole('dialog',{name:'DICOM-Studienantwort'})).not.toBeInTheDocument()
 expect(screen.queryByText('OLD STUDY')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Studien suchen'}))
 expect(await screen.findByText('OLD STUDY')).toBeVisible()
 await userEvent.type(screen.getByLabelText('Host'),'2')
 expect(screen.queryByText('OLD STUDY')).not.toBeInTheDocument()
})

it('does not display a late response for inputs changed during the request',async()=>{
 vi.spyOn(api,'targets').mockResolvedValue([])
 let resolveFirst!: (value:Awaited<ReturnType<typeof api.studies>>)=>void
 const first=new Promise<Awaited<ReturnType<typeof api.studies>>>(resolve=>{resolveFirst=resolve})
 const studies=vi.spyOn(api,'studies').mockReturnValueOnce(first).mockResolvedValueOnce({success:true,status:'0x0000',duration_ms:12,count:1,entries:[study('NEW STUDY')]})
 setup()
 await userEvent.type(screen.getByLabelText('Host'),'127.0.0.1')
 await userEvent.type(screen.getByLabelText('Called AE'),'PACSQR')
 await userEvent.click(screen.getByRole('button',{name:'Studien suchen'}))
 await waitFor(()=>expect(studies).toHaveBeenCalledTimes(1))
 await userEvent.type(screen.getByLabelText('Patient ID'),'P2')
 resolveFirst({success:true,status:'0x0000',duration_ms:10,count:1,entries:[study('OLD STUDY')]})
 await waitFor(()=>expect(screen.getByRole('button',{name:'Studien suchen'})).toBeEnabled())
 expect(screen.queryByText('OLD STUDY')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Studien suchen'}))
 expect(await screen.findByText('NEW STUDY')).toBeVisible()
 expect(studies).toHaveBeenLastCalledWith(expect.objectContaining({filters:expect.objectContaining({patient_id:'P2'})}))
})
