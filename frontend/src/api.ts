const fragment = new URLSearchParams(location.hash.slice(1));
const token = fragment.get('session') ?? sessionStorage.getItem('vtd-session') ?? '';
if (token) sessionStorage.setItem('vtd-session',token);
if (fragment.has('session')) history.replaceState(null,'',location.pathname);

/** Секрет доступен только локальному окну; FormData отправляется без ручного Content-Type. */
export async function request<T>(path:string, init:RequestInit={}):Promise<T> {
  const response = await fetch(`/api${path}`,{...init,headers:{...init.headers,'X-VTD-Session':token}});
  if (!response.ok) {
    const body = await response.json().catch(()=>({detail:`HTTP ${response.status}`}));
    throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));
  }
  return response.json();
}
export async function downloadReport(id:string) {
  const response=await fetch(`/api/projects/${id}/export`,{headers:{'X-VTD-Session':token}});
  if(!response.ok) throw new Error('Не удалось экспортировать отчёт');
  const url=URL.createObjectURL(await response.blob());
  const a=document.createElement('a');a.href=url;a.download='vtd-results.xlsx';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
