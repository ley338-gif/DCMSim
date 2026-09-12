import {ReactNode,useState} from 'react'
import {CircleHelp,Clock3,Home,Menu,Search,Server,Settings,ShieldAlert,Stethoscope,UploadCloud,X} from 'lucide-react'
import {Link,NavLink} from 'react-router-dom'
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
export function AppShell({children}:{children:ReactNode}){
 const [mobileOpen,setMobileOpen]=useState(false)
 return <div className="app-shell">
  <a className="skip-link" href="#main-content">Zum Inhalt springen</a>
  <aside className={mobileOpen?'sidebar sidebar--open':'sidebar'}>
   <Link className="sidebar__brand" to="/" aria-label="Zur Übersicht" onClick={()=>setMobileOpen(false)}><img src="/DCMSim-Logo-dark.png" alt="DCMSim"/></Link>
   <nav aria-label="Hauptnavigation">{navigation.map(item=>{const Icon=item.icon;return <NavLink key={item.to} to={item.to} end={item.end} onClick={()=>setMobileOpen(false)}><Icon size={20}/><span>{item.label}</span></NavLink>})}</nav>
   <div className="sidebar__footer"><p><span className="ready-dot"/>DCMSim bereit</p><small>Version 0.3.20</small><small>© 2026 DCMSim</small></div>
  </aside>
  <div className="app-frame">
   <div className="topbar">
    <Button variant="ghost" className="mobile-menu" aria-label="Navigation öffnen" aria-expanded={mobileOpen} icon={mobileOpen?<X/>:<Menu/>} onClick={()=>setMobileOpen(!mobileOpen)}/>
    <div className="topbar__spacer"/>
    <Link className="topbar__link" to="/help" aria-label="Hilfe öffnen"><CircleHelp size={19}/><span>Hilfe</span></Link>
    <Link className="topbar__link" to="/history" aria-label="Test-Historie öffnen"><Clock3 size={19}/><span>Test-Historie</span></Link>
    <span className="topbar__security" title="Keine Anmeldung: nur in vertrauenswürdigen internen Netzen betreiben"><ShieldAlert size={18}/>Ohne Anmeldung</span>
   </div>
   <main id="main-content" tabIndex={-1} className="main-content">{children}</main>
  </div>
 </div>
}
