export type Target={id:number;name:string;host:string;mwl_enabled:boolean;mwl_port:number|null;mwl_called_ae:string|null;store_enabled:boolean;store_port:number|null;store_called_ae:string|null;default_calling_ae:string;created_at:string;updated_at:string}
export type Endpoint={host:string;port:number;called_ae:string;calling_ae:string;target_id?:number|null}
export type DicomElement={tag:string;name:string;vr:string;value:string|DicomElement[][]}
export type WorklistEntry={patient_name:string;patient_id:string;birth_date:string;accession_number:string;modality:string;station_ae:string;start_date:string;start_time:string;sps_description:string;requested_procedure_description:string;dataset:DicomElement[]}
export type Result={success:boolean;status?:string;code?:string;message?:string;duration_ms:number;steps?:string[];count?:number;entries?:WorklistEntry[];active_filters?:Record<string,string>;[key:string]:unknown}
export type Run={id:number;test_type:string;target_id:number|null;manual_target_json:Endpoint|null;started_at:string;duration_ms:number;success:boolean;status:string;result_json:Result}

async function request<T>(path:string,init?:RequestInit):Promise<T>{const response=await fetch(`/api${path}`,{...init,headers:init?.body instanceof FormData?init.headers:{'Content-Type':'application/json',...init?.headers}});if(!response.ok){const body=await response.json().catch(()=>({detail:response.statusText}));throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail))}return response.status===204?undefined as T:response.json()}
export const api={
  targets:()=>request<Target[]>('/targets'),
  createTarget:(target:Omit<Target,'id'|'created_at'|'updated_at'>)=>request<Target>('/targets',{method:'POST',body:JSON.stringify(target)}),
  updateTarget:(id:number,target:Omit<Target,'id'|'created_at'|'updated_at'>)=>request<Target>(`/targets/${id}`,{method:'PUT',body:JSON.stringify(target)}),
  deleteTarget:(id:number)=>request<void>(`/targets/${id}`,{method:'DELETE'}),
  echo:(endpoint:Endpoint)=>request<Result>('/dicom/echo',{method:'POST',body:JSON.stringify(endpoint)}),
  mwl:(payload:Endpoint&{broad:boolean;filters:Record<string,string|null>})=>request<Result>('/dicom/mwl',{method:'POST',body:JSON.stringify(payload)}),
  store:(payload:Endpoint&{sop_class:string;transfer_syntax:string})=>request<Result>('/dicom/store/generated',{method:'POST',body:JSON.stringify(payload)}),
  analyzeUpload:(data:FormData)=>request<Record<string,string>>('/dicom/store/analyze',{method:'POST',body:data}),
  storeUpload:(data:FormData)=>request<Result>('/dicom/store/upload',{method:'POST',body:data}),
  runs:()=>request<Run[]>('/test-runs'),run:(id:string)=>request<Run>(`/test-runs/${id}`)
}
