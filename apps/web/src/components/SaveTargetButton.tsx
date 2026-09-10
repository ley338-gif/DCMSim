import {useState} from 'react'
import {useQueryClient} from '@tanstack/react-query'
import {api,Endpoint} from '../api/client'

export function SaveTargetButton({endpoint,service}:{endpoint:Endpoint;service:'mwl'|'store'}){
 const client=useQueryClient();const [saved,setSaved]=useState(false)
 if(endpoint.target_id||saved)return null
 const save=async()=>{const name=window.prompt('Name für das neue Ziel:');if(!name)return;await api.createTarget({name,host:endpoint.host,mwl_enabled:service==='mwl',mwl_port:service==='mwl'?endpoint.port:null,mwl_called_ae:service==='mwl'?endpoint.called_ae:null,store_enabled:service==='store',store_port:service==='store'?endpoint.port:null,store_called_ae:service==='store'?endpoint.called_ae:null,default_calling_ae:endpoint.calling_ae});setSaved(true);client.invalidateQueries({queryKey:['targets']})}
 return <button type="button" className="ghost" onClick={save}>{saved?'Ziel gespeichert':'Als Ziel speichern'}</button>
}
