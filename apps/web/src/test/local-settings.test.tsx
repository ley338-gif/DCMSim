import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {MemoryRouter} from 'react-router-dom'
import {afterEach} from 'vitest'
import {api} from '../api/client'
import {Modalities} from '../pages/Modalities'
import {Targets} from '../pages/Targets'
import {Worklist} from '../pages/Worklist'
import {loadLocalSettings} from '../settings/localSettings'

function wrapper(children:React.ReactNode){return <QueryClientProvider client={new QueryClient()}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>}

afterEach(()=>{vi.restoreAllMocks();localStorage.clear()})

it('normalizes invalid locally stored values',()=>{localStorage.setItem('dcmsim-settings',JSON.stringify({callingAe:'invalid ae title that is too long',retention:-1,compact:'yes'}));expect(loadLocalSettings()).toEqual(expect.objectContaining({callingAe:'DCMSIM',retention:90,compact:false}))})

it('uses the saved Calling AE for manual tests and new configuration',async()=>{
 localStorage.setItem('dcmsim-settings',JSON.stringify({callingAe:'LOCAL_AET'}))
 vi.spyOn(api,'targets').mockResolvedValue([])
 vi.spyOn(api,'targetStatuses').mockResolvedValue([])
 const worklist=render(wrapper(<Worklist/>))
 expect(await screen.findByLabelText('Calling AE')).toHaveValue('LOCAL_AET')
 worklist.unmount()

 vi.spyOn(api,'modalityProfiles').mockResolvedValue([])
 const targets=render(wrapper(<Targets/>))
 await userEvent.click(await screen.findByRole('button',{name:'Neues Ziel'}))
 expect(screen.getByLabelText('Default Calling AE')).toHaveValue('LOCAL_AET')
 targets.unmount()

 render(wrapper(<Modalities/>))
 await userEvent.click(await screen.findByRole('button',{name:'Neue Modalität'}))
 expect(screen.getByLabelText('Calling AE')).toHaveValue('LOCAL_AET')
})
