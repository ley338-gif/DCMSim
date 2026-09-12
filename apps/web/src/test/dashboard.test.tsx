import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen} from '@testing-library/react'
import {MemoryRouter} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api,Run,Target} from '../api/client'
import {Dashboard} from '../pages/Dashboard'

const target:Target={id:1,name:'PACS Archiv',host:'127.0.0.1',mwl_enabled:false,mwl_port:null,mwl_called_ae:null,store_enabled:false,store_port:null,store_called_ae:null,qr_enabled:true,qr_port:11114,qr_called_ae:'PACSQR',default_calling_ae:'DCMSIM',created_at:'',updated_at:''}
const runs:Run[]=[
 {id:2,test_type:'qr_find',target_id:1,manual_target_json:{host:'127.0.0.1',port:11114,called_ae:'PACSQR',calling_ae:'DCMSIM'},started_at:new Date().toISOString(),duration_ms:21,success:true,status:'0x0000',result_json:{success:true,duration_ms:21,count:3}},
 {id:1,test_type:'modality_check',target_id:null,manual_target_json:null,started_at:new Date().toISOString(),duration_ms:42,success:true,status:'success',result_json:{success:true,duration_ms:42,profile_name:'CT Notaufnahme',overall:'success'}},
]

afterEach(()=>vi.restoreAllMocks())

it('integrates PACS query targets and runs across the dashboard',async()=>{
 vi.spyOn(api,'targets').mockResolvedValue([target])
 vi.spyOn(api,'runs').mockResolvedValue(runs)
 vi.spyOn(api,'targetStatuses').mockResolvedValue([{target_id:1,run_id:3,test_type:'dicom_echo',started_at:new Date().toISOString(),duration_ms:50,success:false,status:'DICOM_TIMEOUT'}])
 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Dashboard/></MemoryRouter></QueryClientProvider>)
 expect(await screen.findByText('PACS Archiv')).toBeVisible()
 expect(screen.getByText('PACSQR')).toBeVisible()
 expect(screen.getByText('PACS-Studien suchen')).toBeVisible()
 expect(screen.getByText('Query/Retrieve SCU')).toBeVisible()
 expect(screen.getAllByText('PACS-Suche').length).toBeGreaterThan(1)
 expect(screen.getAllByText('Modalitätsprüfung').length).toBeGreaterThan(1)
 expect(screen.getByText('3 Treffer')).toBeVisible()
 expect(screen.getByText('PASS')).toBeVisible()
 expect(screen.getByText('CT Notaufnahme')).toBeVisible()
 expect(screen.getByText('Query/Retrieve-Ziele')).toBeVisible()
 expect(screen.getByText('Fehlgeschlagen')).toBeVisible()
})
