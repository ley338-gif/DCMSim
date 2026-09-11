import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {render,screen,waitFor} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {afterEach} from 'vitest'
import {api} from '../api/client'
import {SettingsPage} from '../pages/Settings'

function setup(){return render(<QueryClientProvider client={new QueryClient()}><SettingsPage/></QueryClientProvider>)}

afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()})

it('purges history using the configured retention without a scheduler',async()=>{vi.stubGlobal('confirm',()=>true);const purge=vi.spyOn(api,'purgeHistory').mockResolvedValue({deleted_count:3,cutoff:''});setup();await userEvent.click(screen.getByRole('button',{name:'Retention'}));await userEvent.click(screen.getByRole('button',{name:'Alte Historie bereinigen'}));await waitFor(()=>expect(purge).toHaveBeenCalledWith(90));expect(await screen.findByText('3 alte Historieneinträge wurden gelöscht.')).toBeVisible()})

it('offers configuration export, import and SQLite backup',async()=>{vi.stubGlobal('URL',{...URL,createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}});vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});const exported=vi.spyOn(api,'exportConfiguration').mockResolvedValue({format_version:1,targets:[],modality_profiles:[]});vi.spyOn(api,'databaseBackup').mockResolvedValue(new Blob(['db']));setup();await userEvent.click(screen.getByRole('button',{name:'Datensicherung'}));await userEvent.click(screen.getByRole('button',{name:'Konfiguration exportieren'}));await waitFor(()=>expect(exported).toHaveBeenCalled());expect(screen.getByLabelText('Konfigurationsdatei auswählen')).toBeInTheDocument();expect(screen.getByRole('button',{name:'SQLite-Backup erstellen'})).toBeVisible()})
