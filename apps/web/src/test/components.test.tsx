import {render,screen} from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {EndpointFields} from '../components/EndpointFields'
import {ResultPanel} from '../components/ResultPanel'
import {TechnicalDetails} from '../components/TechnicalDetails'

const target={id:1,name:'JiveX Test',host:'127.0.0.1',mwl_enabled:true,mwl_port:11112,mwl_called_ae:'MWL',store_enabled:true,store_port:11113,store_called_ae:'PACS',default_calling_ae:'DCMSIM',created_at:'',updated_at:''}

it('selects a saved target and fills its worklist endpoint',async()=>{const changed=vi.fn();render(<EndpointFields value={{host:'',port:104,called_ae:'',calling_ae:'DCMSIM'}} onChange={changed} targets={[target]} service="mwl"/>);await userEvent.selectOptions(screen.getByLabelText('Quelle'),'1');expect(changed).toHaveBeenCalledWith(expect.objectContaining({host:'127.0.0.1',port:11112,called_ae:'MWL'}))})

it('renders technical dataset elements',async()=>{render(<TechnicalDetails data={[{tag:'(0010,0020)',name:'Patient ID',vr:'LO',value:'DCMSIM-TEST-0001'}]}/>);await userEvent.click(screen.getByText('Technische Details'));expect(screen.getByText('DCMSIM-TEST-0001')).toBeVisible()})

it('renders a presentation context failure with stable code',()=>{render(<ResultPanel result={{success:false,code:'DICOM_NO_PRESENTATION_CONTEXT',message:'No acceptable presentation context',duration_ms:20}}/>);expect(screen.getByText('No acceptable presentation context')).toBeVisible();expect(screen.getAllByText('DICOM_NO_PRESENTATION_CONTEXT').length).toBeGreaterThan(0)})

