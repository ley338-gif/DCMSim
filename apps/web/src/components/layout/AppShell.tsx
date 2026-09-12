import {ReactNode,useState} from 'react'
import {Bell,ChevronDown,CircleHelp,Clock3,Home,Menu,Search,Server,Settings,Stethoscope,UploadCloud,X} from 'lucide-react'
import {NavLink} from 'react-router-dom'
import {Button} from '../ui/Button'

const navigation=[
 {to:'/',label:'Übersicht',icon:Home,end:true},
 {to:'/worklist',label:'Worklist',icon:Menu},
 {to:'/pacs-store',label:'PACS Store',icon:UploadCloud},
 {to:'/pacs-query',label:'PACS-Suche',icon:Search},
 {to:'/targets',label:'Ziele',icon:Server},
 {to:'/modalities',label:'Modalitäten',icon:Stethoscope},
 {to:'/history',label:'Historie',icon:Clock3},
 {to:'/settings',label:'Einstellungen',icon:Settings},
]
export function AppShell({children}:{children:ReactNode}){const [mobileOpen,setMobileOpen]=useState(false);return <div className="app-shell"><a className="skip-link" href="#main-content">Zum Inhalt springen</a><aside className={mobileOpen?'sidebar sidebar--open':'sidebar'}><div className="sidebar__brand"><img src="/DCMSim-Logo-dark.png" alt="DCMSim"/></div><nav aria-label="Hauptnavigation">{navigation.map(item=>{const Icon=item.icon;return <NavLink key={item.to} to={item.to} end={item.end} onClick={()=>setMobileOpen(false)}><Icon size={20}/><span>{item.label}</span></NavLink>})}</nav><div className="sidebar__footer"><p><span className="ready-dot"/>DCMSim bereit</p><small>Version 0.3.5</small><small>© 2026 DCMSim</small></div></aside><div className="app-frame"><div className="topbar"><Button variant="ghost" className="mobile-menu" aria-label="Navigation öffnen" aria-expanded={mobileOpen} icon={mobileOpen?<X/>:<Menu/>} onClick={()=>setMobileOpen(!mobileOpen)}/><div className="topbar__spacer"/><Button variant="ghost" aria-label="Hilfe" icon={<CircleHelp size={19}/>}/><Button variant="ghost" aria-label="Benachrichtigungen" icon={<Bell size={19}/>}/><span className="avatar">AD</span><span className="user-name">Admin</span><ChevronDown size={16}/></div><main id="main-content" tabIndex={-1} className="main-content">{children}</main></div></div>}
