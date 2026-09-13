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
 vi.spyOn(api,'dicomSystems').mockResolvedValue([{id:2,name:'PACS Archiv',created_at:'',updated_at:''}])
 vi.spyOn(api,'dicomEndpoints').mockResolvedValue([{id:3,system_id:2,name:'PACS Query',service:'QR',host:'127.0.0.1',port:11114,called_ae:'PACSQR',created_at:'',updated_at:''}])
 vi.spyOn(api,'runs').mockResolvedValue(runs)
 vi.spyOn(api,'dashboardSummary').mockResolvedValue({today_total:110,today_success:101,by_type:{qr_find:120,modality_check:80,mwl_find:5,dicom_store:7,dicom_echo:3}})
 vi.spyOn(api,'targetStatuses').mockResolvedValue([{target_id:1,run_id:3,test_type:'dicom_echo',started_at:new Date().toISOString(),duration_ms:50,success:false,status:'DICOM_TIMEOUT',configuration_state:'current'}])
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
 expect(screen.getByText('Query/Retrieve-Endpoints')).toBeVisible()
 expect(screen.getByText('Fehlgeschlagen')).toBeVisible()
 expect(screen.getByText('110')).toBeVisible()
 expect(screen.getByText('101 erfolgreich')).toBeVisible()
 expect(screen.getByText('92 %')).toBeVisible()
 expect(screen.getByText('120 Tests')).toBeVisible()
 expect(screen.getByText('80 Tests')).toBeVisible()
 expect(screen.getByText('3 Tests')).toBeVisible()
 const [dayStart,dayEnd]=vi.mocked(api.dashboardSummary).mock.calls[0]
 expect(new Date(dayStart).getHours()).toBe(0)
 expect(new Date(dayEnd).getHours()).toBe(0)
})
