export type Target={id:number;name:string;host:string;mwl_enabled:boolean;mwl_port:number|null;mwl_called_ae:string|null;store_enabled:boolean;store_port:number|null;store_called_ae:string|null;qr_enabled?:boolean;qr_port?:number|null;qr_called_ae?:string|null;default_calling_ae:string;created_at:string;updated_at:string}
export type TargetTestStatus={target_id:number;run_id:number;test_type:string;started_at:string;duration_ms:number;success:boolean;status:string;configuration_state:'current'|'changed'|'unknown'}
export type Endpoint={host:string;port:number;called_ae:string;calling_ae:string;target_id?:number|null}
export type DicomElement={tag:string;name:string;vr:string;value:string|DicomElement[][]}
export type WorklistEntry={patient_name:string;patient_id:string;birth_date:string;accession_number:string;modality:string;station_ae:string;start_date:string;start_time:string;sps_description:string;requested_procedure_description:string;dataset:DicomElement[]}
export type StudyEntry={patient_name:string;patient_id:string;accession_number:string;study_date:string;study_time:string;study_description:string;study_instance_uid:string;modalities:string;series_count:number;instance_count:number;dataset:DicomElement[]}
export type Result={success:boolean;status?:string;code?:string;message?:string;recommendation?:string;duration_ms:number;steps?:string[];count?:number;entries?:WorklistEntry[];active_filters?:Record<string,string>;[key:string]:unknown}
export type StudyQueryResult={success:boolean;status?:string;code?:string;message?:string;recommendation?:string;duration_ms:number;steps?:string[];count?:number;entries?:StudyEntry[];active_filters?:Record<string,string>;run_id?:number}
export type Run={id:number;test_type:string;target_id:number|null;manual_target_json:Endpoint|null;target_snapshot_json?:Endpoint&{name?:string}|null;started_at:string;duration_ms:number;success:boolean;status:string;result_json:Result}
export type HistoryPage={items:Run[];total:number;limit:number;offset:number}
export type DashboardSummary={today_total:number;today_success:number;by_type:Record<string,number>}
export type HistoryFilters={test_type?:string;success?:boolean;search?:string;limit?:number;offset?:number}
export type ModalityProfile={id:number;name:string;description:string|null;modality:'CT'|'MR'|'US'|'CR'|'DX'|'OT'|'XA'|'MG'|'NM'|'PT';calling_ae:string;mwl_enabled:boolean;mwl_target_id:number|null;store_enabled:boolean;store_target_id:number|null;created_at:string;updated_at:string}
export type ModalityProfileDraft=Omit<ModalityProfile,'id'|'created_at'|'updated_at'>
export type ModalityServiceResult=Result&{skipped?:boolean;association?:boolean;target_name?:string;query?:Record<string,string>;diagnostic_retry?:Result&{without_station_ae?:boolean};observation?:string;sop_class?:string;transfer_syntax?:string;fallback_secondary_capture?:boolean}
export type ModalityCheckResult=Result&{overall:'success'|'failure';profile_id:number;profile_name:string;modality:string;calling_ae:string;worklist:ModalityServiceResult;store:ModalityServiceResult;run_id:number}
export type ConfigurationExport={format_version:1;exported_at?:string;targets:Array<Omit<Target,'id'|'created_at'|'updated_at'>>;modality_profiles:Array<{name:string;description:string|null;modality:ModalityProfile['modality'];calling_ae:string;mwl_enabled:boolean;mwl_target_name:string|null;store_enabled:boolean;store_target_name:string|null}>}
export type ImportSummary={created_targets:number;updated_targets:number;created_profiles:number;updated_profiles:number}

