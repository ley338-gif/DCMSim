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
