import {DicomElement} from '../api/client'
function Element({item,depth=0}:{item:DicomElement;depth?:number}){return <div className="tag" style={{paddingLeft:depth*18}}><span>{item.tag}</span> <b>{item.name}</b>{Array.isArray(item.value)?item.value.flat().map((child,i)=><Element key={i} item={child} depth={depth+1}/>):<code>{item.value||'—'}</code>}</div>}
export function TechnicalDetails({data,title='Technische Details'}:{data:unknown;title?:string}){const elements=Array.isArray(data)?data as DicomElement[]:null;return <details className="technical"><summary>{title}</summary>{elements?elements.map((item,i)=><Element key={i} item={item}/>):<pre>{JSON.stringify(data,null,2)}</pre>}</details>}

