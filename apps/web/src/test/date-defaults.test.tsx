import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen} from '@testing-library/react'
import {MemoryRouter} from 'react-router-dom'
import {afterEach,expect,it,vi} from 'vitest'
import {api} from '../api/client'
import {StudyQuery} from '../pages/StudyQuery'
import {Worklist} from '../pages/Worklist'

afterEach(()=>{vi.useRealTimers();vi.restoreAllMocks()})

it('initializes DICOM date filters from the local day on each page mount',()=>{
 vi.useFakeTimers({toFake:['Date']})
 vi.spyOn(api,'targets').mockResolvedValue([])
 vi.setSystemTime(new Date(2026,8,12,12))
 const first=render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Worklist/></MemoryRouter></QueryClientProvider>)
 expect(screen.getByLabelText('Datum')).toHaveValue('2026-09-12')
 first.unmount()

 vi.setSystemTime(new Date(2026,8,13,12))
 const second=render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><Worklist/></MemoryRouter></QueryClientProvider>)
 expect(screen.getByLabelText('Datum')).toHaveValue('2026-09-13')
 second.unmount()

 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><StudyQuery/></MemoryRouter></QueryClientProvider>)
 expect(document.querySelector<HTMLInputElement>('#study-date')).toHaveValue('2026-09-13')
})