async function request<T>(path:string,init?:RequestInit):Promise<T>{const response=await fetch(`/api${path}`,{...init,headers:init?.body instanceof FormData?init.headers:{'Content-Type':'application/json',...init?.headers}});if(!response.ok){const body=await response.json().catch(()=>({detail:response.statusText}));throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail))}return response.status===204?undefined as T:response.json()}
async function requestBlob(path:string):Promise<Blob>{const response=await fetch(`/api${path}`);if(!response.ok)throw new Error(response.statusText);return response.blob()}
function queryString(values:Record<string,string|number|boolean|undefined>){const params=new URLSearchParams();Object.entries(values).forEach(([key,value])=>{if(value!==undefined&&value!=='')params.set(key,String(value))});const query=params.toString();return query?`?${query}`:''}
export const api={
  targets:()=>request<Target[]>('/targets'),
  targetStatuses:()=>request<TargetTestStatus[]>('/targets/test-status'),
  createTarget:(target:Omit<Target,'id'|'created_at'|'updated_at'>)=>request<Target>('/targets',{method:'POST',body:JSON.stringify(target)}),
  updateTarget:(id:number,target:Omit<Target,'id'|'created_at'|'updated_at'>)=>request<Target>(`/targets/${id}`,{method:'PUT',body:JSON.stringify(target)}),
  deleteTarget:(id:number)=>request<void>(`/targets/${id}`,{method:'DELETE'}),
  modalityProfiles:()=>request<ModalityProfile[]>('/modality-profiles'),
  modalityProfile:(id:number)=>request<ModalityProfile>(`/modality-profiles/${id}`),
  createModalityProfile:(profile:ModalityProfileDraft)=>request<ModalityProfile>('/modality-profiles',{method:'POST',body:JSON.stringify(profile)}),
  updateModalityProfile:(id:number,profile:ModalityProfileDraft)=>request<ModalityProfile>(`/modality-profiles/${id}`,{method:'PUT',body:JSON.stringify(profile)}),
  deleteModalityProfile:(id:number)=>request<void>(`/modality-profiles/${id}`,{method:'DELETE'}),
  checkModalityProfile:(id:number,transfer_syntax='explicit_vr_little_endian',signal?:AbortSignal)=>request<ModalityCheckResult>(`/modality-profiles/${id}/check`,{method:'POST',body:JSON.stringify({transfer_syntax}),signal}),
  echo:(endpoint:Endpoint)=>request<Result>('/dicom/echo',{method:'POST',body:JSON.stringify(endpoint)}),
  mwl:(payload:Endpoint&{broad:boolean;filters:Record<string,string|null>})=>request<Result>('/dicom/mwl',{method:'POST',body:JSON.stringify(payload)}),
  studies:(payload:Endpoint&{filters:Record<string,string|null>})=>request<StudyQueryResult>('/dicom/studies',{method:'POST',body:JSON.stringify(payload)}),
  store:(payload:Endpoint&{sop_class:string;transfer_syntax:string})=>request<Result>('/dicom/store/generated',{method:'POST',body:JSON.stringify(payload)}),
  analyzeUpload:(data:FormData)=>request<Record<string,string>>('/dicom/store/analyze',{method:'POST',body:data}),
  storeUpload:(data:FormData)=>request<Result>('/dicom/store/upload',{method:'POST',body:data}),
  runs:()=>request<Run[]>('/test-runs?limit=6'),run:(id:string)=>request<Run>(`/test-runs/${id}`),
  dashboardSummary:(dayStart:string,dayEnd:string)=>request<DashboardSummary>(`/dashboard/summary${queryString({day_start:dayStart,day_end:dayEnd})}`),
  history:(filters:HistoryFilters)=>request<HistoryPage>(`/test-runs/search${queryString(filters)}`),
  exportHistory:(filters:HistoryFilters)=>requestBlob(`/test-runs/export.csv${queryString(filters)}`),
  exportConfiguration:()=>request<ConfigurationExport>('/configuration/export'),
  importConfiguration:(configuration:ConfigurationExport)=>request<ImportSummary>('/configuration/import',{method:'POST',body:JSON.stringify(configuration)}),
  purgeHistory:(days:number)=>request<{deleted_count:number;cutoff:string}>('/maintenance/history-retention',{method:'POST',body:JSON.stringify({days})}),
  databaseBackup:()=>requestBlob('/maintenance/database-backup'),
}
