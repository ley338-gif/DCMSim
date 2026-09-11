import {useMemo,useState} from 'react'
import {Result} from '../../api/client'
import {CopyButton,DownloadButton} from '../ui/Disclosure'
import {Toggle} from '../ui/Form'

function buildDicomLog(result:Result|undefined,context:Record<string,string|number|undefined>={}){const now=new Date().toLocaleTimeString('de-DE',{hour12:false});const lines=[`[${now}] Initializing DICOM operation`,context.target?`[${now}] Target: ${context.target}`:'',context.calling?`[${now}] Calling AE: ${context.calling}`:'',context.called?`[${now}] Called AE: ${context.called}`:'',...(result?.steps??[]).map(step=>`[${now}] ${step}`),result?.status?`[${now}] Response status: ${result.status}`:'',result?.code?`[${now}] Error: ${result.code}`:'',result?`[${now}] Operation ${result.success?'completed successfully':'failed'}`:''].filter(Boolean);return lines.join('\n')}
export function DicomLogViewer({result,context}:{result?:Result;context?:Record<string,string|number|undefined>}){const [live,setLive]=useState(true);const log=useMemo(()=>buildDicomLog(result,context),[result,context]);return <div className="log-viewer"><div className="log-toolbar"><Toggle label="Live Log" checked={live} onChange={e=>setLive(e.target.checked)}/><CopyButton value={log}/><DownloadButton value={log} filename="dcmsim-dicom.log"/></div><pre aria-label="DICOM Log">{log||'[bereit] Warte auf DICOM-Test …'}</pre></div>}
