import {Navigate,Route,Routes} from 'react-router-dom'
import {AppShell} from './components/layout/AppShell'
import {Dashboard} from './pages/Dashboard'
import {History,HistoryDetail} from './pages/History'
import {Help} from './pages/Help'
import {Modalities} from './pages/Modalities'
import {SettingsPage} from './pages/Settings'
import {StudyQuery} from './pages/StudyQuery'
import {Store} from './pages/Store'
import {Topology} from './pages/Topology'
import {UiShowcase} from './pages/UiShowcase'
import {Worklist} from './pages/Worklist'

export default function App(){return <AppShell><Routes><Route path="/" element={<Dashboard/>}/><Route path="/help" element={<Help/>}/><Route path="/worklist" element={<Worklist/>}/><Route path="/pacs-store" element={<Store/>}/><Route path="/store" element={<Navigate to="/pacs-store" replace/>}/><Route path="/pacs-query" element={<StudyQuery/>}/><Route path="/systems" element={<Topology/>}/><Route path="/targets" element={<Topology/>}/><Route path="/modalities" element={<Modalities/>}/><Route path="/history" element={<History/>}/><Route path="/history/:id" element={<HistoryDetail/>}/><Route path="/settings" element={<SettingsPage/>}/><Route path="/dev/ui" element={<UiShowcase/>}/></Routes></AppShell>}
