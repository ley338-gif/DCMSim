import {NavLink,Route,Routes} from 'react-router-dom'
import {Dashboard} from './pages/Dashboard'
import {Worklist} from './pages/Worklist'
import {Store} from './pages/Store'
import {Targets} from './pages/Targets'
import {History,HistoryDetail} from './pages/History'
const links=[['/','Übersicht'],['/worklist','Worklist'],['/store','PACS Store'],['/targets','Ziele'],['/history','Historie']]
export default function App(){return <div className="shell"><aside><div className="brand"><span>DCM</span>Sim<small>DICOM Troubleshooting</small></div><nav>{links.map(([to,label])=><NavLink key={to} to={to} end={to==='/'}>{label}</NavLink>)}</nav><footer>Local only · v0.1.0</footer></aside><main><Routes><Route path="/" element={<Dashboard/>}/><Route path="/worklist" element={<Worklist/>}/><Route path="/store" element={<Store/>}/><Route path="/targets" element={<Targets/>}/><Route path="/history" element={<History/>}/><Route path="/history/:id" element={<HistoryDetail/>}/></Routes></main></div>}

