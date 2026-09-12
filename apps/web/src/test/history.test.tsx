import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {fireEvent,render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter,Route,Routes} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api,Run} from '../api/client'
import {History,HistoryDetail} from '../pages/History'
import {localDayAfterIso,localDayStartIso} from '../utils/dates'

const run:Run={id:1,test_type:'dicom_echo',target_id:null,manual_target_json:{host:'127.0.0.1',port:104,called_ae:'PACS',calling_ae:'DCMSIM'},started_at:'2026-09-12T10:00:00Z',duration_ms:12,success:true,status:'0x0000',result_json:{success:true,duration_ms:12}}

afterEach(()=>vi.restoreAllMocks())

it('filters and paginates history through the server query',async()=>{
 const history=vi.spyOn(api,'history').mockResolvedValue({items:[run],total:75,limit:50,offset:0})
 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><History/></MemoryRouter></QueryClientProvider>)
 expect(await screen.findByText('1–50 von 75 Tests')).toBeVisible()
 expect(history).toHaveBeenCalledWith(expect.objectContaining({limit:50,offset:0}))

 await userEvent.selectOptions(screen.getByLabelText('Status'),'false')
 await waitFor(()=>expect(history).toHaveBeenCalledWith(expect.objectContaining({success:false,offset:0})))

 await userEvent.click(screen.getByRole('button',{name:'Weiter'}))
 await waitFor(()=>expect(history).toHaveBeenCalledWith(expect.objectContaining({success:false,offset:50})))
})

it('filters history by whole local days and rejects reversed dates',async()=>{
 const history=vi.spyOn(api,'history').mockResolvedValue({items:[run],total:1,limit:50,offset:0})
 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><History/></MemoryRouter></QueryClientProvider>)
 await screen.findByText('1–1 von 1 Tests')
 fireEvent.change(screen.getByLabelText('Von'),{target:{value:'2026-09-12'}})
 fireEvent.change(screen.getByLabelText('Bis'),{target:{value:'2026-09-12'}})
 await waitFor(()=>expect(history).toHaveBeenCalledWith(expect.objectContaining({started_from:localDayStartIso('2026-09-12'),started_before:localDayAfterIso('2026-09-12'),offset:0})))
 const calls=history.mock.calls.length
 fireEvent.change(screen.getByLabelText('Bis'),{target:{value:'2026-09-11'}})
 expect(await screen.findByText('Das Bis-Datum muss am oder nach dem Von-Datum liegen.')).toBeVisible()
 expect(screen.getByRole('button',{name:'CSV exportieren'})).toBeDisabled()
 expect(history).toHaveBeenCalledTimes(calls)
})

it('shows the original endpoint snapshot for a saved target',async()=>{
 const saved:Run={...run,target_id:7,manual_target_json:null,target_snapshot_json:{name:'PACS Alt',host:'192.0.2.1',port:11112,called_ae:'PACSOLD',calling_ae:'DCMSIM'}}
 vi.spyOn(api,'run').mockResolvedValue(saved)
 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={['/history/1']}><Routes><Route path="/history/:id" element={<HistoryDetail/>}/></Routes></MemoryRouter></QueryClientProvider>)
 expect(await screen.findByText('PACS Alt')).toBeVisible()
 expect(screen.getByText('192.0.2.1')).toBeVisible()
 expect(screen.getByText('11112')).toBeVisible()
 expect(screen.getByText('PACSOLD')).toBeVisible()
})
