import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen} from '@testing-library/react'
import {MemoryRouter} from 'react-router-dom'
import {api} from '../api/client'
import {AppShell} from '../components/layout/AppShell'

it('shows the proxy user in the header',async()=>{
 vi.spyOn(api,'session').mockResolvedValue({username:'alice'})
 render(<QueryClientProvider client={new QueryClient()}><MemoryRouter><AppShell><div>Inhalt</div></AppShell></MemoryRouter></QueryClientProvider>)
 expect(await screen.findByText('alice')).toBeVisible()
 expect(screen.queryByText('Ohne Anmeldung')).not.toBeInTheDocument()
 vi.restoreAllMocks()
})
