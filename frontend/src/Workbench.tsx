import {useEffect,useMemo,useState} from 'react';
import {Alert,Button,Empty,Input,Select,Space,Table,Tabs,Tag} from 'antd';
import type {TableProps} from 'antd';
import {Navigation,type Page} from './components/Navigation';
import {ImportWorkbook} from './components/ImportWorkbook';
import {CalculationCard} from './components/CalculationCard';
import {request,downloadReport} from './api';
import type {Project,RecordDefect} from './types/project';

/** Рабочая область использует только проекты API. Демонстрационные fixtures не импортируются. */
export default function Workbench(){
  const [page,setPage]=useState<Page>('upload');
  const [projects,setProjects]=useState<{id:string;name:string}[]>([]);
  const [project,setProject]=useState<Project|null>(null);
  const [selected,setSelected]=useState<string|null>(null);
  const [open,setOpen]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [tab,setTab]=useState('all');
  const [query,setQuery]=useState('');
  const [pipe,setPipe]=useState<string>();
  const [category,setCategory]=useState<string>();
  const [side,setSide]=useState<string>();
  const [kind,setKind]=useState<string>();
  const [section,setSection]=useState<string>();
  const [model,setModel]=useState<string>();
  const [pagination,setPagination]=useState({current:1,pageSize:15});
  const reset=()=>{setQuery('');setPipe(undefined);setCategory(undefined);setSide(undefined);setKind(undefined);setSection(undefined);setModel(undefined);setPagination(p=>({...p,current:1}));};
  async function load(id:string){setBusy(true);setError('');try{setProject(await request<Project>(`/projects/${id}`));reset();setSelected(null);setOpen(false);setPage('registry');}catch(e){setError(String(e));}finally{setBusy(false);}}
  useEffect(()=>{request<{id:string;name:string}[]>('/projects').then(setProjects).catch(e=>setError(String(e)));},[]);
  async function imported(p:Project){setProject(p);setProjects(await request('/projects'));reset();setPage('registry');}
  async function recalculate(){if(!project)return;setBusy(true);setError('');try{setProject(await request<Project>(`/projects/${project.id}/recalculate`,{method:'POST'}));}catch(e){setError(String(e));}finally{setBusy(false);}}
  async function rm3(evidence:string){if(!project||!selected)return;setBusy(true);setError('');try{setProject(await request<Project>(`/projects/${project.id}/dents/${encodeURIComponent(selected)}/rm3`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({evidence})}));}catch(e){setError(String(e));}finally{setBusy(false);}}
  const filtered=useMemo(()=>(project?.defects??[]).filter(d=>(tab==='all'||(tab==='dent'?d.kind==='dent':d.kind!=='dent'))&&
    (!query||d.sourceId.includes(query.trim())||d.members?.some(m=>m.sourceId.includes(query.trim())))&&(!pipe||d.pipeNumber===pipe)&&(!category||d.result.category===category)&&(!side||d.side===side)&&(!kind||d.kind===kind)&&(!section||String(d.raw.id_mu)===section)&&(!model||d.result.model===model)),[project,tab,query,pipe,category,side,kind,section,model]);
  useEffect(()=>{setPagination(p=>({...p,current:1}));},[category,side,kind,section,model]);
  const num=(v:number|null)=>v==null?'—':v.toLocaleString('ru-RU',{maximumFractionDigits:6});
  const statuses:Record<string,string>={provisional:'Предварительный расчёт',invalid:'Ошибка данных',needs_parameters:'Недостаточно данных',needs_group:'Взаимодействующие дефекты'};
  const columns:TableProps<RecordDefect>['columns']=[
    {title:'ID',dataIndex:'sourceId',sorter:(a,b)=>a.sourceId.localeCompare(b.sourceId)},
    {title:'Тип',render:(_,d)=>d.kind==='dent'?'Вмятина':d.kind==='group'?'Группа':'Коррозия'},
    {title:'№ трубы',dataIndex:'pipeNumber',sorter:(a,b)=>a.pipeNumber.localeCompare(b.pipeNumber,'ru',{numeric:true})},
    ...(['positionM','lengthMm','widthMm','depthMm'] as const).map((key,i)=>({title:['Положение, м','Длина, мм','Ширина, мм','Глубина, мм'][i],dataIndex:key,render:num,sorter:(a:RecordDefect,b:RecordDefect)=>(a[key]??-1)-(b[key]??-1)})),
    {title:'Режим',dataIndex:'side'},
    {title:'Модель',render:(_,d)=>d.result.model??(d.kind==='dent'?'Не выбрана':'СТО')},
    {title:'Разруш. давление, МПа',render:(_,d)=>num(d.result.pressureMpa),sorter:(a,b)=>(a.result.pressureMpa??-1)-(b.result.pressureMpa??-1)},
    {title:'Категория',render:(_,d)=>d.result.category?<Tag color="orange">{d.result.category} · предвар.</Tag>:'—'},
    {title:'Статус',render:(_,d)=><Tag color={d.result.status==='invalid'?'red':'gold'}>{statuses[d.result.status]??d.result.status}</Tag>}];
  return <div className="app"><header className="topbar"><div className="brand"><span className="brand-mark">В</span><div><strong>ВТД Аналитика</strong><small className="brand-description">Локальное приложение</small></div></div>
    <Space><span>Проект</span><Select style={{width:420}} placeholder="Импортируйте Excel" value={project?.id} options={projects.map(p=>({value:p.id,label:p.name}))} onChange={load}/></Space><Tag color="blue">Данные на устройстве</Tag></header>
    <div className="app-body"><Navigation page={page} onChange={setPage}/><main>
      {error&&<Alert closable onClose={()=>setError('')} type="error" showIcon title="Ошибка" description={error}/>}
      {page==='upload'?<ImportWorkbook onImported={imported}/>:page==='methodology'?<section className="surface"><h1>Методика и происхождение данных</h1><p>СТО Lamart 2-2.3-112-2007; приложение В ТЗ; методика вмятин.</p><p>В карточке каждой записи доступны исходные ячейки, выбранные параметры и промежуточные результаты. Категория из исходной БД сохраняется отдельно от вычисленной.</p>{project?.assumptions.map(a=><Alert key={a} style={{marginBottom:12}} type="warning" title={a}/>)}</section>:<>
      <div className="page-heading"><div><h1>Общий реестр дефектов</h1><p>{project?.name??'Проект не выбран'}</p></div><Space><Button onClick={()=>setPage('upload')}>Загрузить Excel</Button><Button disabled={!project} loading={busy} onClick={recalculate}>Пересчитать</Button><Button disabled={!project} onClick={()=>project&&downloadReport(project.id).catch(e=>setError(String(e)))}>Экспорт Excel</Button></Space></div>
      {project&&<Alert type="warning" showIcon title="Расчёты на реальных данных с явными допущениями" description={project.assumptions.join(' ')}/>}
      {!!project?.errors.length&&<Alert type="error" title={`Ошибки данных: ${project.errors.length}`} description={project.errors.slice(0,4).map(e=>`Строка ${e.row}: ${e.message}`).join('; ')}/>}
      <Tabs activeKey={tab} onChange={v=>{setTab(v);setPagination(p=>({...p,current:1}));}} items={[{key:'all',label:'Все дефекты'},{key:'corrosion',label:'Коррозия'},{key:'dent',label:'Вмятины'}]}/>
      <Space wrap style={{marginBottom:20}}><Input.Search aria-label="Поиск по ID" placeholder="Поиск по ID" value={query} onChange={e=>{setQuery(e.target.value);setPagination(p=>({...p,current:1}));}}/>
        <Select allowClear placeholder="Участок (id_mu)" style={{width:180}} value={section} onChange={setSection} options={[...new Set(project?.defects.map(d=>String(d.raw.id_mu)))].map(v=>({value:v,label:v}))}/>
        <Select allowClear placeholder="Модель вмятины" style={{width:180}} value={model} onChange={setModel} options={['РМ1','РМ2','РМ3'].map(v=>({value:v,label:v}))}/>
        <Select allowClear placeholder="Труба" style={{width:150}} value={pipe} onChange={v=>{setPipe(v);setPagination(p=>({...p,current:1}));}} options={[...new Set(project?.defects.map(d=>d.pipeNumber))].map(p=>({value:p,label:p}))}/>
        <Select allowClear placeholder="Категория" style={{width:150}} value={category} onChange={setCategory} options={['A','B','C'].map(v=>({value:v,label:v+' (предвар.)'}))}/>
        <Select allowClear placeholder="Режим" style={{width:150}} value={side} onChange={setSide} options={[{value:'EXT',label:'Наружная'},{value:'INT',label:'Внутренняя'}]}/>
        <Select allowClear placeholder="Тип расчёта" style={{width:180}} value={kind} onChange={setKind} options={[{value:'single',label:'Одиночная коррозия'},{value:'group',label:'Групповая коррозия'},{value:'dent',label:'Вмятина'}]}/><Button onClick={reset}>Сбросить</Button></Space>
      <Table className="defect-table" loading={busy} rowKey="id" columns={columns} dataSource={filtered} scroll={{x:1450}} rowClassName={d=>d.id===selected?'selected-row':''}
        expandable={{rowExpandable:d=>!!d.members?.length,expandedRowRender:d=><Table rowKey="id" size="small" pagination={false} columns={columns} dataSource={d.members} onRow={m=>({onClick:()=>{setSelected(m.id);setOpen(true);}})}/>}}
        onRow={d=>({onClick:()=>{setSelected(d.id);setOpen(true);}})} pagination={{...pagination,showSizeChanger:true,showTotal:n=>`Найдено: ${n}`,onChange:(current,pageSize)=>setPagination({current,pageSize})}}
        locale={{emptyText:<Empty description="Нет записей. Загрузите Excel или измените фильтры."/>}}/>
      </>}
    </main></div><CalculationCard key={selected} defect={open?project?.defects.flatMap(d=>[d,...(d.members??[])]).find(d=>d.id===selected)??null:null} onClose={()=>setOpen(false)} onRecalculate={recalculate} busy={busy} onRm3={rm3}/></div>;
}
