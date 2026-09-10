import {render,screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {DicomLogViewer} from '../components/dicom/DicomLogViewer'
import {TargetSelector} from '../components/dicom/TargetSelector'
import {TransferProgress} from '../components/dicom/TransferProgress'
import {Button} from '../components/ui/Button'
import {DataTable} from '../components/ui/DataTable'
import {StatusBadge} from '../components/ui/Status'

const target={id:1,name:'JiveX Test',host:'10.10.10.50',mwl_enabled:true,mwl_port:104,mwl_called_ae:'JIVEXWL',store_enabled:true,store_port:11112,store_called_ae:'JIVEX',default_calling_ae:'DCMSIM',created_at:'',updated_at:''}

it('supports button variants and loading state',()=>{render(<><Button variant="secondary">Senden</Button><Button loading>Warten</Button></>);expect(screen.getByRole('button',{name:'Senden'})).toBeEnabled();expect(screen.getByRole('button',{name:'Warten'})).toBeDisabled()})

it('renders status with text and not color alone',()=>{render(<StatusBadge tone="success">Online</StatusBadge>);expect(screen.getByText('Online')).toBeVisible()})

it('fills endpoint fields from a target selection',async()=>{const changed=vi.fn();render(<TargetSelector value={{host:'',port:104,called_ae:'',calling_ae:'DCMSIM'}} onChange={changed} targets={[target]} service="store"/>);await userEvent.selectOptions(screen.getByLabelText('Ziel'),'1');expect(changed).toHaveBeenCalledWith(expect.objectContaining({host:'10.10.10.50',port:11112,called_ae:'JIVEX'}))})

it('data table supports keyboard row selection',async()=>{const selected=vi.fn();render(<DataTable columns={[{key:'name',header:'Name',render:(row:{name:string})=>row.name}]} rows={[{name:'PACS Test'}]} getKey={row=>row.name} onRowClick={selected}/>);screen.getByText('PACS Test').closest('tr')?.focus();await userEvent.keyboard('{Enter}');expect(selected).toHaveBeenCalledWith({name:'PACS Test'})})

it('shows transfer success and technical log',()=>{const result={success:true,status:'0x0000',duration_ms:42,steps:['Association accepted']};render(<><TransferProgress loading={false} result={result} hasFile/><DicomLogViewer result={result} context={{target:'10.10.10.50:104'}}/></>);expect(screen.getByText('Abgeschlossen')).toBeVisible();expect(screen.getByLabelText('DICOM Log')).toHaveTextContent('Association accepted')})
