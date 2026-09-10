import {Result} from '../api/client'
import {TechnicalDetails} from './TechnicalDetails'
export function ResultPanel({result}:{result:Result}){return <section className={`result ${result.success?'ok':'bad'}`}><div className="result-title"><span className="status-dot"/>{result.success?'Test erfolgreich':result.message??'Test fehlgeschlagen'}<strong>{result.status??result.code}</strong></div>{result.steps&&<ol className="steps">{result.steps.map(step=><li key={step}>✓ {step}</li>)}</ol>}<div className="metrics"><span>Antwortzeit <b>{result.duration_ms} ms</b></span>{result.count!==undefined&&<span>Treffer <b>{result.count}</b></span>}</div>{!result.success&&result.code&&<p className="error-code mono">{result.code}</p>}<TechnicalDetails data={result}/></section>}

