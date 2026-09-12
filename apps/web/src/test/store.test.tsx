import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach,vi} from 'vitest'
import {api,Result} from '../api/client'
import {Store} from '../pages/Store'

const stored:Result={success:true,status:'0x0000',duration_ms:20,study_instance_uid:'1.2.3',patient_name:'DCMSIM^TEST'}

function setup(){vi.spyOn(api,'targets').mockResolvedValue([]);return render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Store/></MemoryRouter></QueryClientProvider>)}
async function configure(){await userEvent.type(screen.getByLabelText('Host'),'127.0.0.1');await userEvent.type(screen.getByLabelText('Called AE'),'PACS')}

afterEach(()=>vi.restoreAllMocks())

it('shows C-ECHO separately from C-STORE transfer progress',async()=>{
 vi.spyOn(api,'echo').mockResolvedValue({success:true,status:'0x0000',duration_ms:9})
 setup()
 await configure()
 await userEvent.click(screen.getByRole('button',{name:'Verbindung testen'}))
 expect(await screen.findByText('C-ECHO erfolgreich')).toBeVisible()
 expect(screen.getByText('Bereit zum Senden')).toBeVisible()
 expect(screen.queryByText('C-STORE erfolgreich')).not.toBeInTheDocument()
})

it('clears an old transfer result when the target, SOP class or test mode changes',async()=>{
 vi.spyOn(api,'store').mockResolvedValue(stored)
 setup()
 await configure()
 await userEvent.click(screen.getByRole('button',{name:'C-STORE senden'}))
 expect(await screen.findByText('C-STORE erfolgreich')).toBeVisible()
 await userEvent.selectOptions(screen.getByLabelText('SOP Class'),'ct')
 expect(screen.queryByText('C-STORE erfolgreich')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'C-STORE senden'}))
 expect(await screen.findByText('C-STORE erfolgreich')).toBeVisible()
 await userEvent.click(screen.getByRole('button',{name:'DICOM-Datei'}))
 expect(screen.queryByText('C-STORE erfolgreich')).not.toBeInTheDocument()
 expect(screen.getByText('Keine Datei ausgewählt')).toBeVisible()
 expect(screen.queryByText('DCMSIM^TEST')).not.toBeInTheDocument()
})

it('ignores late C-STORE and C-ECHO answers after the endpoint changes',async()=>{
 let resolveStore!: (value:Result)=>void
 const firstStore=new Promise<Result>(resolve=>{resolveStore=resolve})
 const store=vi.spyOn(api,'store').mockReturnValueOnce(firstStore).mockResolvedValueOnce(stored)
 let resolveEcho!: (value:Result)=>void
 const firstEcho=new Promise<Result>(resolve=>{resolveEcho=resolve})
 vi.spyOn(api,'echo').mockReturnValueOnce(firstEcho)
 setup()
 await configure()
 await userEvent.click(screen.getByRole('button',{name:'C-STORE senden'}))
 await userEvent.clear(screen.getByLabelText('Host'))
 await userEvent.type(screen.getByLabelText('Host'),'127.0.0.2')
 resolveStore(stored)
 await waitFor(()=>expect(screen.getByRole('button',{name:'C-STORE senden'})).toBeEnabled())
 expect(screen.queryByText('C-STORE erfolgreich')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Verbindung testen'}))
 await userEvent.clear(screen.getByLabelText('Host'))
 await userEvent.type(screen.getByLabelText('Host'),'127.0.0.3')
 resolveEcho({success:true,status:'0x0000',duration_ms:9})
 await waitFor(()=>expect(screen.getByRole('button',{name:'Verbindung testen'})).toBeEnabled())
 expect(screen.queryByText('C-ECHO erfolgreich')).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'C-STORE senden'}))
 expect(await screen.findByText('C-STORE erfolgreich')).toBeVisible()
 expect(store).toHaveBeenLastCalledWith(expect.objectContaining({host:'127.0.0.3'}))
})

it('ignores metadata analysis for a file removed before the answer arrives',async()=>{
 let resolveAnalysis!: (value:Record<string,string>)=>void
 const analysis=new Promise<Record<string,string>>(resolve=>{resolveAnalysis=resolve})
 vi.spyOn(api,'analyzeUpload').mockReturnValue(analysis)
 const view=setup()
 await userEvent.click(screen.getByRole('button',{name:'DICOM-Datei'}))
 const input=view.container.querySelector('input[type="file"]') as HTMLInputElement
 await userEvent.upload(input,new File(['DICOM'],'sample.dcm',{type:'application/dicom'}))
 expect(screen.getAllByText('sample.dcm')).toHaveLength(2)
 await userEvent.click(screen.getByRole('button',{name:'Datei entfernen'}))
 resolveAnalysis({patient_name:'PRIVATE^PATIENT',patient_id:'P123'})
 await waitFor(()=>expect(screen.getByText('Keine Datei ausgewählt')).toBeVisible())
 expect(screen.queryByText('PRIVATE^PATIENT')).not.toBeInTheDocument()
})
