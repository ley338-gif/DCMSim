import {ArrowRight,BookOpen,Clock3,Server} from 'lucide-react'
import {Link} from 'react-router-dom'
import {PageHeader} from '../components/layout/PageHeader'
import {SectionCard} from '../components/ui/Card'
import {AlertBox} from '../components/ui/Feedback'

export function Help(){
 return <>
  <PageHeader title="Hilfe & Schnellstart" subtitle="DCMSim sicher einrichten, testen und Ergebnisse richtig einordnen"/>
  <div className="help-grid">
   <SectionCard title="In drei Schritten starten" subtitle="Ein gespeichertes Ziel ist praktisch, manuelle Eingaben bleiben möglich.">
    <ol className="help-steps">
     <li><strong>Ziel einrichten</strong><span>Host, Dienst-Port sowie Calling und Called AE prüfen.</span><Link to="/targets">Ziele öffnen <ArrowRight size={15}/></Link></li>
     <li><strong>Passenden DICOM-Test ausführen</strong><span>Worklist abfragen, ein synthetisches Bild senden oder Studien suchen.</span><div className="help-links"><Link to="/worklist">Worklist</Link><Link to="/pacs-store">PACS Store</Link><Link to="/pacs-query">PACS-Suche</Link></div></li>
     <li><strong>Ergebnis nachvollziehen</strong><span>Statuscode, Antwortzeit und technische Details in der Historie ansehen.</span><Link to="/history">Historie öffnen <ArrowRight size={15}/></Link></li>
    </ol>
   </SectionCard>
   <SectionCard title="Status richtig verstehen">
    <div className="help-facts">
     <p><Server size={18}/><span><strong>Ein Ziel ist nicht dauerhaft „online“.</strong> Der Status zeigt nur den letzten zugeordneten Einzeltest. Nach einer Konfigurationsänderung ist ein neuer Test nötig.</span></p>
     <p><Clock3 size={18}/><span><strong>Keine Hintergrundüberwachung.</strong> DCMSim startet Tests nur auf Anforderung; es gibt weder Scheduler noch automatische Benachrichtigungen.</span></p>
     <p><BookOpen size={18}/><span><strong>Bei Fehlern zuerst die Details öffnen.</strong> Host, Port, AE-Titel, Statuscode und die empfohlene Diagnose mit der Gegenstelle abgleichen.</span></p>
    </div>
   </SectionCard>
  </div>
  <SectionCard title="Sicherer Betrieb und Grenzen">
   <AlertBox tone="warning">DCMSim hat keine Benutzeranmeldung. Nur in einem vertrauenswürdigen internen Netz betreiben und den Zugang über die Infrastruktur begrenzen.</AlertBox>
   <div className="help-facts">
    <p>Hochgeladene DICOM-Dateien können Patientendaten enthalten. Sie werden flüchtig verarbeitet; die Testhistorie speichert nur datensparsame technische Angaben.</p>
    <p>Unterstützt werden C-ECHO, Modality Worklist C-FIND, Study Root C-FIND auf Studienebene und C-STORE. C-MOVE, C-GET, Storage Commitment und ein produktiver Storage SCP sind nicht enthalten.</p>
   </div>
  </SectionCard>
 </>
}
